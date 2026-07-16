import { useState } from 'react';
import { useSelector } from 'react-redux';
import { X, CheckCircle2, XCircle, User, Clock, ThumbsUp, MessageSquareText, Package, ShieldAlert, Stethoscope, Loader2, AlertCircle } from 'lucide-react';

export default function ConfirmationModal({ onConfirm, onCancel }) {
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
    <div className="fixed inset-0 bg-black/45 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-all duration-200">
      <div className="bg-white rounded-xl shadow-2xl max-w-sm w-full overflow-hidden border border-gray-100">
        
        {/* ── HEADER ──────────────────────────────────── */}
        <div className="bg-[#1e3a8a] text-white px-5 py-4 relative flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="bg-white/10 p-2 rounded-lg">
              <Stethoscope className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-bold leading-tight">Confirm Save</h3>
              <p className="text-blue-100 text-[11px] leading-tight mt-0.5">Review before saving to database</p>
            </div>
          </div>
          <button onClick={onCancel} className="p-1.5 rounded-lg hover:bg-white/15 transition-all duration-200 cursor-pointer">
            <X className="w-4 h-4 text-white" />
          </button>
        </div>

        {/* ── BODY (DATA LIST) ─────────────────────────── */}
        <div className="px-5 py-4 space-y-3.5 bg-gray-50/50 max-h-[60vh] overflow-y-auto scrollbar">
          <SummaryRow icon={User} label="HCP" value={fields.hcp_name} />
          <SummaryRow icon={MessageSquareText} label="Type" value={fields.interaction_type} />
          <SummaryRow icon={Clock} label="Duration" value={`${fields.duration_minutes} min`} />
          <SummaryRow icon={ThumbsUp} label="Sentiment" value={fields.sentiment} />
          {fields.topics_discussed && <SummaryRow icon={MessageSquareText} label="Topics" value={fields.topics_discussed} />}
          {fields.products?.length > 0 && <SummaryRow icon={Package} label="Products" value={fields.products.map(p => p.product_name).join(', ')} />}
          {complianceFlag && (
            <div className="flex items-center gap-2 bg-red-50 border border-red-100 text-red-700 px-3.5 py-2.5 rounded-lg text-xs mt-2">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <span className="font-bold">Compliance flag is set</span>
            </div>
          )}
        </div>

        {/* ── FEEDBACK ─────────────────────────────────── */}
        {feedback && (
          <div className={`px-5 py-2.5 text-xs font-bold flex items-center gap-2 ${feedback.type === 'success' ? 'bg-emerald-50 text-emerald-700 border-t border-b border-emerald-100' : 'bg-red-50 text-red-700 border-t border-b border-red-100'}`}>
            {feedback.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <AlertCircle className="w-4 h-4 text-red-600" />}
            {feedback.message}
          </div>
        )}

        {/* ── FOOTER BUTTONS ───────────────────────────── */}
        <div className="flex gap-3.5 px-5 py-4 border-t border-gray-100 bg-white justify-end">
          <button onClick={onCancel} disabled={saving} className="px-4 py-2 border border-gray-300 rounded-lg text-xs font-bold text-gray-700 hover:bg-gray-50 flex-1 flex items-center justify-center gap-2 transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
            <XCircle className="w-3.5 h-3.5" /> Cancel
          </button>
          <button onClick={handleConfirm} disabled={saving} className="px-6 py-2 bg-[#2563eb] hover:bg-[#1d4ed8] rounded-lg text-xs font-bold text-white flex-1 flex items-center justify-center gap-2 shadow-sm transition-all duration-200 cursor-pointer disabled:bg-gray-200 disabled:text-gray-400 disabled:shadow-none disabled:cursor-not-allowed">
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
            {saving ? 'Saving...' : 'Confirm Save'}
          </button>
        </div>
      </div>
    </div>
  );
}

function SummaryRow({ icon: Icon, label, value }) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-3">
      <div className="bg-blue-50 p-2 rounded-lg shrink-0 mt-0.5 border border-blue-100">
        <Icon className="w-3.5 h-3.5 text-blue-600" />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{label}</p>
        <p className="text-xs text-slate-800 font-bold truncate mt-0.5">{value}</p>
      </div>
    </div>
  );
}
