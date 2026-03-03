"""
Reporting Module
================
Generates visual charts, signal reports, and export files.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# ─── Color scheme matching handbook ───────────────────────────────────
COLORS = {
    "bg": "#0F1923",
    "card_bg": "#1B2838",
    "blue": "#2196F3",
    "teal": "#00BCD4",
    "green": "#4CAF50",
    "orange": "#FF9800",
    "red": "#F44336",
    "purple": "#9C27B0",
    "gold": "#FFD700",
    "text": "#E0E6ED",
    "subtle": "#8899AA",
    "grid": "#2A3A4A",
    "buy": "#4CAF50",
    "sell": "#F44336",
}

STRATEGY_COLORS = {
    "Breakout_Retest": COLORS["blue"],
    "EMA_Trend_Pullback": COLORS["teal"],
    "Mean_Reversion": COLORS["orange"],
}


def setup_dark_style():
    """Configure matplotlib for dark theme matching handbook."""
    plt.rcParams.update({
        "figure.facecolor": COLORS["bg"],
        "axes.facecolor": COLORS["card_bg"],
        "axes.edgecolor": COLORS["grid"],
        "axes.labelcolor": COLORS["text"],
        "text.color": COLORS["text"],
        "xtick.color": COLORS["subtle"],
        "ytick.color": COLORS["subtle"],
        "grid.color": COLORS["grid"],
        "grid.alpha": 0.3,
        "font.family": "sans-serif",
        "font.size": 10,
    })


def plot_signals_on_chart(
    df: pd.DataFrame,
    signals: list,
    symbol: str,
    title: str = None,
    save_path: str = None,
):
    """
    Plot price chart with buy/sell signal markers.
    """
    setup_dark_style()

    fig, axes = plt.subplots(3, 1, figsize=(16, 12), height_ratios=[3, 1, 1],
                             gridspec_kw={"hspace": 0.08})

    # ─── Price Chart ──────────────────────────────────────────
    ax1 = axes[0]
    ax1.plot(df.index, df["close"], color=COLORS["text"], linewidth=1, alpha=0.9, label="Price")

    if "ema_fast" in df.columns:
        ax1.plot(df.index, df["ema_fast"], color=COLORS["blue"], linewidth=1,
                 alpha=0.7, linestyle="--", label="50 EMA")
    if "ema_slow" in df.columns:
        ax1.plot(df.index, df["ema_slow"], color=COLORS["orange"], linewidth=1,
                 alpha=0.7, linestyle="--", label="200 EMA")

    # Plot signals
    buy_signals = [s for s in signals if s.signal.value == "BUY"]
    sell_signals = [s for s in signals if s.signal.value == "SELL"]

    if buy_signals:
        buy_times = [s.timestamp for s in buy_signals]
        buy_prices = [s.entry_price for s in buy_signals]
        ax1.scatter(buy_times, buy_prices, marker="^", color=COLORS["buy"],
                    s=120, zorder=5, label=f"BUY ({len(buy_signals)})", edgecolors="white", linewidth=0.5)

    if sell_signals:
        sell_times = [s.timestamp for s in sell_signals]
        sell_prices = [s.entry_price for s in sell_signals]
        ax1.scatter(sell_times, sell_prices, marker="v", color=COLORS["sell"],
                    s=120, zorder=5, label=f"SELL ({len(sell_signals)})", edgecolors="white", linewidth=0.5)

    ax1.set_title(title or f"{symbol} — Signal Chart", fontsize=14, fontweight="bold",
                  color=COLORS["gold"], pad=12)
    ax1.legend(loc="upper left", fontsize=8, framealpha=0.3)
    ax1.grid(True, alpha=0.2)
    ax1.set_ylabel("Price", fontsize=10)

    # ─── Volume Chart ─────────────────────────────────────────
    ax2 = axes[1]
    colors_vol = [COLORS["buy"] if c > o else COLORS["sell"]
                  for c, o in zip(df["close"], df["open"])]
    ax2.bar(df.index, df["volume"], color=colors_vol, alpha=0.5, width=0.8)
    if "volume_sma" in df.columns:
        ax2.plot(df.index, df["volume_sma"], color=COLORS["gold"], linewidth=1, alpha=0.7)
    ax2.set_ylabel("Volume", fontsize=9)
    ax2.grid(True, alpha=0.2)

    # ─── ATR Chart ────────────────────────────────────────────
    ax3 = axes[2]
    if "atr" in df.columns:
        ax3.plot(df.index, df["atr"], color=COLORS["purple"], linewidth=1)
        ax3.fill_between(df.index, 0, df["atr"], color=COLORS["purple"], alpha=0.15)
    ax3.set_ylabel("ATR", fontsize=9)
    ax3.grid(True, alpha=0.2)

    # Format x-axis
    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax.xaxis.set_major_locator(mdates.MonthLocator())

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=COLORS["bg"])
        logger.info(f"Chart saved: {save_path}")

    plt.close()
    return save_path


def plot_equity_curve(trade_log: pd.DataFrame, save_path: str = None):
    """Plot equity curve from backtest results."""
    setup_dark_style()

    if trade_log.empty:
        return None

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), height_ratios=[2, 1],
                             gridspec_kw={"hspace": 0.08})

    # ─── Equity Curve ─────────────────────────────────────────
    ax1 = axes[0]
    ax1.plot(range(len(trade_log)), trade_log["balance"],
             color=COLORS["gold"], linewidth=2)
    ax1.fill_between(range(len(trade_log)),
                     trade_log["balance"].iloc[0],
                     trade_log["balance"],
                     where=trade_log["balance"] >= trade_log["balance"].iloc[0],
                     color=COLORS["green"], alpha=0.15)
    ax1.fill_between(range(len(trade_log)),
                     trade_log["balance"].iloc[0],
                     trade_log["balance"],
                     where=trade_log["balance"] < trade_log["balance"].iloc[0],
                     color=COLORS["red"], alpha=0.15)

    ax1.axhline(y=trade_log["balance"].iloc[0], color=COLORS["subtle"],
                linestyle="--", alpha=0.5, label="Starting Balance")
    ax1.set_title("Equity Curve — Backtest Simulation", fontsize=14,
                  fontweight="bold", color=COLORS["gold"], pad=12)
    ax1.set_ylabel("Account Balance ($)", fontsize=10)
    ax1.legend(fontsize=9, framealpha=0.3)
    ax1.grid(True, alpha=0.2)

    # ─── Drawdown Chart ───────────────────────────────────────
    ax2 = axes[1]
    ax2.fill_between(range(len(trade_log)), 0, -trade_log["drawdown_pct"],
                     color=COLORS["red"], alpha=0.4)
    ax2.plot(range(len(trade_log)), -trade_log["drawdown_pct"],
             color=COLORS["red"], linewidth=1)
    ax2.axhline(y=-5, color=COLORS["orange"], linestyle="--", alpha=0.6, label="5% DD Warning")
    ax2.axhline(y=-8, color=COLORS["red"], linestyle="--", alpha=0.6, label="8% DD Max")
    ax2.set_ylabel("Drawdown (%)", fontsize=10)
    ax2.set_xlabel("Trade Number", fontsize=10)
    ax2.legend(fontsize=8, framealpha=0.3)
    ax2.grid(True, alpha=0.2)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=COLORS["bg"])
        logger.info(f"Equity curve saved: {save_path}")

    plt.close()
    return save_path


def plot_strategy_breakdown(signals_summary: pd.DataFrame, save_path: str = None):
    """Plot signal distribution by strategy and asset."""
    setup_dark_style()

    if signals_summary.empty:
        return None

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # ─── By Strategy ──────────────────────────────────────────
    ax1 = axes[0]
    by_strat = signals_summary.groupby("strategy")["count"].sum()
    colors = [STRATEGY_COLORS.get(s, COLORS["blue"]) for s in by_strat.index]
    bars1 = ax1.barh(by_strat.index, by_strat.values, color=colors, height=0.5, edgecolor="white", linewidth=0.5)
    ax1.set_title("Signals by Strategy", fontsize=12, fontweight="bold", color=COLORS["gold"])
    ax1.set_xlabel("Signal Count")
    for bar, val in zip(bars1, by_strat.values):
        ax1.text(val + 0.5, bar.get_y() + bar.get_height()/2, str(val),
                 va="center", fontsize=10, color=COLORS["text"])

    # ─── By Asset ─────────────────────────────────────────────
    ax2 = axes[1]
    by_asset = signals_summary.groupby("symbol")["count"].sum()
    asset_colors = [COLORS["blue"], COLORS["orange"], COLORS["teal"], COLORS["green"]]
    bars2 = ax2.barh(by_asset.index, by_asset.values,
                     color=asset_colors[:len(by_asset)], height=0.5,
                     edgecolor="white", linewidth=0.5)
    ax2.set_title("Signals by Asset", fontsize=12, fontweight="bold", color=COLORS["gold"])
    ax2.set_xlabel("Signal Count")
    for bar, val in zip(bars2, by_asset.values):
        ax2.text(val + 0.5, bar.get_y() + bar.get_height()/2, str(val),
                 va="center", fontsize=10, color=COLORS["text"])

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=COLORS["bg"])
        logger.info(f"Breakdown chart saved: {save_path}")

    plt.close()
    return save_path


def generate_signal_report(
    results: dict,
    engine,
    output_dir: str = "output",
) -> dict:
    """
    Generate complete visual report with all charts and CSV exports.

    Returns:
        Dict of file paths generated
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    files = {}

    # ─── Signal Charts per Asset ──────────────────────────────
    for symbol in engine.data:
        asset_signals = [s for s in engine.approved_signals if s.symbol == symbol]
        if engine.data[symbol] is not None and len(engine.data[symbol]) > 0:
            chart_path = str(output / f"chart_{symbol}.png")
            plot_signals_on_chart(
                engine.data[symbol],
                asset_signals,
                symbol,
                save_path=chart_path,
            )
            files[f"chart_{symbol}"] = chart_path

    # ─── Equity Curve ─────────────────────────────────────────
    trade_log = results.get("trade_log")
    if trade_log is not None and not trade_log.empty:
        eq_path = str(output / "equity_curve.png")
        plot_equity_curve(trade_log, save_path=eq_path)
        files["equity_curve"] = eq_path

    # ─── Strategy Breakdown ───────────────────────────────────
    summary = engine.get_signals_summary()
    if not summary.empty:
        bd_path = str(output / "strategy_breakdown.png")
        plot_strategy_breakdown(summary, save_path=bd_path)
        files["breakdown"] = bd_path

    # ─── CSV Exports ──────────────────────────────────────────
    # All signals
    all_sig_df = engine.get_latest_signals(n=1000)
    if not all_sig_df.empty:
        csv_path = str(output / "all_signals.csv")
        all_sig_df.to_csv(csv_path, index=False)
        files["signals_csv"] = csv_path

    # Trade log
    if trade_log is not None and not trade_log.empty:
        log_path = str(output / "trade_log.csv")
        trade_log.to_csv(log_path, index=False)
        files["trade_log_csv"] = log_path

    # Per-asset signals
    for symbol in engine.data:
        asset_df = engine.get_signals_by_asset(symbol)
        if not asset_df.empty:
            csv_path = str(output / f"signals_{symbol}.csv")
            asset_df.to_csv(csv_path, index=False)
            files[f"signals_{symbol}_csv"] = csv_path

    return files
