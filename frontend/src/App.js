import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Activity, Radio, Wifi, WifiOff, RefreshCw, Send, Eye, EyeOff,
  TrendingUp, TrendingDown, AlertCircle, CheckCircle, Clock, XCircle,
  LogOut, BarChart3, Zap, Phone, Key, Lock, Copy, Check, Users, Filter
} from 'lucide-react';
import "@/App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

// API Helper
const api = {
  async get(endpoint) {
    const response = await fetch(`${BACKEND_URL}${endpoint}`);
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || 'API Error');
    }
    return response.json();
  },
  async post(endpoint, data = {}) {
    const response = await fetch(`${BACKEND_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || 'API Error');
    }
    return response.json();
  },
  async put(endpoint, data = {}) {
    const response = await fetch(`${BACKEND_URL}${endpoint}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || 'API Error');
    }
    return response.json();
  }
};

// Copy to clipboard hook
const useCopyToClipboard = () => {
  const [copiedId, setCopiedId] = useState(null);
  const copy = async (text, id) => {
    await navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };
  return { copiedId, copy };
};

// Status Badge Component
const StatusBadge = ({ status }) => {
  const styles = {
    sent: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    pending: 'bg-amber-100 text-amber-700 border-amber-200',
    failed: 'bg-red-100 text-red-700 border-red-200',
    modified: 'bg-blue-100 text-blue-700 border-blue-200',
    cancelled: 'bg-gray-100 text-gray-700 border-gray-200',
    closed: 'bg-purple-100 text-purple-700 border-purple-200',
    active: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    inactive: 'bg-gray-100 text-gray-500 border-gray-200'
  };
  return (
    <span className={`px-2 py-1 text-xs font-semibold rounded-full border ${styles[status] || styles.pending}`}>
      {status?.toUpperCase()}
    </span>
  );
};

