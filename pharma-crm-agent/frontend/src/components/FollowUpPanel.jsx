import { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { addFollowUp } from '../store/formSlice';
import { scheduleFollowUp } from '../api';
import { Calendar, Plus, Loader2, AlertCircle, CheckCircle } from 'lucide-react';

const INPUT_CLASS = 'w-full h-[40px] px-3.5 py-2 border border-[#e2e8f0] rounded-lg text-[13px] text-[#1f2937] placeholder-[#9ca3af] focus:outline-none focus:border-black focus:ring-1 focus:ring-black bg-[#f8fafc] disabled:bg-[#f8fafc] disabled:opacity-90 disabled:cursor-not-allowed transition-all duration-200';
const LABEL_CLASS = 'block text-[13px] font-bold text-[#374151] mb-1.5';

export default function FollowUpPanel({ hcpName }) {
  const dispatch = useDispatch();
  const { followUps } = useSelector((s) => s.form);
  const [dueDescription, setDueDescription] = useState('');
  const [note, setNote] = useState('');
  const [error, setError] = useState('');
  const [isScheduling, setIsScheduling] = useState(false);

  const handleSchedule = async () => {
    if (!hcpName.trim() || !dueDescription.trim() || !note.trim()) { setError('Please fill in all fields'); return; }
    setError('');
    setIsScheduling(true);
    try {
      const result = await scheduleFollowUp(hcpName, dueDescription, note);
      if (result.status === 'scheduled') {
        dispatch(addFollowUp({ id: result.id, due_date: result.due_date, note: result.note, status: 'scheduled' }));
        setDueDescription(''); setNote('');
      } else if (result.status === 'not_found') { setError(result.message || 'HCP not found'); }
      else { setError('Failed to schedule follow-up'); }
    } catch { setError('Failed to schedule follow-up.'); }
    finally { setIsScheduling(false); }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <div className="bg-green-100 rounded-lg p-1.5"><Calendar className="w-3.5 h-3.5 text-green-600" /></div>
        <h3 className="text-[15px] font-bold text-[#111827] mb-0">Schedule Follow-up</h3>
      </div>

      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-100 text-red-700 px-3.5 py-2.5 rounded-lg text-xs mt-1">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" /> {error}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className={LABEL_CLASS}>When?</label>
          <input type="text" value={dueDescription} onChange={(e) => setDueDescription(e.target.value)}
            placeholder="e.g. next Tuesday, in 2 weeks" className={`${INPUT_CLASS} placeholder:text-[13px]`} />
        </div>
        <div>
          <label className={LABEL_CLASS}>What?</label>
          <input type="text" value={note} onChange={(e) => setNote(e.target.value)}
            placeholder="Follow-up action..." className={`${INPUT_CLASS} placeholder:text-[13px]`} />
        </div>
      </div>
      <button onClick={handleSchedule}
        disabled={isScheduling || !hcpName.trim() || !dueDescription.trim() || !note.trim()}
        className="w-full flex items-center justify-center gap-2 px-5 py-2 text-[13px] font-bold text-white bg-green-600 hover:bg-green-700 rounded-lg shadow-sm transition-all duration-200 cursor-pointer disabled:bg-gray-200 disabled:text-gray-400 disabled:shadow-none disabled:cursor-not-allowed">
        {isScheduling ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
        Schedule Follow-up
      </button>

      {followUps?.length > 0 && (
        <div className="space-y-1.5">
          {followUps.map((f, i) => (
            <div key={i} className="flex items-center gap-2 text-[11px] text-slate-600 bg-green-50 rounded-lg px-2.5 py-1.5 border border-green-100">
              <CheckCircle className="w-3 h-3 text-green-600 shrink-0" />
              <span className="font-medium">{f.due_date}</span> — {f.note}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
