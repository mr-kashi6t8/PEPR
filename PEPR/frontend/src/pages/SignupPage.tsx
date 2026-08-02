import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Lock, Mail, User, ShieldCheck, ArrowRight, CheckCircle2, Info } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { PIDELogo } from '../components/PIDELogo';
import { Button } from '../components/ui/Button';

export const SignupPage: React.FC = () => {
  const navigate = useNavigate();
  const { signup } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsLoading(true);

    try {
      // Public signup is restricted to RESEARCHER role
      await signup(email, password, fullName, 'RESEARCHER');
      setSuccessMsg('Researcher account registered successfully! Redirecting to Radar Dashboard...');
      setTimeout(() => {
        navigate('/dashboard');
      }, 600);
    } catch (err: any) {
      setErrorMsg(err.message || 'Signup failed. Please check your information.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col lg:flex-row bg-slate-900 font-sans">
      {/* Left Column: Hero */}
      <div className="lg:w-1/2 bg-[#071930] p-8 lg:p-16 flex flex-col justify-between relative overflow-hidden border-b lg:border-b-0 lg:border-r border-slate-800">
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#005A36]/20 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-[#D4AF37]/10 rounded-full blur-3xl -ml-20 -mb-20 pointer-events-none" />

        <div className="relative z-10">
          <PIDELogo size="lg" variant="dark" />
        </div>

        <div className="relative z-10 my-12 space-y-6 max-w-lg">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold rounded-full">
            <ShieldCheck className="w-4 h-4" />
            <span>Policy Researcher Registration</span>
          </div>

          <h1 className="text-3xl lg:text-4xl font-extrabold font-serif text-white leading-tight">
            Register as a PIDE Policy Researcher
          </h1>

          <p className="text-sm text-slate-300 leading-relaxed font-sans">
            Set up your researcher account to participate in evidence-based macroeconomic intelligence, statutory policy evaluation, and PIDE Research Showcase recommendations.
          </p>

          <div className="space-y-3 pt-4">
            <div className="flex items-center gap-3 text-xs text-slate-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>Full Access to Indicator Trends & RAG Working Papers</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>Generate Executive Weekly Economic Reports</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>ICT & Management Roles Provisioned by Admin Secretariat</span>
            </div>
          </div>
        </div>

        <div className="relative z-10 text-xs text-slate-400 font-mono">
          Pakistan Institute of Development Economics (PIDE) © 2026
        </div>
      </div>

      {/* Right Column: Signup Form */}
      <div className="lg:w-1/2 bg-slate-900 p-8 lg:p-16 flex items-center justify-center">
        <div className="w-full max-w-md bg-white rounded-2xl p-8 shadow-2xl border border-slate-200 space-y-5">
          <div>
            <div className="text-xs font-bold text-[#0284c7] uppercase tracking-wider">Public Registration</div>
            <h2 className="text-2xl font-bold font-serif text-[#0B2545] mt-1">Researcher Signup</h2>
            <p className="text-xs text-slate-500 mt-1">
              Enter your full name, email, and password to create your account.
            </p>
          </div>

          {/* Institutional Role Notice */}
          <div className="p-3 bg-sky-50 border border-sky-200 rounded-xl text-xs text-sky-900 flex items-start gap-2.5">
            <Info className="w-4 h-4 text-sky-600 flex-shrink-0 mt-0.5" />
            <div>
              <strong>Institutional Role Notice:</strong> All public registrations are assigned the <strong>RESEARCHER</strong> role by default. Management, ICT Data Team, and Administrator accounts are provisioned exclusively by the PIDE Admin Secretariat.
            </div>
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
              <label className="block text-xs font-bold text-slate-700 mb-1">Full Name & Title</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  placeholder="e.g. Dr. Afia Malik"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-[#005A36]/30 focus:border-[#005A36] outline-none"
                />
              </div>
            </div>

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

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  placeholder="Minimum 6 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
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
              Register Researcher Account
            </Button>
          </form>

          <div className="text-center text-xs text-slate-600 pt-3 border-t border-slate-100">
            Already have an account?{' '}
            <Link to="/login" className="text-[#005A36] font-extrabold hover:underline">
              Sign In Here →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
