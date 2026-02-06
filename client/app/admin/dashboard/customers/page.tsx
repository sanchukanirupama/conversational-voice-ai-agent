"use client";
import { useState, useEffect } from 'react';
import { Users, RefreshCw, Search, CreditCard, CheckCircle, XCircle } from 'lucide-react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Customer {
  id: string;
  name: string;
  account_number: string;
  phone: string;
  balance: number;
  card_id: string;
  card_status: string;
}

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [filteredCustomers, setFilteredCustomers] = useState<Customer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCustomers();
  }, []);

  useEffect(() => {
    if (searchQuery) {
      const filtered = customers.filter(customer =>
        customer.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        customer.account_number.includes(searchQuery) ||
        customer.phone.includes(searchQuery) ||
        customer.id.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredCustomers(filtered);
    } else {
      setFilteredCustomers(customers);
    }
  }, [searchQuery, customers]);

  const fetchCustomers = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('admin_token');
      const response = await fetch(`${API_BASE_URL}/admin/customers`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setCustomers(data.customers);
        setFilteredCustomers(data.customers);
      } else {
        setError('Failed to load customers');
      }
    } catch (error) {
      setError('Error loading customers');
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-white/60">Loading customers...</div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Users className="w-8 h-8" />
            Customer Database
          </h1>
          <p className="text-white/50 mt-1">
            {filteredCustomers.length} {filteredCustomers.length === 1 ? 'customer' : 'customers'}
            {searchQuery && ` matching "${searchQuery}"`}
          </p>
        </div>
        <button
          onClick={fetchCustomers}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 text-white rounded-xl transition-all disabled:opacity-50"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name, account number, phone, or customer ID..."
            className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50 transition-all"
          />
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Customer Table */}
      <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left px-6 py-4 text-sm font-semibold text-white/70">Customer ID</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-white/70">Name</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-white/70">Account</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-white/70">Phone</th>
                <th className="text-right px-6 py-4 text-sm font-semibold text-white/70">Balance</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-white/70">Card Status</th>
                <th className="text-left px-6 py-4 text-sm font-semibold text-white/70">Card ID</th>
              </tr>
            </thead>
            <tbody>
              {filteredCustomers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center px-6 py-12 text-white/40">
                    {searchQuery ? 'No customers found matching your search' : 'No customers in database'}
                  </td>
                </tr>
              ) : (
                filteredCustomers.map((customer) => (
                  <tr
                    key={customer.id}
                    className="border-b border-white/5 hover:bg-white/5 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <code className="text-sm text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">
                        {customer.id}
                      </code>
                    </td>
                    <td className="px-6 py-4 text-white font-medium">{customer.name}</td>
                    <td className="px-6 py-4">
                      <code className="text-sm text-blue-400 bg-blue-500/10 px-2 py-1 rounded">
                        {customer.account_number}
                      </code>
                    </td>
                    <td className="px-6 py-4 text-white/70">{customer.phone}</td>
                    <td className="px-6 py-4 text-right">
                      <span className={`font-semibold ${
                        customer.balance > 0 ? 'text-green-400' : 'text-white/60'
                      }`}>
                        {formatCurrency(customer.balance)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {customer.card_status === 'active' ? (
                          <>
                            <CheckCircle className="w-4 h-4 text-green-400" />
                            <span className="text-green-400 text-sm font-medium">Active</span>
                          </>
                        ) : (
                          <>
                            <XCircle className="w-4 h-4 text-red-400" />
                            <span className="text-red-400 text-sm font-medium">Blocked</span>
                          </>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {customer.card_id ? (
                        <div className="flex items-center gap-2 text-white/70">
                          <CreditCard className="w-4 h-4" />
                          <span className="text-sm">{customer.card_id}</span>
                        </div>
                      ) : (
                        <span className="text-white/30 text-sm">No card</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Footer with count */}
        {filteredCustomers.length > 0 && (
          <div className="px-6 py-4 border-t border-white/10 bg-white/[0.02]">
            <p className="text-sm text-white/50">
              Showing {filteredCustomers.length} of {customers.length} customers
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