// Channel Type Badge
const ChannelTypeBadge = ({ type }) => {
  const styles = {
    channel: 'bg-blue-100 text-blue-700',
    supergroup: 'bg-purple-100 text-purple-700',
    group: 'bg-green-100 text-green-700'
  };
  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded ${styles[type] || 'bg-gray-100 text-gray-600'}`}>
      {type?.toUpperCase()}
    </span>
  );
};

// Toggle Switch Component
const ToggleSwitch = ({ enabled, onChange, loading }) => (
  <button
    onClick={onChange}
    disabled={loading}
    className={`relative inline-flex h-7 w-14 items-center rounded-full transition-colors ${
      enabled ? 'bg-emerald-500' : 'bg-gray-300'
    } ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
  >
    <span className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${enabled ? 'translate-x-8' : 'translate-x-1'}`} />
  </button>
);

// Stat Card Component
const StatCard = ({ icon: Icon, label, value, subtext }) => (
  <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
    <div className="flex items-center gap-4">
      <div className="p-3 rounded-lg bg-indigo-100">
        <Icon className="w-6 h-6 text-indigo-600" />
      </div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-2xl font-bold text-gray-800">{value}</p>
        {subtext && <p className="text-xs text-gray-400">{subtext}</p>}
      </div>
    </div>
  </div>
);

// Auth Modal Component
const AuthModal = ({ isOpen, onClose, onSuccess }) => {
  const [step, setStep] = useState('phone');
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [phoneCodeHash, setPhoneCodeHash] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const sendCode = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await api.post('/api/session/send-code', { phone_number: phone });
      setPhoneCodeHash(result.phone_code_hash);
      setStep('code');
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const verifyCode = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await api.post('/api/session/verify-code', {
        phone_number: phone,
        code: code,
        phone_code_hash: phoneCodeHash
      });
      if (result.needs_password) {
        setStep('password');
      } else if (result.success) {
        onSuccess();
        onClose();
      }
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const verifyPassword = async () => {
    setLoading(true);
    setError('');
    try {
      const result = await api.post('/api/session/verify-password', { password });
      if (result.success) {
        onSuccess();
        onClose();
      }
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-6 w-full max-w-md mx-4 shadow-xl">
        <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
          <Lock className="w-5 h-5 text-indigo-600" />
          Telegram Authentication
        </h2>
        {error && <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm">{error}</div>}
        {step === 'phone' && (
          <div>
            <p className="text-gray-600 mb-4">Enter your phone number with country code</p>
            <div className="flex items-center gap-2 mb-4">
              <Phone className="w-5 h-5 text-gray-400" />
              <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+1234567890" className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500" />
            </div>
            <button onClick={sendCode} disabled={loading || !phone} className="w-full py-2.5 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2">
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              Send Code
            </button>
          </div>
        )}
        {step === 'code' && (
          <div>
            <p className="text-gray-600 mb-4">Enter the verification code sent to {phone}</p>
            <div className="flex items-center gap-2 mb-4">
              <Key className="w-5 h-5 text-gray-400" />
              <input type="text" value={code} onChange={(e) => setCode(e.target.value)} placeholder="12345" className="flex-1 px-4 py-2 border border-gray-200 rounded-lg text-center text-2xl tracking-widest" />
            </div>
            <button onClick={verifyCode} disabled={loading || !code} className="w-full py-2.5 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2">
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
              Verify Code
            </button>
          </div>
        )}
        {step === 'password' && (
          <div>
            <p className="text-gray-600 mb-4">Enter your 2FA password</p>
            <div className="flex items-center gap-2 mb-4">
              <Lock className="w-5 h-5 text-gray-400" />
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Your 2FA password" className="flex-1 px-4 py-2 border border-gray-200 rounded-lg" />
            </div>
            <button onClick={verifyPassword} disabled={loading || !password} className="w-full py-2.5 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2">
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
              Verify Password
            </button>
          </div>
        )}
        <button onClick={onClose} className="w-full mt-3 py-2 text-gray-500 hover:text-gray-700">Cancel</button>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [monitoredChannels, setMonitoredChannels] = useState([]);
  const [availableChannels, setAvailableChannels] = useState([]);
  const [signals, setSignals] = useState([]);
  const [sessionStatus, setSessionStatus] = useState({ is_connected: false, is_monitoring: false });
  const [loading, setLoading] = useState(true);
  const [channelsLoading, setChannelsLoading] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [signalPage, setSignalPage] = useState(1);
  const [signalStatusFilter, setSignalStatusFilter] = useState('');
  const [signalChannelFilter, setSignalChannelFilter] = useState('');
  const [totalSignalPages, setTotalSignalPages] = useState(1);
  const [togglingChannels, setTogglingChannels] = useState({});
  const { copiedId, copy } = useCopyToClipboard();

  const fetchSessionStatus = useCallback(async () => {
    try {
      const status = await api.get('/api/session/status');
      setSessionStatus(status);
      return status;
    } catch (err) {
      console.error('Failed to fetch session status:', err);
      return null;
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const data = await api.get('/api/stats');
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }, []);

  const fetchMonitoredChannels = useCallback(async () => {
    try {
      const data = await api.get('/api/channels');
      setMonitoredChannels(data);
    } catch (err) {
      console.error('Failed to fetch monitored channels:', err);
    }
  }, []);

  const fetchAvailableChannels = useCallback(async () => {
    setChannelsLoading(true);
    try {
      const data = await api.get('/api/channels/available');
      setAvailableChannels(data);
    } catch (err) {
      console.error('Failed to fetch available channels:', err);
    }
    setChannelsLoading(false);
  }, []);

  const fetchSignals = useCallback(async () => {
    try {
      const params = new URLSearchParams({ page: signalPage, limit: 50 });
      if (signalStatusFilter) params.append('status', signalStatusFilter);
      if (signalChannelFilter) params.append('channel_id', signalChannelFilter);
      const data = await api.get(`/api/signals?${params}`);
      setSignals(data.signals);
      setTotalSignalPages(data.pages);
    } catch (err) {
      console.error('Failed to fetch signals:', err);
    }
  }, [signalPage, signalStatusFilter, signalChannelFilter]);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      const status = await fetchSessionStatus();
      await fetchStats();
      await fetchMonitoredChannels();
      if (status?.is_connected) {
        await fetchAvailableChannels();
      }
      setLoading(false);
    };
    init();
  }, [fetchSessionStatus, fetchStats, fetchMonitoredChannels, fetchAvailableChannels]);

  useEffect(() => {
    const interval = setInterval(() => {
      fetchSessionStatus();
      if (activeTab === 'dashboard') fetchStats();
      if (activeTab === 'channels') {
        fetchMonitoredChannels();
        if (sessionStatus.is_connected) fetchAvailableChannels();
      }
      if (activeTab === 'signals') fetchSignals();
    }, 5000);
    return () => clearInterval(interval);
  }, [activeTab, sessionStatus.is_connected, fetchSessionStatus, fetchStats, fetchMonitoredChannels, fetchAvailableChannels, fetchSignals]);

  useEffect(() => {
    if (activeTab === 'signals') fetchSignals();
  }, [activeTab, signalPage, signalStatusFilter, signalChannelFilter, fetchSignals]);

  const handleConnect = async () => {
    try {
      const result = await api.post('/api/session/connect');
      if (result.success) {
        await fetchSessionStatus();
        await fetchAvailableChannels();
      } else {
        setShowAuthModal(true);
      }
    } catch (err) {
      setShowAuthModal(true);
    }
  };

  const handleAuthSuccess = async () => {
    await fetchSessionStatus();
    await fetchAvailableChannels();
    await fetchMonitoredChannels();
  };

  const handleDisconnect = async () => {
    try {
      await api.post('/api/session/disconnect');
      await fetchSessionStatus();
      setAvailableChannels([]);
    } catch (err) {
      console.error('Failed to disconnect:', err);
    }
  };

  const toggleMonitoring = async () => {
    try {
      if (sessionStatus.is_monitoring) {
        await api.post('/api/monitoring/stop');
      } else {
        await api.post('/api/monitoring/start');
      }
      await fetchSessionStatus();
    } catch (err) {
      console.error('Failed to toggle monitoring:', err);
    }
  };

  const toggleChannelMonitoring = async (channel, isCurrentlyMonitored) => {
    const channelId = channel.channel_id;
    setTogglingChannels(prev => ({ ...prev, [channelId]: true }));
    try {
      if (isCurrentlyMonitored) {
        await api.put(`/api/channels/${channelId}`, { is_active: false });
      } else {
        const existingChannel = monitoredChannels.find(c => c.channel_id === channelId);
        if (existingChannel) {
          await api.put(`/api/channels/${channelId}`, { is_active: true });
        } else {
          await api.post('/api/channels', {
            channel_id: channel.channel_id,
            channel_name: channel.channel_name,
            channel_username: channel.channel_username,
            channel_type: channel.channel_type
          });
        }
      }
      await fetchMonitoredChannels();
      await fetchAvailableChannels();
    } catch (err) {
      console.error('Failed to toggle channel:', err);
    }
    setTogglingChannels(prev => ({ ...prev, [channelId]: false }));
  };

  const getCombinedChannels = useMemo(() => {
    const monitoredMap = {};
    monitoredChannels.forEach(ch => { monitoredMap[ch.channel_id] = ch; });
    const combined = availableChannels.map(ch => ({
      ...ch,
      isMonitored: monitoredMap[ch.channel_id]?.is_active || false,
      monitoredData: monitoredMap[ch.channel_id] || null
    }));
    return combined.sort((a, b) => {
      if (a.isMonitored && !b.isMonitored) return -1;
      if (!a.isMonitored && b.isMonitored) return 1;
      return a.channel_name.localeCompare(b.channel_name);
    });
  }, [availableChannels, monitoredChannels]);

  const activeMonitoredChannels = useMemo(() => monitoredChannels.filter(c => c.is_active), [monitoredChannels]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <RefreshCw className="w-10 h-10 text-indigo-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  const activeMonitoredCount = monitoredChannels.filter(c => c.is_active).length;

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-gradient-to-b from-indigo-600 to-purple-700 text-white fixed h-full">
        <div className="p-6">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Zap className="w-6 h-6" />
            Signal Extractor
          </h1>
        </div>
        <nav className="px-4 space-y-1">
          {[{ id: 'dashboard', icon: BarChart3, label: 'Dashboard' }, { id: 'channels', icon: Radio, label: 'Channels' }, { id: 'signals', icon: TrendingUp, label: 'Signals' }].map(item => (
            <button key={item.id} onClick={() => setActiveTab(item.id)} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeTab === item.id ? 'bg-white/20 text-white' : 'text-white/70 hover:bg-white/10 hover:text-white'}`}>
              <item.icon className="w-5 h-5" />
              {item.label}
              {item.id === 'channels' && activeMonitoredCount > 0 && <span className="ml-auto bg-white/20 px-2 py-0.5 rounded-full text-xs">{activeMonitoredCount}</span>}
            </button>
          ))}
        </nav>
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/20">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-white/70">Telegram</span>
            <span className={`flex items-center gap-1 text-sm ${sessionStatus.is_connected ? 'text-emerald-300' : 'text-red-300'}`}>
              {sessionStatus.is_connected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
              {sessionStatus.is_connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          {sessionStatus.is_connected ? (
            <div className="space-y-2">
              <button onClick={toggleMonitoring} className={`w-full py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-2 ${sessionStatus.is_monitoring ? 'bg-amber-500 hover:bg-amber-600' : 'bg-emerald-500 hover:bg-emerald-600'}`}>
                {sessionStatus.is_monitoring ? <><EyeOff className="w-4 h-4" /> Stop Monitoring</> : <><Eye className="w-4 h-4" /> Start Monitoring</>}
              </button>
              <button onClick={handleDisconnect} className="w-full py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm font-medium flex items-center justify-center gap-2">
                <LogOut className="w-4 h-4" /> Disconnect
              </button>
            </div>
          ) : (
            <button onClick={handleConnect} className="w-full py-2 bg-emerald-500 hover:bg-emerald-600 rounded-lg text-sm font-medium flex items-center justify-center gap-2">
              <Wifi className="w-4 h-4" /> Connect
            </button>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 p-8">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && stats && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-800">Dashboard</h2>
              {sessionStatus.is_monitoring && (
                <span className="flex items-center gap-2 px-3 py-1.5 bg-emerald-100 text-emerald-700 rounded-full text-sm font-medium">
                  <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                  Monitoring Active
                </span>
              )}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <StatCard icon={BarChart3} label="Total Signals" value={stats.total_signals} />
              <StatCard icon={CheckCircle} label="Sent" value={stats.sent_signals} />
              <StatCard icon={Clock} label="Pending" value={stats.pending_signals} />
              <StatCard icon={XCircle} label="Failed" value={stats.failed_signals} />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <StatCard icon={Radio} label="Active Channels" value={stats.active_channels} subtext={`of ${stats.total_channels} total`} />
              <StatCard icon={Activity} label="Today's Signals" value={stats.signals_today} />
              <StatCard icon={TrendingUp} label="Success Rate" value={`${stats.success_rate}%`} />
            </div>
          </div>
        )}

        {/* Channels Tab */}
        {activeTab === 'channels' && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-800">Channel Management</h2>
                <p className="text-gray-500 mt-1">Toggle monitoring for your Telegram channels.</p>
              </div>
              {sessionStatus.is_connected && (
                <button onClick={fetchAvailableChannels} disabled={channelsLoading} className="px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2">
                  <RefreshCw className={`w-4 h-4 ${channelsLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              )}
            </div>
            {!sessionStatus.is_connected ? (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 text-center">
                <WifiOff className="w-12 h-12 text-amber-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-amber-800 mb-2">Not Connected</h3>
                <p className="text-amber-700 mb-4">Connect to Telegram to view and manage your channels</p>
                <button onClick={handleConnect} className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700">Connect to Telegram</button>
              </div>
            ) : channelsLoading && availableChannels.length === 0 ? (
              <div className="text-center py-12">
                <RefreshCw className="w-10 h-10 text-indigo-600 animate-spin mx-auto mb-4" />
                <p className="text-gray-600">Fetching your channels...</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-4 text-white flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Users className="w-6 h-6" />
                    <div><span className="font-bold text-lg">{activeMonitoredCount}</span><span className="ml-2">channels actively monitored</span></div>
                  </div>
                  <div className="text-white/80">{getCombinedChannels.length} total channels</div>
                </div>
                {activeMonitoredCount > 0 && (
                  <div className="bg-emerald-50 border-2 border-emerald-200 rounded-xl overflow-hidden">
                    <div className="bg-emerald-100 px-6 py-3 border-b border-emerald-200">
                      <h3 className="font-bold text-emerald-800 flex items-center gap-2"><Eye className="w-5 h-5" />Monitored Channels ({activeMonitoredCount})</h3>
                    </div>
                    <div className="divide-y divide-emerald-100">
                      {getCombinedChannels.filter(c => c.isMonitored).map(channel => (
                        <div key={channel.channel_id} className="px-6 py-4 flex items-center justify-between hover:bg-emerald-100/50">
                          <div className="flex-1">
                            <div className="flex items-center gap-3">
                              <p className="font-bold text-gray-800">{channel.channel_name}</p>
                              <ChannelTypeBadge type={channel.channel_type} />
                            </div>
                            <div className="flex items-center gap-4 mt-1">
                              <code className="text-xs bg-white px-2 py-0.5 rounded font-mono text-gray-600 border">{channel.channel_id}</code>
                              <button onClick={() => copy(channel.channel_id, channel.channel_id)} className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1">
                                {copiedId === channel.channel_id ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                                {copiedId === channel.channel_id ? 'Copied!' : 'Copy ID'}
                              </button>
                              {channel.monitoredData && <span className="text-xs text-emerald-700 font-medium">{channel.monitoredData.total_signals || 0} signals</span>}
                            </div>
                          </div>
                          <ToggleSwitch enabled={true} loading={togglingChannels[channel.channel_id]} onChange={() => toggleChannelMonitoring(channel, true)} />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                  <div className="bg-gray-50 px-6 py-3 border-b border-gray-100">
                    <h3 className="font-semibold text-gray-700 flex items-center gap-2"><Radio className="w-5 h-5 text-gray-500" />Available Channels ({getCombinedChannels.filter(c => !c.isMonitored).length})</h3>
                  </div>
                  <div className="divide-y divide-gray-50 max-h-[400px] overflow-y-auto">
                    {getCombinedChannels.filter(c => !c.isMonitored).map(channel => (
                      <div key={channel.channel_id} className="px-6 py-3 flex items-center justify-between hover:bg-gray-50">
                        <div className="flex-1">
                          <div className="flex items-center gap-3">
                            <p className="font-medium text-gray-700">{channel.channel_name}</p>
                            <ChannelTypeBadge type={channel.channel_type} />
                          </div>
                          <code className="text-xs bg-gray-100 px-2 py-0.5 rounded font-mono text-gray-500">{channel.channel_id}</code>
                        </div>
                        <ToggleSwitch enabled={false} loading={togglingChannels[channel.channel_id]} onChange={() => toggleChannelMonitoring(channel, false)} />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Signals Tab */}
        {activeTab === 'signals' && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-800">Extracted Signals</h2>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 text-gray-400" />
                  <select value={signalChannelFilter} onChange={(e) => { setSignalChannelFilter(e.target.value); setSignalPage(1); }} className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
                    <option value="">All Channels</option>
                    {activeMonitoredChannels.map(ch => <option key={ch.channel_id} value={ch.channel_id}>{ch.channel_name}</option>)}
                  </select>
                </div>
                <select value={signalStatusFilter} onChange={(e) => { setSignalStatusFilter(e.target.value); setSignalPage(1); }} className="px-3 py-2 border border-gray-200 rounded-lg text-sm">
                  <option value="">All Status</option>
                  <option value="pending">Pending</option>
                  <option value="sent">Sent</option>
                  <option value="failed">Failed</option>
                </select>
              </div>
            </div>
            {signals.length === 0 ? (
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
                <TrendingUp className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-700 mb-2">No Signals Yet</h3>
                <p className="text-gray-500 mb-4">{sessionStatus.is_monitoring ? 'Waiting for signals from monitored channels...' : 'Start monitoring to capture signals'}</p>
                {!sessionStatus.is_monitoring && sessionStatus.is_connected && <button onClick={toggleMonitoring} className="px-6 py-2 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600">Start Monitoring</button>}
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-100">
                      <tr>
                        <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600">Channel</th>
                        <th className="text-left px-4 py-3 text-sm font-semibold text-gray-600">Symbol</th>
                        <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">Direction</th>
                        <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">Entry</th>
                        <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">SL</th>
                        <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">TP1</th>
                        <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">Method</th>
                        <th className="text-center px-4 py-3 text-sm font-semibold text-gray-600">Status</th>
                        <th className="text-right px-4 py-3 text-sm font-semibold text-gray-600">Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {signals.map(signal => (
                        <tr key={signal.id} className="border-b border-gray-50 hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm text-gray-600">{signal.channel_name || 'Unknown'}</td>
                          <td className="px-4 py-3 font-semibold text-gray-800">{signal.symbol || '-'}</td>
                          <td className="text-center px-4 py-3">
                            {signal.direction && <span className={`flex items-center justify-center gap-1 font-medium ${signal.direction === 'BUY' ? 'text-emerald-600' : 'text-red-600'}`}>
                              {signal.direction === 'BUY' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}{signal.direction}
                            </span>}
                          </td>
                          <td className="text-right px-4 py-3 font-mono text-sm">{signal.entry_price?.toFixed(2) || '-'}</td>
                          <td className="text-right px-4 py-3 font-mono text-sm text-red-600">{signal.stop_loss?.toFixed(2) || '-'}</td>
                          <td className="text-right px-4 py-3 font-mono text-sm text-emerald-600">{signal.take_profit_1?.toFixed(2) || '-'}</td>
                          <td className="text-center px-4 py-3"><span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium text-gray-600 capitalize">{signal.parsing_method || '-'}</span></td>
                          <td className="text-center px-4 py-3"><StatusBadge status={signal.status} /></td>
                          <td className="text-right px-4 py-3 text-xs text-gray-500">{new Date(signal.created_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {totalSignalPages > 1 && (
                  <div className="flex items-center justify-center gap-4 p-4 border-t border-gray-100">
                    <button onClick={() => setSignalPage(p => Math.max(1, p - 1))} disabled={signalPage === 1} className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50">Previous</button>
                    <span className="text-sm text-gray-600">Page {signalPage} of {totalSignalPages}</span>
                    <button onClick={() => setSignalPage(p => Math.min(totalSignalPages, p + 1))} disabled={signalPage >= totalSignalPages} className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50">Next</button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>

      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} onSuccess={handleAuthSuccess} />
    </div>
  );
}

export default App;
