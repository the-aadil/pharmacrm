import { useState, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { X, CheckCircle, Loader2, AlertCircle } from 'lucide-react';

export default function ConfirmModal({ onConfirm, onCancel }) {
  const { fields, complianceFlag } = useSelector((s) => s.form);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const handleConfirm = useCallback(async () => {
    if (saving) return;

    if (!fields.hcp_name?.trim()) {
      setFeedback({ type: 'error', message: 'HCP Name is required.' });
      return;
    }

    setSaving(true);
    setFeedback(null);

    try {
      await onConfirm();
      setFeedback({ type: 'success', message: 'Saved successfully!' });
      setTimeout(() => onCancel(), 1200);
    } catch (e) {
      setFeedback({ type: 'error', message: e.message || 'Save failed. Please try again.' });
    } finally {
      setSaving(false);
    }
  }, [saving, fields.hcp_name, onConfirm, onCancel]);

  const rows = [
    { label: 'HCP Name', value: fields.hcp_name },
    { label: 'Type', value: fields.interaction_type },
    { label: 'Date', value: fields.date },
    { label: 'Time', value: fields.time },
    { label: 'Attendees', value: fields.attendees },
    { label: 'Sentiment', value: fields.sentiment },
    { label: 'Topics', value: fields.topics_discussed },
    { label: 'Outcomes', value: fields.outcomes },
    { label: 'Products', value: fields.products?.map(p => p.product_name).join(', ') },
    { label: 'Summary', value: fields.ai_summary },
  ];

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-sm overflow-hidden">
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-sm font-bold text-gray-800">Confirm Save</h3>
          <button onClick={onCancel} disabled={saving} className="p-1 rounded hover:bg-gray-100 cursor-pointer disabled:opacity-50">
            <X className="w-4 h-4 text-gray-500" />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-4 space-y-2.5 max-h-[50vh] overflow-y-auto">
          {rows.map((r, i) => {
            if (!r.value) return null;
            return (
              <div key={i} className="flex text-sm">
                <span className="w-24 shrink-0 text-gray-500 font-medium">{r.label}</span>
                <span className="text-gray-800 font-semibold truncate">{r.value}</span>
              </div>
            );
          })}
          {complianceFlag && (
            <div className="mt-2 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-xs font-semibold text-red-700">
              Compliance flag is set
            </div>
          )}
        </div>

        {/* Feedback */}
        {feedback && (
          <div className={`px-5 py-2.5 text-xs font-bold flex items-center gap-2 ${feedback.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
            {feedback.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
            {feedback.message}
          </div>
        )}

        {/* Footer */}
        <div className="px-5 py-3 border-t border-gray-200 flex justify-end gap-3">
          <button onClick={onCancel} disabled={saving} className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 hover:bg-gray-50 cursor-pointer disabled:opacity-50">
            Cancel
          </button>
          <button onClick={handleConfirm} disabled={saving} className="px-5 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-semibold text-white flex items-center gap-2 cursor-pointer disabled:opacity-50">
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}
