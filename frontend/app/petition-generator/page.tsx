"use client";

import { useState } from "react";
import { FileText, Download, Sparkles } from "lucide-react";
import api from "@/lib/api";
import { useAuthGuard } from "@/lib/useAuthGuard";
import { PetitionOut } from "@/types";

export default function PetitionGeneratorPage() {
  const { ready } = useAuthGuard();
  const [form, setForm] = useState({
    petitioner_name: "",
    respondent_name: "",
    court_name: "",
    case_summary: "",
    relief_sought: "",
    applicable_sections: "",
  });
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState<"pdf" | "docx" | null>(null);
  const [result, setResult] = useState<PetitionOut | null>(null);
  const [error, setError] = useState("");

  function update<K extends keyof typeof form>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    setResult(null);
    try {
      const { data } = await api.post<PetitionOut>("/petitions/generate", {
        petitioner_name: form.petitioner_name,
        respondent_name: form.respondent_name,
        court_name: form.court_name,
        case_summary: form.case_summary,
        relief_sought: form.relief_sought,
        applicable_sections: form.applicable_sections
          ? form.applicable_sections.split(",").map((s) => s.trim())
          : null,
      });
      setResult(data);
    } catch (err) {
      setError("Could not generate the petition. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDownload(format: "pdf" | "docx") {
    if (!result) return;
    setDownloading(format);
    try {
      const response = await api.get(`/petitions/${result.id}/download`, {
        params: { file_format: format },
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${result.title}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      setDownloading(null);
    }
  }

  if (!ready) return null;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center gap-2 mb-1 text-brand-700">
        <FileText className="w-6 h-6" />
        <h1 className="text-2xl font-bold">Automated Petition Draft Generator</h1>
      </div>
      <p className="text-slate-500 mb-6">
        Fill in the case details and let the AI draft a formal legal petition, ready to
        download as PDF or Word.
      </p>

      <form onSubmit={handleSubmit} className="card space-y-4 mb-8">
        <div className="grid sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Petitioner Name</label>
            <input required className="input-field" value={form.petitioner_name}
              onChange={(e) => update("petitioner_name", e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Respondent Name</label>
            <input required className="input-field" value={form.respondent_name}
              onChange={(e) => update("respondent_name", e.target.value)} />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Court Name</label>
          <input required className="input-field" placeholder="e.g. Court of the Chief Judicial Magistrate, Indore"
            value={form.court_name} onChange={(e) => update("court_name", e.target.value)} />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Case Summary / Facts</label>
          <textarea required minLength={20} rows={5} className="input-field"
            value={form.case_summary} onChange={(e) => update("case_summary", e.target.value)} />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Relief Sought</label>
          <textarea required rows={3} className="input-field"
            placeholder="e.g. Direct registration of FIR under applicable BNS sections and immediate protection order"
            value={form.relief_sought} onChange={(e) => update("relief_sought", e.target.value)} />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Applicable Sections (optional, comma-separated)</label>
          <input className="input-field" placeholder="e.g. BNS 303, BNS 351"
            value={form.applicable_sections} onChange={(e) => update("applicable_sections", e.target.value)} />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
          <Sparkles className="w-4 h-4" />
          {loading ? "Drafting petition..." : "Generate Petition"}
        </button>
      </form>

      {result && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-lg">{result.title}</h2>
            <div className="flex gap-2">
              <button
                onClick={() => handleDownload("pdf")}
                disabled={downloading !== null}
                className="btn-secondary text-sm flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" />
                {downloading === "pdf" ? "..." : "PDF"}
              </button>
              <button
                onClick={() => handleDownload("docx")}
                disabled={downloading !== null}
                className="btn-secondary text-sm flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" />
                {downloading === "docx" ? "..." : "Word"}
              </button>
            </div>
          </div>
          <pre className="whitespace-pre-wrap text-sm font-sans text-slate-700 leading-relaxed max-h-[600px] overflow-y-auto border border-slate-200 rounded-lg p-4 bg-slate-50">
            {result.content_text}
          </pre>
        </div>
      )}
    </div>
  );
}
