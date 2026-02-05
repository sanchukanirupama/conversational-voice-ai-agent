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
    <div className="min-h-screen w-full bg-[#0A0A0A] flex">
      {/* Sidebar */}
      <aside className="w-64 bg-black/40 backdrop-blur-xl border-r border-white/10 flex flex-col">
        {/* Logo/Header */}
        <div className="p-6 border-b border-white/10">
          <h1 className="text-xl font-bold text-white">Admin Dashboard</h1>
          <p className="text-xs text-white/50 mt-1">Bank ABC Voice AI</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          <Link 
            href="/admin/dashboard/config"
            className="flex items-center gap-3 px-4 py-3 text-white/70 hover:text-white hover:bg-white/10 rounded-lg transition-all group"
          >
            <Settings className="w-5 h-5" />
            <span className="font-medium">Configuration</span>
          </Link>
          
          <Link 
            href="/admin/dashboard/calls"
            className="flex items-center gap-3 px-4 py-3 text-white/70 hover:text-white hover:bg-white/10 rounded-lg transition-all group"
          >
            <Activity className="w-5 h-5" />
            <span className="font-medium">Live Calls</span>
          </Link>
        </nav>

        {/* Logout Button */}
        <div className="p-4 border-t border-white/10">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-4 py-3 text-white/70 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
