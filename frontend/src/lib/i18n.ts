/**
 * DATASHIELD - Arabic/English Translation Dictionary
 */
export type Locale = 'en' | 'ar';

export const translations: Record<Locale, Record<string, string>> = {
  en: {
    // Navigation
    'nav.dashboard': 'Dashboard',
    'nav.assets': 'Data Assets',
    'nav.lineage': 'Data Lineage',
    'nav.monitoring': 'Security Monitoring',
    'nav.policies': 'Policies',
    'nav.audit': 'Audit Logs',
    'nav.copilot': 'Governance Copilot',
    'nav.settings': 'Settings',

    // Dashboard
    'dashboard.title': 'Executive Risk Dashboard',
    'dashboard.compliance_score': 'Compliance Score',
    'dashboard.total_assets': 'Total Assets',
    'dashboard.events_today': 'Events Today',
    'dashboard.anomalies': 'Anomalies Detected',
    'dashboard.active_alerts': 'Active Alerts',
    'dashboard.risk_distribution': 'Risk Distribution',
    'dashboard.recent_alerts': 'Recent Alerts',
    'dashboard.top_risks': 'Top Risk Users',

    // Classification
    'classification.public': 'Public',
    'classification.internal': 'Internal',
    'classification.confidential': 'Confidential',
    'classification.highly_sensitive': 'Highly Sensitive',
    'classification.regulated': 'Regulated',
    'classification.unclassified': 'Unclassified',

    // Risk Levels
    'risk.low': 'Low',
    'risk.medium': 'Medium',
    'risk.high': 'High',
    'risk.critical': 'Critical',

    // Actions
    'action.read': 'Read',
    'action.write': 'Write',
    'action.delete': 'Delete',
    'action.export': 'Export',

    // Alerts
    'alert.anomaly': 'Anomaly',
    'alert.policy_violation': 'Policy Violation',
    'alert.threshold_breach': 'Threshold Breach',
    'alert.open': 'Open',
    'alert.investigating': 'Investigating',
    'alert.resolved': 'Resolved',

    // Common
    'common.search': 'Search...',
    'common.filter': 'Filter',
    'common.export': 'Export',
    'common.refresh': 'Refresh',
    'common.loading': 'Loading...',
    'common.no_data': 'No data available',
    'common.view_all': 'View All',
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.confirm': 'Confirm',
    'common.language': 'Language',
    'common.english': 'English',
    'common.arabic': 'العربية',

    // Copilot
    'copilot.title': 'Governance Copilot',
    'copilot.placeholder': 'Ask about your data governance...',
    'copilot.greeting': 'Hello! How can I help you secure your data today?',

    // Auth
    'auth.login': 'Login',
    'auth.logout': 'Logout',
    'auth.username': 'Username',
    'auth.password': 'Password',
  },
  ar: {
    // Navigation
    'nav.dashboard': 'لوحة المعلومات',
    'nav.assets': 'الأصول الرقمية',
    'nav.lineage': 'سلسلة البيانات',
    'nav.monitoring': 'المراقبة الأمنية',
    'nav.policies': 'السياسات',
    'nav.audit': 'سجلات التدقيق',
    'nav.copilot': 'مساعد الحوكمة',
    'nav.settings': 'الإعدادات',

    // Dashboard
    'dashboard.title': 'لوحة المخاطر التنفيذية',
    'dashboard.compliance_score': 'درجة الامتثال',
    'dashboard.total_assets': 'إجمالي الأصول',
    'dashboard.events_today': 'أحداث اليوم',
    'dashboard.anomalies': 'الشذوذات المكتشفة',
    'dashboard.active_alerts': 'التنبيهات النشطة',
    'dashboard.risk_distribution': 'توزيع المخاطر',
    'dashboard.recent_alerts': 'التنبيهات الأخيرة',
    'dashboard.top_risks': 'أعلى المستخدمين خطورة',

    // Classification
    'classification.public': 'عام',
    'classification.internal': 'داخلي',
    'classification.confidential': 'سري',
    'classification.highly_sensitive': 'حساس جداً',
    'classification.regulated': 'منظم',
    'classification.unclassified': 'غير مصنف',

    // Risk Levels
    'risk.low': 'منخفض',
    'risk.medium': 'متوسط',
    'risk.high': 'عالي',
    'risk.critical': 'حرج',

    // Actions
    'action.read': 'قراءة',
    'action.write': 'كتابة',
    'action.delete': 'حذف',
    'action.export': 'تصدير',

    // Alerts
    'alert.anomaly': 'شذوذ',
    'alert.policy_violation': 'انتهاك سياسة',
    'alert.threshold_breach': 'تجاوز الحد',
    'alert.open': 'مفتوح',
    'alert.investigating': 'قيد التحقيق',
    'alert.resolved': 'تم الحل',

    // Common
    'common.search': 'بحث...',
    'common.filter': 'تصفية',
    'common.export': 'تصدير',
    'common.refresh': 'تحديث',
    'common.loading': 'جاري التحميل...',
    'common.no_data': 'لا توجد بيانات',
    'common.view_all': 'عرض الكل',
    'common.save': 'حفظ',
    'common.cancel': 'إلغاء',
    'common.confirm': 'تأكيد',
    'common.language': 'اللغة',
    'common.english': 'English',
    'common.arabic': 'العربية',

    // Copilot
    'copilot.title': 'مساعد الحوكمة',
    'copilot.placeholder': 'من استخدم بيانات العملاء؟',
    'copilot.greeting': 'مرحباً! كيف يمكنني مساعدتك في تأمين بياناتك اليوم؟',

    // Auth
    'auth.login': 'تسجيل الدخول',
    'auth.logout': 'تسجيل الخروج',
    'auth.username': 'اسم المستخدم',
    'auth.password': 'كلمة المرور',
  },
};

export function t(key: string, locale: Locale = 'en'): string {
  return translations[locale]?.[key] || key;
}
