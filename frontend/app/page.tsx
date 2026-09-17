"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileSearch, FileText, ShieldCheck, Clock } from "lucide-react";
import api from "@/lib/api";
import { useAuthGuard } from "@/lib/useAuthGuard";
import { CaseAnalysisOut, PetitionOut } from "@/types";

export default function DashboardPage() {
  const { user, ready } = useAuthGuard();
  const [cases, setCases] = useState<CaseAnalysisOut[]>([]);
  const [petitions, setPetitions] = useState<PetitionOut[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ready) return;
    (async () => {
      try {
        const [casesRes, petitionsRes] = await Promise.all([
          api.get<CaseAnalysisOut[]>("/cases/history"),
          api.get<PetitionOut[]>("/petitions/history"),
        ]);
        setCases(casesRes.data);
        setPetitions(petitionsRes.data);
      } finally {
        setLoading(false);
      }
    })();
  }, [ready]);

  if (!ready) return null;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">Welcome back{user ? `, ${user.full_name}` : ""}</h1>
      <p className="text-slate-500 mb-8">Here's a summary of your recent legal activity.</p>

      <div className="grid sm:grid-cols-3 gap-4 mb-10">
        <Link href="/case-analysis" className="card hover:shadow-md transition-shadow">
          <FileSearch className="w-6 h-6 text-brand-600 mb-2" />
          <p className="font-semibold">New Case Analysis</p>
          <p className="text-sm text-slate-500">Predict applicable BNS sections</p>
        </Link>
        <Link href="/petition-generator" className="card hover:shadow-md transition-shadow">
          <FileText className="w-6 h-6 text-brand-600 mb-2" />
          <p className="font-semibold">Generate Petition</p>
          <p className="text-sm text-slate-500">Auto-draft a formal petition</p>
        </Link>
        <Link href="/petition-scanner" className="card hover:shadow-md transition-shadow">
          <ShieldCheck className="w-6 h-6 text-brand-600 mb-2" />
          <p className="font-semibold">Scan Petition</p>
          <p className="text-sm text-slate-500">Validate an existing draft</p>
        </Link>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-5 h-5 text-slate-400" />
            <h2 className="font-semibold text-lg">Recent Case Analyses</h2>
          </div>
          {loading ? (
            <p className="text-sm text-slate-400">Loading...</p>
          ) : cases.length === 0 ? (
            <p className="text-sm text-slate-400">No case analyses yet.</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {cases.slice(0, 5).map((c) => (
                <li key={c.id} className="py-3">
                  <p className="text-sm font-medium line-clamp-2">{c.case_summary}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-brand-50 text-brand-700">
                      {c.predicted_sections?.overall_severity || "N/A"}
                    </span>
                    <span className="text-xs text-slate-400">
                      {new Date(c.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-5 h-5 text-slate-400" />
            <h2 className="font-semibold text-lg">Recent Petitions</h2>
          </div>
          {loading ? (
            <p className="text-sm text-slate-400">Loading...</p>
          ) : petitions.length === 0 ? (
            <p className="text-sm text-slate-400">No petitions yet.</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {petitions.slice(0, 5).map((p) => (
                <li key={p.id} className="py-3">
                  <p className="text-sm font-medium line-clamp-1">{p.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 capitalize">
                      {p.source_type}
                    </span>
                    {p.scan_result && (
                      <span className="text-xs text-slate-500">
                        Validity: {p.scan_result.validity_score}/100
                      </span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
