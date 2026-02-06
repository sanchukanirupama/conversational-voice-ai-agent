"use client";
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/app/hooks/useAuth';
import { LogOut, Settings, Activity } from 'lucide-react';
import Link from 'next/link';

export default function AdminDashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/admin/login');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen w-full bg-[#0A0A0A] flex items-center justify-center">
        <div className="text-white/60">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const handleLogout = () => {
    logout();
    router.push('/admin/login');
  };

  return (
    <div className="min-h-screen w-full bg-black flex">
      {/* Sidebar */}
      <aside className="w-64 bg-neutral-950 border-r border-white/10 flex flex-col">
        {/* Logo/Header */}
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Dashboard</h1>
              <p className="text-xs text-white/40">ABC Bank AI</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          <Link
            href="/admin/dashboard/config"
            className="flex items-center gap-3 px-4 py-3 text-white/60 hover:text-white hover:bg-emerald-500/10 hover:border-emerald-500/20 border border-transparent rounded-xl transition-all group"
          >
            <Settings className="w-5 h-5 group-hover:text-emerald-400 transition-colors" />
            <span className="font-medium">Configuration</span>
          </Link>

          <Link
            href="/admin/dashboard/calls"
            className="flex items-center gap-3 px-4 py-3 text-white/60 hover:text-white hover:bg-emerald-500/10 hover:border-emerald-500/20 border border-transparent rounded-xl transition-all group"
          >
            <Activity className="w-5 h-5 group-hover:text-emerald-400 transition-colors" />
            <span className="font-medium">Live Calls</span>
          </Link>
        </nav>

        {/* Logout Button */}
        <div className="p-4 border-t border-white/10">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-4 py-3 text-white/60 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 rounded-xl transition-all"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-black">
        {children}
      </main>
    </div>
  );
}
