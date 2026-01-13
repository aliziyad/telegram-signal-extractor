import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Activity, Radio, Wifi, WifiOff, RefreshCw, Send, Eye, EyeOff,
  TrendingUp, TrendingDown, CheckCircle, Clock, XCircle,
  LogOut, BarChart3, Zap, Phone, Key, Lock, Copy, Check, Users, Filter,
  ChevronLeft, ChevronRight, Sun, Moon, User, Shield
} from 'lucide-react';
import "@/App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

// Format date to UK style (dd/mm/yyyy) with 24hr time in MVT timezone (GMT+5)
const formatDateMVT = (dateString) => {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    // MVT is GMT+5, so we add 5 hours to UTC
    const mvtOffset = 5 * 60; // 5 hours in minutes
    const utcTime = date.getTime() + (date.getTimezoneOffset() * 60000);
    const mvtTime = new Date(utcTime + (mvtOffset * 60000));
    
    const day = mvtTime.getDate().toString().padStart(2, '0');
    const month = (mvtTime.getMonth() + 1).toString().padStart(2, '0');
    const year = mvtTime.getFullYear();
    const hours = mvtTime.getHours().toString().padStart(2, '0');
    const minutes = mvtTime.getMinutes().toString().padStart(2, '0');
    const seconds = mvtTime.getSeconds().toString().padStart(2, '0');
    
    return `${day}/${month}/${year}, ${hours}:${minutes}:${seconds}`;
  } catch (e) {
    return dateString;
  }
};

// API Helper with timeout
const api = {
  async get(endpoint, timeout = 30000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    try {
      const response = await fetch(`${BACKEND_URL}${endpoint}`, {
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || 'API Error');
      }
      return response.json();
    } catch (err) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        throw new Error('Request timed out. Please try again.');
      }
      throw err;
    }
  },
  async post(endpoint, data = {}, timeout = 60000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    try {
      const response = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || 'API Error');
      }
      return response.json();
    } catch (err) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        throw new Error('Request timed out. Please try again.');
      }
      throw err;
    }
  },
  async put(endpoint, data = {}, timeout = 30000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    try {
      const response = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || 'API Error');
      }
      return response.json();
    } catch (err) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        throw new Error('Request timed out. Please try again.');
      }
      throw err;
    }
  }
};

// Theme Context
const ThemeContext = React.createContext();

// Auth will be validated server-side

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
const StatusBadge = ({ status, theme }) => {
  const styles = {
    sent: theme === 'dark' ? 'bg-emerald-900/50 text-emerald-400 border-emerald-700' : 'bg-emerald-100 text-emerald-700 border-emerald-200',
    pending: theme === 'dark' ? 'bg-amber-900/50 text-amber-400 border-amber-700' : 'bg-amber-100 text-amber-700 border-amber-200',
    failed: theme === 'dark' ? 'bg-red-900/50 text-red-400 border-red-700' : 'bg-red-100 text-red-700 border-red-200',
    modified: theme === 'dark' ? 'bg-blue-900/50 text-blue-400 border-blue-700' : 'bg-blue-100 text-blue-700 border-blue-200',
    cancelled: theme === 'dark' ? 'bg-gray-800 text-gray-400 border-gray-600' : 'bg-gray-100 text-gray-700 border-gray-200',
    closed: theme === 'dark' ? 'bg-purple-900/50 text-purple-400 border-purple-700' : 'bg-purple-100 text-purple-700 border-purple-200',
    active: theme === 'dark' ? 'bg-emerald-900/50 text-emerald-400 border-emerald-700' : 'bg-emerald-100 text-emerald-700 border-emerald-200',
    inactive: theme === 'dark' ? 'bg-gray-800 text-gray-500 border-gray-600' : 'bg-gray-100 text-gray-500 border-gray-200'
  };
  return (
    <span className={`px-2 py-1 text-xs font-semibold rounded-full border ${styles[status] || styles.pending}`}>
      {status?.toUpperCase()}
    </span>
  );
};

