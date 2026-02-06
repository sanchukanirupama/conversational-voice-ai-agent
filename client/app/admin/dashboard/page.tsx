"use client";
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function AdminDashboardPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to configuration page by default
    router.push('/admin/dashboard/config');
  }, [router]);

  return (
    <div className="flex items-center justify-center h-screen">
      <p className="text-white/60">Redirecting...</p>
    </div>
  );
}
