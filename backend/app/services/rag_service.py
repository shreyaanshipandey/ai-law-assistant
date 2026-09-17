"""
BNS Knowledge Base RAG service.

Loads the BNS sections CSV into a pandas DataFrame and builds an
in-memory FAISS vector index (via LangChain) over each section's text,
so that `retrieve()` can pull the top-k most relevant sections for a
given case summary before handing them to the LLM as grounding context.

The CSV can be replaced/extended at runtime through the admin
"Upload BNS CSV" endpoint (api/routes/bns_kb.py), which calls
`kb.reload_from_path()` or `kb.reload_from_dataframe()`.

Column handling:
- REQUIRED: section_number, section_title, description — every real BNS
  export (including the official bare-act text) has these.
- OPTIONAL: punishment, imprisonment_term, bailable, cognizable — many
  raw BNS exports (e.g. scraped bare-act text) don't carry these as
  separate structured fields; that classification data (bailable/
  cognizable/punishment) actually lives in the BNS First Schedule, not
  in the section text itself. When these columns are absent or blank,
  we leave them blank in the record and instead tell the LLM (in
  ai_service.py) to read the full section description and determine
  punishment/imprisonment/bailability/cognizability from its own
  knowledge of the BNS First Schedule, clearly labelling that as
  AI-inferred rather than sourced verbatim from the CSV.
"""
from __future__ import annotations

import re
import threading

import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings

REQUIRED_COLUMNS = {"section_number", "section_title", "description"}
OPTIONAL_COLUMNS = ["punishment", "imprisonment_term", "bailable", "cognizable"]
# Extra columns some exports include (e.g. official bare-act scrapes) — kept as metadata if present.
PASSTHROUGH_COLUMNS = ["Chapter", "Chapter_name", "Chapter_subtype"]

ALL_COLUMNS = ["section_number", "section_title", "description", *OPTIONAL_COLUMNS, *PASSTHROUGH_COLUMNS]


def _clean_text(value: object) -> str:
    """Collapses embedded newlines/whitespace so text reads cleanly in prompts and search results."""
    text = "" if value is None else str(value)
    return re.sub(r"\s+", " ", text).strip()


class BNSKnowledgeBase:
    """Thread-safe singleton wrapping the current BNS DataFrame + vector store."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.df: pd.DataFrame = pd.DataFrame(columns=ALL_COLUMNS)
        self.vector_store: FAISS | None = None
        self._embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY or None,
            base_url=settings.OPENAI_BASE_URL or None,
            check_embedding_ctx_length=False,  # Gemini's compat endpoint doesn't support this tiktoken check
            chunk_size=90,
        )

    def reload_from_path(self, csv_path: str) -> int:
        df = pd.read_csv(csv_path)
        return self.reload_from_dataframe(df)

    def reload_from_dataframe(self, df: pd.DataFrame) -> int:
        df = df.rename(columns=lambda c: c.strip())
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

        # Fill any missing optional/passthrough columns so downstream code can rely on their presence.
        for col in OPTIONAL_COLUMNS + PASSTHROUGH_COLUMNS:
            if col not in df.columns:
                df[col] = ""

        df = df.fillna("")
        # Normalise section_number to a consistent "BNS <n>" display form when it's a bare number.
        df["section_number"] = df["section_number"].apply(
            lambda v: f"BNS {v}" if str(v).strip().isdigit() else str(v).strip()
        )
        df["section_title"] = df["section_title"].apply(_clean_text)
        df["description"] = df["description"].apply(_clean_text)
        for col in OPTIONAL_COLUMNS:
            df[col] = df[col].apply(_clean_text)

        with self._lock:
            self.df = df.reset_index(drop=True)
            documents = []
            for _, row in self.df.iterrows():
                extra_bits = []
                if row["punishment"]:
                    extra_bits.append(f"Punishment (source data): {row['punishment']}.")
                if row["imprisonment_term"]:
                    extra_bits.append(f"Imprisonment term (source data): {row['imprisonment_term']}.")
                if row["bailable"]:
                    extra_bits.append(f"Bailable (source data): {row['bailable']}.")
                if row["cognizable"]:
                    extra_bits.append(f"Cognizable (source data): {row['cognizable']}.")
                extra_text = " ".join(extra_bits)

                content = f"{row['section_number']} - {row['section_title']}: {row['description']} {extra_text}".strip()
                documents.append(Document(page_content=content, metadata=row.to_dict()))

            if documents:
                self.vector_store = FAISS.from_documents(documents, self._embeddings)
            else:
                self.vector_store = None
        return len(self.df)

    def retrieve(self, query: str, k: int = 6) -> list[dict]:
        """Return top-k BNS section dicts most relevant to the query text."""
        with self._lock:
            store = self.vector_store
        if store is None:
            # Fallback: no embeddings available -> keyword-overlap ranking
            # (NOT just "first row that matches any word" — that used to always
            # surface generic sections like BNS 1-4 since they contain common words).
            return self._keyword_fallback_retrieve(query, k)

        results = store.similarity_search(query, k=k)
        return [doc.metadata for doc in results]

    _STOPWORDS = {
        "the", "a", "an", "of", "to", "in", "on", "and", "or", "is", "are", "was",
        "were", "be", "by", "for", "with", "at", "from", "that", "this", "it",
        "as", "his", "her", "their", "he", "she", "they", "any", "who", "whoever",
        "shall", "which", "not", "such", "may", "if", "than", "into",
    }

    def _keyword_fallback_retrieve(self, query: str, k: int) -> list[dict]:
        if self.df.empty:
            return []

        query_tokens = {
            tok.lower().strip(".,;:()")
            for tok in query.split()
            if len(tok) > 2 and tok.lower() not in self._STOPWORDS
        }
        if not query_tokens:
            return []

        def score_row(row) -> int:
            haystack = (str(row["description"]) + " " + str(row["section_title"])).lower()
            return sum(1 for tok in query_tokens if tok in haystack)

        scored = self.df.copy()
        scored["_score"] = scored.apply(score_row, axis=1)
        scored = scored[scored["_score"] > 0].sort_values("_score", ascending=False)
        return scored.head(k).drop(columns="_score").to_dict(orient="records")

    def as_records(self) -> list[dict]:
        return self.df.to_dict(orient="records")


# Singleton instance used across the app
knowledge_base = BNSKnowledgeBase()


def bootstrap_default_kb() -> None:
    """Called on app startup to load the bundled seed CSV."""
    import traceback

    try:
        count = knowledge_base.reload_from_path(settings.BNS_CSV_PATH)
        vs_status = "vector search (embeddings) ACTIVE" if knowledge_base.vector_store else \
            "⚠️ FALLING BACK to keyword search — embeddings failed to build silently"
        print(f"[BNS KB] Loaded {count} BNS sections from {settings.BNS_CSV_PATH} — {vs_status}")
    except Exception as exc:  # noqa: BLE001 - log and continue, don't crash startup
        print(f"[BNS KB] Could not load default CSV ({settings.BNS_CSV_PATH}): {exc}")
        traceback.print_exc()