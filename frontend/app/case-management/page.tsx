"use client";

import { useEffect, useState } from "react";
import { Gavel, Plus, CalendarClock } from "lucide-react";
import api from "@/lib/api";
import { useAuthGuard } from "@/lib/useAuthGuard";
import { CaseRecord, CaseStatus } from "@/types";

const STATUS_OPTIONS: CaseStatus[] = ["Pending", "Adjourned", "Reserved for Orders", "Disposed", "Dismissed"];

const statusColor: Record<CaseStatus, string> = {
  "Pending": "bg-blue-100 text-blue-700",
  "Adjourned": "bg-amber-100 text-amber-700",
  "Reserved for Orders": "bg-purple-100 text-purple-700",
  "Disposed": "bg-green-100 text-green-700",
  "Dismissed": "bg-slate-200 text-slate-600",
};

const emptyForm = {
  case_number: "",
  court_name: "",
  petitioner_name: "",
  respondent_name: "",
  filing_date: "",
  next_hearing_date: "",
  status: "Pending" as CaseStatus,
  stage_notes: "",
};

export default function CaseManagementPage() {
  const { ready } = useAuthGuard();
  const [cases, setCases] = useState<CaseRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(emptyForm);

  async function loadCases() {
    setLoading(true);
    try {
      const { data } = await api.get<CaseRecord[]>("/case-management/");
      setCases(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (ready) loadCases();
  }, [ready]);

  function update<K extends keyof typeof form>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleAddCase(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/case-management/", {
        ...form,
        filing_date: form.filing_date || null,
        next_hearing_date: form.next_hearing_date || null,
      });
      setForm(emptyForm);
      setShowForm(false);
      await loadCases();
    } finally {
      setSaving(false);
    }
  }

  async function handleStatusChange(id: string, status: CaseStatus) {
    await api.patch(`/case-management/${id}`, { status });
    await loadCases();
  }

  if (!ready) return null;

  const ongoingCount = cases.filter((c) => c.is_ongoing).length;
  const closedCount = cases.length - ongoingCount;

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-1">
        <div className="flex items-center gap-2 text-brand-700">
          <Gavel className="w-6 h-6" />
          <h1 className="text-2xl font-bold">Digital Case Management</h1>
        </div>
        <button onClick={() => setShowForm((v) => !v)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Track New Case
        </button>
      </div>
      <p className="text-slate-500 mb-6">
        Track whether your cases are still ongoing in court, or have already been disposed.
      </p>

      <div className="grid sm:grid-cols-2 gap-4 mb-6">
        <div className="card flex items-center gap-3">
          <div className="text-3xl font-bold text-blue-600">{ongoingCount}</div>
          <div className="text-sm text-slate-500">Case(s) still ongoing in court</div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="text-3xl font-bold text-green-600">{closedCount}</div>
          <div className="text-sm text-slate-500">Case(s) closed (disposed/dismissed)</div>
        </div>
      </div>

      {showForm && (
        <form onSubmit={handleAddCase} className="card space-y-4 mb-8">
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Case Number</label>
              <input required className="input-field" value={form.case_number}
                onChange={(e) => update("case_number", e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Court Name</label>
              <input required className="input-field" value={form.court_name}
                onChange={(e) => update("court_name", e.target.value)} />
            </div>
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
            <div>
              <label className="block text-sm font-medium mb-1">Filing Date</label>
              <input type="date" className="input-field" value={form.filing_date}
                onChange={(e) => update("filing_date", e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Next Hearing Date</label>
              <input type="date" className="input-field" value={form.next_hearing_date}
                onChange={(e) => update("next_hearing_date", e.target.value)} />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Current Status</label>
            <select className="input-field" value={form.status}
              onChange={(e) => update("status", e.target.value)}>
              {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Notes (optional)</label>
            <textarea rows={2} className="input-field" value={form.stage_notes}
              onChange={(e) => update("stage_notes", e.target.value)} />
          </div>
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? "Saving..." : "Save Case"}
          </button>
        </form>
      )}

      {loading ? (
        <p className="text-sm text-slate-400">Loading...</p>
      ) : cases.length === 0 ? (
        <p className="text-sm text-slate-400">No cases tracked yet. Click &quot;Track New Case&quot; to add one.</p>
      ) : (
        <div className="space-y-3">
          {cases.map((c) => (
            <div key={c.id} className="card">
              <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                <div>
                  <p className="font-semibold text-brand-700">{c.case_number}</p>
                  <p className="text-sm text-slate-500">{c.court_name}</p>
                </div>
                <span className={`text-xs px-3 py-1 rounded-full font-medium ${statusColor[c.status]}`}>
                  {c.is_ongoing ? "Ongoing" : "Closed"} — {c.status}
                </span>
              </div>
              <p className="text-sm text-slate-600 mb-2">{c.petitioner_name} vs {c.respondent_name}</p>
              {c.next_hearing_date && (
                <p className="text-xs text-slate-500 flex items-center gap-1 mb-2">
                  <CalendarClock className="w-3.5 h-3.5" />
                  Next hearing: {new Date(c.next_hearing_date).toLocaleDateString()}
                </p>
              )}
              {c.stage_notes && <p className="text-sm text-slate-500 italic mb-3">{c.stage_notes}</p>}
              <div className="flex items-center gap-2">
                <label className="text-xs text-slate-500">Update status:</label>
                <select
                  className="text-sm border border-slate-300 rounded-lg px-2 py-1"
                  value={c.status}
                  onChange={(e) => handleStatusChange(c.id, e.target.value as CaseStatus)}
                >
                  {STATUS_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}