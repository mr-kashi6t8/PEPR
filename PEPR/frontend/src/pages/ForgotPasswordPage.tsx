import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowRight, ShieldCheck, CheckCircle2, KeyRound, Lock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { PIDELogo } from '../components/PIDELogo';
import { Button } from '../components/ui/Button';

export const ForgotPasswordPage: React.FC = () => {
  const { forgotPassword, resetPassword } = useAuth();

  const [step, setStep] = useState<'REQUEST' | 'RESET'>('REQUEST');
  const [email, setEmail] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleRequestSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsLoading(true);

    try {
      const res = await forgotPassword(email);
      setSuccessMsg(res.message);
      if (res.reset_token) {
        setResetToken(res.reset_token);
        setStep('RESET');
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to dispatch reset instructions.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsLoading(true);

    try {
      const res = await resetPassword(resetToken, newPassword, verificationCode);
      setSuccessMsg(res.message || 'Password updated successfully!');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to reset password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col lg:flex-row bg-slate-900 font-sans">
      {/* Left Hero */}
      <div className="lg:w-1/2 bg-[#071930] p-8 lg:p-16 flex flex-col justify-between relative overflow-hidden border-b lg:border-b-0 lg:border-r border-slate-800">
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#005A36]/20 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-[#D4AF37]/10 rounded-full blur-3xl -ml-20 -mb-20 pointer-events-none" />

        <div className="relative z-10">
          <PIDELogo size="lg" variant="dark" />
        </div>

        <div className="relative z-10 my-12 space-y-6 max-w-lg">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-bold rounded-full">
            <ShieldCheck className="w-4 h-4" />
            <span>Account Security & Recovery Portal</span>
          </div>

          <h1 className="text-3xl lg:text-4xl font-extrabold font-serif text-white leading-tight">
            Reset Your Password
          </h1>

          <p className="text-sm text-slate-300 leading-relaxed font-sans">
            If you lost access to your PIDE institutional account, request an email verification token to securely update your password and regain access to the radar.
          </p>

          <div className="space-y-3 pt-4">
            <div className="flex items-center gap-3 text-xs text-slate-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>Encrypted SHA-256 HMAC Security Tokens</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>Instant Verification & Access Recovery</span>
            </div>
          </div>
        </div>

        <div className="relative z-10 text-xs text-slate-400 font-mono">
          Pakistan Institute of Development Economics (PIDE) © 2026
        </div>
      </div>

      {/* Right Column: Form */}
      <div className="lg:w-1/2 bg-slate-900 p-8 lg:p-16 flex items-center justify-center">
        <div className="w-full max-w-md bg-white rounded-2xl p-8 shadow-2xl border border-slate-200 space-y-6">
          <div>
            <div className="text-xs font-bold text-[#0284c7] uppercase tracking-wider">Account Recovery</div>
            <h2 className="text-2xl font-bold font-serif text-[#0B2545] mt-1">
              {step === 'REQUEST' ? 'Forgot Password?' : 'Update Password'}
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              {step === 'REQUEST'
                ? 'Enter your email address to receive password reset instructions.'
                : 'Enter the 6-digit verification code sent to your Gmail and set a new password.'}
            </p>
          </div>

          {errorMsg && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs font-semibold text-red-700">
              {errorMsg}
            </div>
          )}

          {successMsg && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs font-semibold text-emerald-800 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {step === 'REQUEST' ? (
            <form onSubmit={handleRequestSubmit} className="space-y-4">
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
                    className="w-full pl-9 pr-3 py-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-[#005A36]/30 focus:border-[#005A36] outline-none"
                  />
                </div>
              </div>

              <Button
                type="submit"
                variant="primary"
                className="w-full justify-center py-3 text-xs"
                isLoading={isLoading}
                icon={<ArrowRight className="w-4 h-4" />}
              >
                Send Password Reset Email
              </Button>
            </form>
          ) : (
            <form onSubmit={handleResetSubmit} className="space-y-4">
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
                    className="w-full pl-9 pr-3 py-2.5 text-xs border border-slate-200 rounded-lg font-mono text-center text-sm font-bold tracking-widest outline-none focus:ring-2 focus:ring-[#005A36]/30 focus:border-[#005A36]"
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
                    className="w-full pl-9 pr-3 py-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-[#005A36]/30 focus:border-[#005A36] outline-none"
                  />
                </div>
              </div>

              <Button
                type="submit"
                variant="primary"
                className="w-full justify-center py-3 text-xs"
                isLoading={isLoading}
                icon={<ArrowRight className="w-4 h-4" />}
              >
                Update Password & Return to Login
              </Button>
            </form>
          )}

          <div className="text-center text-xs text-slate-600 pt-4 border-t border-slate-100 flex items-center justify-between">
            <Link to="/login" className="text-[#005A36] font-bold hover:underline">
              ← Return to Login
            </Link>
            {step === 'REQUEST' && (
              <button
                type="button"
                onClick={() => setStep('RESET')}
                className="text-slate-500 hover:text-slate-700"
              >
                Have a token? Reset password →
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
