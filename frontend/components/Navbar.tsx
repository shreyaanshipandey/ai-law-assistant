"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Scale,
  LayoutDashboard,
  FileSearch,
  FileText,
  MessageSquare,
  PhoneCall,
  ShieldCheck,
  Gavel,
  LogOut,
  Menu,
  X,
} from "lucide-react";
import { getStoredUser, isAuthenticated, logoutUser } from "@/lib/auth";
import { User } from "@/types";

const navLinks = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/case-analysis", label: "Case Analysis", icon: FileSearch },
  { href: "/petition-generator", label: "Petition Generator", icon: FileText },
  { href: "/petition-scanner", label: "Petition Scanner", icon: ShieldCheck },
  { href: "/case-management", label: "Case Management", icon: Gavel },
  { href: "/chatbot", label: "Legal Chatbot", icon: MessageSquare },
  { href: "/helplines", label: "Helplines", icon: PhoneCall },
];

export default function Navbar() {
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [authed, setAuthed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    setUser(getStoredUser());
    setAuthed(isAuthenticated());
  }, [pathname]);

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="flex items-center gap-2 font-bold text-brand-700 text-lg">
            <Scale className="w-6 h-6" />
            AI Law Assistant
          </Link>

          {authed && (
            <nav className="hidden md:flex items-center gap-1">
              {navLinks.map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-slate-600 hover:text-brand-700 hover:bg-brand-50 transition-colors"
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </Link>
              ))}
              {user?.role === "admin" && (
                <Link
                  href="/admin"
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-amber-700 hover:bg-amber-50 transition-colors"
                >
                  <ShieldCheck className="w-4 h-4" />
                  Admin
                </Link>
              )}
            </nav>
          )}

          <div className="hidden md:flex items-center gap-3">
            {authed ? (
              <button
                onClick={logoutUser}
                className="flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-red-600"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            ) : (
              <>
                <Link href="/login" className="btn-secondary text-sm">Login</Link>
                <Link href="/register" className="btn-primary text-sm">Sign Up</Link>
              </>
            )}
          </div>

          <button className="md:hidden" onClick={() => setMobileOpen((v) => !v)}>
            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {mobileOpen && (
          <div className="md:hidden pb-4 flex flex-col gap-1">
            {authed &&
              navLinks.map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-slate-600 hover:bg-brand-50"
                  onClick={() => setMobileOpen(false)}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </Link>
              ))}
            {authed ? (
              <button
                onClick={logoutUser}
                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-600"
              >
                <LogOut className="w-4 h-4" /> Logout
              </button>
            ) : (
              <div className="flex gap-2 px-3 pt-2">
                <Link href="/login" className="btn-secondary text-sm flex-1 text-center">Login</Link>
                <Link href="/register" className="btn-primary text-sm flex-1 text-center">Sign Up</Link>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
