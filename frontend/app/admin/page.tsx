"use client";

import { useEffect, useRef, useState } from "react";
import { ShieldCheck, Users, BarChart3, UploadCloud, Trash2 } from "lucide-react";
import api from "@/lib/api";
import { useAuthGuard } from "@/lib/useAuthGuard";
import { User } from "@/types";

interface Stats {
  total_users: number;
  total_case_analyses: number;
  total_petitions: number;
}

export default function AdminPage() {
  const { user, ready } = useAuthGuard();
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploadMsg, setUploadMsg] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!ready) return;
    if (user && user.role !== "admin") {
      window.location.href = "/dashboard";
      return;
    }
    (async () => {
      const [usersRes, statsRes] = await Promise.all([
        api.get<User[]>("/admin/users"),
        api.get<Stats>("/admin/stats"),
      ]);
      setUsers(usersRes.data);
      setStats(statsRes.data);
      setLoading(false);
    })();
  }, [ready, user]);

  async function toggleActive(u: User) {
    const { data } = await api.patch<User>(`/admin/users/${u.id}`, { is_active: !u.is_active });
    setUsers((prev) => prev.map((x) => (x.id === u.id ? data : x)));
  }

  async function deleteUser(u: User) {
    if (!confirm(`Delete user ${u.email}? This cannot be undone.`)) return;
    await api.delete(`/admin/users/${u.id}`);
    setUsers((prev) => prev.filter((x) => x.id !== u.id));
  }

  async function handleCsvUpload(file: File) {
    setUploading(true);
    setUploadMsg("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await api.post("/bns-kb/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadMsg(`✓ ${data.message} (${data.sections_loaded} sections loaded)`);
    } catch (err) {
      setUploadMsg("✗ Upload failed. Check the CSV format and required columns.");
    } finally {
      setUploading(false);
    }
  }

  if (!ready || loading) return null;

  return (
    <div>
      <div className="flex items-center gap-2 mb-6 text-amber-700">
        <ShieldCheck className="w-6 h-6" />
        <h1 className="text-2xl font-bold">Admin Dashboard</h1>
      </div>

      <div className="grid sm:grid-cols-3 gap-4 mb-8">
        <div className="card flex items-center gap-3">
          <Users className="w-8 h-8 text-brand-600" />
          <div>
            <p className="text-2xl font-bold">{stats?.total_users}</p>
            <p className="text-sm text-slate-500">Total Users</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <BarChart3 className="w-8 h-8 text-brand-600" />
          <div>
            <p className="text-2xl font-bold">{stats?.total_case_analyses}</p>
            <p className="text-sm text-slate-500">Case Analyses</p>
          </div>
        </div>
        <div className="card flex items-center gap-3">
          <BarChart3 className="w-8 h-8 text-brand-600" />
          <div>
            <p className="text-2xl font-bold">{stats?.total_petitions}</p>
            <p className="text-sm text-slate-500">Petitions</p>
          </div>
        </div>
      </div>

      <div className="card mb-8">
        <h2 className="font-semibold text-lg mb-3">Update BNS Knowledge Base (CSV)</h2>
        <p className="text-sm text-slate-500 mb-4">
          Required columns: section_number, section_title, description, punishment,
          imprisonment_term, bailable, cognizable.
        </p>
        <div className="flex items-center gap-3">
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleCsvUpload(e.target.files[0])}
          />
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="btn-primary flex items-center gap-2"
          >
            <UploadCloud className="w-4 h-4" />
            {uploading ? "Uploading..." : "Upload CSV"}
          </button>
          {uploadMsg && <p className="text-sm text-slate-600">{uploadMsg}</p>}
        </div>
      </div>

      <div className="card">
        <h2 className="font-semibold text-lg mb-4">User Management</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="py-2 pr-4">Name</th>
                <th className="py-2 pr-4">Email</th>
                <th className="py-2 pr-4">Role</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2 pr-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-slate-100">
                  <td className="py-2 pr-4">{u.full_name}</td>
                  <td className="py-2 pr-4 text-slate-500">{u.email}</td>
                  <td className="py-2 pr-4 capitalize">{u.role}</td>
                  <td className="py-2 pr-4">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${u.is_active ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"}`}>
                      {u.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="py-2 pr-4 flex gap-2">
                    <button onClick={() => toggleActive(u)} className="btn-secondary text-xs py-1">
                      {u.is_active ? "Deactivate" : "Activate"}
                    </button>
                    <button onClick={() => deleteUser(u)} className="text-red-500 hover:text-red-700">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