// Channel Type Badge
const ChannelTypeBadge = ({ type, theme }) => {
  const styles = {
    channel: theme === 'dark' ? 'bg-blue-900/50 text-blue-400' : 'bg-blue-100 text-blue-700',
    supergroup: theme === 'dark' ? 'bg-purple-900/50 text-purple-400' : 'bg-purple-100 text-purple-700',
    group: theme === 'dark' ? 'bg-green-900/50 text-green-400' : 'bg-green-100 text-green-700'
  };
  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded ${styles[type] || (theme === 'dark' ? 'bg-gray-800 text-gray-400' : 'bg-gray-100 text-gray-600')}`}>
      {type?.toUpperCase()}
    </span>
  );
};

// Toggle Switch Component
const ToggleSwitch = ({ enabled, onChange, loading }) => (
  <button
    onClick={onChange}
    disabled={loading}
    className={`relative inline-flex h-6 w-12 items-center rounded-full transition-colors ${
      enabled ? 'bg-emerald-500' : 'bg-gray-600'
    } ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
  >
    <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${enabled ? 'translate-x-7' : 'translate-x-1'}`} />
  </button>
);

// Stat Card Component
const StatCard = ({ icon: Icon, label, value, subtext, theme }) => (
  <div className={`rounded-xl p-4 border transition-all hover:scale-[1.02] ${
    theme === 'dark' 
      ? 'bg-[#1e2329] border-gray-700/50 hover:border-emerald-500/50' 
      : 'bg-white border-gray-200 hover:border-emerald-500/50 shadow-sm'
  }`}>
    <div className="flex items-center gap-3">
      <div className={`p-2.5 rounded-lg ${theme === 'dark' ? 'bg-emerald-500/20' : 'bg-emerald-100'}`}>
        <Icon className={`w-5 h-5 ${theme === 'dark' ? 'text-emerald-400' : 'text-emerald-600'}`} />
      </div>
      <div>
        <p className={`text-xs ${theme === 'dark' ? 'text-gray-500' : 'text-gray-500'}`}>{label}</p>
        <p className={`text-xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>{value}</p>
        {subtext && <p className={`text-xs ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>{subtext}</p>}
      </div>
    </div>
  </div>
);

// Login Screen Component
const LoginScreen = ({ onLogin, theme, toggleTheme }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await api.post('/api/auth/login', { username, password });
      if (response.success && response.token) {
        localStorage.setItem('fastsignal_auth', JSON.stringify({ 
          username, 
          token: response.token,
          timestamp: Date.now() 
        }));
        onLogin(true);
      } else {
        setError('Invalid credentials');
      }
    } catch (err) {
      // Show user-friendly message instead of API error details
      setError('Invalid credentials');
    }
    setLoading(false);
  };

  return (
    <div className={`min-h-screen flex items-center justify-center ${theme === 'dark' ? 'bg-[#0f1419]' : 'bg-gray-100'}`}>
      <div className="absolute top-4 right-4">
        <button
          onClick={toggleTheme}
          className={`p-2 rounded-lg ${theme === 'dark' ? 'bg-gray-800 text-yellow-400 hover:bg-gray-700' : 'bg-white text-gray-600 hover:bg-gray-50 shadow'}`}
        >
          {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>
      </div>
      
      <div className={`w-full max-w-md p-8 rounded-2xl ${theme === 'dark' ? 'bg-[#1a1d21] border border-gray-800' : 'bg-white shadow-xl'}`}>
        <div className="text-center mb-8">
          <div className={`inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4 ${theme === 'dark' ? 'bg-emerald-500/20' : 'bg-emerald-100'}`}>
            <Zap className={`w-8 h-8 ${theme === 'dark' ? 'text-emerald-400' : 'text-emerald-600'}`} />
          </div>
          <h1 className={`text-2xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>FastSignal Admin</h1>
          <p className={`mt-2 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-500'}`}>Sign in to access the dashboard</p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-500/20 border border-red-500/50 text-red-400 text-sm text-center">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className={`block text-sm font-medium mb-2 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Username</label>
            <div className="relative">
              <User className={`absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`} />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className={`w-full pl-10 pr-4 py-3 rounded-lg border ${
                  theme === 'dark' 
                    ? 'bg-[#0f1419] border-gray-700 text-white placeholder-gray-600 focus:border-emerald-500' 
                    : 'bg-gray-50 border-gray-200 text-gray-800 placeholder-gray-400 focus:border-emerald-500'
                } focus:outline-none focus:ring-1 focus:ring-emerald-500`}
                placeholder="Enter username"
              />
            </div>
          </div>
          <div>
            <label className={`block text-sm font-medium mb-2 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Password</label>
            <div className="relative">
              <Lock className={`absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={`w-full pl-10 pr-4 py-3 rounded-lg border ${
                  theme === 'dark' 
                    ? 'bg-[#0f1419] border-gray-700 text-white placeholder-gray-600 focus:border-emerald-500' 
                    : 'bg-gray-50 border-gray-200 text-gray-800 placeholder-gray-400 focus:border-emerald-500'
                } focus:outline-none focus:ring-1 focus:ring-emerald-500`}
                placeholder="Enter password"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading || !username || !password}
            className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-lg flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Shield className="w-5 h-5" />}
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
};

// Telegram Auth Modal Component
const TelegramAuthModal = ({ isOpen, onClose, onSuccess, theme }) => {
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
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 backdrop-blur-sm">
      <div className={`w-full max-w-md p-6 rounded-2xl ${theme === 'dark' ? 'bg-[#1a1d21] border border-gray-800' : 'bg-white shadow-xl'}`}>
        <h2 className={`text-xl font-bold mb-4 flex items-center gap-2 ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>
          <Lock className="w-5 h-5 text-emerald-500" />
          Telegram Authentication
        </h2>
        {error && <div className="bg-red-500/20 border border-red-500/50 text-red-400 p-3 rounded-lg mb-4 text-sm">{error}</div>}
        {step === 'phone' && (
          <div>
            <p className={`mb-4 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Enter your phone number with country code</p>
            <div className="relative mb-4">
              <Phone className={`absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`} />
              <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+1234567890"
                className={`w-full pl-10 pr-4 py-3 rounded-lg border ${theme === 'dark' ? 'bg-[#0f1419] border-gray-700 text-white' : 'bg-gray-50 border-gray-200 text-gray-800'} focus:outline-none focus:ring-1 focus:ring-emerald-500`} />
            </div>
            <button onClick={sendCode} disabled={loading || !phone}
              className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-lg flex items-center justify-center gap-2 disabled:opacity-50">
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              {loading ? 'Sending...' : 'Send Code'}
            </button>
          </div>
        )}
        {step === 'code' && (
          <div>
            <p className={`mb-4 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Enter the verification code sent to {phone}</p>
            <div className="relative mb-4">
              <Key className={`absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`} />
              <input type="text" value={code} onChange={(e) => setCode(e.target.value)} placeholder="12345"
                className={`w-full pl-10 pr-4 py-3 rounded-lg border text-center text-2xl tracking-widest ${theme === 'dark' ? 'bg-[#0f1419] border-gray-700 text-white' : 'bg-gray-50 border-gray-200 text-gray-800'} focus:outline-none focus:ring-1 focus:ring-emerald-500`} />
            </div>
            <button onClick={verifyCode} disabled={loading || !code}
              className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-lg flex items-center justify-center gap-2 disabled:opacity-50">
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
              {loading ? 'Verifying...' : 'Verify Code'}
            </button>
          </div>
        )}
        {step === 'password' && (
          <div>
            <p className={`mb-4 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>Enter your 2FA password</p>
            <div className="relative mb-4">
              <Lock className={`absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`} />
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Your 2FA password"
                className={`w-full pl-10 pr-4 py-3 rounded-lg border ${theme === 'dark' ? 'bg-[#0f1419] border-gray-700 text-white' : 'bg-gray-50 border-gray-200 text-gray-800'} focus:outline-none focus:ring-1 focus:ring-emerald-500`} />
            </div>
            <button onClick={verifyPassword} disabled={loading || !password}
              className="w-full py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-lg flex items-center justify-center gap-2 disabled:opacity-50">
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
              {loading ? 'Verifying...' : 'Verify Password'}
            </button>
          </div>
        )}
        <button onClick={onClose} className={`w-full mt-3 py-2 ${theme === 'dark' ? 'text-gray-500 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'}`}>Cancel</button>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [theme, setTheme] = useState('dark');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
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

  // Hide "Made with Emergent" badge
  useEffect(() => {
    const hideBadge = () => {
      const badge = document.getElementById('emergent-badge');
      if (badge) {
        badge.style.display = 'none';
      }
    };
    hideBadge();
    const interval = setInterval(hideBadge, 500);
    return () => clearInterval(interval);
  }, []);

  // Check auth on mount
  useEffect(() => {
    const auth = localStorage.getItem('fastsignal_auth');
    if (auth) {
      const { timestamp } = JSON.parse(auth);
      // Session expires after 24 hours
      if (Date.now() - timestamp < 24 * 60 * 60 * 1000) {
        setIsAuthenticated(true);
      } else {
        localStorage.removeItem('fastsignal_auth');
      }
    }
    
    // Load saved theme
    const savedTheme = localStorage.getItem('fastsignal_theme');
    if (savedTheme) setTheme(savedTheme);
    
    // Load sidebar state
    const savedSidebar = localStorage.getItem('fastsignal_sidebar');
    if (savedSidebar) setSidebarCollapsed(savedSidebar === 'collapsed');
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('fastsignal_theme', newTheme);
  };

  const toggleSidebar = () => {
    const newState = !sidebarCollapsed;
    setSidebarCollapsed(newState);
    localStorage.setItem('fastsignal_sidebar', newState ? 'collapsed' : 'expanded');
  };

  const handleLogout = () => {
    localStorage.removeItem('fastsignal_auth');
    setIsAuthenticated(false);
  };

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
    if (!isAuthenticated) return;
    const init = async () => {
      setLoading(true);
      const status = await fetchSessionStatus();
      await fetchStats();
      await fetchMonitoredChannels();
      if (status?.is_connected) await fetchAvailableChannels();
      setLoading(false);
    };
    init();
  }, [isAuthenticated, fetchSessionStatus, fetchStats, fetchMonitoredChannels, fetchAvailableChannels]);

  useEffect(() => {
    if (!isAuthenticated) return;
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
  }, [isAuthenticated, activeTab, sessionStatus.is_connected, fetchSessionStatus, fetchStats, fetchMonitoredChannels, fetchAvailableChannels, fetchSignals]);

  useEffect(() => {
    if (isAuthenticated && activeTab === 'signals') fetchSignals();
  }, [isAuthenticated, activeTab, signalPage, signalStatusFilter, signalChannelFilter, fetchSignals]);

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

  // Show login screen if not authenticated
  if (!isAuthenticated) {
    return <LoginScreen onLogin={setIsAuthenticated} theme={theme} toggleTheme={toggleTheme} />;
  }

  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${theme === 'dark' ? 'bg-[#0f1419]' : 'bg-gray-100'}`}>
        <div className="text-center">
          <RefreshCw className={`w-10 h-10 animate-spin mx-auto mb-4 ${theme === 'dark' ? 'text-emerald-400' : 'text-emerald-600'}`} />
          <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>Loading...</p>
        </div>
      </div>
    );
  }

  const activeMonitoredCount = monitoredChannels.filter(c => c.is_active).length;

  return (
    <div className={`min-h-screen flex ${theme === 'dark' ? 'bg-[#0f1419]' : 'bg-gray-100'}`}>
      {/* Sidebar */}
      <aside className={`${sidebarCollapsed ? 'w-16' : 'w-64'} ${theme === 'dark' ? 'bg-[#1a1d21] border-gray-800' : 'bg-white border-gray-200'} border-r fixed h-full transition-all duration-300 flex flex-col`}>
        {/* Logo */}
        <div className={`p-4 border-b ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'} flex items-center ${sidebarCollapsed ? 'justify-center' : 'justify-between'}`}>
          {!sidebarCollapsed && (
            <div className="flex items-center gap-2">
              <div className={`p-1.5 rounded-lg ${theme === 'dark' ? 'bg-emerald-500/20' : 'bg-emerald-100'}`}>
                <Zap className={`w-5 h-5 ${theme === 'dark' ? 'text-emerald-400' : 'text-emerald-600'}`} />
              </div>
              <span className={`font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>FastSignal</span>
            </div>
          )}
          <button onClick={toggleSidebar} className={`p-1.5 rounded-lg ${theme === 'dark' ? 'hover:bg-gray-800 text-gray-400' : 'hover:bg-gray-100 text-gray-600'}`}>
            {sidebarCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-2 space-y-1">
          {[{ id: 'dashboard', icon: BarChart3, label: 'Dashboard' }, { id: 'channels', icon: Radio, label: 'Channels', badge: activeMonitoredCount }, { id: 'signals', icon: TrendingUp, label: 'Signals' }].map(item => (
            <button key={item.id} onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${sidebarCollapsed ? 'justify-center' : ''} ${
                activeTab === item.id 
                  ? (theme === 'dark' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-emerald-100 text-emerald-700')
                  : (theme === 'dark' ? 'text-gray-400 hover:bg-gray-800 hover:text-white' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-800')
              }`}
              title={sidebarCollapsed ? item.label : ''}
            >
              <item.icon className="w-5 h-5" />
              {!sidebarCollapsed && (
                <>
                  <span className="flex-1 text-left">{item.label}</span>
                  {item.badge > 0 && <span className={`px-2 py-0.5 rounded-full text-xs ${theme === 'dark' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-emerald-100 text-emerald-700'}`}>{item.badge}</span>}
                </>
              )}
            </button>
          ))}
        </nav>

        {/* Connection Status */}
        <div className={`p-3 border-t ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'}`}>
          {!sidebarCollapsed && (
            <div className="flex items-center justify-between mb-2">
              <span className={`text-xs ${theme === 'dark' ? 'text-gray-500' : 'text-gray-500'}`}>Telegram</span>
              <span className={`flex items-center gap-1 text-xs ${sessionStatus.is_connected ? 'text-emerald-400' : 'text-red-400'}`}>
                {sessionStatus.is_connected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
                {sessionStatus.is_connected ? 'Connected' : 'Offline'}
              </span>
            </div>
          )}
          {sessionStatus.is_connected ? (
            <div className={`space-y-2 ${sidebarCollapsed ? 'flex flex-col items-center' : ''}`}>
              <button onClick={toggleMonitoring} title={sessionStatus.is_monitoring ? 'Stop' : 'Start'}
                className={`${sidebarCollapsed ? 'p-2' : 'w-full py-2 px-3'} rounded-lg text-sm font-medium flex items-center justify-center gap-2 ${
                  sessionStatus.is_monitoring ? 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30' : 'bg-emerald-500 text-white hover:bg-emerald-600'
                }`}>
                {sessionStatus.is_monitoring ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                {!sidebarCollapsed && (sessionStatus.is_monitoring ? 'Stop' : 'Start')}
              </button>
              {!sidebarCollapsed && (
                <button onClick={handleDisconnect} className={`w-full py-2 rounded-lg text-sm flex items-center justify-center gap-2 ${theme === 'dark' ? 'bg-gray-800 text-gray-400 hover:text-white' : 'bg-gray-100 text-gray-600 hover:text-gray-800'}`}>
                  <LogOut className="w-4 h-4" /> Disconnect
                </button>
              )}
            </div>
          ) : (
            <button onClick={handleConnect} title="Connect"
              className={`${sidebarCollapsed ? 'p-2' : 'w-full py-2'} bg-emerald-500 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2 hover:bg-emerald-600`}>
              <Wifi className="w-4 h-4" />
              {!sidebarCollapsed && 'Connect'}
            </button>
          )}
        </div>

        {/* Bottom Actions */}
        <div className={`p-3 border-t ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'} space-y-2`}>
          <button onClick={toggleTheme} title={theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
            className={`${sidebarCollapsed ? 'w-full p-2 justify-center' : 'w-full py-2 px-3'} rounded-lg text-sm flex items-center gap-2 ${theme === 'dark' ? 'text-gray-400 hover:bg-gray-800' : 'text-gray-600 hover:bg-gray-100'}`}>
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            {!sidebarCollapsed && (theme === 'dark' ? 'Light Mode' : 'Dark Mode')}
          </button>
          <button onClick={handleLogout} title="Sign Out"
            className={`${sidebarCollapsed ? 'w-full p-2 justify-center' : 'w-full py-2 px-3'} rounded-lg text-sm flex items-center gap-2 ${theme === 'dark' ? 'text-red-400 hover:bg-red-500/20' : 'text-red-600 hover:bg-red-50'}`}>
            <LogOut className="w-4 h-4" />
            {!sidebarCollapsed && 'Sign Out'}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`flex-1 p-6 ${sidebarCollapsed ? 'ml-16' : 'ml-64'} transition-all duration-300`}>
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && stats && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className={`text-2xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>Dashboard</h2>
              {sessionStatus.is_monitoring && (
                <span className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/20 text-emerald-400 rounded-full text-sm font-medium">
                  <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                  Monitoring Active
                </span>
              )}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <StatCard icon={BarChart3} label="Total Signals" value={stats.total_signals} theme={theme} />
              <StatCard icon={CheckCircle} label="Sent" value={stats.sent_signals} theme={theme} />
              <StatCard icon={Clock} label="Pending" value={stats.pending_signals} theme={theme} />
              <StatCard icon={XCircle} label="Failed" value={stats.failed_signals} theme={theme} />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <StatCard icon={Radio} label="Active Channels" value={stats.active_channels} subtext={`of ${stats.total_channels} total`} theme={theme} />
              <StatCard icon={Activity} label="Today's Signals" value={stats.signals_today} theme={theme} />
              <StatCard icon={TrendingUp} label="Success Rate" value={`${stats.success_rate}%`} theme={theme} />
            </div>
          </div>
        )}

        {/* Channels Tab */}
        {activeTab === 'channels' && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className={`text-2xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>Channels</h2>
                <p className={theme === 'dark' ? 'text-gray-500' : 'text-gray-500'}>Manage monitored channels</p>
              </div>
              {sessionStatus.is_connected && (
                <button onClick={fetchAvailableChannels} disabled={channelsLoading}
                  className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 ${theme === 'dark' ? 'bg-gray-800 text-white hover:bg-gray-700' : 'bg-white text-gray-800 hover:bg-gray-50 shadow'}`}>
                  <RefreshCw className={`w-4 h-4 ${channelsLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              )}
            </div>
            {!sessionStatus.is_connected ? (
              <div className={`rounded-xl p-8 text-center border ${theme === 'dark' ? 'bg-[#1e2329] border-gray-800' : 'bg-white border-gray-200'}`}>
                <WifiOff className={`w-12 h-12 mx-auto mb-4 ${theme === 'dark' ? 'text-gray-600' : 'text-gray-400'}`} />
                <h3 className={`text-lg font-semibold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>Not Connected</h3>
                <p className={`mb-4 ${theme === 'dark' ? 'text-gray-500' : 'text-gray-500'}`}>Connect to Telegram to manage channels</p>
                <button onClick={handleConnect} className="px-6 py-2 bg-emerald-500 text-white rounded-lg font-medium hover:bg-emerald-600">Connect</button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className={`rounded-xl p-4 border ${theme === 'dark' ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-emerald-50 border-emerald-200'}`}>
                  <div className="flex items-center gap-3">
                    <Users className={theme === 'dark' ? 'text-emerald-400' : 'text-emerald-600'} />
                    <span className={theme === 'dark' ? 'text-emerald-400' : 'text-emerald-700'}>
                      <strong>{activeMonitoredCount}</strong> channels actively monitored • {getCombinedChannels.length} total
                    </span>
                  </div>
                </div>
                {/* Monitored */}
                {activeMonitoredCount > 0 && (
                  <div className={`rounded-xl border overflow-hidden ${theme === 'dark' ? 'bg-[#1e2329] border-emerald-500/30' : 'bg-white border-emerald-200'}`}>
                    <div className={`px-4 py-3 border-b ${theme === 'dark' ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-emerald-50 border-emerald-200'}`}>
                      <h3 className={`font-semibold flex items-center gap-2 ${theme === 'dark' ? 'text-emerald-400' : 'text-emerald-700'}`}>
                        <Eye className="w-4 h-4" /> Monitored ({activeMonitoredCount})
                      </h3>
                    </div>
                    <div className="divide-y divide-gray-800/50">
                      {getCombinedChannels.filter(c => c.isMonitored).map(channel => (
                        <div key={channel.channel_id} className={`px-4 py-3 flex items-center justify-between ${theme === 'dark' ? 'hover:bg-gray-800/50' : 'hover:bg-gray-50'}`}>
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className={`font-medium ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>{channel.channel_name}</span>
                              <ChannelTypeBadge type={channel.channel_type} theme={theme} />
                            </div>
                            <div className="flex items-center gap-3 mt-1">
                              <code className={`text-xs px-1.5 py-0.5 rounded ${theme === 'dark' ? 'bg-gray-800 text-gray-400' : 'bg-gray-100 text-gray-600'}`}>{channel.channel_id}</code>
                              <button onClick={() => copy(channel.channel_id, channel.channel_id)} className="text-xs text-emerald-500 hover:text-emerald-400 flex items-center gap-1">
                                {copiedId === channel.channel_id ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                                {copiedId === channel.channel_id ? 'Copied' : 'Copy'}
                              </button>
                              {channel.monitoredData && <span className={`text-xs ${theme === 'dark' ? 'text-gray-500' : 'text-gray-500'}`}>{channel.monitoredData.total_signals || 0} signals</span>}
                            </div>
                          </div>
                          <ToggleSwitch enabled={true} loading={togglingChannels[channel.channel_id]} onChange={() => toggleChannelMonitoring(channel, true)} />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {/* Available */}
                <div className={`rounded-xl border overflow-hidden ${theme === 'dark' ? 'bg-[#1e2329] border-gray-800' : 'bg-white border-gray-200'}`}>
                  <div className={`px-4 py-3 border-b ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'}`}>
                    <h3 className={`font-semibold flex items-center gap-2 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                      <Radio className="w-4 h-4" /> Available ({getCombinedChannels.filter(c => !c.isMonitored).length})
                    </h3>
                  </div>
                  <div className={`divide-y max-h-[400px] overflow-y-auto ${theme === 'dark' ? 'divide-gray-800/50' : 'divide-gray-100'}`}>
                    {getCombinedChannels.filter(c => !c.isMonitored).map(channel => (
                      <div key={channel.channel_id} className={`px-4 py-3 flex items-center justify-between ${theme === 'dark' ? 'hover:bg-gray-800/50' : 'hover:bg-gray-50'}`}>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className={theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}>{channel.channel_name}</span>
                            <ChannelTypeBadge type={channel.channel_type} theme={theme} />
                          </div>
                          <code className={`text-xs ${theme === 'dark' ? 'text-gray-600' : 'text-gray-400'}`}>{channel.channel_id}</code>
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
              <h2 className={`text-2xl font-bold ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>Signals</h2>
              <div className="flex items-center gap-3">
                <Filter className={theme === 'dark' ? 'text-gray-500' : 'text-gray-400'} />
                <select value={signalChannelFilter} onChange={(e) => { setSignalChannelFilter(e.target.value); setSignalPage(1); }}
                  className={`px-3 py-2 rounded-lg text-sm ${theme === 'dark' ? 'bg-[#1e2329] border-gray-700 text-white' : 'bg-white border-gray-200 text-gray-800'} border`}>
                  <option value="">All Channels</option>
                  {activeMonitoredChannels.map(ch => <option key={ch.channel_id} value={ch.channel_id}>{ch.channel_name}</option>)}
                </select>
                <select value={signalStatusFilter} onChange={(e) => { setSignalStatusFilter(e.target.value); setSignalPage(1); }}
                  className={`px-3 py-2 rounded-lg text-sm ${theme === 'dark' ? 'bg-[#1e2329] border-gray-700 text-white' : 'bg-white border-gray-200 text-gray-800'} border`}>
                  <option value="">All Status</option>
                  <option value="sent">Sent</option>
                  <option value="pending">Pending</option>
                  <option value="failed">Failed</option>
                </select>
              </div>
            </div>
            {signals.length === 0 ? (
              <div className={`rounded-xl p-12 text-center border ${theme === 'dark' ? 'bg-[#1e2329] border-gray-800' : 'bg-white border-gray-200'}`}>
                <TrendingUp className={`w-16 h-16 mx-auto mb-4 ${theme === 'dark' ? 'text-gray-700' : 'text-gray-300'}`} />
                <h3 className={`text-lg font-semibold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>No Signals</h3>
                <p className={theme === 'dark' ? 'text-gray-500' : 'text-gray-500'}>{sessionStatus.is_monitoring ? 'Waiting for signals...' : 'Start monitoring to capture signals'}</p>
              </div>
            ) : (
              <div className={`rounded-xl border overflow-hidden ${theme === 'dark' ? 'bg-[#1e2329] border-gray-800' : 'bg-white border-gray-200'}`}>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className={theme === 'dark' ? 'bg-gray-800/50' : 'bg-gray-50'}>
                      <tr>
                        {['Channel', 'Symbol', 'Direction', 'Entry', 'SL', 'TP1', 'Method', 'Status', 'Time'].map(h => (
                          <th key={h} className={`px-4 py-3 text-left text-xs font-semibold ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className={`divide-y ${theme === 'dark' ? 'divide-gray-800' : 'divide-gray-100'}`}>
                      {signals.map(signal => (
                        <tr key={signal.id} className={theme === 'dark' ? 'hover:bg-gray-800/50' : 'hover:bg-gray-50'}>
                          <td className={`px-4 py-3 text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>{signal.channel_name || '-'}</td>
                          <td className={`px-4 py-3 font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-800'}`}>{signal.symbol || '-'}</td>
                          <td className="px-4 py-3">
                            {signal.direction && (
                              <span className={`flex items-center gap-1 font-medium ${signal.direction === 'BUY' ? 'text-emerald-400' : 'text-red-400'}`}>
                                {signal.direction === 'BUY' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                                {signal.direction}
                              </span>
                            )}
                          </td>
                          <td className={`px-4 py-3 font-mono text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>{signal.entry_price?.toFixed(2) || '-'}</td>
                          <td className="px-4 py-3 font-mono text-sm text-red-400">{signal.stop_loss?.toFixed(2) || '-'}</td>
                          <td className="px-4 py-3 font-mono text-sm text-emerald-400">{signal.take_profit_1?.toFixed(2) || '-'}</td>
                          <td className="px-4 py-3"><span className={`px-2 py-1 rounded text-xs ${theme === 'dark' ? 'bg-gray-800 text-gray-400' : 'bg-gray-100 text-gray-600'}`}>{signal.parsing_method || '-'}</span></td>
                          <td className="px-4 py-3"><StatusBadge status={signal.status} theme={theme} /></td>
                          <td className={`px-4 py-3 text-xs ${theme === 'dark' ? 'text-gray-500' : 'text-gray-500'}`}>{formatDateMVT(signal.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {totalSignalPages > 1 && (
                  <div className={`flex items-center justify-center gap-4 p-4 border-t ${theme === 'dark' ? 'border-gray-800' : 'border-gray-200'}`}>
                    <button onClick={() => setSignalPage(p => Math.max(1, p - 1))} disabled={signalPage === 1}
                      className={`px-4 py-2 rounded-lg text-sm ${theme === 'dark' ? 'bg-gray-800 text-white disabled:opacity-50' : 'bg-gray-100 text-gray-800 disabled:opacity-50'}`}>Previous</button>
                    <span className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>Page {signalPage} of {totalSignalPages}</span>
                    <button onClick={() => setSignalPage(p => Math.min(totalSignalPages, p + 1))} disabled={signalPage >= totalSignalPages}
                      className={`px-4 py-2 rounded-lg text-sm ${theme === 'dark' ? 'bg-gray-800 text-white disabled:opacity-50' : 'bg-gray-100 text-gray-800 disabled:opacity-50'}`}>Next</button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>

      <TelegramAuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} onSuccess={handleAuthSuccess} theme={theme} />
    </div>
  );
}

export default App;
