"use client";

import { useEffect, useMemo, useState } from "react";
import { PhoneCall, Search } from "lucide-react";
import api from "@/lib/api";
import { Helpline } from "@/types";

export default function HelplinesPage() {
  const [helplines, setHelplines] = useState<Helpline[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const [helplinesRes, categoriesRes] = await Promise.all([
        api.get("/helplines/"),
        api.get<string[]>("/helplines/categories"),
      ]);
      setHelplines(helplinesRes.data.helplines);
      setCategories(categoriesRes.data);
      setLoading(false);
    })();
  }, []);

  const filtered = useMemo(() => {
    return helplines.filter((h) => {
      const matchesQuery =
        !query ||
        h.name.toLowerCase().includes(query.toLowerCase()) ||
        h.description.toLowerCase().includes(query.toLowerCase());
      const matchesCategory = !activeCategory || h.category === activeCategory;
      return matchesQuery && matchesCategory;
    });
  }, [helplines, query, activeCategory]);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center gap-2 mb-1 text-brand-700">
        <PhoneCall className="w-6 h-6" />
        <h1 className="text-2xl font-bold">Government Helpline Directory</h1>
      </div>
      <p className="text-slate-500 mb-6">
        Quick access to essential Indian legal and emergency helplines.
      </p>

      <div className="relative mb-4">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          className="input-field pl-9"
          placeholder="Search helplines..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={() => setActiveCategory(null)}
          className={`text-xs px-3 py-1.5 rounded-full font-medium ${
            !activeCategory ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600"
          }`}
        >
          All
        </button>
        {categories.map((c) => (
          <button
            key={c}
            onClick={() => setActiveCategory(c)}
            className={`text-xs px-3 py-1.5 rounded-full font-medium ${
              activeCategory === c ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600"
            }`}
          >
            {c}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-sm text-slate-400">Loading...</p>
      ) : (
        <div className="grid sm:grid-cols-2 gap-4">
          {filtered.map((h) => (
            <div key={h.name + h.number} className="card">
              <div className="flex items-start justify-between mb-1">
                <p className="font-semibold">{h.name}</p>
                <span className="text-xs px-2 py-0.5 rounded-full bg-brand-50 text-brand-700 shrink-0">
                  {h.available}
                </span>
              </div>
              <p className="text-2xl font-bold text-brand-600 mb-1">{h.number}</p>
              <p className="text-sm text-slate-500">{h.description}</p>
              <p className="text-xs text-slate-400 mt-2">{h.category}</p>
            </div>
          ))}
          {filtered.length === 0 && (
            <p className="text-sm text-slate-400 col-span-2">No helplines match your search.</p>
          )}
        </div>
      )}
    </div>
  );
}
