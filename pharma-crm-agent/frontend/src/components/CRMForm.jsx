import { useState, memo } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { setFormField, resetForm } from '../store/formSlice';
import { addMessage } from '../store/chatSlice';
import { confirmInteraction } from '../api';
import ConfirmModal from './ConfirmModal';
import { CheckCircle, Edit2, RotateCcw, AlertTriangle, Clock, Mic, Search, Plus } from 'lucide-react';

const INTERACTION_TYPES = [
  { value: 'meeting', label: 'Meeting' },
  { value: 'visit',   label: 'Visit'   },
  { value: 'call',    label: 'Call'    },
  { value: 'email',   label: 'Email'   },
  { value: 'conference', label: 'Conference' },
];

/* ─────────────────── STYLE CONSTANTS ─────────────────── */

const TITLE_CLASS = 'text-xl font-bold text-gray-800 mb-6';
const SECTION_HEADING_CLASS = 'text-[10px] uppercase font-bold tracking-wider text-gray-500 mt-6 mb-3';
const LABEL_CLASS = 'text-[10px] uppercase font-semibold text-gray-500 block mb-2';

const INPUT_CLASS = '!bg-white border border-gray-300 rounded-md px-3 py-2.5 text-sm text-gray-800 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:opacity-70 disabled:cursor-not-allowed shadow-sm placeholder:text-gray-400';
const TEXTAREA_CLASS = 'w-full bg-white border border-gray-300 rounded-md px-3 py-2.5 text-sm text-gray-800 shadow-sm placeholder:text-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 resize-y h-24 min-h-[6rem]';

/* ─────────────────── HELPERS ─────────────────── */

const formatDateForInput = (dateStr) => {
  if (!dateStr) return '';
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return dateStr;
  
  const mdParts = dateStr.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (mdParts) {
    return `${mdParts[3]}-${mdParts[1].padStart(2, '0')}-${mdParts[2].padStart(2, '0')}`;
  }
  
  const dmParts = dateStr.match(/^(\d{1,2})-(\d{1,2})-(\d{4})$/);
  if (dmParts) {
    return `${dmParts[3]}-${dmParts[2].padStart(2, '0')}-${dmParts[1].padStart(2, '0')}`;
  }

  try {
    const d = new Date(dateStr);
    if (!isNaN(d.getTime())) {
      const year = d.getFullYear();
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    }
  } catch {}
  return '';
};

const formatTimeForInput = (timeStr) => {
  if (!timeStr) return '';
  if (/^\d{2}:\d{2}$/.test(timeStr)) return timeStr;
  if (/^\d{2}:\d{2}:\d{2}$/.test(timeStr)) return timeStr.slice(0, 5);

  const pmParts = timeStr.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
  if (pmParts) {
    let [_, h, m, ampm] = pmParts;
    let hours = parseInt(h, 10);
    if (ampm.toUpperCase() === 'PM' && hours < 12) hours += 12;
    if (ampm.toUpperCase() === 'AM' && hours === 12) hours = 0;
    return `${hours.toString().padStart(2, '0')}:${m}`;
  }
  return '';
};

/* ─────────────────────────────────────────────────────────────── */

