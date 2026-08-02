import React from 'react';
import { Globe, Cpu } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

export const SettingsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold font-serif text-[#0B2545]">System Settings & Configuration</h1>
        <p className="text-xs text-slate-500 mt-1">
          Configure API base URL, OpenRouter models, and display preferences.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle><Globe className="w-4 h-4 text-[#005A36]" /><span>API Configuration</span></CardTitle>
          </CardHeader>
          <div className="space-y-3 text-xs">
            <div>
              <label className="block font-bold text-slate-700 mb-1">Backend API Base URL</label>
              <input
                type="text"
                defaultValue="/api/v1"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-slate-50 font-mono focus:outline-none focus:ring-2 focus:ring-[#005A36]/30"
              />
            </div>
            <div>
              <label className="block font-bold text-slate-700 mb-1">OpenRouter Base URL</label>
              <input
                type="text"
                defaultValue="https://openrouter.ai/api/v1"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-slate-50 font-mono focus:outline-none focus:ring-2 focus:ring-[#005A36]/30"
              />
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle><Cpu className="w-4 h-4 text-[#005A36]" /><span>LLM Model Configuration</span></CardTitle>
          </CardHeader>
          <div className="space-y-3 text-xs">
            <div>
              <label className="block font-bold text-slate-700 mb-1">Primary Model</label>
              <select className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-slate-50 font-medium focus:outline-none">
                <option>google/gemini-2.5-flash</option>
                <option>anthropic/claude-sonnet-4</option>
                <option>openai/gpt-4o</option>
              </select>
            </div>
            <div>
              <label className="block font-bold text-slate-700 mb-1">Fallback Model</label>
              <select className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-slate-50 font-medium focus:outline-none">
                <option>openai/gpt-4o-mini</option>
                <option>google/gemini-2.5-flash</option>
              </select>
            </div>
          </div>
        </Card>
      </div>

      <div className="flex justify-end">
        <Button variant="primary">Save Configuration</Button>
      </div>
    </div>
  );
};
