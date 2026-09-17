"use client";

import { useRef, useState } from "react";
import { ShieldCheck, UploadCloud, CheckCircle2, AlertCircle, XCircle } from "lucide-react";
import api from "@/lib/api";
import { useAuthGuard } from "@/lib/useAuthGuard";
import { PetitionOut } from "@/types";

const MAX_SIZE_MB = 10;
const ACCEPTED = [".pdf", ".docx", ".txt"];

const severityStyle: Record<string, { bg: string; icon: typeof AlertCircle }> = {
  High: { bg: "bg-red-50 border-red-200 text-red-700", icon: XCircle },
  Medium: { bg: "bg-amber-50 border-amber-200 text-amber-700", icon: AlertCircle },
  Low: { bg: "bg-blue-50 border-blue-200 text-blue-700", icon: AlertCircle },
};

export default function PetitionScannerPage() {
  const { ready } = useAuthGuard();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PetitionOut | null>(null);
  const [error, setError] = useState("");

  function validateFile(f: File): string | null {
    const ext = "." + f.name.split(".").pop()?.toLowerCase();
    if (!ACCEPTED.includes(ext)) return `Unsupported file type. Allowed: ${ACCEPTED.join(", ")}`;
    if (f.size > MAX_SIZE_MB * 1024 * 1024) return `File exceeds the ${MAX_SIZE_MB}MB limit.`;
    return null;
  }

  function handleFileChange(f: File | null) {
    setError("");
    setResult(null);
    if (!f) return setFile(null);
    const validationError = validateFile(f);
    if (validationError) {
      setError(validationError);
      setFile(null);
      return;
    }
    setFile(f);
  }

  async function handleScan() {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await api.post<PetitionOut>("/petitions/scan", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(data);
    } catch (err) {
      setError("Could not scan the petition. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  if (!ready) return null;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center gap-2 mb-1 text-brand-700">
        <ShieldCheck className="w-6 h-6" />
        <h1 className="text-2xl font-bold">Petition Verification & Document Scanner</h1>
      </div>
      <p className="text-slate-500 mb-6">
        Upload a petition or complaint draft (PDF, DOCX, or TXT — max {MAX_SIZE_MB}MB) to
        check for missing legal points, weak arguments, and formatting issues.
      </p>

      <div
        className="card border-dashed border-2 border-slate-300 text-center py-10 mb-6 cursor-pointer hover:border-brand-400 transition-colors"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          if (e.dataTransfer.files?.[0]) handleFileChange(e.dataTransfer.files[0]);
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED.join(",")}
          className="hidden"
          onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
        />
        <UploadCloud className="w-10 h-10 mx-auto text-slate-400 mb-3" />
        <p className="font-medium text-slate-700">
          {file ? file.name : "Click to upload or drag & drop"}
        </p>
        <p className="text-sm text-slate-400 mt-1">PDF, DOCX, or TXT — up to {MAX_SIZE_MB}MB</p>
      </div>

      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      <button
        onClick={handleScan}
        disabled={!file || loading}
        className="btn-primary flex items-center gap-2 mb-8"
      >
        <ShieldCheck className="w-4 h-4" />
        {loading ? "Scanning..." : "Scan Petition"}
      </button>

      {result?.scan_result && (
        <div className="space-y-6">
          <div className="card flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-lg mb-1">Validity Score</h2>
              <p className="text-sm text-slate-500">{result.scan_result.summary}</p>
            </div>
            <div className="text-4xl font-bold text-brand-600">
              {result.scan_result.validity_score}
              <span className="text-lg text-slate-400">/100</span>
            </div>
          </div>

          {result.scan_result.strengths.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-lg mb-3 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-green-600" /> Strengths
              </h2>
              <ul className="list-disc list-inside space-y-1 text-sm text-slate-600">
                {result.scan_result.strengths.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>
          )}

          <div className="card">
            <h2 className="font-semibold text-lg mb-4">Issues Detected</h2>
            <div className="space-y-3">
              {result.scan_result.issues.map((issue, i) => {
                const style = severityStyle[issue.severity] || severityStyle.Low;
                const Icon = style.icon;
                return (
                  <div key={i} className={`border rounded-lg p-4 ${style.bg}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className="w-4 h-4" />
                      <span className="font-medium text-sm">{issue.category}</span>
                      <span className="text-xs opacity-70">({issue.severity})</span>
                    </div>
                    <p className="text-sm mb-1">{issue.description}</p>
                    <p className="text-sm italic opacity-90">Suggestion: {issue.suggestion}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {result.scan_result.missing_sections_detected.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-lg mb-3">Possibly Missing BNS Sections</h2>
              <div className="flex flex-wrap gap-2">
                {result.scan_result.missing_sections_detected.map((s, i) => (
                  <span key={i} className="text-xs px-3 py-1 rounded-full bg-slate-100 text-slate-700">{s}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
