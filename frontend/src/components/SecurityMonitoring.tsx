'use client';

import { Locale, t } from '@/lib/i18n';
import { Shield, Eye, Download, Trash2, Edit3 } from 'lucide-react';

interface SecurityMonitoringProps {
  locale: Locale;
}

const actionIcons: Record<string, any> = {
  READ: Eye,
  WRITE: Edit3,
  EXPORT: Download,
  DELETE: Trash2,
};

const demoLogs = [
  { id: 'evt-001', user: 'ahmad@bank.sa', user_ar: 'أحمد@bank.sa', action: 'EXPORT', asset: 'customers', risk: 'HIGH', risk_score: 82, time: '10:42 AM', ip: '192.168.1.105', anomaly: true },
  { id: 'evt-002', user: 'sara@bank.sa', user_ar: 'سارة@bank.sa', action: 'READ', asset: 'transactions', risk: 'LOW', risk_score: 15, time: '10:38 AM', ip: '10.0.0.52', anomaly: false },
  { id: 'evt-003', user: 'omar@bank.sa', user_ar: 'عمر@bank.sa', action: 'WRITE', asset: 'employees', risk: 'MEDIUM', risk_score: 45, time: '10:35 AM', ip: '172.16.0.12', anomaly: false },
  { id: 'evt-004', user: 'fatima@bank.sa', user_ar: 'فاطمة@bank.sa', action: 'DELETE', asset: 'kyc_docs', risk: 'CRITICAL', risk_score: 95, time: '10:30 AM', ip: '192.168.2.200', anomaly: true },
  { id: 'evt-005', user: 'khalid@bank.sa', user_ar: 'خالد@bank.sa', action: 'READ', asset: 'reports', risk: 'LOW', risk_score: 8, time: '10:28 AM', ip: '10.0.0.15', anomaly: false },
  { id: 'evt-006', user: 'nora@bank.sa', user_ar: 'نورة@bank.sa', action: 'EXPORT', asset: 'transactions', risk: 'HIGH', risk_score: 78, time: '10:22 AM', ip: '192.168.3.50', anomaly: true },
];

const riskColors: Record<string, string> = {
  CRITICAL: 'text-red-400 bg-red-500/10 border-red-500/20',
  HIGH: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
  MEDIUM: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  LOW: 'text-green-400 bg-green-500/10 border-green-500/20',
};

const actionColors: Record<string, string> = {
  READ: 'text-blue-400 bg-blue-500/10',
  WRITE: 'text-purple-400 bg-purple-500/10',
  EXPORT: 'text-amber-400 bg-amber-500/10',
  DELETE: 'text-red-400 bg-red-500/10',
};

export default function SecurityMonitoring({ locale }: SecurityMonitoringProps) {
  const isAr = locale === 'ar';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Shield className="w-6 h-6 text-brand-400" />
            {t('nav.monitoring', locale)}
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            {isAr ? 'مراقبة النشاط في الوقت الفعلي' : 'Real-time activity monitoring'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-green-500/10 text-green-400 text-xs font-medium border border-green-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            {isAr ? 'مباشر' : 'Live Stream'}
          </span>
        </div>
      </div>

      {/* Activity Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead className="bg-slate-800/50 text-slate-400">
              <tr>
                <th>{isAr ? 'المستخدم' : 'User'}</th>
                <th>{isAr ? 'الإجراء' : 'Action'}</th>
                <th>{isAr ? 'الأصل' : 'Asset'}</th>
                <th>{isAr ? 'عنوان IP' : 'IP Address'}</th>
                <th className="text-end">{isAr ? 'درجة الخطورة' : 'Risk Score'}</th>
                <th className="text-end">{isAr ? 'مستوى الخطورة' : 'Risk Level'}</th>
                <th className="text-end">{isAr ? 'الوقت' : 'Time'}</th>
              </tr>
            </thead>
            <tbody>
              {demoLogs.map((log) => {
                const ActionIcon = actionIcons[log.action] || Eye;
                return (
                  <tr key={log.id} className={log.anomaly ? 'bg-red-500/5' : ''}>
                    <td>
                      <div className="flex items-center gap-2">
                        {log.anomaly && <span className="w-2 h-2 rounded-full bg-red-400 animate-pulse shrink-0" />}
                        <span className="font-mono text-xs">{isAr ? log.user_ar : log.user}</span>
                      </div>
                    </td>
                    <td>
                      <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium ${actionColors[log.action]}`}>
                        <ActionIcon className="w-3 h-3" />
                        {t(`action.${log.action.toLowerCase()}`, locale)}
                      </span>
                    </td>
                    <td><span className="font-mono text-xs text-slate-300">{log.asset}</span></td>
                    <td><span className="font-mono text-xs text-slate-500">{log.ip}</span></td>
                    <td className="text-end">
                      <div className="inline-flex items-center gap-2">
                        <div className="w-16 h-1.5 rounded-full bg-slate-800">
                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              width: `${log.risk_score}%`,
                              backgroundColor: log.risk_score >= 85 ? '#f87171' : log.risk_score >= 60 ? '#fb923c' : log.risk_score >= 30 ? '#facc15' : '#4ade80',
                            }}
                          />
                        </div>
                        <span className="text-xs font-mono w-6 text-end">{log.risk_score}</span>
                      </div>
                    </td>
                    <td className="text-end">
                      <span className={`badge border ${riskColors[log.risk]}`}>
                        {t(`risk.${log.risk.toLowerCase()}`, locale)}
                      </span>
                    </td>
                    <td className="text-end text-xs text-slate-500">{log.time}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
