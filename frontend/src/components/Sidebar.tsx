'use client';

import { Locale, t } from '@/lib/i18n';
import {
  LayoutDashboard, Database, GitBranch, Shield, FileText,
  ScrollText, Bot, Settings, Languages, LogOut
} from 'lucide-react';

interface SidebarProps {
  locale: Locale;
  activeView: string;
  onNavigate: (view: string) => void;
  onToggleLocale: () => void;
}

const navItems = [
  { key: 'dashboard', icon: LayoutDashboard, label: 'nav.dashboard' },
  { key: 'assets', icon: Database, label: 'nav.assets' },
  { key: 'lineage', icon: GitBranch, label: 'nav.lineage' },
  { key: 'monitoring', icon: Shield, label: 'nav.monitoring' },
  { key: 'policies', icon: FileText, label: 'nav.policies' },
  { key: 'audit', icon: ScrollText, label: 'nav.audit' },
];

export default function Sidebar({ locale, activeView, onNavigate, onToggleLocale }: SidebarProps) {
  return (
    <aside className="fixed inset-y-0 start-0 w-64 bg-surface-950/95 backdrop-blur-xl border-e border-slate-800/50 flex flex-col z-40">
      {/* Logo */}
      <div className="p-6 border-b border-slate-800/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center shadow-lg shadow-brand-500/20">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold gradient-text">DATASHIELD</h1>
            <p className="text-[10px] text-slate-500 uppercase tracking-[0.2em]">
              {locale === 'ar' ? 'حوكمة البيانات' : 'Data Governance'}
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navItems.map(({ key, icon: Icon, label }) => (
          <button
            key={key}
            id={`nav-${key}`}
            onClick={() => onNavigate(key)}
            className={`nav-item w-full ${activeView === key ? 'active' : 'text-slate-400 hover:text-slate-200'}`}
          >
            <Icon className="w-4 h-4 shrink-0" />
            <span>{t(label, locale)}</span>
          </button>
        ))}
      </nav>

      {/* Bottom Actions */}
      <div className="p-3 border-t border-slate-800/50 space-y-1">
        <button
          id="toggle-language"
          onClick={onToggleLocale}
          className="nav-item w-full text-slate-400 hover:text-slate-200"
        >
          <Languages className="w-4 h-4 shrink-0" />
          <span>{locale === 'ar' ? 'English' : 'العربية'}</span>
        </button>
        <button className="nav-item w-full text-slate-400 hover:text-red-400">
          <LogOut className="w-4 h-4 shrink-0" />
          <span>{t('auth.logout', locale)}</span>
        </button>
      </div>
    </aside>
  );
}
