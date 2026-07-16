import { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { setSearchResults, setIsLoadingSearch, setFormField } from '../store/formSlice';
import { searchHCPs } from '../api';
import { Search, User, Loader2, AlertCircle } from 'lucide-react';

export default function HCPSearch() {
  const dispatch = useDispatch();
  const { searchResults, isLoadingSearch } = useSelector((s) => s.form);
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');

  const handleSearch = async () => {
    if (!query.trim()) { setError('Please enter a search term'); return; }
    setError('');
    dispatch(setIsLoadingSearch(true));
    try {
      const result = await searchHCPs(query);
      if (result.status === 'no_results') { setError(result.message || 'No HCPs found'); dispatch(setSearchResults([])); }
      else if (result.status === 'single_match' || result.status === 'multiple_matches') { dispatch(setSearchResults(result.hcps || [])); }
      else { setError('Failed to search HCPs'); }
    } catch { setError('Failed to search HCPs.'); }
    finally { dispatch(setIsLoadingSearch(false)); }
  };

  const selectHCP = (hcp) => {
    dispatch(setFormField({ key: 'hcp_name', value: hcp.name }));
    setQuery('');
    dispatch(setSearchResults([]));
  };

  return (
    <div className="space-y-2">
      {error && (
        <div className="flex items-center gap-1 bg-red-50 border border-red-200 text-red-600 px-2 py-1.5 rounded text-[11px]">
          <AlertCircle className="w-3 h-3 shrink-0" /> {error}
        </div>
      )}

      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
          <input type="text" value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleSearch(); } }}
            placeholder="Search by name or specialty..."
            className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-200" />
        </div>
        <button onClick={handleSearch} disabled={isLoadingSearch || !query.trim()}
          className="flex items-center gap-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white px-3 py-2 rounded text-sm font-medium transition-colors">
          {isLoadingSearch ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
          Search
        </button>
      </div>

      {searchResults?.length > 0 && (
        <div className="space-y-1">
          {searchResults.map((hcp) => (
            <button key={hcp.id} onClick={() => selectHCP(hcp)}
              className="w-full flex items-center justify-between gap-2 p-2 bg-white hover:bg-blue-50 rounded border border-gray-200 hover:border-blue-300 transition-colors text-left">
              <div className="flex items-center gap-2 min-w-0">
                <div className="bg-blue-100 p-1 rounded shrink-0">
                  <User className="w-3 h-3 text-blue-600" />
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-gray-800 truncate">{hcp.name}</div>
                  <div className="text-[10px] text-gray-500 truncate">{hcp.specialty}</div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
