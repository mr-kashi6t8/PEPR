import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Lock, Mail, ArrowRight, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { PIDELogo } from '../components/PIDELogo';
import { Button } from '../components/ui/Button';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsLoading(true);

    try {
      await login(email, password);
      setSuccessMsg('Authenticated successfully! Redirecting to Dashboard...');
      setTimeout(() => {
        navigate('/dashboard');
      }, 500);
    } catch (err: any) {
      setErrorMsg(err.message || 'Invalid institutional email or password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col lg:flex-row bg-slate-900 font-sans">
      {/* Left Column: Institutional Hero Section */}
      <div className="lg:w-1/2 bg-[#071930] p-8 lg:p-16 flex flex-col justify-between relative overflow-hidden border-b lg:border-b-0 lg:border-r border-slate-800">
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#005A36]/20 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-[#D4AF37]/10 rounded-full blur-3xl -ml-20 -mb-20 pointer-events-none" />

        <div className="relative z-10">
          <PIDELogo size="lg" variant="dark" />
        </div>

        <div className="relative z-10 my-12 space-y-6 max-w-lg">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold rounded-full">
            <ShieldCheck className="w-4 h-4" />
            <span>Official Policy Decision Support System</span>
          </div>

          <h1 className="text-3xl lg:text-4xl font-extrabold font-serif text-white leading-tight">
            Pakistan Economics Problem Radar (PEPR)
          </h1>

          <p className="text-sm text-slate-300 leading-relaxed font-sans">
            Synthesizing 7-day empirical database evidence across time-series anomalies, statutory policy gaps, media sentiment, and official PIDE Research Showcase publications.
          </p>

          <div className="space-y-3 pt-4">
            <div className="flex items-center gap-3 text-xs text-slate-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>Real-Time ML Anomaly & Trend Detection (IsolationForest)</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>Statutory Policy Target Gap Evaluation (SBP, FBR, MoE)</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>PIDE Working Papers RAG Engine for Policy Interventions</span>
            </div>
          </div>
        </div>

        <div className="relative z-10 text-xs text-slate-400 font-mono">
          Pakistan Institute of Development Economics (PIDE) © 2026
        </div>
      </div>

      {/* Right Column: Login Form */}
      <div className="lg:w-1/2 bg-slate-900 p-8 lg:p-16 flex items-center justify-center">
        <div className="w-full max-w-md bg-white rounded-2xl p-8 shadow-2xl border border-slate-200 space-y-6">
          <div>
            <div className="text-xs font-bold text-[#0284c7] uppercase tracking-wider">Authentication Portal</div>
            <h2 className="text-2xl font-bold font-serif text-[#0B2545] mt-1">Sign in to PEPR</h2>
            <p className="text-xs text-slate-500 mt-1">
              Enter your institutional email and password to access policy engines.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
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

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Institutional Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  placeholder="admin@pide.org.pk"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-[#005A36]/30 focus:border-[#005A36] outline-none"
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-bold text-slate-700">Password</label>
                <Link to="/forgot-password" className="text-[11px] text-[#005A36] font-bold hover:underline">
                  Forgot Password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-[#005A36]/30 focus:border-[#005A36] outline-none"
                />
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full justify-center py-3 mt-2 text-xs font-bold"
              isLoading={isLoading}
              icon={<ArrowRight className="w-4 h-4" />}
            >
              Sign In to Dashboard
            </Button>
          </form>

          <div className="text-center text-xs text-slate-600 pt-4 border-t border-slate-100">
            Don't have an account yet?{' '}
            <Link to="/signup" className="text-[#005A36] font-extrabold hover:underline">
              Register New Account →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
