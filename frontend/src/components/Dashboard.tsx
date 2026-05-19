'use client';

import { Locale, t } from '@/lib/i18n';
import { ShieldCheck, Database, Activity, AlertTriangle, BarChart3, TrendingUp } from 'lucide-react';

interface DashboardProps {
  locale: Locale;
}

// Demo data
const riskData = [
  { level: 'CRITICAL', count: 3, color: 'text-red-400', bg: 'bg-red-500/10' },
  { level: 'HIGH', count: 12, color: 'text-orange-400', bg: 'bg-orange-500/10' },
  { level: 'MEDIUM', count: 45, color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
  { level: 'LOW', count: 234, color: 'text-green-400', bg: 'bg-green-500/10' },
];

const recentAlerts = [
  { id: 1, type: 'ANOMALY', severity: 'HIGH', title: 'Unusual data export detected', title_ar: 'اكتشاف تصدير بيانات غير عادي', time: '10 min ago', time_ar: 'منذ 10 دقائق' },
  { id: 2, type: 'POLICY_VIOLATION', severity: 'CRITICAL', title: 'Regulated data access violation', title_ar: 'انتهاك الوصول للبيانات المنظمة', time: '25 min ago', time_ar: 'منذ 25 دقيقة' },
  { id: 3, type: 'ANOMALY', severity: 'MEDIUM', title: 'Off-hours database query', title_ar: 'استعلام قاعدة بيانات خارج ساعات العمل', time: '1 hour ago', time_ar: 'منذ ساعة' },
  { id: 4, type: 'THRESHOLD_BREACH', severity: 'HIGH', title: 'Bulk record extraction attempt', title_ar: 'محاولة استخراج سجلات بالجملة', time: '2 hours ago', time_ar: 'منذ ساعتين' },
];

const severityBadge: Record<string, string> = {
  CRITICAL: 'badge-critical',
  HIGH: 'badge-high',
  MEDIUM: 'badge-medium',
  LOW: 'badge-low',
};

export default function Dashboard({ locale }: DashboardProps) {
  const isAr = locale === 'ar';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{t('dashboard.title', locale)}</h1>
          <p className="text-sm text-slate-400 mt-1">
            {isAr ? 'نظرة عامة في الوقت الفعلي على حالة أمن البيانات' : 'Real-time overview of your data security posture'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-green-500/10 text-green-400 text-xs font-medium border border-green-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
            {isAr ? 'مباشر' : 'Live'}
          </span>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={<ShieldCheck className="w-5 h-5" />}
          label={t('dashboard.compliance_score', locale)}
          value="92"
          suffix="/100"
          trend="+2.4%"
          trendUp
          color="text-emerald-400"
          gradient="from-emerald-500/20 to-teal-500/10"
        />
        <MetricCard
          icon={<Database className="w-5 h-5" />}
          label={t('dashboard.total_assets', locale)}
          value="1,247"
          trend="+18"
          trendUp
          color="text-brand-400"
          gradient="from-brand-500/20 to-purple-500/10"
        />
        <MetricCard
          icon={<Activity className="w-5 h-5" />}
          label={t('dashboard.events_today', locale)}
          value="34,891"
          trend="+12%"
          trendUp
          color="text-cyan-400"
          gradient="from-cyan-500/20 to-blue-500/10"
        />
        <MetricCard
          icon={<AlertTriangle className="w-5 h-5" />}
          label={t('dashboard.anomalies', locale)}
          value="7"
          trend="-3"
          trendUp={false}
          color="text-red-400"
          gradient="from-red-500/20 to-orange-500/10"
        />
      </div>

      {/* Risk Distribution + Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Risk Distribution */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-brand-400" />
            {t('dashboard.risk_distribution', locale)}
          </h3>
          <div className="space-y-3">
            {riskData.map(({ level, count, color, bg }) => {
              const total = riskData.reduce((s, d) => s + d.count, 0);
              const pct = Math.round((count / total) * 100);
              return (
                <div key={level} className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className={`font-medium ${color}`}>{t(`risk.${level.toLowerCase()}`, locale)}</span>
                    <span className="text-slate-400">{count} ({pct}%)</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-800">
                    <div
                      className={`h-full rounded-full ${bg} transition-all duration-1000`}
                      style={{ width: `${pct}%`, backgroundColor: color.includes('red') ? '#f87171' : color.includes('orange') ? '#fb923c' : color.includes('yellow') ? '#facc15' : '#4ade80' }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="glass-card p-6 lg:col-span-2">
          <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-400" />
            {t('dashboard.recent_alerts', locale)}
          </h3>
          <div className="space-y-2">
            {recentAlerts.map((alert) => (
              <div key={alert.id} className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/30 hover:bg-slate-800/50 transition-colors cursor-pointer">
                <div className={`w-2 h-2 rounded-full shrink-0 ${
                  alert.severity === 'CRITICAL' ? 'bg-red-400 animate-pulse' :
                  alert.severity === 'HIGH' ? 'bg-orange-400' : 'bg-yellow-400'
                }`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{isAr ? alert.title_ar : alert.title}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className={`badge ${severityBadge[alert.severity]}`}>
                      {t(`risk.${alert.severity.toLowerCase()}`, locale)}
                    </span>
                    <span className="text-xs text-slate-500">{isAr ? alert.time_ar : alert.time}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Compliance Frameworks */}
      <div className="glass-card p-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">
          {isAr ? 'حالة الامتثال للأطر التنظيمية' : 'Compliance Framework Status'}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ComplianceCard name="GDPR" score={94} locale={locale} />
          <ComplianceCard name="ISO 27001" score={88} locale={locale} />
          <ComplianceCard name="PCI-DSS" score={91} locale={locale} />
        </div>
      </div>
    </div>
  );
}

function MetricCard({ icon, label, value, suffix, trend, trendUp, color, gradient }: {
  icon: React.ReactNode; label: string; value: string; suffix?: string;
  trend: string; trendUp: boolean; color: string; gradient: string;
}) {
  return (
    <div className={`glass-card p-5 bg-gradient-to-br ${gradient}`}>
      <div className="flex items-center justify-between mb-3">
        <span className={color}>{icon}</span>
        <span className={`text-xs font-medium flex items-center gap-1 ${trendUp ? 'text-emerald-400' : 'text-red-400'}`}>
          <TrendingUp className={`w-3 h-3 ${!trendUp ? 'rotate-180' : ''}`} />
          {trend}
        </span>
      </div>
      <div className="metric-value">
        <span className={color}>{value}</span>
        {suffix && <span className="text-lg text-slate-500">{suffix}</span>}
      </div>
      <p className="metric-label mt-1">{label}</p>
    </div>
  );
}

function ComplianceCard({ name, score, locale }: { name: string; score: number; locale: Locale }) {
  const color = score >= 90 ? 'text-emerald-400' : score >= 80 ? 'text-yellow-400' : 'text-red-400';
  const ring = score >= 90 ? 'border-emerald-500/30' : score >= 80 ? 'border-yellow-500/30' : 'border-red-500/30';
  return (
    <div className="flex items-center gap-4 p-4 rounded-xl bg-slate-800/30">
      <div className={`w-16 h-16 rounded-full border-4 ${ring} flex items-center justify-center`}>
        <span className={`text-xl font-bold ${color}`}>{score}%</span>
      </div>
      <div>
        <p className="font-semibold">{name}</p>
        <p className="text-xs text-slate-400">
          {score >= 90 ? (locale === 'ar' ? 'ممتثل' : 'Compliant') :
           score >= 80 ? (locale === 'ar' ? 'يحتاج تحسين' : 'Needs Improvement') :
           (locale === 'ar' ? 'غير ممتثل' : 'Non-Compliant')}
        </p>
      </div>
    </div>
  );
}
