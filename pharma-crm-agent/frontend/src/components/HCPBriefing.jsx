import { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { setBriefing, setIsLoadingBriefing } from '../store/formSlice';
import { getHCPBriefing } from '../api';
import { User, Stethoscope, Calendar, Loader2, AlertCircle, Sparkles } from 'lucide-react';

export default function HCPBriefing({ hcpName }) {
  const dispatch = useDispatch();
  const { briefing, isLoadingBriefing } = useSelector((s) => s.form);
  const [error, setError] = useState('');

  const fetchBriefing = async () => {
    if (!hcpName.trim()) { setError('Please enter an HCP name first'); return; }
    setError('');
    dispatch(setIsLoadingBriefing(true));
    try {
      const result = await getHCPBriefing(hcpName);
      if (result.status === 'not_found') { setError(result.message || 'HCP not found'); dispatch(setBriefing(null)); }
      else if (result.status === 'success') { dispatch(setBriefing(result)); }
      else { setError('Failed to fetch briefing'); }
    } catch { setError('Failed to fetch briefing.'); }
    finally { dispatch(setIsLoadingBriefing(false)); }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="bg-blue-100 rounded-lg p-1.5"><Sparkles className="w-3.5 h-3.5 text-blue-600" /></div>
          <h3 className="text-xs font-bold text-blue-800 uppercase tracking-wide">AI Pre-Visit Briefing</h3>
        </div>
        <button onClick={fetchBriefing} disabled={isLoadingBriefing || !hcpName.trim()}
          className="flex items-center gap-1.5 px-2.5 py-1.5 text-[10px] font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors disabled:opacity-50">
          {isLoadingBriefing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
          {briefing ? 'Refresh' : 'Get Briefing'}
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-xs">
          <AlertCircle className="w-3 h-3 shrink-0" /> {error}
        </div>
      )}

      {briefing && !error && (
        <div className="space-y-2">
          {briefing.hcp && (
            <div className="bg-white rounded-lg p-3 border border-blue-100">
              <div className="flex items-center gap-2 text-xs">
                <User className="w-3.5 h-3.5 text-blue-600" />
                <span className="font-semibold text-slate-800">{briefing.hcp.name}</span>
                <span className="text-slate-400">•</span>
                <Stethoscope className="w-3 h-3 text-slate-400" />
                <span className="text-slate-500">{briefing.hcp.specialty}</span>
              </div>
            </div>
          )}
          {briefing.recent?.length > 0 && (
            <div className="bg-white rounded-lg p-3 border border-blue-100">
              <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Recent</h4>
              {briefing.recent.slice(0, 3).map((r, i) => (
                <div key={i} className="flex items-center gap-1.5 text-[11px] text-slate-600">
                  <Calendar className="w-3 h-3 text-slate-300 shrink-0" />
                  <span className="font-medium">{r.type}</span> • <span>{r.duration}min</span> • <span>{r.sentiment}</span>
                </div>
              ))}
            </div>
          )}
          {briefing.briefing && (
            <div className="bg-white rounded-lg p-3 border border-blue-100">
              <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Briefing</h4>
              <p className="text-xs text-slate-600 leading-relaxed">{briefing.briefing}</p>
            </div>
          )}
        </div>
      )}

      {!briefing && !error && !isLoadingBriefing && (
        <p className="text-[11px] text-blue-500 text-center py-1">Click "Get Briefing" to generate an AI pre-visit briefing.</p>
      )}
    </div>
  );
}
