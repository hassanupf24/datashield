'use client';

import { useState } from 'react';
import { Locale, t } from '@/lib/i18n';
import { Bot, Send, X, Sparkles } from 'lucide-react';

interface CopilotChatProps {
  locale: Locale;
  onClose: () => void;
}

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
}

const demoResponses: Record<string, Record<Locale, string>> = {
  default: {
    en: "I can help you with data governance queries. Try asking:\n• Who accessed customer data today?\n• What's the current compliance score?\n• Show me high-risk users",
    ar: "يمكنني مساعدتك في استفسارات حوكمة البيانات. جرّب:\n• من استخدم بيانات العملاء اليوم؟\n• ما درجة الامتثال الحالية؟\n• أظهر لي المستخدمين ذوي الخطورة العالية",
  },
  customer: {
    en: "📊 **Customer Data Access Report (Today)**\n\n3 users accessed customer data:\n1. **ahmad@bank.sa** — EXPORT at 10:42 AM ⚠️ Risk: HIGH (82)\n2. **sara@bank.sa** — READ at 10:38 AM ✅ Risk: LOW (15)\n3. **nora@bank.sa** — EXPORT at 10:22 AM ⚠️ Risk: HIGH (78)\n\n🔴 2 anomalous exports detected. Recommend immediate review.\n\n_Source: Access Events DB, Trace IDs: evt-001, evt-002, evt-006_",
    ar: "📊 **تقرير الوصول لبيانات العملاء (اليوم)**\n\n3 مستخدمين وصلوا لبيانات العملاء:\n1. **أحمد@bank.sa** — تصدير في 10:42 ص ⚠️ خطورة: عالية (82)\n2. **سارة@bank.sa** — قراءة في 10:38 ص ✅ خطورة: منخفضة (15)\n3. **نورة@bank.sa** — تصدير في 10:22 ص ⚠️ خطورة: عالية (78)\n\n🔴 تم اكتشاف عمليتي تصدير شاذة. يُوصى بالمراجعة الفورية.\n\n_المصدر: قاعدة أحداث الوصول_",
  },
};

export default function CopilotChat({ locale, onClose }: CopilotChatProps) {
  const isAr = locale === 'ar';
  const [messages, setMessages] = useState<Message[]>([
    { id: 0, role: 'assistant', content: t('copilot.greeting', locale) },
  ]);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg: Message = { id: Date.now(), role: 'user', content: input };
    setMessages((prev) => [...prev, userMsg]);

    // Simple demo response matching
    const lower = input.toLowerCase();
    const isCustomerQuery = lower.includes('customer') || lower.includes('عملاء') || lower.includes('بيانات');
    const response = isCustomerQuery ? demoResponses.customer[locale] : demoResponses.default[locale];

    setTimeout(() => {
      setMessages((prev) => [...prev, { id: Date.now() + 1, role: 'assistant', content: response }]);
    }, 800);
    setInput('');
  };

  return (
    <div className="fixed bottom-24 end-6 z-50 w-96 h-[520px] flex flex-col glass-card overflow-hidden shadow-2xl shadow-brand-500/10 animated-border">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-800/50 bg-slate-900/80">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <span className="font-semibold text-sm">{t('copilot.title', locale)}</span>
            <p className="text-[10px] text-slate-500">{isAr ? 'مدعوم بالذكاء الاصطناعي' : 'AI-Powered'}</p>
          </div>
        </div>
        <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-800 transition-colors">
          <X className="w-4 h-4 text-slate-400" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-xl px-4 py-2.5 text-sm whitespace-pre-wrap ${
              msg.role === 'user'
                ? 'bg-brand-600 text-white rounded-ee-sm'
                : 'bg-slate-800/60 text-slate-200 rounded-es-sm border border-slate-700/50'
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="p-3 border-t border-slate-800/50 bg-slate-900/50">
        <div className="relative">
          <input
            type="text"
            dir="auto"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={t('copilot.placeholder', locale)}
            className="w-full bg-slate-800/80 border border-slate-700/50 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500 pe-10 placeholder:text-slate-500"
          />
          <button
            onClick={handleSend}
            className="absolute end-2 top-2 p-1 text-slate-400 hover:text-brand-400 transition-colors"
          >
            <Send className={`w-4 h-4 ${isAr ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>
    </div>
  );
}
