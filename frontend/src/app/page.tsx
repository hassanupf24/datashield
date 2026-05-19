'use client';

import { useState } from 'react';
import Sidebar from '@/components/Sidebar';
import Dashboard from '@/components/Dashboard';
import SecurityMonitoring from '@/components/SecurityMonitoring';
import CopilotChat from '@/components/CopilotChat';
import { Locale } from '@/lib/i18n';

export default function Home() {
  const [locale, setLocale] = useState<Locale>('en');
  const [activeView, setActiveView] = useState('dashboard');
  const [copilotOpen, setCopilotOpen] = useState(false);
  const dir = locale === 'ar' ? 'rtl' : 'ltr';

  const toggleLocale = () => {
    const next = locale === 'en' ? 'ar' : 'en';
    setLocale(next);
    document.documentElement.lang = next;
    document.documentElement.dir = next === 'ar' ? 'rtl' : 'ltr';
  };

  return (
    <div dir={dir} className="flex min-h-screen">
      <Sidebar
        locale={locale}
        activeView={activeView}
        onNavigate={setActiveView}
        onToggleLocale={toggleLocale}
      />
      <main className="flex-1 ms-64 p-6 overflow-auto">
        {activeView === 'dashboard' && <Dashboard locale={locale} />}
        {activeView === 'monitoring' && <SecurityMonitoring locale={locale} />}
      </main>
      {/* Copilot FAB */}
      <button
        id="copilot-fab"
        onClick={() => setCopilotOpen(!copilotOpen)}
        className="fixed bottom-6 end-6 z-50 w-14 h-14 rounded-full bg-brand-600 hover:bg-brand-500 text-white shadow-lg shadow-brand-500/30 flex items-center justify-center transition-all hover:scale-110 animate-glow"
        aria-label="Open Governance Copilot"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="m2 14 6-6 6 6 6-6"/></svg>
      </button>
      {copilotOpen && (
        <CopilotChat locale={locale} onClose={() => setCopilotOpen(false)} />
      )}
    </div>
  );
}
