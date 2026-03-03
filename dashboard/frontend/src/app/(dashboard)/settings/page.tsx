'use client';
import { useEffect } from 'react';
import { Header } from '@/components/dashboard/Header';
import { Card, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useStore } from '@/store/useStore';
import { fetchAllSettings, fetchSystemInfo } from '@/lib/api';
import { useState } from 'react';
import { Settings, Server, Shield, TrendingUp } from 'lucide-react';

export default function SettingsPage() {
  const { settings, setSettings } = useStore();
  const [sysInfo, setSysInfo] = useState<any>(null);

  useEffect(() => {
    fetchAllSettings().then(setSettings).catch(console.error);
    fetchSystemInfo().then(setSysInfo).catch(console.error);
  }, []);

  const Row = ({ label, value, color }: { label: string; value: any; color?: string }) => (
    <div className="flex justify-between items-center py-2 border-b border-bg-border/50 text-sm">
      <span className="text-text-secondary font-mono">{label}</span>
      <span className={`font-mono font-semibold ${color || 'text-text-primary'}`}>{String(value)}</span>
    </div>
  );

  return (
    <div className="animate-fade-in">
      <Header title="Settings" subtitle="System configuration and parameters" />
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

          {/* Risk Config */}
          <Card>
            <CardHeader title="Risk Configuration" action={<Shield className="w-4 h-4 text-accent-yellow" />} />
            {settings?.risk ? (
              <div>
                <Row label="Risk Per Trade" value={`${settings.risk.risk_per_trade_pct}%`} color="text-accent-green" />
                <Row label="Max Trades/Day" value={settings.risk.max_trades_per_day} />
                <Row label="Max Consecutive Losses" value={settings.risk.max_consecutive_losses} />
                <Row label="Daily Loss Cap" value={`${settings.risk.max_daily_loss_pct}%`} color="text-accent-red" />
                <Row label="Max Overall Drawdown" value={`${settings.risk.max_overall_drawdown_pct}%`} color="text-accent-red" />
                <Row label="Min R:R Ratio" value={`1:${settings.risk.min_reward_risk_ratio}`} color="text-accent-blue" />
                <Row label="Challenge Target" value={`${settings.risk.challenge_profit_target_pct}%`} color="text-accent-green" />
                <Row label="Trail Activation" value={`${settings.risk.trail_activation_rr}R`} />
              </div>
            ) : <p className="text-text-secondary text-sm">Loading...</p>}
          </Card>

          {/* Strategy Config */}
          <Card>
            <CardHeader title="Strategy Configuration" action={<TrendingUp className="w-4 h-4 text-accent-blue" />} />
            {settings?.strategy ? (
              <div>
                <Row label="EMA Fast Period" value={settings.strategy.ema_fast_period} />
                <Row label="EMA Slow Period" value={settings.strategy.ema_slow_period} />
                <Row label="Lookback Period" value={`${settings.strategy.lookback_period} bars`} />
                <Row label="ATR Period" value={settings.strategy.atr_period} />
                <Row label="ATR SL Multiplier" value={`${settings.strategy.atr_sl_multiplier}×`} />
                <Row label="ATR TP Multiplier" value={`${settings.strategy.atr_tp_multiplier}×`} />
                <Row label="Min R:R" value={`1:${settings.strategy.min_reward_risk_ratio}`} color="text-accent-blue" />
                <Row label="Min Body %"  value={`${(settings.strategy.breakout_min_body_pct*100).toFixed(0)}%`} />
                <Row label="Volume Factor" value={`${settings.strategy.volume_expansion_factor}×`} />
                <Row label="Retest Tolerance" value={`${settings.strategy.retest_tolerance_pct}%`} />
              </div>
            ) : <p className="text-text-secondary text-sm">Loading...</p>}
          </Card>

          {/* Assets */}
          <Card>
            <CardHeader title="Configured Assets" action={<Settings className="w-4 h-4 text-text-secondary" />} />
            <div className="space-y-3">
              {(settings?.assets || []).map((a: any) => (
                <div key={a.symbol} className="flex items-center justify-between p-3 rounded-lg bg-bg-secondary border border-bg-border">
                  <div>
                    <p className="text-text-primary font-mono font-semibold text-sm">{a.symbol}</p>
                    <p className="text-text-secondary text-xs">{a.display_name}</p>
                  </div>
                  <div className="flex items-center gap-2 text-right">
                    <div>
                      <p className="text-text-secondary text-[10px]">Pip: {a.pip_value}</p>
                      <p className="text-text-secondary text-[10px]">Spread: {a.spread_pips}</p>
                    </div>
                    <Badge variant={a.asset_class === 'crypto' ? 'purple' : a.asset_class === 'forex' ? 'blue' : 'yellow'}>
                      {a.asset_class}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* System Info */}
          <Card>
            <CardHeader title="System Information" action={<Server className="w-4 h-4 text-text-secondary" />} />
            {sysInfo ? (
              <div>
                <Row label="Version" value={sysInfo.version} color="text-accent-green" />
                <Row label="WS Clients" value={sysInfo.ws_clients} />
                <Row label="Scan Count" value={sysInfo.last_scan?.scan_count ?? 0} />
                <Row label="Last Scan Signals" value={sysInfo.last_scan?.signals ?? 0} />
                <Row label="Telegram" value={sysInfo.notifications?.telegram ? '✓ Enabled' : '✗ Disabled'}
                  color={sysInfo.notifications?.telegram ? 'text-accent-green' : 'text-text-muted'} />
                <Row label="Email" value={sysInfo.notifications?.email ? '✓ Enabled' : '✗ Disabled'}
                  color={sysInfo.notifications?.email ? 'text-accent-green' : 'text-text-muted'} />
                <Row label="SMS" value={sysInfo.notifications?.sms ? '✓ Enabled' : '✗ Disabled'}
                  color={sysInfo.notifications?.sms ? 'text-accent-green' : 'text-text-muted'} />
                <Row label="Scheduler" value={sysInfo.scheduler?.running ? '✓ Running' : '✗ Stopped'}
                  color={sysInfo.scheduler?.running ? 'text-accent-green' : 'text-accent-red'} />
                <Row label="Next Scan" value={sysInfo.scheduler?.next_run ? new Date(sysInfo.scheduler.next_run).toLocaleTimeString() : '—'} />
              </div>
            ) : <p className="text-text-secondary text-sm">Loading...</p>}
          </Card>
        </div>

        <Card>
          <CardHeader title="Environment Configuration" subtitle="Set these in your .env file or docker-compose.yml" />
          <div className="bg-bg-primary rounded-lg p-4 font-mono text-xs text-text-secondary overflow-x-auto">
            <pre>{`# ─── App ──────────────────────────────────────
APP_NAME=PropAlgo Trading Dashboard
SECRET_KEY=<generate with: openssl rand -hex 32>

# ─── Trading ──────────────────────────────────
INITIAL_BALANCE=10000.0
LIVE_SCAN_INTERVAL=60

# ─── Telegram ─────────────────────────────────
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=<your-bot-token>
TELEGRAM_CHAT_ID=<your-chat-id>

# ─── Email ────────────────────────────────────
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=you@gmail.com
SMTP_PASSWORD=<gmail-app-password>
SMTP_FROM_EMAIL=you@gmail.com
EMAIL_RECIPIENTS=["you@gmail.com"]

# ─── SMS (Twilio) ─────────────────────────────
SMS_ENABLED=true
TWILIO_ACCOUNT_SID=ACxxxxxxxxxx
TWILIO_AUTH_TOKEN=<auth-token>
TWILIO_FROM_NUMBER=+1xxxxxxxxxx
SMS_RECIPIENTS=["+1xxxxxxxxxx"]

# ─── Notifications ────────────────────────────
NOTIFY_ON_SIGNAL=true
NOTIFY_ON_RISK_ALERT=true
MIN_CONFIDENCE_NOTIFY=0.65`}</pre>
          </div>
        </Card>
      </div>
    </div>
  );
}
