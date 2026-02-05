"use client";
import { useState, useEffect } from 'react';
import { RefreshCw, Phone, User, Clock, CheckCircle, XCircle } from 'lucide-react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ActiveCall {
  call_id: string;
  customer_id: string | null;
  start_time: string;
  duration_seconds: number;
  is_verified: boolean;
  current_flow: string | null;
  message_count: number;
  latest_message: string | null;
}

export default function LiveCallsPage() {
  const [calls, setCalls] = useState<ActiveCall[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCall, setSelectedCall] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchCalls();
    
    if (autoRefresh) {
      const interval = setInterval(fetchCalls, 3000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const fetchCalls = async () => {
    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${API_BASE_URL}/admin/calls/live`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setCalls(data);
        setError(null);
      } else {
        setError('Failed to fetch live calls');
      }
    } catch (error) {
      setError('Error fetching live calls');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatTime = (isoString: string): string => {
    return new Date(isoString).toLocaleTimeString();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-white/60">Loading live calls...</div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Live Call Monitoring</h1>
          <p className="text-white/60 mt-1">Real-time active call tracking</p>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-white/80 text-sm">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="w-4 h-4"
            />
            Auto-refresh (3s)
          </label>
          <button
            onClick={fetchCalls}
            className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-all"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {/* Active Calls Count */}
      <div className="mb-6">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-500/10 border border-green-500/30 rounded-lg">
          <Phone className="w-5 h-5 text-green-400" />
          <span className="text-white font-medium">{calls.length} Active Call{calls.length !== 1 ? 's' : ''}</span>
        </div>
      </div>

      {/* Calls List */}
      {calls.length === 0 ? (
        <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-12 text-center">
          <Phone className="w-12 h-12 text-white/30 mx-auto mb-4" />
          <p className="text-white/60 text-lg">No active calls at the moment</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {calls.map((call) => (
            <div
              key={call.call_id}
              className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-6 hover:bg-white/10 transition-all cursor-pointer"
              onClick={() => setSelectedCall(selectedCall === call.call_id ? null : call.call_id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 grid grid-cols-2 md:grid-cols-4 gap-4">
                  {/* Customer Info */}
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <User className="w-4 h-4 text-white/50" />
                      <span className="text-xs text-white/50">Customer</span>
                    </div>
                    <p className="text-white font-medium">
                      {call.customer_id || 'Not verified'}
                    </p>
                  </div>

                  {/* Duration */}
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Clock className="w-4 h-4 text-white/50" />
                      <span className="text-xs text-white/50">Duration</span>
                    </div>
                    <p className="text-white font-medium font-mono">
                      {formatDuration(call.duration_seconds)}
                    </p>
                  </div>

                  {/* Verification Status */}
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      {call.is_verified ? (
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-400" />
                      )}
                      <span className="text-xs text-white/50">Status</span>
                    </div>
                    <p className={`font-medium ${call.is_verified ? 'text-green-400' : 'text-red-400'}`}>
                      {call.is_verified ? 'Verified' : 'Not verified'}
                    </p>
                  </div>

                  {/* Message Count */}
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-white/50">Messages</span>
                    </div>
                    <p className="text-white font-medium">
                      {call.message_count} exchanges
                    </p>
                  </div>
                </div>
              </div>

              {/* Latest Message */}
              {call.latest_message && (
                <div className="mt-4 pt-4 border-t border-white/10">
                  <p className="text-xs text-white/50 mb-1">Latest message:</p>
                  <p className="text-white/80 text-sm italic">"{call.latest_message}"</p>
                </div>
              )}

              {/* Call Details (Expandable) */}
              {selectedCall === call.call_id && (
                <div className="mt-4 pt-4 border-t border-white/10">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-white/50">Call ID:</span>
                      <p className="text-white font-mono text-xs mt-1">{call.call_id}</p>
                    </div>
                    <div>
                      <span className="text-white/50">Started at:</span>
                      <p className="text-white mt-1">{formatTime(call.start_time)}</p>
                    </div>
                    {call.current_flow && (
                      <div className="col-span-2">
                        <span className="text-white/50">Current Flow:</span>
                        <p className="text-white mt-1">{call.current_flow}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
