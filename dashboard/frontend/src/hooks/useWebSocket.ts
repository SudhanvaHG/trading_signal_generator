import { useEffect } from 'react';
import { wsClient } from '@/lib/websocket';
import { useStore } from '@/store/useStore';
import toast from 'react-hot-toast';

export function useWebSocket() {
  const {
    setWsConnected,
    addLiveSignal,
    setScanSummary,
    setIsScanning,
    setBacktestRunning,
    setBacktestProgress,
    setBacktestResult,
  } = useStore();

  useEffect(() => {
    wsClient.connect();

    const offConn = wsClient.on('connection', ({ status }) => {
      setWsConnected(status === 'connected');
      if (status === 'connected') {
        toast.success('Live feed connected', { duration: 2000 });
      }
    });

    const offSignal = wsClient.on('signal', (msg) => {
      addLiveSignal(msg.data);
      const s = msg.data;
      const dir = s.signal === 'BUY' ? '🟢' : '🔴';
      toast(`${dir} ${s.symbol} ${s.signal} — ${s.strategy?.replace('_', ' ')}`, {
        duration: 6000,
        style: {
          background: '#141D2B',
          color: '#E0E6ED',
          border: '1px solid #1E2D3D',
          fontFamily: 'monospace',
        },
      });
    });

    const offScan = wsClient.on('scan_status', (msg) => {
      setIsScanning(msg.status === 'running');
      if (msg.status === 'complete') {
        setScanSummary(msg.summary);
      }
    });

    const offBtProgress = wsClient.on('backtest_progress', (msg) => {
      setBacktestProgress(msg.progress, msg.message);
    });

    const offBtComplete = wsClient.on('backtest_complete', (msg) => {
      setBacktestRunning(false);
      setBacktestProgress(100, 'Complete');
      toast.success(`Backtest complete — ${msg.data?.total_return_pct?.toFixed(2)}% return`, {
        duration: 5000,
      });
    });

    const offBtError = wsClient.on('backtest_error', (msg) => {
      setBacktestRunning(false);
      toast.error(`Backtest failed: ${msg.error}`, { duration: 6000 });
    });

    const offRisk = wsClient.on('risk_alert', (msg) => {
      toast.error(`⚠️ Risk: ${msg.message}`, { duration: 8000 });
    });

    return () => {
      offConn(); offSignal(); offScan();
      offBtProgress(); offBtComplete(); offBtError(); offRisk();
    };
  }, []);
}
