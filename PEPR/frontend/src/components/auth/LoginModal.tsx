import React, { useState } from 'react';
import { X, Lock, Mail, User, ShieldCheck, ArrowRight, KeyRound, CheckCircle2 } from 'lucide-react';
import { useAuth, type UserRole } from '../../context/AuthContext';
import { Button } from '../ui/Button';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialMode?: 'LOGIN' | 'SIGNUP' | 'FORGOT';
}

export const LoginModal: React.FC<LoginModalProps> = ({
  isOpen,
  onClose,
  initialMode = 'LOGIN',
}) => {
  const { login, signup, forgotPassword, resetPassword } = useAuth();

  const [mode, setMode] = useState<'LOGIN' | 'SIGNUP' | 'FORGOT' | 'RESET'>(initialMode);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<UserRole>('RESEARCHER');
  
  const [resetToken, setResetToken] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsLoading(true);

    try {
      if (mode === 'LOGIN') {
        await login(email, password);
        setSuccessMsg('Authenticated successfully!');
        setTimeout(onClose, 800);
      } else if (mode === 'SIGNUP') {
        await signup(email, password, fullName, role);
        setSuccessMsg('Account created successfully!');
        setTimeout(onClose, 800);
      } else if (mode === 'FORGOT') {
        const res = await forgotPassword(email);
        setSuccessMsg(res.message);
        if (res.reset_token) {
          setResetToken(res.reset_token);
          setTimeout(() => setMode('RESET'), 1500);
        }
      } else if (mode === 'RESET') {
        const res = await resetPassword(resetToken, newPassword, verificationCode);
        setSuccessMsg(res.message);
        setTimeout(() => setMode('LOGIN'), 1500);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'An error occurred. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const roleDescriptions: Record<UserRole, string> = {
    RESEARCHER: 'Policy Economist & Researcher: Full analysis, RAG document upload, trend view.',
    MANAGEMENT: 'Executive Management: Executive dashboards, weekly report overview, macro indicators.',
    ICT: 'ICT Technical Team: Full system access + Permission to run live data ingestion pipelines.',
    ADMIN: 'System Administrator: Full unrestricted system control, user management & pipeline triggers.',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-xs animate-fadeIn">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-md overflow-hidden relative">
        {/* Header */}
        <div className="bg-[#0B2545] p-6 text-white relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-full hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2 text-[11px] font-bold text-[#D4AF37] uppercase tracking-wider">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>PIDE PEPR Security Portal</span>
          </div>
          <h2 className="text-xl font-bold font-serif mt-1">
            {mode === 'LOGIN' && 'Sign in to PEPR Core'}
            {mode === 'SIGNUP' && 'Create PIDE Radar Account'}
            {mode === 'FORGOT' && 'Reset Your Password'}
            {mode === 'RESET' && 'Set New Password'}
          </h2>
          <p className="text-xs text-slate-300 mt-1">
            {mode === 'LOGIN' && 'Enter your institutional email & password to access policy engines.'}
            {mode === 'SIGNUP' && 'Select your organizational role to register for system access.'}
            {mode === 'FORGOT' && 'Enter your registered email to receive a password reset token.'}
            {mode === 'RESET' && 'Enter the 6-digit verification code sent to your Gmail.'}
          </p>
        </div>

        {/* Body Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {errorMsg && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-xs font-semibold text-red-400">
              {errorMsg}
            </div>
          )}

          {successMsg && (
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-xs font-semibold text-emerald-400 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}



          {/* SIGNUP: Full Name */}
          {mode === 'SIGNUP' && (
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Full Name & Title</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  placeholder="e.g. Dr. Afia Malik"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-[#005A36]/30 focus:border-[#005A36] outline-none"
                />
              </div>
            </div>
          )}

          {/* Email input for LOGIN, SIGNUP, FORGOT */}
          {mode !== 'RESET' && (
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Institutional Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  placeholder="user@pide.org.pk"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-[#005A36]/30 focus:border-[#005A36] outline-none"
                />
              </div>
            </div>
          )}

          {/* SIGNUP: Role Selector */}
          {mode === 'SIGNUP' && (
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Organizational Role</label>
              <div className="grid grid-cols-2 gap-2">
                {(['RESEARCHER', 'MANAGEMENT', 'ICT', 'ADMIN'] as UserRole[]).map((r) => (
                  <button
                    type="button"
                    key={r}
                    onClick={() => setRole(r)}
                    className={`p-2 rounded-lg border text-left text-xs transition-all ${
                      role === r
                        ? 'border-[#005A36] bg-emerald-50 text-[#005A36] font-bold ring-2 ring-[#005A36]/20'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span>{r}</span>
                      {role === r && <span className="w-2 h-2 rounded-full bg-[#005A36]" />}
                    </div>
                  </button>
                ))}
              </div>
              <p className="text-[10px] text-slate-500 mt-1.5 bg-slate-50 p-2 rounded border border-slate-100 italic">
                {roleDescriptions[role]}
              </p>
            </div>
          )}

          {/* Password Input for LOGIN & SIGNUP */}
          {(mode === 'LOGIN' || mode === 'SIGNUP') && (
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-bold text-slate-700">Password</label>
                {mode === 'LOGIN' && (
                  <button
                    type="button"
                    onClick={() => setMode('FORGOT')}
                    className="text-[11px] text-[#005A36] hover:underline font-medium"
                  >
                    Forgot Password?
                  </button>
                )}
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-[#005A36]/30 focus:border-[#005A36] outline-none"
                />
              </div>
            </div>
          )}

          {/* RESET Mode Inputs */}
          {mode === 'RESET' && (
            <>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">6-Digit Verification Code</label>
                <div className="relative">
                  <KeyRound className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    maxLength={6}
                    placeholder="e.g. 123456"
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-lg font-mono text-center text-sm font-bold tracking-widest outline-none focus:ring-2 focus:ring-[#005A36]/30 focus:border-[#005A36]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">New Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    required
                    placeholder="Minimum 6 characters"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-lg outline-none"
                  />
                </div>
              </div>
            </>
          )}

          {/* Demo Login Shortcuts */}
          {mode === 'LOGIN' && (
            <div className="pt-2 border-t border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Quick Demo Login Credentials:</span>
              <div className="grid grid-cols-2 gap-1.5 mt-1 text-[10px]">
                <button
                  type="button"
                  onClick={() => { setEmail('researcher@pide.org.pk'); setPassword('pide2026'); }}
                  className="p-1.5 bg-slate-50 hover:bg-slate-100 rounded text-slate-700 text-left border border-slate-200"
                >
                  🟢 <strong>Researcher</strong>: researcher@pide.org.pk
                </button>
                <button
                  type="button"
                  onClick={() => { setEmail('management@pide.org.pk'); setPassword('pide2026'); }}
                  className="p-1.5 bg-slate-50 hover:bg-slate-100 rounded text-slate-700 text-left border border-slate-200"
                >
                  🔵 <strong>Management</strong>: management@pide.org.pk
                </button>
                <button
                  type="button"
                  onClick={() => { setEmail('ict@pide.org.pk'); setPassword('pide2026'); }}
                  className="p-1.5 bg-amber-50 hover:bg-amber-100 rounded text-amber-900 text-left border border-amber-200"
                >
                  ⚡ <strong>ICT Team</strong>: ict@pide.org.pk
                </button>
                <button
                  type="button"
                  onClick={() => { setEmail('admin@pide.org.pk'); setPassword('pide2026'); }}
                  className="p-1.5 bg-purple-50 hover:bg-purple-100 rounded text-purple-900 text-left border border-purple-200"
                >
                  👑 <strong>Admin</strong>: admin@pide.org.pk
                </button>
              </div>
            </div>
          )}

          <Button
            type="submit"
            variant="primary"
            className="w-full justify-center py-2.5 mt-2"
            isLoading={isLoading}
            icon={<ArrowRight className="w-4 h-4" />}
          >
            {mode === 'LOGIN' && 'Sign In'}
            {mode === 'SIGNUP' && 'Create Account'}
            {mode === 'FORGOT' && 'Dispatch Reset Email'}
            {mode === 'RESET' && 'Update Password'}
          </Button>
        </form>

        {/* Footer Navigation */}
        <div className="bg-slate-50 p-4 border-t border-slate-100 text-center text-xs text-slate-600">
          {mode === 'LOGIN' && (
            <span>
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => { setMode('SIGNUP'); setErrorMsg(null); }}
                className="text-[#005A36] font-bold hover:underline"
              >
                Create Account
              </button>
            </span>
          )}
          {mode === 'SIGNUP' && (
            <span>
              Already registered?{' '}
              <button
                type="button"
                onClick={() => { setMode('LOGIN'); setErrorMsg(null); }}
                className="text-[#005A36] font-bold hover:underline"
              >
                Sign In
              </button>
            </span>
          )}
          {(mode === 'FORGOT' || mode === 'RESET') && (
            <button
              type="button"
              onClick={() => { setMode('LOGIN'); setErrorMsg(null); }}
              className="text-[#005A36] font-bold hover:underline"
            >
              ← Back to Sign In
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
