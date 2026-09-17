"use client";

import { useState } from "react";
import { FileSearch, Gavel, AlertTriangle } from "lucide-react";
import api from "@/lib/api";
import { useAuthGuard } from "@/lib/useAuthGuard";
import { CaseAnalysisOut } from "@/types";

const severityColor: Record<string, string> = {
  Low: "bg-green-100 text-green-700",
  Moderate: "bg-yellow-100 text-yellow-700",
  High: "bg-orange-100 text-orange-700",
  Severe: "bg-red-100 text-red-700",
};

export default function CaseAnalysisPage() {
  const { ready } = useAuthGuard();
  const [summary, setSummary] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CaseAnalysisOut | null>(null);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    setResult(null);
    try {
      const { data } = await api.post<CaseAnalysisOut>("/cases/analyze", {
        case_summary: summary,
        case_category: category || null,
      });
      setResult(data);
    } catch (err) {
      setError("Could not analyze the case. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  if (!ready) return null;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center gap-2 mb-1 text-brand-700">
        <FileSearch className="w-6 h-6" />
        <h1 className="text-2xl font-bold">BNS Case Analysis & Penalty Predictor</h1>
      </div>
      <p className="text-slate-500 mb-6">
        Describe the incident in plain language. Our AI will identify applicable BNS
        sections, penalties, bail status, and overall severity.
      </p>

      <form onSubmit={handleSubmit} className="card space-y-4 mb-8">
        <div>
          <label className="block text-sm font-medium mb-1">Case Summary</label>
          <textarea
            required
            minLength={20}
            rows={6}
            className="input-field"
            placeholder="e.g. On the night of 12 August, the accused forcibly entered the complainant's house and took jewellery worth ₹2,00,000 while threatening the family with a knife..."
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Category (optional)</label>
          <input
            type="text"
            className="input-field"
            placeholder="e.g. theft, assault, cybercrime"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2">
          <Gavel className="w-4 h-4" />
          {loading ? "Analyzing..." : "Analyze Case"}
        </button>
      </form>

      {result && (
        <div className="space-y-6">
          <div className="card">
            <div className="flex items-center justify-between mb-2">
              <h2 className="font-semibold text-lg">Overall Severity</h2>
              <span
                className={`text-sm font-medium px-3 py-1 rounded-full ${
                  severityColor[result.predicted_sections.overall_severity] || "bg-slate-100"
                }`}
              >
                {result.predicted_sections.overall_severity}
              </span>
            </div>
            <p className="text-slate-600 text-sm">{result.predicted_sections.severity_explanation}</p>
          </div>

          <div className="card">
            <h2 className="font-semibold text-lg mb-4">Applicable BNS Sections</h2>
            <div className="space-y-3">
              {result.predicted_sections.applicable_sections.map((s, i) => (
                <div key={i} className="border border-slate-200 rounded-lg p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
                    <p className="font-semibold text-brand-700">
                      {s.section_number} — {s.section_title}
                    </p>
                    <div className="flex gap-2">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          s.bailable === "Bailable" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                        }`}
                      >
                        {s.bailable}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                        {s.cognizable}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-slate-600 mb-2">{s.description}</p>
                  <div className="flex flex-wrap gap-4 text-xs text-slate-500">
                    <span><strong>Punishment:</strong> {s.punishment}</span>
                    <span><strong>Imprisonment:</strong> {s.imprisonment_term}</span>
                    <span><strong>Relevance:</strong> {(s.relevance_score * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h2 className="font-semibold text-lg mb-3">Recommended Next Steps</h2>
            <ul className="list-disc list-inside space-y-1 text-sm text-slate-600">
              {result.predicted_sections.recommended_next_steps.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ul>
          </div>

          <div className="flex items-start gap-2 text-xs text-slate-400 bg-slate-100 rounded-lg p-3">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <p>{result.predicted_sections.disclaimer}</p>
          </div>
        </div>
      )}
    </div>
  );
}
