'use client';
import { useEffect, useState } from 'react';
import { Header } from '@/components/dashboard/Header';
import { Card, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { useStore } from '@/store/useStore';
import {
  fetchNotificationStatus, testTelegram, testEmail,
  testSms, sendTestSignal,
} from '@/lib/api';
import { Bell, Send, CheckCircle, XCircle } from 'lucide-react';
import toast from 'react-hot-toast';

function StatusDot({ ok }: { ok: boolean }) {
  return <span className={`inline-block w-2 h-2 rounded-full ${ok ? 'bg-accent-green' : 'bg-text-muted'}`} />;
}

export default function NotificationsPage() {
  const { notificationStatus, setNotificationStatus } = useStore();
  const [loading, setLoading] = useState<string | null>(null);

  // Telegram form
  const [tgToken, setTgToken] = useState('');
  const [tgChat, setTgChat]   = useState('');

  // Email form
  const [emailHost, setEmailHost]   = useState('smtp.gmail.com');
  const [emailPort, setEmailPort]   = useState(587);
  const [emailUser, setEmailUser]   = useState('');
  const [emailPass, setEmailPass]   = useState('');
  const [emailFrom, setEmailFrom]   = useState('');
  const [emailTo, setEmailTo]       = useState('');

  // SMS form
  const [smsSid, setSmsSid]     = useState('');
  const [smsToken, setSmsToken] = useState('');
  const [smsFrom, setSmsFrom]   = useState('');
  const [smsTo, setSmsTo]       = useState('');

  useEffect(() => {
    fetchNotificationStatus().then(setNotificationStatus).catch(console.error);
  }, []);

  const status = notificationStatus;

  const handleTestTelegram = async () => {
    setLoading('telegram');
    try {
      const r = await testTelegram({ bot_token: tgToken, chat_id: tgChat });
      toast.success(r.message);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Telegram test failed');
    } finally { setLoading(null); }
  };

  const handleTestEmail = async () => {
    setLoading('email');
    try {
      const r = await testEmail({ smtp_host: emailHost, smtp_port: emailPort, username: emailUser, password: emailPass, from_email: emailFrom, to_email: emailTo });
      toast.success(r.message);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Email test failed');
    } finally { setLoading(null); }
  };

  const handleTestSms = async () => {
    setLoading('sms');
    try {
      const r = await testSms({ account_sid: smsSid, auth_token: smsToken, from_number: smsFrom, to_number: smsTo });
      toast.success(r.message);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'SMS test failed');
    } finally { setLoading(null); }
  };

  const handleTestSignal = async (channel: string) => {
    setLoading(`test-${channel}`);
    try {
      await sendTestSignal(channel);
      toast.success(`Test signal sent via ${channel}`);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Test failed');
    } finally { setLoading(null); }
  };

  const inputCls = "w-full bg-bg-border border border-bg-border text-text-primary text-sm rounded-lg px-3 py-2 font-mono focus:outline-none focus:border-accent-blue/50";
  const labelCls = "block text-text-secondary text-[10px] uppercase tracking-wider mb-1";

  return (
    <div className="animate-fade-in">
      <Header title="Notifications" subtitle="Configure Telegram, Email, and SMS alerts" />
      <div className="p-6 space-y-6">

        {/* Status Overview */}
        <Card>
          <CardHeader title="Channel Status" />
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { label: 'Telegram', key: 'telegram', icon: '📨' },
              { label: 'Email',    key: 'email',    icon: '📧' },
              { label: 'SMS',      key: 'sms',      icon: '📱' },
            ].map(({ label, key, icon }) => {
              const ch = status?.[key];
              return (
                <div key={key} className="flex items-center gap-3 p-4 rounded-lg bg-bg-secondary border border-bg-border">
                  <span className="text-2xl">{icon}</span>
                  <div className="flex-1">
                    <p className="text-text-primary font-medium text-sm">{label}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <StatusDot ok={ch?.enabled} />
                      <span className="text-xs text-text-secondary">{ch?.enabled ? 'Enabled' : 'Disabled'}</span>
                      <span className="text-text-muted">·</span>
                      <StatusDot ok={ch?.configured} />
                      <span className="text-xs text-text-secondary">{ch?.configured ? 'Configured' : 'Not set'}</span>
                    </div>
                  </div>
                  {ch?.enabled && ch?.configured
                    ? <Badge variant="green">Active</Badge>
                    : <Badge variant="gray">Inactive</Badge>}
                </div>
              );
            })}
          </div>
          <p className="text-text-secondary text-xs mt-4">
            To enable channels, set the corresponding environment variables and restart the container. Use the test forms below to validate credentials.
          </p>
        </Card>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

          {/* Telegram */}
          <Card>
            <CardHeader title="Telegram" subtitle="Bot API credentials" action={<span className="text-2xl">📨</span>} />
            <div className="space-y-3">
              <div>
                <label className={labelCls}>Bot Token</label>
                <input type="password" placeholder="123456:ABCdef..." value={tgToken} onChange={e=>setTgToken(e.target.value)} className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>Chat ID</label>
                <input type="text" placeholder="-1001234567890" value={tgChat} onChange={e=>setTgChat(e.target.value)} className={inputCls} />
              </div>
              <div className="flex gap-2 pt-1">
                <Button size="sm" variant="primary" icon={<CheckCircle className="w-3.5 h-3.5"/>}
                  onClick={handleTestTelegram} loading={loading==='telegram'} disabled={!tgToken||!tgChat}>
                  Test Connection
                </Button>
                <Button size="sm" variant="secondary" icon={<Send className="w-3.5 h-3.5"/>}
                  onClick={()=>handleTestSignal('telegram')} loading={loading==='test-telegram'}>
                  Send Test Signal
                </Button>
              </div>
              <div className="bg-bg-secondary rounded-lg p-3 text-xs text-text-secondary border border-bg-border mt-2">
                <p className="font-semibold text-text-primary mb-1">Setup Instructions:</p>
                <ol className="space-y-0.5 list-decimal list-inside">
                  <li>Create a bot via <span className="text-accent-blue">@BotFather</span> on Telegram</li>
                  <li>Copy the API token above</li>
                  <li>Add bot to a channel/group or use direct chat</li>
                  <li>Get Chat ID via <span className="text-accent-blue">@userinfobot</span></li>
                  <li>Set <code>TELEGRAM_BOT_TOKEN</code> and <code>TELEGRAM_CHAT_ID</code> in .env</li>
                </ol>
              </div>
            </div>
          </Card>

          {/* Email */}
          <Card>
            <CardHeader title="Email (SMTP)" subtitle="Gmail or custom SMTP" action={<span className="text-2xl">📧</span>} />
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={labelCls}>SMTP Host</label>
                  <input type="text" value={emailHost} onChange={e=>setEmailHost(e.target.value)} className={inputCls} />
                </div>
                <div>
                  <label className={labelCls}>Port</label>
                  <input type="number" value={emailPort} onChange={e=>setEmailPort(Number(e.target.value))} className={inputCls} />
                </div>
              </div>
              <div>
                <label className={labelCls}>Username / Email</label>
                <input type="email" placeholder="you@gmail.com" value={emailUser} onChange={e=>setEmailUser(e.target.value)} className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>App Password</label>
                <input type="password" placeholder="Gmail App Password" value={emailPass} onChange={e=>setEmailPass(e.target.value)} className={inputCls} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={labelCls}>From</label>
                  <input type="email" value={emailFrom} onChange={e=>setEmailFrom(e.target.value)} className={inputCls} />
                </div>
                <div>
                  <label className={labelCls}>To (test)</label>
                  <input type="email" value={emailTo} onChange={e=>setEmailTo(e.target.value)} className={inputCls} />
                </div>
              </div>
              <div className="flex gap-2 pt-1">
                <Button size="sm" variant="primary" icon={<CheckCircle className="w-3.5 h-3.5"/>}
                  onClick={handleTestEmail} loading={loading==='email'} disabled={!emailUser||!emailPass}>
                  Test Connection
                </Button>
                <Button size="sm" variant="secondary" icon={<Send className="w-3.5 h-3.5"/>}
                  onClick={()=>handleTestSignal('email')} loading={loading==='test-email'}>
                  Send Test Signal
                </Button>
              </div>
            </div>
          </Card>

          {/* SMS */}
          <Card>
            <CardHeader title="SMS (Twilio)" subtitle="Twilio account credentials" action={<span className="text-2xl">📱</span>} />
            <div className="space-y-3">
              <div>
                <label className={labelCls}>Account SID</label>
                <input type="text" placeholder="ACxxxxxxxxxxxxxxxx" value={smsSid} onChange={e=>setSmsSid(e.target.value)} className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>Auth Token</label>
                <input type="password" value={smsToken} onChange={e=>setSmsToken(e.target.value)} className={inputCls} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={labelCls}>From Number</label>
                  <input type="text" placeholder="+1234567890" value={smsFrom} onChange={e=>setSmsFrom(e.target.value)} className={inputCls} />
                </div>
                <div>
                  <label className={labelCls}>To Number (test)</label>
                  <input type="text" placeholder="+1234567890" value={smsTo} onChange={e=>setSmsTo(e.target.value)} className={inputCls} />
                </div>
              </div>
              <div className="flex gap-2 pt-1">
                <Button size="sm" variant="primary" icon={<CheckCircle className="w-3.5 h-3.5"/>}
                  onClick={handleTestSms} loading={loading==='sms'} disabled={!smsSid||!smsToken}>
                  Test Connection
                </Button>
                <Button size="sm" variant="secondary" icon={<Send className="w-3.5 h-3.5"/>}
                  onClick={()=>handleTestSignal('sms')} loading={loading==='test-sms'}>
                  Send Test Signal
                </Button>
              </div>
            </div>
          </Card>

          {/* Test All */}
          <Card>
            <CardHeader title="Broadcast Test" subtitle="Send test signal to all active channels" />
            <div className="flex flex-col gap-3">
              {['telegram','email','sms','all'].map(ch => (
                <Button key={ch} variant="secondary" size="sm"
                  icon={<Send className="w-3.5 h-3.5"/>}
                  onClick={()=>handleTestSignal(ch)}
                  loading={loading===`test-${ch}`}
                  className="justify-start capitalize">
                  Send test via {ch === 'all' ? 'ALL channels' : ch}
                </Button>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