function CRMForm() {
  const dispatch = useDispatch();
  const { fields, complianceFlag, complianceNotes, status, suggestions } = useSelector((s) => s.form);
  const isStatusPending = useSelector((s) => s.form.isStatusPending);
  const [showModal, setShowModal]   = useState(false);
  const [error, setError]           = useState('');
  const [isEditing, setIsEditing]   = useState(false);

  const handleChange = (key, value) => dispatch(setFormField({ key, value }));
  const handleConfirm = () => setShowModal(true);

  const handleConfirmedSave = async () => {
    try {
      const payload = { ...fields, compliance_flag: complianceFlag, compliance_notes: complianceNotes };
      const result = await confirmInteraction(payload);
      if (result.status === 'committed_to_db' || result.status === 'confirmed') {
        dispatch(addMessage({ role: 'ai', content: 'Interaction saved to database successfully!', toolsCalled: ['confirm_and_save_interaction'] }));
        dispatch(resetForm());
        setIsEditing(false);
        return;
      }
      setError(result.message || 'Failed to save interaction.');
    } catch (err) {
      setError(err.message || 'Failed to save interaction.');
    }
  };

  const handleEdit  = () => setIsEditing(true);
  const handleReset = () => { dispatch(resetForm()); setIsEditing(false); setError(''); };

  return (
    <div className="flex flex-col h-full bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden">
      
      {/* Scrollable form content with card padding */}
      <div className="flex-1 overflow-y-auto p-6 pr-5 pb-4">
        
        {/* ── Status banners ── */}
        {isStatusPending && (
          <div className="mb-4 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 flex items-center gap-2 text-sm font-semibold shadow-sm">
            <Clock size={16} className="shrink-0 text-amber-700" />
            Pending Confirmation — Review data before saving
          </div>
        )}
        {complianceFlag && (
          <div className="mb-4 rounded-lg flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm shadow-sm">
            <AlertTriangle size={16} className="shrink-0" />
            <span className="font-semibold">COMPLIANCE ALERT: Adverse event or off-label use detected</span>
          </div>
        )}
        {error && (
          <div className="mb-4 rounded-lg flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm shadow-sm">
            <AlertTriangle size={16} className="shrink-0" /> {error}
          </div>
        )}

        {/* ── Page title ── */}
        <h1 className={TITLE_CLASS}>Log HCP Interaction</h1>

        {/* ══════════════════════════════════════
            INTERACTION DETAILS
        ══════════════════════════════════════ */}
        <div className="mb-4">
          <label className={SECTION_HEADING_CLASS}>Interaction Details</label>

          {/* Grid Layout for HCP Name, Interaction Type, Date, Time */}
          <div className="grid grid-cols-2 gap-5 w-full min-w-0">
            <div>
              <label className={LABEL_CLASS}>HCP Name</label>
              <input
                type="text"
                value={fields.hcp_name || ''}
                onChange={(e) => handleChange('hcp_name', e.target.value)}
                readOnly={!isEditing}
                disabled={!isEditing}
                placeholder="Search or select HCP..."
                className={INPUT_CLASS}
              />
            </div>
            <div>
              <label className={LABEL_CLASS}>Interaction Type</label>
              <select
                value={fields.interaction_type || 'meeting'}
                onChange={(e) => handleChange('interaction_type', e.target.value)}
                disabled={!isEditing}
                className={INPUT_CLASS + ' appearance-auto cursor-pointer'}
              >
                {INTERACTION_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className={LABEL_CLASS}>Date</label>
              <input
                type="date"
                value={fields.date || ''}
                onChange={(e) => handleChange('date', e.target.value)}
                className="w-full bg-white border border-gray-300 rounded-md px-3 py-2.5 text-sm text-gray-800 shadow-sm appearance-auto"
              />
            </div>
            <div>
              <label className={LABEL_CLASS}>Time</label>
              <input
                type="time"
                value={fields.time || ''}
                onChange={(e) => handleChange('time', e.target.value)}
                className="w-full bg-white border border-gray-300 rounded-md px-3 py-2.5 text-sm text-gray-800 shadow-sm appearance-auto"
              />
            </div>
          </div>
        </div>

        {/* Attendees (Full-width, outside grid but inside Interaction Details section) */}
        <div className="mb-4">
          <label className={LABEL_CLASS}>Attendees</label>
          <input
            type="text"
            value={fields.attendees || ''}
            onChange={(e) => handleChange('attendees', e.target.value)}
            readOnly={!isEditing}
            disabled={!isEditing}
            placeholder="Enter names or search..."
            className={INPUT_CLASS}
          />
        </div>

        <div className="border-t border-gray-200 my-5"></div>

        {/* ══════════════════════════════════════
            TOPICS DISCUSSED
        ══════════════════════════════════════ */}
        <div className="mb-4">
          <label className={SECTION_HEADING_CLASS}>Topics Discussed</label>

          <textarea
            value={fields.topics_discussed || ''}
            onChange={(e) => handleChange('topics_discussed', e.target.value)}
            readOnly={!isEditing}
            disabled={!isEditing}
            placeholder="Enter key discussion points..."
            className={TEXTAREA_CLASS}
          />
          <button
            type="button"
            className="flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-700 mt-2 transition-colors cursor-pointer"
          >
            <Mic size={14} className="text-gray-500" />
            <span>Summarize from Voice Note (Requires Consent)</span>
          </button>
        </div>

        <div className="border-t border-gray-200 my-5"></div>

        {/* ══════════════════════════════════════
            MATERIALS SHARED / SAMPLES DISTRIBUTED
        ══════════════════════════════════════ */}
        <div className="mb-4">
          <label className={SECTION_HEADING_CLASS}>Materials Shared / Samples Distributed</label>

          {/* Materials Shared */}
          <div className="flex items-center justify-between border border-gray-100 rounded-lg p-3 bg-gray-50/50 mb-3">
            <div>
              <label className={LABEL_CLASS}>Materials Shared</label>
              {(!fields.products || fields.products.length === 0) ? (
                <p className="text-xs text-gray-550 mt-1">No materials added.</p>
              ) : (
                <ul className="mt-1 space-y-0.5">
                  {fields.products.map((prod, i) => (
                    <li key={i} className="text-xs text-gray-900 font-medium">
                      {prod.product_name || prod.productName || ''}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <button
              type="button"
              className="flex items-center gap-1.5 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg px-3 py-1.5 text-xs font-semibold shadow-sm transition-colors cursor-pointer shrink-0 ml-4"
            >
              <Search size={14} className="text-blue-500" />
              Search/Add
            </button>
          </div>

          {/* Samples Distributed */}
          <div className="flex items-center justify-between border border-gray-100 rounded-lg p-3 bg-gray-50/50">
            <div>
              <label className={LABEL_CLASS}>Samples Distributed</label>
              <p className="text-xs text-gray-550 mt-1">No samples added.</p>
            </div>
            <button
              type="button"
              className="flex items-center gap-1.5 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 rounded-lg px-3 py-1.5 text-xs font-semibold shadow-sm transition-colors cursor-pointer shrink-0 ml-4"
            >
              <Plus size={14} className="text-purple-500" />
              Add Sample
            </button>
          </div>
        </div>

        <div className="border-t border-gray-200 my-5"></div>

        {/* ══════════════════════════════════════
            OBSERVED/INFERRED HCP SENTIMENT
        ══════════════════════════════════════ */}
        <div className="mb-4">
          <label className={SECTION_HEADING_CLASS}>Observed/Inferred HCP Sentiment</label>

          <div className="flex items-center gap-6 mt-2">
            {[
              { value: 'positive', emoji: '😊', label: 'Positive' },
              { value: 'neutral',  emoji: '😐', label: 'Neutral'  },
              { value: 'negative', emoji: '🙁', label: 'Negative' },
            ].map((opt) => (
              <div
                key={opt.value}
                onClick={() => isEditing && handleChange('sentiment', opt.value)}
                className={`flex items-center gap-2 text-sm font-medium text-gray-700 cursor-pointer select-none ${!isEditing ? 'pointer-events-none opacity-75' : ''}`}
              >
                <input
                  type="radio"
                  name="sentiment"
                  value={opt.value}
                  checked={fields.sentiment === opt.value}
                  onChange={() => handleChange('sentiment', opt.value)}
                  disabled={!isEditing}
                  className="h-4 w-4 text-purple-600 border-gray-300 focus:ring-purple-500 disabled:opacity-50 cursor-pointer"
                />
                <span>{opt.emoji} {opt.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-gray-200 my-5"></div>

        {/* ══════════════════════════════════════
            OUTCOMES
        ══════════════════════════════════════ */}
        <div className="mb-4">
          <label className={LABEL_CLASS}>Outcomes</label>
          <textarea
            value={fields.outcomes || ''}
            onChange={(e) => handleChange('outcomes', e.target.value)}
            readOnly={!isEditing}
            disabled={!isEditing}
            placeholder="Key outcomes or agreements..."
            className={TEXTAREA_CLASS}
          />
        </div>

        <div className="border-t border-gray-200 my-5"></div>

        {/* ══════════════════════════════════════
            FOLLOW-UP ACTIONS
        ══════════════════════════════════════ */}
        <div className="mb-4">
          <label className={LABEL_CLASS}>Follow-up Actions</label>
          <textarea
            value={(fields.follow_ups || []).map((fu) => `${fu.due_date ? `Due: ${fu.due_date} — ` : ''}${fu.note || ''}`).join('\n') || ''}
            onChange={(e) => handleChange('follow_ups', e.target.value ? [{ note: e.target.value }] : [])}
            readOnly={!isEditing}
            disabled={!isEditing}
            placeholder="Describe follow-up actions..."
            className={TEXTAREA_CLASS}
          />
        </div>

        {/* ── Suggestions ── */}
        {suggestions && suggestions.length > 0 && (
          <div className="space-y-1.5 mb-6">
            {suggestions.map((s, i) => (
              <p key={i} className="text-sm font-semibold text-blue-600">+ {s}</p>
            ))}
          </div>
        )}

        {/* ── AI Summary ── */}
        {fields.ai_summary && (
          <div className="mb-6 bg-blue-50 border border-blue-150 rounded-lg px-4 py-3">
            <p className="text-xs font-bold text-blue-700 uppercase tracking-wider mb-1.5">AI Summary</p>
            <textarea
              value={fields.ai_summary || ''}
              readOnly
              className="w-full bg-transparent border-none text-sm text-gray-800 leading-relaxed resize-none outline-none"
              rows={3}
            />
          </div>
        )}

        {/* ── Compliance Notes ── */}
        {complianceNotes && (
          <div className="mb-6 bg-red-50 border border-red-150 rounded-lg px-4 py-3">
            <p className="text-xs font-bold text-red-700 uppercase tracking-wider mb-1.5">Compliance Notes</p>
            <p className="text-sm text-red-700 font-medium leading-relaxed">{complianceNotes}</p>
          </div>
        )}
      </div>

      <div className="mt-auto pt-4 pb-3 border-t border-gray-200 flex items-center justify-end gap-3 bg-white rounded-b-xl px-6">
        <button onClick={handleConfirm} disabled={status !== 'pending_confirmation'} className="px-4 py-1.5 border border-gray-300 rounded-md bg-white hover:bg-gray-50 text-[11px] font-semibold flex items-center gap-1.5 text-gray-700 shadow-sm transition-colors disabled:opacity-50">
          <CheckCircle size={14} /> Confirm
        </button>
        <button onClick={handleEdit} disabled={status !== 'pending_confirmation' || isEditing} className="px-4 py-1.5 border border-gray-300 rounded-md bg-white hover:bg-gray-50 text-[11px] font-semibold flex items-center gap-1.5 text-gray-700 shadow-sm transition-colors disabled:opacity-50">
          <Edit2 size={14} /> Edit
        </button>
        <button onClick={handleReset} className="px-4 py-1.5 border border-gray-300 rounded-md bg-white hover:bg-gray-50 text-[11px] font-semibold flex items-center gap-1.5 text-gray-700 shadow-sm transition-colors">
          <RotateCcw size={14} /> Reset
        </button>
      </div>

      {showModal && <ConfirmModal onConfirm={handleConfirmedSave} onCancel={() => setShowModal(false)} />}
    </div>
  );
}

export default memo(CRMForm);
