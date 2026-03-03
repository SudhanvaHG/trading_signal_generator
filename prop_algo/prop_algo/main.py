#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║        PROP FIRM ALGO TRADING SYSTEM — MAIN ENTRY POINT        ║
║                                                                  ║
║  Assets: XAUUSD (Gold), BTCUSD, XRPUSD, EURUSD                ║
║  Strategies: Breakout+Retest, EMA Trend Pullback, Mean Revert  ║
║  Risk: 0.5%/trade, 2 trades/day max, 2% daily cap              ║
║                                                                  ║
║  USAGE:                                                          ║
║    python -m prop_algo.main              → live signal loop     ║
║    python -m prop_algo.main --backtest   → run backtest once    ║
║    python -m prop_algo.main --interval 300  → refresh every 5m ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prop_algo.config.settings import (
    ASSETS, DEFAULT_RISK, DEFAULT_STRATEGY, RiskConfig, StrategyConfig
)
from prop_algo.signals.engine import SignalEngine
from prop_algo.utils.reporting import generate_signal_report

# ─── Logging Setup ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def print_banner():
    """Display system banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   ██████╗ ██████╗  ██████╗ ██████╗      █████╗ ██╗      ██████╗  ██████╗ ║
║   ██╔══██╗██╔══██╗██╔═══██╗██╔══██╗    ██╔══██╗██║     ██╔════╝ ██╔═══██╗║
║   ██████╔╝██████╔╝██║   ██║██████╔╝    ███████║██║     ██║  ███╗██║   ██║║
║   ██╔═══╝ ██╔══██╗██║   ██║██╔═══╝     ██╔══██║██║     ██║   ██║██║   ██║║
║   ██║     ██║  ██║╚██████╔╝██║         ██║  ██║███████╗╚██████╔╝╚██████╔╝║
║   ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝         ╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝║
║                                                                          ║
║   Prop Firm Algo Trading System v1.0                                     ║
║   Assets: XAUUSD | BTCUSD | XRPUSD | EURUSD                            ║
║   Rules:  0.5% risk | 2 trades/day | 1:2 RR min | 8% max DD            ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_section(title: str):
    """Print formatted section header."""
    width = 65
    print(f"\n{'═' * width}")
    print(f"  {title}")
    print(f"{'═' * width}")


def print_data_status(data_status: dict):
    """Display data fetch results."""
    print_section("📊 DATA STATUS")
    for symbol, info in data_status.items():
        asset = ASSETS.get(symbol)
        name = asset.display_name if asset else symbol
        if info["status"] == "OK":
            print(f"  ✅ {name:25s} | {info['bars']:4d} bars | {info['start']} → {info['end']}")
        else:
            print(f"  ❌ {name:25s} | FAILED ({info.get('bars', 0)} bars)")


def print_signal_summary(engine):
    """Display signal generation summary."""
    print_section("📡 SIGNAL GENERATION")
    print(f"  Raw signals generated:   {len(engine.all_signals)}")
    print(f"  Approved (post-risk):    {len(engine.approved_signals)}")
    print(f"  Rejected by risk mgr:    {len(engine.rejected_signals)}")

    # By strategy
    strat_counts = {}
    for s in engine.approved_signals:
        key = s.strategy_name
        strat_counts[key] = strat_counts.get(key, 0) + 1

    if strat_counts:
        print(f"\n  By Strategy:")
        for strat, count in sorted(strat_counts.items()):
            print(f"    {strat:25s} → {count} signals")

    # By asset
    asset_counts = {}
    for s in engine.approved_signals:
        asset_counts[s.symbol] = asset_counts.get(s.symbol, 0) + 1

    if asset_counts:
        print(f"\n  By Asset:")
        for asset, count in sorted(asset_counts.items()):
            name = ASSETS[asset].display_name if asset in ASSETS else asset
            print(f"    {name:25s} → {count} signals")


def print_recent_signals(engine, n: int = 15):
    """Display most recent signals in a formatted table."""
    print_section("🎯 CURRENT SIGNALS")

    df = engine.get_latest_signals(n=n)
    if df.empty:
        print("  No signals found in this scan.")
        return

    # Header
    header = (
        f"  {'Date':12s} {'Symbol':8s} {'Signal':6s} {'Strategy':22s} "
        f"{'Entry':>12s} {'SL':>12s} {'TP':>12s} {'RR':>5s} {'Conf':>5s} {'Vol':>4s}"
    )
    print(header)
    print(f"  {'─' * 100}")

    for _, row in df.iterrows():
        ts = str(row['timestamp'])[:10] if hasattr(row['timestamp'], 'strftime') else str(row['timestamp'])[:10]
        sig_color = "🟢" if row['signal'] == 'BUY' else "🔴"
        print(
            f"  {ts:12s} {row['symbol']:8s} {sig_color}{row['signal']:5s} {row['strategy']:22s} "
            f"{row['entry']:12.4f} {row['stop_loss']:12.4f} {row['take_profit']:12.4f} "
            f"{row['rr_ratio']:5.1f} {row['confidence']:5.2f} {'✓' if row['volume_ok'] else '✗':>4s}"
        )


def print_backtest_results(summary: dict):
    """Display backtest results."""
    print_section("📈 BACKTEST RESULTS")

    ret = summary["total_return_pct"]
    ret_color = "🟢" if ret >= 0 else "🔴"

    print(f"  Starting Balance:     ${summary['initial_balance']:,.2f}")
    print(f"  Final Balance:        ${summary['current_balance']:,.2f}")
    print(f"  Total Return:         {ret_color} {ret:+.2f}%")
    print(f"  ")
    print(f"  Total Trades:         {summary['total_trades']}")
    print(f"  Wins / Losses:        {summary['wins']} / {summary['losses']}")
    print(f"  Win Rate:             {summary['win_rate_pct']:.1f}%")
    print(f"  Max Drawdown:         {summary['max_drawdown_pct']:.2f}%")
    print(f"  Current Drawdown:     {summary['current_drawdown_pct']:.2f}%")
    print(f"  ")

    # Challenge status
    if summary.get("challenge_passed"):
        print(f"  🏆 CHALLENGE STATUS:   ✅ PASSED ({ret:.1f}% ≥ {summary['challenge_target_pct']}% target)")
    elif summary.get("account_blown"):
        print(f"  💀 CHALLENGE STATUS:   ❌ BLOWN (Max drawdown breached)")
    else:
        remaining = summary["challenge_target_pct"] - ret
        print(f"  ⏳ CHALLENGE STATUS:   IN PROGRESS ({remaining:.1f}% remaining to target)")


def print_risk_rules():
    """Display active risk rules."""
    print_section("🔐 ACTIVE RISK RULES")
    rules = [
        f"Risk per trade:          {DEFAULT_RISK.risk_per_trade_pct}%",
        f"Max trades/day:          {DEFAULT_RISK.max_trades_per_day}",
        f"Stop after losses:       {DEFAULT_RISK.max_consecutive_losses} consecutive",
        f"Daily loss cap:          {DEFAULT_RISK.max_daily_loss_pct}%",
        f"Overall DD limit:        {DEFAULT_RISK.max_overall_drawdown_pct}%",
        f"Min Reward:Risk:         1:{DEFAULT_RISK.min_reward_risk_ratio:.0f}",
        f"Challenge target:        {DEFAULT_RISK.challenge_profit_target_pct}%",
        f"Trail activation:        {DEFAULT_RISK.trail_activation_rr}R",
    ]
    for rule in rules:
        print(f"  ✦ {rule}")


def print_position_sizing_examples(engine):
    """Show position sizing for recent signals."""
    if not engine.approved_signals:
        return

    print_section("📐 POSITION SIZING")
    recent = engine.approved_signals[-4:]

    for signal in recent:
        asset = ASSETS.get(signal.symbol)
        pip_val = asset.pip_value if asset else 0.0001
        sizing = engine.risk_manager.calculate_position_size(signal, pip_val)

        print(f"  {signal.symbol} {signal.signal.value}:")
        print(f"    Entry: {signal.entry_price:.4f}  |  SL: {signal.stop_loss:.4f}  |  Risk: ${sizing['risk_amount']:.2f}")
        print(f"    Position: {sizing['lots']:.4f} lots ({sizing['units']:.0f} units)")
        print()


def build_engine(assets, initial_balance):
    """Create a fresh SignalEngine instance."""
    return SignalEngine(
        assets=assets,
        risk_config=DEFAULT_RISK,
        strategy_config=DEFAULT_STRATEGY,
        initial_balance=initial_balance,
    )


# ─── MODE 1: LIVE SIGNAL LOOP ─────────────────────────────────────────

def run_live(args):
    """
    Continuously scan for signals, refreshing every `interval` seconds.
    Press Ctrl+C to stop.
    """
    assets = ["XAUUSD", "BTCUSD", "XRPUSD", "EURUSD"]
    initial_balance = 10000.0
    refresh_seconds = args.interval
    data_period = args.period       # lookback window for signal context
    data_interval = args.timeframe  # candle size

    print_banner()
    print_risk_rules()

    print(f"\n  Mode:      LIVE SIGNAL MONITOR")
    print(f"  Refresh:   every {refresh_seconds}s")
    print(f"  Period:    {data_period} of {data_interval} candles")
    print(f"  Assets:    {', '.join(assets)}")
    print(f"\n  Press Ctrl+C to stop.\n")

    scan_count = 0

    while True:
        scan_count += 1
        scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n{'━' * 65}")
        print(f"  SCAN #{scan_count}  —  {scan_time}")
        print(f"{'━' * 65}")

        try:
            engine = build_engine(assets, initial_balance)
            results = engine.run_signals_only(period=data_period, interval=data_interval)

            print_data_status(results["data_status"])
            print_signal_summary(engine)
            print_recent_signals(engine, n=20)
            print_position_sizing_examples(engine)

        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error(f"Scan #{scan_count} failed: {e}")

        print(f"\n  Next scan in {refresh_seconds}s  (Ctrl+C to quit)...")

        try:
            time.sleep(refresh_seconds)
        except KeyboardInterrupt:
            print("\n\n  Signal monitor stopped. Goodbye.")
            break


# ─── MODE 2: BACKTEST ─────────────────────────────────────────────────

def run_backtest(args):
    """Run a full backtest simulation once and exit."""
    assets = ["XAUUSD", "BTCUSD", "XRPUSD", "EURUSD"]
    initial_balance = 10000.0
    data_period = args.period
    data_interval = args.timeframe

    print_banner()
    print_risk_rules()

    print(f"\n  Mode:      BACKTEST")
    print(f"  Period:    {data_period} of {data_interval} candles")
    print(f"  Balance:   ${initial_balance:,.2f}")
    print(f"  Assets:    {', '.join(assets)}")

    engine = build_engine(assets, initial_balance)

    results = engine.run_full_pipeline(
        period=data_period,
        interval=data_interval,
    )

    print_data_status(results["data_status"])
    print_signal_summary(engine)
    print_recent_signals(engine, n=20)
    print_position_sizing_examples(engine)
    print_backtest_results(results["backtest_summary"])

    # Generate charts + CSVs
    output_dir = str(Path(__file__).parent / "output")
    print_section("📊 GENERATING REPORTS")

    files = generate_signal_report(results, engine, output_dir=output_dir)
    for name, path in files.items():
        print(f"  📄 {name:30s} → {path}")

    print_section("✅ BACKTEST COMPLETE")
    print(f"  Timestamp:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Assets analyzed:  {len(engine.data)}")
    print(f"  Strategies run:   {len(engine.strategies)}")
    print(f"  Signals approved: {len(engine.approved_signals)}")
    print(f"  Output files:     {len(files)}")
    print(f"\n  All outputs saved to: {output_dir}/")
    print()

    return results, engine


# ─── CLI ENTRY POINT ──────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Prop Firm Algo Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m prop_algo.main                      # live signals, refresh every 60s
  python -m prop_algo.main --interval 300       # live signals, refresh every 5 min
  python -m prop_algo.main --backtest           # run backtest once and exit
  python -m prop_algo.main --backtest --period 6mo  # backtest on 6 months of data
        """,
    )

    parser.add_argument(
        "--backtest",
        action="store_true",
        help="Run backtest simulation once and exit (default: live signal loop)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        metavar="SECONDS",
        help="Seconds between live signal refreshes (default: 60, live mode only)",
    )
    parser.add_argument(
        "--period",
        type=str,
        default="3mo",
        choices=["1mo", "3mo", "6mo", "1y", "2y"],
        help="Lookback data period (default: 3mo for live, use 1y for backtest)",
    )
    parser.add_argument(
        "--timeframe",
        type=str,
        default="1d",
        choices=["1h", "4h", "1d"],
        help="Candle interval (default: 1d)",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # When running backtest, default period to 1y if user didn't specify
    if args.backtest and args.period == "3mo":
        args.period = "1y"

    if args.backtest:
        run_backtest(args)
    else:
        run_live(args)


if __name__ == "__main__":
    main()
