import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL
  ? `${process.env.NEXT_PUBLIC_API_URL}/api`
  : '/api';

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// ─── Signals ──────────────────────────────────────────────────────────
export const fetchLatestSignals = (params?: Record<string, any>) =>
  api.get('/signals/latest', { params }).then(r => r.data);

export const fetchSignalSummary = () =>
  api.get('/signals/summary').then(r => r.data);

export const fetchScanStatus = () =>
  api.get('/signals/scan-status').then(r => r.data);

export const triggerManualScan = () =>
  api.post('/signals/scan-now').then(r => r.data);

export const setScanInterval = (seconds: number) =>
  api.put('/signals/scan-interval', null, { params: { seconds } }).then(r => r.data);

// ─── Backtest ─────────────────────────────────────────────────────────
export const runBacktest = (data: {
  period: string;
  timeframe: string;
  initial_balance: number;
  symbols?: string[];
  start_date?: string | null;
  end_date?: string | null;
}) => api.post('/backtest/run', data).then(r => r.data);

export const fetchBacktestStatus = () =>
  api.get('/backtest/status').then(r => r.data);

export const fetchBacktestResult = () =>
  api.get('/backtest/result').then(r => r.data);

export const fetchEquityCurve = () =>
  api.get('/backtest/result/equity-curve').then(r => r.data);

export const fetchTradeLog = (params?: Record<string, any>) =>
  api.get('/backtest/result/trade-log', { params }).then(r => r.data);

export const fetchStrategyBreakdown = () =>
  api.get('/backtest/result/breakdown').then(r => r.data);

// ─── Settings ─────────────────────────────────────────────────────────
export const fetchAllSettings = () =>
  api.get('/settings/all').then(r => r.data);

// ─── Notifications ────────────────────────────────────────────────────
export const fetchNotificationStatus = () =>
  api.get('/notifications/status').then(r => r.data);

export const testTelegram = (data: { bot_token: string; chat_id: string }) =>
  api.post('/notifications/test/telegram', data).then(r => r.data);

export const testEmail = (data: any) =>
  api.post('/notifications/test/email', data).then(r => r.data);

export const testSms = (data: any) =>
  api.post('/notifications/test/sms', data).then(r => r.data);

export const sendTestSignal = (channel: string) =>
  api.post('/notifications/test/signal', { channel }).then(r => r.data);

// ─── System ───────────────────────────────────────────────────────────
export const fetchSystemInfo = () =>
  api.get('/system').then(r => r.data);

export const fetchHealth = () =>
  api.get('/health').then(r => r.data);
