import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/apiService';

// Layout style helpers with modern neutral, green, and amber tones
const CARD_BASE = 'bg-[#fcfcfc] dark:bg-[#121215] border border-[#e5e7eb] dark:border-[#1e1e24] rounded-xl p-6 shadow-sm transition-all duration-200 hover:shadow-md';
const INPUT_TXT = 'w-full text-[12px] bg-canvas dark:bg-[#1a1a1f] border border-[#d1d5db] dark:border-[#2e2e38] px-3.5 py-2.5 text-ink dark:text-[#d0d0d0] rounded-lg focus:outline-none focus:ring-1 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all font-sans';
const BTN_PRIMARY = 'px-5 py-2.5 text-[10px] font-bold tracking-widest text-white dark:text-black bg-emerald-600 hover:bg-emerald-700 dark:bg-[#a3e635] dark:hover:bg-[#bef264] rounded-lg uppercase transition-all duration-150 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-emerald-500/10 active:scale-95';
const BTN_SECONDARY = 'px-4 py-2 border border-border dark:border-[#2e2e38] text-ink-muted dark:text-[#888] hover:text-ink dark:hover:text-white bg-transparent text-[10px] font-bold uppercase tracking-wider rounded-lg cursor-pointer transition-colors';

export default function DashboardPage() {
  const { user, setUser } = useAuth();
  const [activeTab, setActiveTab] = useState<'profile' | 'keys' | 'usage'>('profile');
  const [activeLang, setActiveLang] = useState<'curl' | 'python' | 'js'>('curl');

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
  const [copiedLangCode, setCopiedLangCode] = useState(false);

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

  // Copy plaintext generated API Key
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

  // Code snippets for Developer Integration Quickstart
  const getCodeSnippet = () => {
    const keyVal = 'YOUR_API_KEY_HERE';
    switch (activeLang) {
      case 'curl':
        return `curl -X GET "http://localhost:8000/api/v1/spectral-data/search?wavelength_min=400&wavelength_max=450" \\
  -H "Authorization: Bearer ${keyVal}"`;
      case 'python':
        return `import requests

url = "http://localhost:8000/api/v1/spectral-data/search"
headers = {
    "Authorization": "Bearer ${keyVal}"
}
params = {
    "wavelength_min": 400.0,
    "wavelength_max": 450.0
}

response = requests.get(url, headers=headers, params=params)
print(response.json())`;
      case 'js':
        return `fetch("http://localhost:8000/api/v1/spectral-data/search?wavelength_min=400&wavelength_max=450", {
  headers: {
    "Authorization": "Bearer ${keyVal}"
  }
})
.then(res => res.json())
.then(data => console.log(data));`;
    }
  };

  const handleCopySnippet = () => {
    navigator.clipboard.writeText(getCodeSnippet());
    setCopiedLangCode(true);
    setTimeout(() => setCopiedLangCode(false), 2000);
  };

  // Role Badge Styling Mapper
  const getRoleColor = (roleStr?: string) => {
    const r = (roleStr || '').toLowerCase();
    if (r.includes('researcher')) return 'bg-emerald-500/10 text-emerald-600 dark:text-[#a3e635] border-emerald-500/20';
    if (r.includes('developer')) return 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20';
    if (r.includes('student')) return 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20';
    if (r.includes('scientist')) return 'bg-teal-500/10 text-teal-600 dark:text-teal-400 border-teal-500/20';
    return 'bg-neutral-500/10 text-neutral-600 dark:text-neutral-400 border-neutral-500/20';
  };

  return (
    <div className="bg-canvas dark:bg-[#0b0b0d] min-h-[calc(100vh-61px)] py-10 transition-colors duration-200 font-sans">
      <div className="max-w-[1300px] mx-auto px-6">
        
        {/* Workspace Title & Host banner */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#e5e7eb] dark:border-[#1a1a1f] pb-6 mb-8">
          <div>
            <div className="text-[10px] font-bold tracking-[3px] text-emerald-500 dark:text-[#a3e635] uppercase mb-1">
              Secure Environment
            </div>
            <h1 className="text-2xl font-black tracking-tight text-ink dark:text-white m-0">
              Researcher Workspace
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-[11px] text-[#666] dark:text-[#888] font-mono tracking-wider">
              Connected to api.libs.isro
            </span>
          </div>
        </div>

        {/* Unified 2-Column Responsive Workspace Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-8 items-start">
          
          {/* LEFT COLUMN: Persistent user profile card (Fills empty space permanently) */}
          <div className="bg-[#fcfcfc] dark:bg-[#121215] border border-[#e5e7eb] dark:border-[#1e1e24] p-6 rounded-xl shadow-sm space-y-6">
            <div className="text-center relative pb-6 border-b border-[#e5e7eb] dark:border-[#1a1a1f]">
              
              {/* Initials Avatar Ring */}
              <div className="w-20 h-20 bg-gradient-to-tr from-emerald-500 via-[#a3e635] to-amber-500 p-[3px] rounded-full mx-auto mb-4 shadow-lg shadow-emerald-500/5">
                <div className="w-full h-full bg-[#fcfcfc] dark:bg-[#121215] rounded-full flex items-center justify-center font-black text-xl text-ink dark:text-white tracking-wide uppercase">
                  {user?.username ? user.username.substring(0, 2) : (user?.email ? user.email.substring(0, 2) : 'RE')}
                </div>
              </div>
              
              <h2 className="text-lg font-bold text-ink dark:text-white m-0 tracking-tight">
                @{user?.username || 'libs_analyst'}
              </h2>
              
              <div className={`inline-block mt-2.5 px-3 py-0.5 text-[9px] font-extrabold tracking-wider border rounded-full uppercase ${getRoleColor(user?.role)}`}>
                {user?.role || 'researcher'}
              </div>
            </div>

            {/* Profile info details block */}
            <div className="space-y-4 text-[12px] border-b border-[#e5e7eb] dark:border-[#1a1a1f] pb-6">
              <div>
                <span className="block text-[9px] font-bold text-ink-muted dark:text-[#555] uppercase tracking-wider mb-1">Email Address</span>
                <span className="font-mono text-ink dark:text-[#ccc] block break-all font-semibold">{user?.email}</span>
              </div>
              <div>
                <span className="block text-[9px] font-bold text-ink-muted dark:text-[#555] uppercase tracking-wider mb-1">Affiliation</span>
                <span className="text-ink dark:text-[#ccc] block font-medium">{user?.institution || 'Academic Institution (Not Added)'}</span>
              </div>
              <div>
                <span className="block text-[9px] font-bold text-ink-muted dark:text-[#555] uppercase tracking-wider mb-1">Research Field</span>
                <span className="text-ink dark:text-[#ccc] block italic font-medium">{user?.interest || 'Spectroscopy Composition Research'}</span>
              </div>
              <div>
                <span className="block text-[9px] font-bold text-ink-muted dark:text-[#555] uppercase tracking-wider mb-1">Registration Date</span>
                <span className="text-ink dark:text-[#ccc] block font-mono text-[11px]">
                  {user?.created_at ? new Date(user.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A'}
                </span>
              </div>
            </div>

            {/* Micro KPI Quick Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-canvas-alt dark:bg-[#1a1a1f] p-3 rounded-lg border border-[#e5e7eb] dark:border-[#1c1c22]">
                <div className="text-[8px] font-bold text-[#888] dark:text-[#555] uppercase tracking-wider mb-1">Active Keys</div>
                <div className="text-base font-black text-emerald-500 dark:text-[#a3e635]">{user?.api_key_count || 0}</div>
              </div>
              <div className="bg-canvas-alt dark:bg-[#1a1a1f] p-3 rounded-lg border border-[#e5e7eb] dark:border-[#1c1c22]">
                <div className="text-[8px] font-bold text-[#888] dark:text-[#555] uppercase tracking-wider mb-1">Verified Role</div>
                <div className="text-[10px] font-bold text-emerald-600 dark:text-[#a3e635] uppercase tracking-widest mt-1">VERIFIED</div>
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN: Tab switcher + Details Panels */}
          <div className="space-y-6">
            
            {/* Custom high-fidelity tab switcher */}
            <div className="flex border border-[#e5e7eb] dark:border-[#1e1e24] bg-canvas-alt dark:bg-[#121215]/50 p-1 rounded-xl">
              <button
                onClick={() => setActiveTab('profile')}
                className={`flex-1 py-3 text-center text-[10px] font-bold tracking-widest uppercase rounded-lg transition-all cursor-pointer ${
                  activeTab === 'profile'
                    ? 'bg-canvas dark:bg-[#1e1e24] text-ink dark:text-white shadow-sm border border-[#e5e7eb] dark:border-[#2e2e38]'
                    : 'text-[#6b7280] dark:text-[#666] hover:text-[#111] dark:hover:text-white border border-transparent'
                }`}
              >
                Profile Settings
              </button>
              <button
                onClick={() => setActiveTab('keys')}
                className={`flex-1 py-3 text-center text-[10px] font-bold tracking-widest uppercase rounded-lg transition-all cursor-pointer ${
                  activeTab === 'keys'
                    ? 'bg-canvas dark:bg-[#1e1e24] text-ink dark:text-white shadow-sm border border-[#e5e7eb] dark:border-[#2e2e38]'
                    : 'text-[#6b7280] dark:text-[#666] hover:text-[#111] dark:hover:text-white border border-transparent'
                }`}
              >
                Developer API Keys
              </button>
              <button
                onClick={() => setActiveTab('usage')}
                className={`flex-1 py-3 text-center text-[10px] font-bold tracking-widest uppercase rounded-lg transition-all cursor-pointer ${
                  activeTab === 'usage'
                    ? 'bg-canvas dark:bg-[#1e1e24] text-ink dark:text-white shadow-sm border border-[#e5e7eb] dark:border-[#2e2e38]'
                    : 'text-[#6b7280] dark:text-[#666] hover:text-[#111] dark:hover:text-white border border-transparent'
                }`}
              >
                Usage Analytics
              </button>
            </div>

            {/* TAB CONTENTS */}
            <div className="transition-all duration-150">
              
              {/* TAB 1: Profile Configuration settings */}
              {activeTab === 'profile' && (
                <div className={CARD_BASE}>
                  <div className="border-b border-[#e5e7eb] dark:border-[#1a1a1f] pb-3 mb-6">
                    <h3 className="text-sm font-bold text-ink dark:text-white uppercase tracking-wider m-0">
                      Configure Academic details
                    </h3>
                    <p className="text-[11px] text-ink-muted mt-1 m-0">Modify institutional affiliation details and research context fields.</p>
                  </div>
                  
                  <form onSubmit={handleSaveProfile} className="space-y-6">
                    <div>
                      <label className="block text-[10px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#666] mb-2">Registered Login Email</label>
                      <input
                        type="text"
                        disabled
                        className={`${INPUT_TXT} opacity-40 bg-[#f3f4f6] dark:bg-[#111115] cursor-not-allowed border-dashed`}
                        value={user?.email || ''}
                      />
                      <span className="text-[9px] text-[#888] mt-1.5 block">Login email credentials cannot be altered. Contact administrator to change root credentials.</span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                      <div>
                        <label className="block text-[10px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#666] mb-2">Researcher Category / Role</label>
                        <select
                          className="w-full text-[12px] bg-canvas dark:bg-[#1a1a1f] border border-[#d1d5db] dark:border-[#2e2e38] px-3 py-2.5 text-ink dark:text-[#d0d0d0] rounded-lg focus:outline-none focus:ring-1 focus:ring-emerald-500/50 cursor-pointer"
                          value={role}
                          onChange={(e) => setRole(e.target.value)}
                          style={{ colorScheme: 'dark' }}
                        >
                          <option value="researcher">Researcher</option>
                          <option value="student">Student</option>
                          <option value="developer">Developer</option>
                          <option value="data_scientist">Data Scientist</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-[10px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#666] mb-2">Joined Date</label>
                        <input
                          type="text"
                          disabled
                          className={`${INPUT_TXT} opacity-40 bg-[#f3f4f6] dark:bg-[#111115] cursor-not-allowed border-dashed`}
                          value={user?.created_at ? new Date(user.created_at).toLocaleString() : 'N/A'}
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-[10px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#666] mb-2">Academic Institution / Organization</label>
                      <input
                        type="text"
                        className={INPUT_TXT}
                        value={institution}
                        onChange={(e) => setInstitution(e.target.value)}
                        placeholder="e.g. Indian Institute of Science (IISc)"
                      />
                    </div>

                    <div>
                      <label className="block text-[10px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#666] mb-2">Scientific Research Interest</label>
                      <input
                        type="text"
                        className={INPUT_TXT}
                        value={interest}
                        onChange={(e) => setInterest(e.target.value)}
                        placeholder="e.g. LIBS elemental spectroscopy, mineral peaks detection"
                      />
                    </div>

                    {profileError && (
                      <div className="text-[11px] font-medium text-red-600 bg-red-500/5 dark:bg-red-950/20 dark:text-red-400 p-3 rounded-lg border border-red-500/25">
                        {profileError}
                      </div>
                    )}

                    {profileSuccess && (
                      <div className="text-[11px] font-medium text-emerald-600 bg-emerald-500/5 dark:bg-emerald-950/20 dark:text-[#a3e635] p-3 rounded-lg border border-emerald-500/25">
                        Profile details saved successfully.
                      </div>
                    )}

                    <button
                      type="submit"
                      disabled={profileLoading}
                      className={BTN_PRIMARY}
                    >
                      {profileLoading ? 'Saving changes...' : 'Save Profile Changes'}
                    </button>
                  </form>
                </div>
              )}

              {/* TAB 2: API Keys Management + Developer Quickstart Guide */}
              {activeTab === 'keys' && (
                <div className="space-y-6">
                  
                  {/* API Key management list */}
                  <div className={CARD_BASE}>
                    <div className="flex justify-between items-center mb-6 border-b border-[#e5e7eb] dark:border-[#1a1a1f] pb-3">
                      <div>
                        <h3 className="text-sm font-bold text-ink dark:text-white uppercase tracking-wider m-0">
                          Active API Keys
                        </h3>
                        <p className="text-[11px] text-ink-muted mt-1 m-0">Generate tokens to interact programmatically with the database server.</p>
                      </div>
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

                    {keysLoading && <div className="text-[11px] font-mono text-ink-muted py-4">Querying workspace keys...</div>}

                    {!keysLoading && keys.length === 0 && (
                      <div className="text-[12px] text-ink-muted py-8 text-center border border-dashed border-[#e5e7eb] dark:border-[#2e2e38] rounded-xl bg-canvas-alt dark:bg-[#121215]/20">
                        No programmatic API keys associated with this account. Click "Generate New Key" above.
                      </div>
                    )}

                    {!keysLoading && keys.length > 0 && (
                      <div className="overflow-x-auto">
                        <table className="w-full border-collapse text-[12px] text-left">
                          <thead>
                            <tr className="border-b border-[#e5e7eb] dark:border-[#1c1c22]">
                              <th className="font-bold text-[#888] dark:text-[#555] uppercase text-[9px] tracking-wider pb-3">Label</th>
                              <th className="font-bold text-[#888] dark:text-[#555] uppercase text-[9px] tracking-wider pb-3">Key Prefix</th>
                              <th className="font-bold text-[#888] dark:text-[#555] uppercase text-[9px] tracking-wider pb-3">Status</th>
                              <th className="font-bold text-[#888] dark:text-[#555] uppercase text-[9px] tracking-wider pb-3">Created</th>
                              <th className="font-bold text-[#888] dark:text-[#555] uppercase text-[9px] tracking-wider pb-3">Last Used</th>
                              <th className="font-bold text-[#888] dark:text-[#555] uppercase text-[9px] tracking-wider pb-3 text-right">Action</th>
                            </tr>
                          </thead>
                          <tbody>
                            {keys.map((k) => (
                              <tr key={k.id} className="hover:bg-canvas-alt dark:hover:bg-[#16161c]/50 transition-colors duration-150">
                                <td className="py-4 border-b border-[#e5e7eb] dark:border-[#1a1a1f] text-ink dark:text-white font-semibold">{k.label}</td>
                                <td className="py-4 border-b border-[#e5e7eb] dark:border-[#1a1a1f] font-mono text-[11px] text-[#444] dark:text-[#bbb]">{k.key_prefix}...</td>
                                <td className="py-4 border-b border-[#e5e7eb] dark:border-[#1a1a1f]">
                                  {k.is_active ? (
                                    <span className="bg-emerald-500/10 text-emerald-600 dark:text-[#a3e635] border border-emerald-500/20 font-bold px-2 py-0.5 rounded-full text-[9px] uppercase tracking-wide">Active</span>
                                  ) : (
                                    <span className="bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 font-bold px-2 py-0.5 rounded-full text-[9px] uppercase tracking-wide">Revoked</span>
                                  )}
                                </td>
                                <td className="py-4 border-b border-[#e5e7eb] dark:border-[#1a1a1f] text-ink-soft text-[11px]">
                                  {k.created_at ? new Date(k.created_at).toLocaleDateString() : 'N/A'}
                                </td>
                                <td className="py-4 border-b border-[#e5e7eb] dark:border-[#1a1a1f] font-mono text-ink-soft text-[10px]">
                                  {k.last_used ? new Date(k.last_used).toLocaleString() : 'Never'}
                                </td>
                                <td className="py-4 border-b border-[#e5e7eb] dark:border-[#1a1a1f] text-right">
                                  {k.is_active && (
                                    <button
                                      onClick={() => handleRevokeKey(k.id)}
                                      className="text-[9px] font-bold text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 border-0 bg-transparent cursor-pointer uppercase tracking-wider transition-colors"
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

                  {/* Programmatic API Quickstart Guide */}
                  <div className={CARD_BASE}>
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#e5e7eb] dark:border-[#1a1a1f] pb-4 mb-5">
                      <div>
                        <h3 className="text-sm font-bold text-ink dark:text-white uppercase tracking-wider m-0">
                          Developer Quickstart Guide
                        </h3>
                        <p className="text-[11px] text-ink-muted mt-1 m-0">Query LIBS spectral datasets directly from your workflow scripts.</p>
                      </div>
                      
                      {/* Language Toggler Buttons */}
                      <div className="flex border border-[#e5e7eb] dark:border-[#2e2e38] rounded-lg p-0.5 bg-canvas-alt dark:bg-[#16161c]">
                        {(['curl', 'python', 'js'] as const).map((lang) => (
                          <button
                            key={lang}
                            onClick={() => setActiveLang(lang)}
                            className={`px-3 py-1.5 text-[9px] font-bold tracking-wider uppercase rounded-md transition-all cursor-pointer ${
                              activeLang === lang
                                ? 'bg-canvas dark:bg-[#282830] text-ink dark:text-white border border-[#d1d5db] dark:border-[#3a3a46]'
                                : 'text-[#888] hover:text-ink dark:hover:text-white border border-transparent'
                            }`}
                          >
                            {lang === 'js' ? 'JavaScript' : lang === 'curl' ? 'cURL' : 'Python'}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Styled code container */}
                    <div className="relative group bg-[#f3f4f6] dark:bg-[#0f0f12] border border-[#e5e7eb] dark:border-[#1e1e24] rounded-xl overflow-hidden shadow-inner">
                      <div className="flex justify-between items-center bg-[#e5e7eb] dark:bg-[#181820] px-4 py-2 text-[10px] text-ink-muted dark:text-[#888] font-mono border-b border-[#d1d5db] dark:border-[#1c1c24]">
                        <span>libs_query.{activeLang === 'js' ? 'js' : activeLang === 'curl' ? 'sh' : 'py'}</span>
                        <button
                          onClick={handleCopySnippet}
                          className="bg-transparent border-0 text-emerald-600 dark:text-[#a3e635] hover:underline cursor-pointer font-semibold uppercase tracking-wider text-[9px] transition-colors"
                        >
                          {copiedLangCode ? 'Copied' : 'Copy Code'}
                        </button>
                      </div>
                      <pre className="p-4 m-0 overflow-x-auto text-[11.5px] font-mono leading-relaxed text-[#333] dark:text-[#d0d0d8] text-left">
                        <code>{getCodeSnippet()}</code>
                      </pre>
                    </div>
                  </div>

                  {/* Secure API Key Generation Modal */}
                  {showKeyGenModal && (
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-[4px] z-[9999] flex items-center justify-center p-4">
                      <div className="bg-canvas dark:bg-[#121215] border border-[#e5e7eb] dark:border-[#2e2e38] rounded-xl max-w-[500px] w-full p-6 shadow-2xl relative animate-in fade-in zoom-in-95 duration-150">
                        
                        {!generatedKey ? (
                          <>
                            <h3 className="text-base font-bold text-ink dark:text-white m-0 mb-4 uppercase tracking-wider">Generate API Access Key</h3>
                            <div className="mb-5">
                              <label className="block text-[10px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#666] mb-2">Friendly Key Label</label>
                              <input
                                type="text"
                                value={newKeyLabel}
                                onChange={(e) => setNewKeyLabel(e.target.value)}
                                className={INPUT_TXT}
                                placeholder="e.g. Local Analytics Server"
                              />
                            </div>
                            <div className="text-[11px] text-ink-muted leading-relaxed mb-6 bg-canvas-alt dark:bg-[#1c1c22] p-3 rounded-lg border border-[#e5e7eb] dark:border-[#1e1e26]">
                              This key permits programmatic access to all search and measurement endpoints. You may configure up to 5 active credentials.
                            </div>
                            <div className="flex justify-end gap-3 border-t border-[#e5e7eb] dark:border-[#1a1a1f] pt-4">
                              <button
                                onClick={() => setShowKeyGenModal(false)}
                                className={BTN_SECONDARY}
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
                            <h3 className="text-base font-bold text-emerald-600 dark:text-[#a3e635] m-0 mb-4 flex items-center gap-2 uppercase tracking-wider">
                              Key Created Successfully
                            </h3>
                            <div className="bg-amber-500/5 border-l-[3px] border-amber-500 p-4 mb-5 rounded-r border border-[#e5e7eb] dark:border-amber-500/25">
                              <strong className="block text-[11px] text-amber-700 dark:text-amber-400 font-bold mb-1 uppercase tracking-wider">Store Secret Key Securely!</strong>
                              <span className="text-[11px] text-[#6b7280] dark:text-[#888] leading-normal">
                                For security reasons, we only store the hash of this credentials. You will **not** be able to see this plaintext key again after closing this window.
                              </span>
                            </div>
                            <div className="mb-6">
                              <label className="block text-[10px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#666] mb-2">Plaintext API Key</label>
                              <div className="flex gap-2">
                                <input
                                  type="text"
                                  readOnly
                                  value={generatedKey}
                                  className={`${INPUT_TXT} font-mono bg-[#f4f4f4] dark:bg-[#1a1a20] text-[13px] text-emerald-600 dark:text-[#a3e635] border-emerald-500/25`}
                                />
                                <button
                                  onClick={handleCopyKey}
                                  className="px-4 bg-emerald-600 dark:bg-[#a3e635] text-white dark:text-black font-bold text-[10px] tracking-wider rounded-lg uppercase cursor-pointer transition-colors"
                                >
                                  {copySuccess ? 'Copied' : 'Copy'}
                                </button>
                              </div>
                            </div>
                            <div className="flex justify-end border-t border-[#e5e7eb] dark:border-[#1a1a1f] pt-4">
                              <button
                                onClick={() => {
                                  setShowKeyGenModal(false);
                                  setGeneratedKey(null);
                                }}
                                className={BTN_PRIMARY}
                              >
                                Close &amp; Save
                              </button>
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: Usage Analytics with High Fidelity SVG bar chart */}
              {activeTab === 'usage' && (
                <div className="space-y-6">
                  
                  {/* Summary KPIs Row */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {[
                      { label: 'Total Requests (30d)', value: usageSummary?.total_requests_30d || 0, color: 'text-emerald-500 dark:text-[#a3e635]' },
                      { label: 'Data Transferred', value: formatBytes(usageSummary?.total_bytes_30d || 0), color: 'text-ink dark:text-white' },
                      { label: 'Primary Endpoint', value: usageSummary?.most_used_endpoint || 'N/A', color: 'text-amber-500 dark:text-amber-400 font-mono text-[10px]' },
                      { label: 'Registered Keys', value: usageSummary?.active_keys || 0, color: 'text-ink dark:text-white' },
                    ].map(({ label, value, color }) => (
                      <div key={label} className="bg-[#fcfcfc] dark:bg-[#121215] border border-[#e5e7eb] dark:border-[#1e1e24] p-5 rounded-xl shadow-sm hover:shadow-md transition-shadow">
                        <div className="text-[8px] font-bold text-ink-muted dark:text-[#555] uppercase tracking-wider mb-2">{label}</div>
                        <div className={`text-lg font-black tracking-tight truncate ${color}`}>{value}</div>
                      </div>
                    ))}
                  </div>

                  {/* Chart and Route Breakdown */}
                  <div className="grid grid-cols-1 lg:grid-cols-[1.6fr_1fr] gap-6">
                    
                    {/* SVG Chart with Emerald Glowing Gradient */}
                    <div className={CARD_BASE}>
                      <h3 className="text-[11px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#555] mb-5 border-b border-[#e5e7eb] dark:border-[#1a1a1f] pb-3">
                        Daily API Request Distribution (30 Days)
                      </h3>
                      {usageSummary?.daily_breakdown?.length > 0 ? (
                        <div className="w-full mt-2">
                          <svg viewBox="0 0 500 160" className="w-full h-[160px] overflow-visible">
                            <defs>
                              <linearGradient id="barGlowGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="0%" stopColor="#a3e635" />
                                <stop offset="100%" stopColor="#059669" />
                              </linearGradient>
                            </defs>
                            
                            {/* Horizontal dotted grid lines */}
                            <line x1="30" y1="20" x2="480" y2="20" stroke="#888" className="opacity-10" strokeDasharray="3,3" />
                            <line x1="30" y1="70" x2="480" y2="70" stroke="#888" className="opacity-10" strokeDasharray="3,3" />
                            <line x1="30" y1="120" x2="480" y2="120" stroke="#888" className="opacity-15" />
                            
                            {/* Bars */}
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
                                  <g key={item.day} className="group">
                                    <rect
                                      x={x}
                                      y={y}
                                      width={barWidth}
                                      height={height}
                                      fill="url(#barGlowGrad)"
                                      className="opacity-75 hover:opacity-100 transition-opacity cursor-pointer"
                                    />
                                    <text
                                      x={x + barWidth / 2}
                                      y={y - 4}
                                      textAnchor="middle"
                                      className="text-[7.5px] font-bold font-mono fill-emerald-600 dark:fill-[#a3e635] opacity-0 group-hover:opacity-100 transition-opacity"
                                    >
                                      {requests}
                                    </text>
                                  </g>
                                );
                              });
                            })()}
                            
                            {/* Axis */}
                            <line x1="30" y1="120" x2="480" y2="120" stroke="#888" strokeWidth="1" className="opacity-30" />
                            
                            <text x="35" y="138" textAnchor="start" className="text-[8.5px] font-mono fill-ink-muted dark:fill-[#555] font-semibold">
                              {usageSummary.daily_breakdown[0]?.day}
                            </text>
                            <text x="480" y="138" textAnchor="end" className="text-[8.5px] font-mono fill-ink-muted dark:fill-[#555] font-semibold">
                              {usageSummary.daily_breakdown[usageSummary.daily_breakdown.length - 1]?.day}
                            </text>
                          </svg>
                        </div>
                      ) : (
                        <div className="h-[120px] flex items-center justify-center text-[11px] text-ink-muted font-mono">
                          No programmatic API operations logged.
                        </div>
                      )}
                    </div>

                    {/* Endpoint route breakdown list */}
                    <div className={CARD_BASE}>
                      <h3 className="text-[11px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#555] mb-4 border-b border-[#e5e7eb] dark:border-[#1a1a1f] pb-3">
                        Routes Breakdown (30 Days)
                      </h3>
                      {usageSummary?.endpoint_breakdown?.length > 0 ? (
                        <div className="max-h-[140px] overflow-y-auto">
                          <table className="w-full border-collapse text-[11px] text-left">
                            <thead>
                              <tr className="text-ink-muted dark:text-[#555] font-bold">
                                <th className="pb-2 text-[9px] uppercase tracking-wider">Route</th>
                                <th className="pb-2 text-right text-[9px] uppercase tracking-wider">Calls</th>
                                <th className="pb-2 text-right text-[9px] uppercase tracking-wider">Latency</th>
                              </tr>
                            </thead>
                            <tbody>
                              {usageSummary.endpoint_breakdown.map((item: any) => (
                                <tr key={item.endpoint} className="border-b border-[#e5e7eb] dark:border-[#1c1c22]/50 last:border-0 hover:bg-canvas-alt dark:hover:bg-[#16161c]/30">
                                  <td className="py-2.5 font-mono truncate max-w-[140px] text-ink dark:text-[#ccc]">{item.endpoint}</td>
                                  <td className="py-2.5 text-right font-black text-emerald-600 dark:text-[#a3e635]">{item.requests}</td>
                                  <td className="py-2.5 text-right text-ink-muted font-mono">{item.avg_response_ms} ms</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <div className="py-8 flex items-center justify-center text-[11px] text-ink-muted font-mono">
                          No active endpoint calls recorded.
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Raw logs list table */}
                  <div className={CARD_BASE}>
                    <h3 className="text-[11px] font-bold uppercase tracking-wider text-ink-muted dark:text-[#555] mb-4 border-b border-[#e5e7eb] dark:border-[#1a1a1f] pb-3">
                      Recent Programmatic API Logs
                    </h3>

                    {usageLogs.length === 0 ? (
                      <div className="text-[11px] text-ink-muted py-6 text-center font-mono">
                        No programmatic API logs recorded.
                      </div>
                    ) : (
                      <>
                        <div className="overflow-x-auto">
                          <table className="w-full border-collapse text-[11.5px] text-left">
                            <thead>
                              <tr className="border-b border-[#e5e7eb] dark:border-[#1c1c22] text-ink-muted dark:text-[#555]">
                                <th className="pb-2.5 font-bold uppercase text-[9px] tracking-wider">Timestamp</th>
                                <th className="pb-2.5 font-bold uppercase text-[9px] tracking-wider">API Key</th>
                                <th className="pb-2.5 font-bold uppercase text-[9px] tracking-wider">Method</th>
                                <th className="pb-2.5 font-bold uppercase text-[9px] tracking-wider">Route</th>
                                <th className="pb-2.5 font-bold uppercase text-[9px] tracking-wider text-center">Status</th>
                                <th className="pb-2.5 font-bold uppercase text-[9px] tracking-wider text-right">Bytes</th>
                                <th className="pb-2.5 font-bold uppercase text-[9px] tracking-wider text-right">Latency</th>
                              </tr>
                            </thead>
                            <tbody>
                              {usageLogs.map((log) => (
                                <tr key={log.id} className="hover:bg-canvas-alt dark:hover:bg-[#16161c]/50 border-b border-[#e5e7eb] dark:border-[#181820]/30 last:border-b-0 transition-colors">
                                  <td className="py-2.5 text-ink-soft font-mono text-[10px]">
                                    {log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A'}
                                  </td>
                                  <td className="py-2.5 font-mono text-[#555] dark:text-[#bbb]">{log.key_prefix ? `${log.key_prefix}...` : 'DEFAULT_KEY'}</td>
                                  <td className="py-2.5">
                                    <span className={`px-2 py-0.5 rounded-full text-[8.5px] font-extrabold border ${
                                      log.method === 'GET' 
                                        ? 'bg-emerald-500/10 text-emerald-600 dark:text-[#a3e635] border-emerald-500/10' 
                                        : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/10'
                                    }`}>{log.method}</span>
                                  </td>
                                  <td className="py-2.5 font-mono truncate max-w-[180px] text-ink dark:text-white">{log.endpoint}</td>
                                  <td className="py-2.5 text-center">
                                    <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold font-mono border ${
                                      log.status_code >= 200 && log.status_code < 300
                                        ? 'bg-emerald-500/10 text-emerald-600 dark:text-[#a3e635] border-emerald-500/10'
                                        : 'bg-red-500/10 text-red-700 dark:text-red-400 border-red-500/10'
                                    }`}>{log.status_code}</span>
                                  </td>
                                  <td className="py-2.5 text-right text-ink-soft font-mono text-[11px]">{formatBytes(log.response_bytes)}</td>
                                  <td className="py-2.5 text-right text-ink-soft font-mono text-[11px]">
                                    {log.response_time_ms ? `${log.response_time_ms.toFixed(1)} ms` : 'N/A'}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>

                        {/* Pagination footer bar */}
                        <div className="flex justify-between items-center mt-5 pt-4 border-t border-[#e5e7eb] dark:border-[#1a1a1f]">
                          <button
                            onClick={() => setLogPage(Math.max(0, logPage - 1))}
                            disabled={logPage === 0 || usageLoading}
                            className={BTN_SECONDARY}
                          >
                            Previous
                          </button>
                          <span className="text-[11px] font-mono text-ink-muted font-bold">Page {logPage + 1}</span>
                          <button
                            onClick={() => setLogPage(logPage + 1)}
                            disabled={usageLogs.length < logsPerPage || usageLoading}
                            className={BTN_SECONDARY}
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

      </div>
    </div>
  );
}
