import { useState } from 'react';
import { useSelector } from 'react-redux';
import { X, CheckCircle, User, Clock, MessageSquare, Stethoscope, ShieldAlert, Loader2, AlertCircle, ThumbsUp } from 'lucide-react';

function SummaryRow({ icon: Icon, label, value }) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-3.5">
      <div className="bg-blue-50 p-2 rounded-lg shrink-0 mt-0.5 border border-blue-100">
        <Icon className="w-4 h-4 text-blue-600" />
      </div>
      <div className="min-w-0">
        <p className="text-[11px] font-bold text-blue-600 uppercase tracking-wider">{label}</p>
        <p className="text-sm font-semibold text-gray-900 truncate mt-0.5">{value}</p>
      </div>
    </div>
  );
}

export default function ConfirmModal({ onConfirm, onCancel }) {
  const { fields, complianceFlag } = useSelector((s) => s.form);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const handleConfirm = async () => {
    setSaving(true);
    setFeedback(null);
    try {
      await onConfirm();
      setFeedback({ type: 'success', message: 'Saved successfully!' });
      setTimeout(() => onCancel(), 1200);
    } catch (e) {
      setFeedback({ type: 'error', message: e.message || 'Save failed.' });
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/45 backdrop-blur-sm z-50 flex items-center justify-center p-4 transition-all duration-200">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden flex flex-col border border-gray-100">
        <div className="bg-[#1e3a8a] px-5 py-4 flex justify-between items-center text-white">
          <div className="flex items-center gap-3">
            <div className="bg-white/10 p-2 rounded-lg">
              <Stethoscope className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-bold leading-tight">Confirm Save</h3>
              <p className="text-blue-100 text-[11px] leading-tight mt-0.5">Review before saving to database</p>
            </div>
          </div>
          <button onClick={onCancel} className="p-1.5 rounded-lg hover:bg-white/15 transition-all duration-200 cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 space-y-4 bg-gray-50/50 max-h-[60vh] overflow-y-auto scrollbar">
          <SummaryRow icon={User} label="HCP Name" value={fields.hcp_name} />
          <SummaryRow icon={MessageSquare} label="Interaction Type" value={fields.interaction_type} />
          <SummaryRow icon={Clock} label="Date & Time" value={[fields.date, fields.time].filter(Boolean).join(' at ') || null} />
          <SummaryRow icon={User} label="Attendees" value={fields.attendees} />
          <SummaryRow icon={ThumbsUp} label="Sentiment" value={fields.sentiment} />
          {fields.topics_discussed && <SummaryRow icon={MessageSquare} label="Topics Discussed" value={fields.topics_discussed} />}
          {fields.outcomes && <SummaryRow icon={MessageSquare} label="Outcomes" value={fields.outcomes} />}
          {fields.products?.length > 0 && <SummaryRow icon={MessageSquare} label="Products" value={fields.products.map(p => p.product_name || p.productName).join(', ')} />}
          {complianceFlag && (
            <div className="flex items-center gap-2 bg-red-50 border border-red-100 text-red-700 px-3.5 py-2.5 rounded-lg text-xs mt-1">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <span className="font-bold">Compliance flag is set</span>
            </div>
          )}
        </div>

        {feedback && (
          <div className={`px-6 py-3 text-xs font-bold flex items-center gap-2 ${feedback.type === 'success' ? 'bg-emerald-50 text-emerald-700 border-t border-b border-emerald-100' : 'bg-red-50 text-red-700 border-t border-b border-red-100'}`}>
            {feedback.type === 'success' ? <CheckCircle className="w-4 h-4 text-emerald-600" /> : <AlertCircle className="w-4 h-4 text-red-600" />}
            {feedback.message}
          </div>
        )}

        <div className="px-6 py-4 bg-white border-t border-gray-100 flex justify-end gap-3.5">
          <button onClick={onCancel} disabled={saving} className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-bold text-gray-700 hover:bg-gray-50 flex items-center gap-2 transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
            Cancel
          </button>
          <button onClick={handleConfirm} disabled={saving} className="px-6 py-2 bg-[#2563eb] hover:bg-[#1d4ed8] rounded-lg text-sm font-bold text-white flex items-center gap-2 shadow-sm transition-all duration-200 cursor-pointer disabled:bg-gray-200 disabled:text-gray-400 disabled:shadow-none disabled:cursor-not-allowed">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
            {saving ? 'Saving...' : 'Confirm Save'}
          </button>
        </div>
      </div>
    </div>
  );
}
