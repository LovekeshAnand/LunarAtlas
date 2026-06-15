import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/apiService';

// Layout style helpers
const CARD = 'bg-[#fcfcfc] dark:bg-[#121212] border border-border dark:border-[#222] rounded-lg p-6 mb-6';
const TAB_BTN = 'px-6 py-3 text-[11px] font-bold tracking-wider uppercase border-b-2 cursor-pointer transition-all';
const INPUT_TXT = 'w-full text-[12px] bg-canvas border border-[#ddd] dark:border-[#333] px-3 py-2 text-ink dark:text-[#d0d0d0] rounded focus:outline-none focus:border-ink dark:focus:border-[#888]';
const BTN_PRIMARY = 'px-5 py-2.5 text-[11px] font-bold tracking-wider text-white dark:text-black bg-ink dark:bg-[#e0e0e0] hover:bg-[#333] dark:hover:bg-[#c8c8c8] rounded uppercase transition-colors cursor-pointer disabled:opacity-50';

export default function DashboardPage() {
  const { user, setUser } = useAuth();
  const [activeTab, setActiveTab] = useState<'profile' | 'keys' | 'usage'>('profile');

  // Profile fields state
  const [role, setRole] = useState(user?.role || 'researcher');
  const [institution, setInstitution] = useState(user?.institution || '');
  const [interest, setInterest] = useState(user?.interest || '');
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileSuccess, setProfileSuccess] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);

  // Sync state if user loads after mount
  useEffect(() => {
    if (user) {
      setRole(user.role);
      setInstitution(user.institution || '');
      setInterest(user.interest || '');
    }
  }, [user]);

  // Keys tab state
  const [keys, setKeys] = useState<any[]>([]);
  const [keysLoading, setKeysLoading] = useState(false);
  const [showKeyGenModal, setShowKeyGenModal] = useState(false);
  const [newKeyLabel, setNewKeyLabel] = useState('Default');
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);

  // Usage tab state
  const [usageSummary, setUsageSummary] = useState<any>(null);
  const [usageLogs, setUsageLogs] = useState<any[]>([]);
  const [usageLoading, setUsageLoading] = useState(false);
  const [logPage, setLogPage] = useState(0);
  const logsPerPage = 10;

  // Load API Keys
  const loadApiKeys = async () => {
    try {
      setKeysLoading(true);
      const data = await apiService.fetchApiKeys();
      setKeys(data);
    } catch (err) {
      console.error(err);
    } finally {
      setKeysLoading(false);
    }
  };

  // Load Usage data
  const loadUsageData = async () => {
    try {
      setUsageLoading(true);
      const summary = await apiService.fetchUsageSummary();
      setUsageSummary(summary);
      
      const logs = await apiService.fetchUsageLog(logsPerPage, logPage * logsPerPage);
      setUsageLogs(logs);
    } catch (err) {
      console.error(err);
    } finally {
      setUsageLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'keys') {
      loadApiKeys();
    } else if (activeTab === 'usage') {
      loadUsageData();
    }
  }, [activeTab, logPage]);

  // Save profile edits
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileLoading(true);
    setProfileSuccess(false);
    setProfileError(null);
    try {
      const updatedUser = await apiService.updateProfile({ role, institution, interest });
      setUser(updatedUser);
      setProfileSuccess(true);
      setTimeout(() => setProfileSuccess(false), 3000);
    } catch (err: any) {
      setProfileError(err.message || 'Failed to update profile.');
    } finally {
      setProfileLoading(false);
    }
  };

  // Generate Key
  const handleCreateKey = async () => {
    try {
      setKeysLoading(true);
      const res = await apiService.createApiKey(newKeyLabel);
      setGeneratedKey(res.key);
      setNewKeyLabel('Default');
      // Update key list
      loadApiKeys();
    } catch (err) {
      console.error(err);
    } finally {
      setKeysLoading(false);
    }
  };

  // Revoke Key
  const handleRevokeKey = async (keyId: number) => {
    if (!confirm('Are you sure you want to revoke this API key? This cannot be undone and clients using it will fail immediately.')) {
      return;
    }
    try {
      setKeysLoading(true);
      await apiService.revokeApiKey(keyId);
      loadApiKeys();
    } catch (err) {
      console.error(err);
    } finally {
      setKeysLoading(false);
    }
  };

  // Copy to clipboard
  const handleCopyKey = () => {
    if (generatedKey) {
      navigator.clipboard.writeText(generatedKey);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  // Size formatter helper
  const formatBytes = (bytes: number) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="bg-canvas dark:bg-[#0d0d0d] min-h-[calc(100vh-61px)] py-12 transition-colors duration-200">
      <div className="max-w-[1200px] mx-auto px-8">
        
        {/* Page title / stats header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-[#eee] dark:border-[#222] pb-6 mb-8">
          <div>
            <div className="text-[9px] font-bold tracking-[2.5px] text-ink-muted dark:text-[#444] uppercase mb-2">
              User Portal
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-ink dark:text-white m-0">
              Researcher Dashboard
            </h1>
          </div>
          <div className="flex gap-4">
            <div className="border border-border dark:border-[#222] px-4 py-2 text-center rounded bg-canvas-alt dark:bg-[#141414]">
              <div className="text-[10px] text-ink-muted dark:text-[#555] font-semibold tracking-[1px] uppercase mb-0.5">Role</div>
              <div className="text-[12px] font-bold text-ink dark:text-[#f0f0f0] uppercase">{user?.role}</div>
            </div>
            <div className="border border-border dark:border-[#222] px-4 py-2 text-center rounded bg-canvas-alt dark:bg-[#141414]">
              <div className="text-[10px] text-ink-muted dark:text-[#555] font-semibold tracking-[1px] uppercase mb-0.5">Active Keys</div>
              <div className="text-[12px] font-bold text-ink dark:text-[#f0f0f0]">{user?.api_key_count || 0}</div>
            </div>
          </div>
        </div>

        {/* Tab switcher */}
        <div className="flex border-b border-[#eee] dark:border-[#222] mb-8">
          <button
            onClick={() => setActiveTab('profile')}
            className={`${TAB_BTN} ${
              activeTab === 'profile'
                ? 'border-ink dark:border-[#e0e0e0] text-ink dark:text-white'
                : 'border-transparent text-[#888] hover:text-[#555]'
            }`}
          >
            Profile Details
          </button>
          <button
            onClick={() => setActiveTab('keys')}
            className={`${TAB_BTN} ${
              activeTab === 'keys'
                ? 'border-ink dark:border-[#e0e0e0] text-ink dark:text-white'
                : 'border-transparent text-[#888] hover:text-[#555]'
            }`}
          >
            Developer API Keys
          </button>
          <button
            onClick={() => setActiveTab('usage')}
            className={`${TAB_BTN} ${
              activeTab === 'usage'
                ? 'border-ink dark:border-[#e0e0e0] text-ink dark:text-white'
                : 'border-transparent text-[#888] hover:text-[#555]'
            }`}
          >
            Usage Analytics
          </button>
        </div>

        {/* Tab contents */}
        <div>
          {/* TAB 1: Profile Details */}
          {activeTab === 'profile' && (
            <div className={CARD}>
              <h2 className="text-lg font-bold text-ink dark:text-[#f0f0f0] m-0 mb-5 border-b border-[#f0f0f0] dark:border-[#1e1e1e] pb-2">
                User Account Profile
              </h2>
              
              <form onSubmit={handleSaveProfile} className="max-w-[580px] space-y-6">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#555] mb-2">Registered Email</label>
                  <input
                    type="text"
                    disabled
                    className={`${INPUT_TXT} opacity-50 bg-[#f7f7f7] cursor-not-allowed`}
                    value={user?.email || ''}
                  />
                  <span className="text-[10px] text-ink-muted mt-1 block">Authentication credentials are tied to your signup email.</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[10px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#555] mb-2">Researcher Category / Role</label>
                    <select
                      className="w-full text-[12px] bg-canvas border border-[#ddd] dark:border-[#333] px-3 py-2 text-ink dark:text-[#d0d0d0] rounded focus:outline-none"
                      value={role}
                      onChange={(e) => setRole(e.target.value)}
                    >
                      <option value="researcher">Researcher</option>
                      <option value="student">Student</option>
                      <option value="teacher">Teacher</option>
                      <option value="developer">Developer</option>
                      <option value="other">Other / Guest</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#555] mb-2">Joined Date</label>
                    <input
                      type="text"
                      disabled
                      className={`${INPUT_TXT} opacity-50 bg-[#f7f7f7] cursor-not-allowed`}
                      value={user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#555] mb-2">Academic Institution / Organization</label>
                  <input
                    type="text"
                    className={INPUT_TXT}
                    value={institution}
                    onChange={(e) => setInstitution(e.target.value)}
                    placeholder="e.g. Indian Institute of Science (IISc)"
                  />
                </div>

                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#555] mb-2">Scientific Interest</label>
                  <input
                    type="text"
                    className={INPUT_TXT}
                    value={interest}
                    onChange={(e) => setInterest(e.target.value)}
                    placeholder="e.g. Lunar Mineralogy, LIBS elemental spectra processing"
                  />
                </div>

                {profileError && (
                  <div className="text-[12px] text-red-600 bg-red-50 dark:bg-red-950 dark:text-red-400 p-3 rounded">
                    {profileError}
                  </div>
                )}

                {profileSuccess && (
                  <div className="text-[12px] text-green-600 bg-green-50 dark:bg-green-950 dark:text-green-400 p-3 rounded">
                    ✓ Profile details saved successfully.
                  </div>
                )}

                <button
                  type="submit"
                  disabled={profileLoading}
                  className={BTN_PRIMARY}
                >
                  {profileLoading ? 'Saving...' : 'Save Profile Changes'}
                </button>
              </form>
            </div>
          )}

          {/* TAB 2: API Keys Management */}
          {activeTab === 'keys' && (
            <div>
              <div className={CARD}>
                <div className="flex justify-between items-center mb-6 border-b border-[#f0f0f0] dark:border-[#1e1e1e] pb-2">
                  <h2 className="text-lg font-bold text-ink dark:text-[#f0f0f0] m-0">
                    Developer API Keys
                  </h2>
                  <button
                    onClick={() => {
                      setGeneratedKey(null);
                      setShowKeyGenModal(true);
                    }}
                    className={BTN_PRIMARY}
                  >
                    Generate New Key
                  </button>
                </div>

                {keysLoading && <div className="text-[12px] text-ink-muted py-4">Loading API keys...</div>}

                {!keysLoading && keys.length === 0 && (
                  <div className="text-[13px] text-ink-soft py-6 text-center">
                    You do not have any API keys generated yet. Click "Generate New Key" above.
                  </div>
                )}

                {!keysLoading && keys.length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse text-[12px] text-left">
                      <thead>
                        <tr>
                          <th className="font-bold text-[#888] dark:text-[#555] uppercase text-[9px] tracking-wider pb-3 border-b border-[#eee] dark:border-[#222]">Label</th>
                          <th className="font-bold text-[#888] dark:text-[#555] uppercase text-[9px] tracking-wider pb-3 border-b border-[#eee] dark:border-[#222]">Key Prefix</th>
                          <th className="font-bold text-[#888] dark:text-[#555] uppercase text-[9px] tracking-wider pb-3 border-b border-[#eee] dark:border-[#222]">Status</th>
                          <th className="font-bold text-[#888] dark:text-[#555] uppercase text-[9px] tracking-wider pb-3 border-b border-[#eee] dark:border-[#222]">Created At</th>
                          <th className="font-bold text-[#888] dark:text-[#555] uppercase text-[9px] tracking-wider pb-3 border-b border-[#eee] dark:border-[#222]">Last Used</th>
                          <th className="font-bold text-[#888] dark:text-[#555] uppercase text-[9px] tracking-wider pb-3 border-b border-[#eee] dark:border-[#222] text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {keys.map((k) => (
                          <tr key={k.id} className="hover:bg-canvas-alt dark:hover:bg-[#141414] transition-colors">
                            <td className="py-4 border-b border-[#f0f0f0] dark:border-[#1a1a1a] text-ink dark:text-white font-medium">{k.label}</td>
                            <td className="py-4 border-b border-[#f0f0f0] dark:border-[#1a1a1a] font-mono text-[11px] text-[#444] dark:text-[#bbb]">{k.key_prefix}...</td>
                            <td className="py-4 border-b border-[#f0f0f0] dark:border-[#1a1a1a]">
                              {k.is_active ? (
                                <span className="bg-green-50 dark:bg-green-950 text-green-700 dark:text-green-400 font-bold px-2 py-0.5 rounded text-[10px] uppercase tracking-wide">Active</span>
                              ) : (
                                <span className="bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-400 font-bold px-2 py-0.5 rounded text-[10px] uppercase tracking-wide">Revoked</span>
                              )}
                            </td>
                            <td className="py-4 border-b border-[#f0f0f0] dark:border-[#1a1a1a] text-ink-soft">{k.created_at ? new Date(k.created_at).toLocaleDateString() : 'N/A'}</td>
                            <td className="py-4 border-b border-[#f0f0f0] dark:border-[#1a1a1a] text-ink-soft">{k.last_used ? new Date(k.last_used).toLocaleString() : 'Never'}</td>
                            <td className="py-4 border-b border-[#f0f0f0] dark:border-[#1a1a1a] text-right">
                              {k.is_active && (
                                <button
                                  onClick={() => handleRevokeKey(k.id)}
                                  className="text-[10px] font-bold text-red-600 dark:text-red-400 hover:underline border-0 bg-transparent cursor-pointer uppercase tracking-wider"
                                >
                                  Revoke
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Secure API Key Generation Modal */}
              {showKeyGenModal && (
                <div className="fixed inset-0 bg-black/55 backdrop-blur-[2px] z-[9999] flex items-center justify-center p-4">
                  <div className="bg-canvas dark:bg-[#121212] border border-[#eee] dark:border-[#222] rounded-lg max-w-[500px] w-full p-6 shadow-2xl relative animate-in fade-in zoom-in-95 duration-150">
                    
                    {!generatedKey ? (
                      <>
                        <h3 className="text-lg font-bold text-ink dark:text-white m-0 mb-4">Generate API Access Key</h3>
                        <div className="mb-4">
                          <label className="block text-[10px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#555] mb-2">Friendly Key Label</label>
                          <input
                            type="text"
                            value={newKeyLabel}
                            onChange={(e) => setNewKeyLabel(e.target.value)}
                            className={INPUT_TXT}
                          />
                        </div>
                        <div className="text-[12px] text-ink-soft leading-relaxed mb-6">
                          This key permits access to all public endpoints. You can define up to 5 active keys.
                        </div>
                        <div className="flex justify-end gap-3 border-t border-[#f0f0f0] dark:border-[#1e1e1e] pt-4">
                          <button
                            onClick={() => setShowKeyGenModal(false)}
                            className="px-4 py-2 border border-border dark:border-[#222] text-[#666] bg-transparent text-[11px] font-bold uppercase tracking-wider rounded cursor-pointer"
                          >
                            Cancel
                          </button>
                          <button
                            onClick={handleCreateKey}
                            className={BTN_PRIMARY}
                          >
                            Generate Key
                          </button>
                        </div>
                      </>
                    ) : (
                      <>
                        <h3 className="text-lg font-bold text-green-600 dark:text-green-400 m-0 mb-4 flex items-center gap-2">
                          ✓ Key Generated Successfully
                        </h3>
                        <div className="bg-red-50 dark:bg-red-950/40 border-l-[3px] border-red-500 p-3.5 mb-5 rounded-r">
                          <strong className="block text-[11.5px] text-red-800 dark:text-red-300 font-bold mb-1 uppercase tracking-wide">Write Down Your Key!</strong>
                          <span className="text-[11.5px] text-red-700 dark:text-red-400 leading-normal">
                            For security purposes, we only store the hash of this key. You will **not** be able to see this plaintext key again after closing this window.
                          </span>
                        </div>
                        <div className="mb-6">
                          <label className="block text-[10px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#555] mb-2">Plaintext API Key</label>
                          <div className="flex gap-2">
                            <input
                              type="text"
                              readOnly
                              value={generatedKey}
                              className={`${INPUT_TXT} font-mono bg-[#f4f4f4] dark:bg-[#1e1e1e] text-[13px]`}
                            />
                            <button
                              onClick={handleCopyKey}
                              className="px-4 bg-ink dark:bg-[#e0e0e0] text-white dark:text-black font-bold text-[11px] rounded uppercase cursor-pointer"
                            >
                              {copySuccess ? 'Copied' : 'Copy'}
                            </button>
                          </div>
                        </div>
                        <div className="flex justify-end border-t border-[#f0f0f0] dark:border-[#1e1e1e] pt-4">
                          <button
                            onClick={() => {
                              setShowKeyGenModal(false);
                              setGeneratedKey(null);
                            }}
                            className={BTN_PRIMARY}
                          >
                            Close &amp; Finish
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: Usage Analytics */}
          {activeTab === 'usage' && (
            <div>
              {/* Summary KPIs */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                {[
                  { label: 'Total Requests (30d)', value: usageSummary?.total_requests_30d || 0 },
                  { label: 'Data Transferred (30d)', value: formatBytes(usageSummary?.total_bytes_30d || 0) },
                  { label: 'Most Used Endpoint', value: usageSummary?.most_used_endpoint || 'N/A' },
                  { label: 'Active Developer Keys', value: usageSummary?.active_keys || 0 },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-[#fcfcfc] dark:bg-[#121212] border border-[#eee] dark:border-[#222] p-5 rounded-lg">
                    <div className="text-[9px] font-bold text-ink-muted dark:text-[#555] uppercase tracking-wider mb-1.5">{label}</div>
                    <div className="text-xl font-extrabold text-ink dark:text-[#f0f0f0] tracking-tight truncate">{value}</div>
                  </div>
                ))}
              </div>

              {/* Chart & Endpoint breakdown */}
              <div className="grid grid-cols-1 lg:grid-cols-[1.5fr_1fr] gap-6 mb-6">
                {/* SVG Chart */}
                <div className={CARD}>
                  <h3 className="text-[12px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#555] mb-5 border-b border-[#f0f0f0] dark:border-[#1e1e1e] pb-1.5">
                    Daily API Request Distribution (30 Days)
                  </h3>
                  {usageSummary?.daily_breakdown?.length > 0 ? (
                    <div className="w-full">
                      {/* SVG Bar Chart */}
                      <svg viewBox="0 0 500 160" className="w-full h-[160px] overflow-visible">
                        {/* Horizontal grid lines */}
                        <line x1="30" y1="20" x2="480" y2="20" stroke="#f0f0f0" className="dark:stroke-[#1c1c1c]" strokeWidth="1" />
                        <line x1="30" y1="70" x2="480" y2="70" stroke="#f0f0f0" className="dark:stroke-[#1c1c1c]" strokeWidth="1" />
                        <line x1="30" y1="120" x2="480" y2="120" stroke="#eee" className="dark:stroke-[#262626]" strokeWidth="1" />
                        
                        {/* Render Bars */}
                        {(() => {
                          const list = usageSummary.daily_breakdown;
                          const maxVal = Math.max(...list.map((d: any) => d.requests), 10);
                          const barWidth = 400 / list.length - 2;
                          return list.map((item: any, idx: number) => {
                            const requests = item.requests;
                            const pct = requests / maxVal;
                            const height = Math.max(pct * 100, requests > 0 ? 3 : 0);
                            const x = 35 + idx * (400 / list.length);
                            const y = 120 - height;
                            return (
                              <g key={item.day}>
                                <rect
                                  x={x}
                                  y={y}
                                  width={barWidth}
                                  height={height}
                                  className="fill-ink dark:fill-[#e0e0e0] opacity-80 hover:opacity-100 transition-opacity"
                                />
                                <text
                                  x={x + barWidth / 2}
                                  y={y - 4}
                                  textAnchor="middle"
                                  className="text-[8px] font-mono fill-[#777] font-semibold"
                                >
                                  {requests > 0 ? requests : ''}
                                </text>
                              </g>
                            );
                          });
                        })()}
                        
                        {/* Axis */}
                        <line x1="30" y1="120" x2="480" y2="120" stroke="#444" strokeWidth="1.5" />
                        
                        {/* Labels for start and end */}
                        <text x="35" y="135" textAnchor="start" className="text-[9px] font-medium fill-[#888] dark:fill-[#555]">
                          {usageSummary.daily_breakdown[0]?.day}
                        </text>
                        <text x="480" y="135" textAnchor="end" className="text-[9px] font-medium fill-[#888] dark:fill-[#555]">
                          {usageSummary.daily_breakdown[usageSummary.daily_breakdown.length - 1]?.day}
                        </text>
                      </svg>
                    </div>
                  ) : (
                    <div className="h-[120px] flex items-center justify-center text-[12px] text-ink-soft">
                      No request logging data recorded.
                    </div>
                  )}
                </div>

                {/* Endpoint breakdown */}
                <div className={CARD}>
                  <h3 className="text-[12px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#555] mb-4 border-b border-[#f0f0f0] dark:border-[#1e1e1e] pb-1.5">
                    Endpoint Breakdown (30 Days)
                  </h3>
                  {usageSummary?.endpoint_breakdown?.length > 0 ? (
                    <div className="max-h-[140px] overflow-y-auto">
                      <table className="w-full border-collapse text-[11px] text-left">
                        <thead>
                          <tr className="text-ink-muted dark:text-[#444] font-bold">
                            <th className="pb-2">Route</th>
                            <th className="pb-2 text-right">Calls</th>
                            <th className="pb-2 text-right">Avg Response</th>
                          </tr>
                        </thead>
                        <tbody>
                          {usageSummary.endpoint_breakdown.map((item: any) => (
                            <tr key={item.endpoint} className="border-b border-[#f0f0f0] dark:border-[#181818] last:border-0">
                              <td className="py-2 font-mono truncate max-w-[150px] text-[#444] dark:text-[#ccc]">{item.endpoint}</td>
                              <td className="py-2 text-right font-bold text-ink dark:text-[#f0f0f0]">{item.requests}</td>
                              <td className="py-2 text-right text-ink-soft font-mono">{item.avg_response_ms} ms</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="py-6 flex items-center justify-center text-[11px] text-ink-soft">
                      No endpoint calls recorded.
                    </div>
                  )}
                </div>
              </div>

              {/* Raw Usage Log Table */}
              <div className={CARD}>
                <h3 className="text-[12px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#555] mb-4 border-b border-[#f0f0f0] dark:border-[#1e1e1e] pb-1.5">
                  Recent API Activity Logs
                </h3>

                {usageLogs.length === 0 ? (
                  <div className="text-[12px] text-ink-soft py-6 text-center">
                    No API log entries recorded.
                  </div>
                ) : (
                  <>
                    <div className="overflow-x-auto">
                      <table className="w-full border-collapse text-[11.5px] text-left">
                        <thead>
                          <tr className="border-b border-[#eee] dark:border-[#222] text-[#888] dark:text-[#555]">
                            <th className="pb-2.5 font-semibold">Timestamp</th>
                            <th className="pb-2.5 font-semibold">API Key Prefix</th>
                            <th className="pb-2.5 font-semibold">HTTP Method</th>
                            <th className="pb-2.5 font-semibold">Endpoint Route</th>
                            <th className="pb-2.5 font-semibold text-center">Status</th>
                            <th className="pb-2.5 font-semibold text-right">Bytes</th>
                            <th className="pb-2.5 font-semibold text-right">Latency</th>
                          </tr>
                        </thead>
                        <tbody>
                          {usageLogs.map((log) => (
                            <tr key={log.id} className="hover:bg-canvas-alt dark:hover:bg-[#141414] border-b border-[#f0f0f0] dark:border-[#181818] last:border-b-0">
                              <td className="py-2.5 text-ink-soft font-mono text-[10px]">{log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A'}</td>
                              <td className="py-2.5 font-mono text-[#555] dark:text-[#bbb]">{log.key_prefix ? `${log.key_prefix}...` : 'DEMO_KEY'}</td>
                              <td className="py-2.5">
                                <span className={`px-1 rounded text-[9px] font-bold ${
                                  log.method === 'GET' ? 'bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-400' : 'bg-amber-50 dark:bg-amber-950 text-amber-700 dark:text-amber-400'
                                }`}>{log.method}</span>
                              </td>
                              <td className="py-2.5 font-mono truncate max-w-[200px] text-ink dark:text-white">{log.endpoint}</td>
                              <td className="py-2.5 text-center">
                                <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                                  log.status_code >= 200 && log.status_code < 300
                                    ? 'bg-green-50 dark:bg-green-950/60 text-green-700 dark:text-green-400'
                                    : 'bg-red-50 dark:bg-red-950/60 text-red-700 dark:text-red-400'
                                }`}>{log.status_code}</span>
                              </td>
                              <td className="py-2.5 text-right text-ink-soft font-mono">{formatBytes(log.response_bytes)}</td>
                              <td className="py-2.5 text-right text-ink-soft font-mono">{log.response_time_ms ? `${log.response_time_ms.toFixed(1)} ms` : 'N/A'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Pagination */}
                    <div className="flex justify-between items-center mt-5 pt-3 border-t border-[#f0f0f0] dark:border-[#1e1e1e]">
                      <button
                        onClick={() => setLogPage(Math.max(0, logPage - 1))}
                        disabled={logPage === 0 || usageLoading}
                        className="px-3 py-1.5 text-[10px] font-bold border border-border dark:border-[#222] bg-transparent text-[#666] uppercase tracking-wider rounded cursor-pointer disabled:opacity-30"
                      >
                        Previous
                      </button>
                      <span className="text-[11px] text-ink-muted">Page {logPage + 1}</span>
                      <button
                        onClick={() => setLogPage(logPage + 1)}
                        disabled={usageLogs.length < logsPerPage || usageLoading}
                        className="px-3 py-1.5 text-[10px] font-bold border border-border dark:border-[#222] bg-transparent text-[#666] uppercase tracking-wider rounded cursor-pointer disabled:opacity-30"
                      >
                        Next
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
