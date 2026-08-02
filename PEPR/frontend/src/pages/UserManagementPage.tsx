import React, { useState, useEffect } from 'react';
import { Users, UserPlus, UserCheck, CheckCircle2, RefreshCw } from 'lucide-react';
import { api } from '../api/client';
import { Card, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

interface UserRecord {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

export const UserManagementPage: React.FC = () => {

  const [usersList, setUsersList] = useState<UserRecord[]>([]);
  const [isProvisioningOpen, setIsProvisioningOpen] = useState(true);
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newFullName, setNewFullName] = useState('');
  const [newRole, setNewRole] = useState('MANAGEMENT');
  const [userMsg, setUserMsg] = useState<{ text: string; isError?: boolean } | null>(null);
  const [isCreatingUser, setIsCreatingUser] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const data = await api.getUsers();
      setUsersList(data);
    } catch (e) {
      console.error('Failed to fetch users', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreateUserSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setUserMsg(null);
    setIsCreatingUser(true);
    try {
      await api.adminCreateUser({
        email: newEmail,
        password: newPassword,
        full_name: newFullName,
        role: newRole,
      });
      setUserMsg({ text: `Account created successfully! ${newFullName} assigned ${newRole} role.` });
      setNewEmail('');
      setNewPassword('');
      setNewFullName('');
      fetchUsers();
    } catch (err: any) {
      setUserMsg({ text: err.message || 'Failed to create user account.', isError: true });
    } finally {
      setIsCreatingUser(false);
    }
  };

  const handleRoleChange = async (userId: string, targetRole: string) => {
    try {
      await api.adminUpdateUserRole(userId, targetRole);
      setUserMsg({ text: `Updated user role to ${targetRole}.` });
      fetchUsers();
    } catch (e: any) {
      setUserMsg({ text: 'Failed to update user role.', isError: true });
    }
  };

  const roleBadgeStyle = (roleStr: string) => {
    switch (roleStr) {
      case 'ADMIN': return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'ICT': return 'bg-amber-100 text-amber-900 border-amber-300';
      case 'MANAGEMENT': return 'bg-blue-100 text-blue-800 border-blue-300';
      default: return 'bg-emerald-100 text-emerald-800 border-emerald-300';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between bg-[#0B2545] text-white p-6 rounded-2xl shadow-md border-l-8 border-purple-500">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-purple-500 text-white uppercase tracking-wider">
              Admin Exclusive Portal
            </span>
            <span className="text-xs text-slate-300">RBAC User Management</span>
          </div>
          <h1 className="text-2xl font-extrabold font-serif tracking-tight mt-1">
            Institutional User Accounts & Role Provisioning
          </h1>
          <p className="text-xs text-slate-300 mt-1 max-w-2xl">
            Provision ICT Technical accounts, Management Executive roles, and Policy Researcher credentials for PIDE personnel.
          </p>

          {userMsg && (
            <div className={`mt-3 p-2.5 rounded-lg text-xs font-semibold ${userMsg.isError ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-emerald-50 text-emerald-900 border border-emerald-200'}`}>
              {userMsg.text}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            className="text-white border-slate-600 hover:bg-white/10"
            icon={<RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />}
            onClick={fetchUsers}
          >
            Refresh Accounts
          </Button>

          <Button
            variant="gold"
            icon={<UserPlus className="w-4 h-4" />}
            onClick={() => setIsProvisioningOpen(!isProvisioningOpen)}
          >
            {isProvisioningOpen ? 'Hide Form' : 'Provision Account'}
          </Button>
        </div>
      </div>

      {/* Account Provisioning Form Card */}
      {isProvisioningOpen && (
        <Card accentBorder>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-[#0B2545]">
              <UserCheck className="w-5 h-5 text-[#005A36]" />
              Provision New PIDE User Account & Assign Role
            </CardTitle>
            <CardDescription>
              Create institutional credentials for PIDE personnel and select their organizational access level.
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleCreateUserSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Full Name & Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Dr. Nadeem ul Haque"
                  value={newFullName}
                  onChange={(e) => setNewFullName(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-[#005A36]/30 focus:border-[#005A36]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Institutional Email</label>
                <input
                  type="email"
                  required
                  placeholder="user@pide.org.pk"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-[#005A36]/30 focus:border-[#005A36]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
                <input
                  type="password"
                  required
                  placeholder="Minimum 6 characters"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-[#005A36]/30 focus:border-[#005A36]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Assigned Institutional Role</label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg outline-none font-bold bg-white focus:ring-2 focus:ring-[#005A36]/30"
                >
                  <option value="MANAGEMENT">🔵 MANAGEMENT (Executive Briefings)</option>
                  <option value="ICT">⚡ ICT (Pipeline & Data Operations)</option>
                  <option value="RESEARCHER">🟢 RESEARCHER (Policy Research)</option>
                  <option value="ADMIN">👑 ADMIN (Full Control)</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <Button type="submit" variant="primary" isLoading={isCreatingUser} icon={<UserPlus className="w-4 h-4" />}>
                Provision User Account
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Registered Users List */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5 text-purple-600" />
              Registered System Accounts ({usersList.length})
            </CardTitle>
            <CardDescription>
              All active PIDE institutional user accounts, active roles, and modification controls.
            </CardDescription>
          </div>
        </CardHeader>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 text-slate-700 font-bold border-y border-slate-200">
              <tr>
                <th className="p-3">User Full Name</th>
                <th className="p-3">Institutional Email</th>
                <th className="p-3">Assigned Role</th>
                <th className="p-3">Account Status</th>
                <th className="p-3 text-right">Modify Role</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {usersList.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="p-3 font-bold text-[#0B2545]">{u.full_name || 'PIDE Member'}</td>
                  <td className="p-3 font-mono text-slate-600">{u.email}</td>
                  <td className="p-3">
                    <span className={`px-2.5 py-0.5 rounded border text-[11px] font-bold ${roleBadgeStyle(u.role)}`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Active
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <select
                      value={u.role}
                      onChange={(e) => handleRoleChange(u.id, e.target.value)}
                      className="px-2 py-1 text-xs border border-slate-200 rounded-lg bg-white font-semibold outline-none focus:ring-2 focus:ring-purple-400"
                    >
                      <option value="RESEARCHER">RESEARCHER</option>
                      <option value="MANAGEMENT">MANAGEMENT</option>
                      <option value="ICT">ICT</option>
                      <option value="ADMIN">ADMIN</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
