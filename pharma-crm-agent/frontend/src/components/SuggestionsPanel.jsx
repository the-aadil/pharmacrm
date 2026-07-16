import { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { setSuggestions, setIsLoadingSuggestions } from '../store/formSlice';
import { getSuggestions } from '../api';
import { Lightbulb, Loader2, AlertCircle, Target, TrendingUp } from 'lucide-react';

const INPUT_CLASS = 'w-full h-[40px] px-3.5 py-2 border border-[#e2e8f0] rounded-lg text-[13px] text-[#1f2937] placeholder-[#9ca3af] focus:outline-none focus:border-black focus:ring-1 focus:ring-black bg-[#f8fafc] disabled:bg-[#f8fafc] disabled:opacity-90 disabled:cursor-not-allowed transition-all duration-200';
const LABEL_CLASS = 'block text-[13px] font-bold text-[#374151] mb-1.5';

export default function SuggestionsPanel({ hcpName }) {
  const dispatch = useDispatch();
  const { suggestions, isLoadingSuggestions } = useSelector((s) => s.form);
  const [error, setError] = useState('');

  const fetchSuggestions = async () => {
    if (!hcpName.trim()) { setError('Please enter an HCP name first'); return; }
    setError('');
    dispatch(setIsLoadingSuggestions(true));
    try {
      const result = await getSuggestions(hcpName);
      if (result.status === 'not_found') { setError(result.message || 'HCP not found'); dispatch(setSuggestions(null)); }
      else if (result.status === 'success') { dispatch(setSuggestions(result)); }
      else { setError('Failed to fetch suggestions'); }
    } catch { setError('Failed to fetch suggestions.'); }
    finally { dispatch(setIsLoadingSuggestions(false)); }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <div className="bg-amber-100 rounded-lg p-1.5"><Lightbulb className="w-3.5 h-3.5 text-amber-600" /></div>
        <h3 className="text-[15px] font-bold text-[#111827] mb-0">Next Best Actions</h3>
      </div>

      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-100 text-red-700 px-3.5 py-2.5 rounded-lg text-xs mt-1">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" /> {error}
        </div>
      )}

      <button onClick={fetchSuggestions} disabled={isLoadingSuggestions || !hcpName.trim()}
        className="w-full flex items-center justify-center gap-2 px-5 py-2 text-[13px] font-bold text-white bg-amber-600 hover:bg-amber-700 rounded-lg shadow-sm transition-all duration-200 cursor-pointer disabled:bg-gray-200 disabled:text-gray-400 disabled:shadow-none disabled:cursor-not-allowed">
        {isLoadingSuggestions ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Target className="w-3.5 h-3.5" />}
        {suggestions ? 'Refresh' : 'Get Suggestions'}
      </button>

      {suggestions && !error && (
        <div className="space-y-2.5">
          <div className="flex items-center gap-3 text-[11px] text-slate-500">
            <span className="flex items-center gap-1"><TrendingUp className="w-3 h-3 text-slate-400" /> {suggestions.total_visits} visits</span>
            {suggestions.products?.length > 0 && <span>{suggestions.products.length} product(s)</span>}
          </div>
          {suggestions.products?.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {suggestions.products.map((p, i) => (
                <span key={i} className="bg-amber-50 text-amber-700 text-[10px] px-2.5 py-[3px] rounded-full font-bold border border-amber-200">
                  {p.name} ({p.samples})
                </span>
              ))}
            </div>
          )}
          {suggestions.suggestions && (
            <div className="bg-white rounded-lg p-4 border border-amber-100 shadow-sm">
              <p className="text-[13px] text-[#374151] leading-relaxed whitespace-pre-wrap">{suggestions.suggestions}</p>
            </div>
          )}
        </div>
      )}

      {!suggestions && !error && !isLoadingSuggestions && (
        <p className="text-[11px] text-amber-500 text-center py-1.5">Click "Get Suggestions" for AI-powered next best actions.</p>
      )}
    </div>
  );
}
