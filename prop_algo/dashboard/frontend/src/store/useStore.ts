import { create } from 'zustand';

export interface Signal {
  timestamp: string;
  symbol: string;
  signal: 'BUY' | 'SELL';
  strategy: string;
  entry: number;
  stop_loss: number;
  take_profit: number;
  rr_ratio: number;
  confidence: number;
  volume_ok: boolean;
  reason: string;
  trend: number;
}

export interface BacktestResult {
  run_at: string;
  period: string;
  timeframe: string;
  symbols?: string[];
  start_date?: string | null;
  end_date?: string | null;
  initial_balance: number;
  final_balance: number;
  total_return_pct: number;
  total_trades: number;
  wins: number;
  losses: number;
  win_rate_pct: number;
  max_drawdown_pct: number;
  current_drawdown_pct?: number;
  challenge_passed: boolean;
  challenge_target_pct?: number;
  account_blown?: boolean;
  equity_curve: any[];
  trade_log: any[];
  strategy_breakdown: Record<string, any>;
  asset_breakdown: Record<string, any>;
  approved_signals?: any[];
  approved_signals_count?: number;
  raw_signals_count?: number;
  rejected_signals_count?: number;
  data_status?: Record<string, any>;
}

interface ScanStatus {
  running: boolean;
  interval_seconds: number;
  next_run: string | null;
  scan_count: number;
  last_scan: string | null;
}

interface Store {
  // WS
  wsConnected: boolean;
  setWsConnected: (v: boolean) => void;

  // Signals
  signals: Signal[];
  setSignals: (s: Signal[]) => void;
  addSignal: (s: Signal) => void;
  liveSignals: Signal[];      // signals received via WS in real time
  addLiveSignal: (s: Signal) => void;
  clearLiveSignals: () => void;

  // Scan
  scanStatus: ScanStatus | null;
  setScanStatus: (s: ScanStatus) => void;
  scanSummary: any;
  setScanSummary: (s: any) => void;
  isScanning: boolean;
  setIsScanning: (v: boolean) => void;

  // Backtest
  backtestResult: BacktestResult | null;
  setBacktestResult: (r: BacktestResult) => void;
  backtestRunning: boolean;
  setBacktestRunning: (v: boolean) => void;
  backtestProgress: number;
  backtestProgressMsg: string;
  setBacktestProgress: (pct: number, msg: string) => void;

  // Notifications
  notificationStatus: any;
  setNotificationStatus: (s: any) => void;

  // Settings
  settings: any;
  setSettings: (s: any) => void;
}

export const useStore = create<Store>((set) => ({
  wsConnected: false,
  setWsConnected: (v) => set({ wsConnected: v }),

  signals: [],
  setSignals: (s) => set({ signals: s }),
  addSignal: (s) => set((state) => ({
    signals: [s, ...state.signals].slice(0, 200),
  })),
  liveSignals: [],
  addLiveSignal: (s) => set((state) => ({
    liveSignals: [s, ...state.liveSignals].slice(0, 50),
  })),
  clearLiveSignals: () => set({ liveSignals: [] }),

  scanStatus: null,
  setScanStatus: (s) => set({ scanStatus: s }),
  scanSummary: null,
  setScanSummary: (s) => set({ scanSummary: s }),
  isScanning: false,
  setIsScanning: (v) => set({ isScanning: v }),

  backtestResult: null,
  setBacktestResult: (r) => set({ backtestResult: r }),
  backtestRunning: false,
  setBacktestRunning: (v) => set({ backtestRunning: v }),
  backtestProgress: 0,
  backtestProgressMsg: '',
  setBacktestProgress: (pct, msg) => set({ backtestProgress: pct, backtestProgressMsg: msg }),

  notificationStatus: null,
  setNotificationStatus: (s) => set({ notificationStatus: s }),

  settings: null,
  setSettings: (s) => set({ settings: s }),
}));
