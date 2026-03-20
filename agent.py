#!/usr/bin/env python3
"""
Quant Levels Agent
支撑阻力位智能分析 Agent，基于技术分析 + 千问 LLM

用法:
  python main.py BTC 4h
  python main.py AAPL 日线 --model qwen-plus
  python main.py 600519 日线 --verbose
"""

import os
import json
import time
import hmac
import hashlib
import base64
import argparse
import urllib.parse
import urllib.request
import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
from openai import OpenAI


# ─────────────────────────────────────────────
# 千问客户端（兼容 OpenAI SDK）
# ─────────────────────────────────────────────
def get_qwen_client() -> OpenAI:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise EnvironmentError("请设置环境变量 DASHSCOPE_API_KEY")
    return OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )


# ─────────────────────────────────────────────
# 数据获取层
# ─────────────────────────────────────────────
CRYPTO_SYMBOLS = {"BTC", "ETH", "SOL", "BNB", "XRP", "DOGE"}


def fetch_ohlcv(symbol: str, timeframe: str, limit: int = 300) -> pd.DataFrame:
    """
    统一数据入口，根据标的自动路由：
      - 加密货币  → ccxt (Binance)
      - A股/港股  → akshare（纯数字 symbol 或港股 .HK 后缀）
      - 美股      → yfinance
    """
    sym = symbol.upper()
    if sym in CRYPTO_SYMBOLS or sym.endswith("USDT"):
        pair = sym if sym.endswith("USDT") else sym + "/USDT"
        tf_map = {"15min": "15m", "1h": "1h", "4h": "4h", "日线": "1d"}
        return _fetch_crypto(pair, tf_map[timeframe], limit)
    elif symbol.isdigit():
        return _fetch_akshare(symbol, timeframe, limit)
    else:
        tf_map = {"15min": "15m", "1h": "1h", "4h": "1h", "日线": "1d"}
        period = {"15min": "60d", "1h": "2y", "4h": "2y", "日线": "5y"}
        return _fetch_yfinance(sym, tf_map[timeframe], period[timeframe], limit)


def _fetch_crypto(pair: str, tf: str, limit: int) -> pd.DataFrame:
    try:
        import ccxt
    except ImportError:
        raise ImportError("pip install ccxt")
    # OKX 对国内 IP 可访问；Binance 在大陆受限(451)
    exchanges = [
        ccxt.okx({"enableRateLimit": True}),
        ccxt.gateio({"enableRateLimit": True}),
        ccxt.bybit({"enableRateLimit": True}),
    ]
    last_err = None
    for ex in exchanges:
        try:
            raw = ex.fetch_ohlcv(pair, tf, limit=limit)
            df = pd.DataFrame(raw, columns=["ts", "open", "high", "low", "close", "volume"])
            df["ts"] = pd.to_datetime(df["ts"], unit="ms")
            return df.set_index("ts")
        except Exception as e:
            last_err = e
            continue
    raise ConnectionError(f"所有交易所均无法访问，最后错误：{last_err}")


def _fetch_yfinance(sym: str, interval: str, period: str, limit: int) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError:
        raise ImportError("pip install yfinance")
    df = yf.Ticker(sym).history(period=period, interval=interval)
    df.index.name = "ts"
    df.columns = [c.lower() for c in df.columns]
    return df[["open", "high", "low", "close", "volume"]].tail(limit)


def _fetch_akshare(sym: str, timeframe: str, limit: int) -> pd.DataFrame:
    try:
        import akshare as ak
    except ImportError:
        raise ImportError("pip install akshare")
    period_map = {"15min": "15", "1h": "60", "4h": "240", "日线": "daily"}
    period = period_map[timeframe]
    if period == "daily":
        df = ak.stock_zh_a_hist(symbol=sym, period="daily", adjust="qfq").tail(limit)
        df = df.rename(columns={"日期": "ts", "开盘": "open", "最高": "high",
                                 "最低": "low", "收盘": "close", "成交量": "volume"})
    else:
        df = ak.stock_zh_a_minute(symbol=sym, period=period, adjust="qfq").tail(limit)
        df = df.rename(columns={"时间": "ts", "开盘": "open", "最高": "high",
                                 "最低": "low", "收盘": "close", "成交量": "volume"})
    df["ts"] = pd.to_datetime(df["ts"])
    return df.set_index("ts")[["open", "high", "low", "close", "volume"]]


# ─────────────────────────────────────────────
# 技术分析层
# ─────────────────────────────────────────────
def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def compute_rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff().dropna()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return round(float((100 - 100 / (1 + rs)).iloc[-1]), 1)


def compute_macd(close: pd.Series) -> tuple:
    macd = _ema(close, 12) - _ema(close, 26)
    signal = _ema(macd, 9)
    hist = macd - signal
    return float(macd.iloc[-1]), float(signal.iloc[-1]), float(hist.iloc[-1])


def find_swing_levels(df: pd.DataFrame, order: int = 5) -> dict:
    """局部极值检测：swing high / swing low"""
    hi_idx = argrelextrema(df["high"].values, np.greater_equal, order=order)[0]
    lo_idx = argrelextrema(df["low"].values,  np.less_equal,    order=order)[0]
    return {
        "resistance_raw": [float(df["high"].iloc[i]) for i in hi_idx],
        "support_raw":    [float(df["low"].iloc[i])  for i in lo_idx],
    }


def cluster_levels(levels: list, current: float, tol: float = 0.005) -> list:
    """将 tol（0.5%）以内的价位聚合，返回 [(价位, 触碰次数), ...]"""
    if not levels:
        return []
    grouped, group = [], [sorted(levels)[0]]
    for lv in sorted(levels)[1:]:
        if (lv - group[-1]) / current < tol:
            group.append(lv)
        else:
            grouped.append(group)
            group = [lv]
    grouped.append(group)
    result = [(round(float(np.mean(g)), 2), len(g)) for g in grouped]
    return sorted(result, key=lambda x: -x[1])


def fibonacci_levels(df: pd.DataFrame) -> dict:
    """近 N 根 K 线的 Fibonacci 回撤位"""
    high, low = float(df["high"].max()), float(df["low"].min())
    diff = high - low
    fibs = {f"fib_{int(r*1000)}": round(high - diff * r, 2)
            for r in [0.236, 0.382, 0.5, 0.618, 0.786]}
    fibs["fib_high"] = round(high, 2)
    fibs["fib_low"]  = round(low, 2)
    return fibs


def volume_clusters(df: pd.DataFrame, bins: int = 20) -> list:
    """简版 Volume Profile：返回成交量最大的价格区间"""
    edges = np.linspace(df["low"].min(), df["high"].max(), bins + 1)
    result = []
    for i in range(bins):
        mask = (df["close"] >= edges[i]) & (df["close"] < edges[i + 1])
        result.append((
            round(float((edges[i] + edges[i + 1]) / 2), 2),
            float(df.loc[mask, "volume"].sum())
        ))
    return sorted(result, key=lambda x: -x[1])[:5]


def analyze(df: pd.DataFrame, symbol: str, timeframe: str) -> dict:
    """整合全部 TA，返回结构化数据供 LLM 消费"""
    close   = df["close"]
    current = float(close.iloc[-1])

    # 指标
    rsi                  = compute_rsi(close)
    macd, sig, hist_val  = compute_macd(close)
    mas = {f"ma{p}": round(float(_ema(close, p).iloc[-1]), 2)
           for p in [20, 50, 200] if len(close) >= p}
    vol = df["volume"]
    vol_ratio = round(float(vol.iloc[-5:].mean() / vol.iloc[-20:].mean()), 2) \
        if len(vol) >= 20 else 1.0

    # 支撑阻力候选（swing + fib + MA）
    order   = max(3, len(df) // 30)
    swings  = find_swing_levels(df, order)
    fibs    = fibonacci_levels(df)
    fib_vals = list(fibs.values())

    r_cands = [v for v in swings["resistance_raw"] + fib_vals + list(mas.values()) if v > current]
    s_cands = [v for v in swings["support_raw"]    + fib_vals + list(mas.values()) if v < current]

    r_clustered = cluster_levels(r_cands, current)[:4]
    s_clustered = cluster_levels(s_cands, current)[:4]

    return {
        "symbol":        symbol,
        "timeframe":     timeframe,
        "current_price": current,
        "as_of":         str(df.index[-1]),
        "indicators": {
            "rsi":               rsi,
            "macd":              round(macd, 4),
            "macd_signal":       round(sig, 4),
            "macd_histogram":    round(hist_val, 4),
            "volume_ratio_5_20": vol_ratio,
            "moving_averages":   mas,
            "price_vs_ma20_pct": round((current / mas["ma20"] - 1) * 100, 2) if "ma20" in mas else None,
            "price_vs_ma50_pct": round((current / mas["ma50"] - 1) * 100, 2) if "ma50" in mas else None,
        },
        "resistance_levels": [{"price": p, "touches": t} for p, t in r_clustered],
        "support_levels":    [{"price": p, "touches": t} for p, t in s_clustered],
        "fibonacci":         fibs,
        "volume_clusters":   [{"price": p, "volume": round(v)} for p, v in volume_clusters(df)],
    }


# ─────────────────────────────────────────────
# LLM 综合层（千问）
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """你是一名专业的量化交易分析师，擅长多维度技术分析。
你会收到一份结构化市场数据，包含：当前价格、支撑/阻力候选（含触碰次数）、Fibonacci 回撤位、成交量聚集区、RSI/MACD/均线指标。

请综合以上信息，生成简洁专业的分析报告，严格使用以下格式：

【{symbol} {timeframe} 关键价位分析】

当前价格：xxx

📌 关键支撑位：
- xxxxx（来源：swing low 3次 / MA50 / Fib 0.618 等，说明为何重要）
- xxxxx（来源：...）

🚧 关键阻力位：
- xxxxx（来源：...）
- xxxxx（来源：...）

📊 市场情绪：
[综合 RSI / MACD / 量比 / 均线位置给出方向判断，2-3 句]

🎯 综合判断：偏突破 / 偏震荡 / 偏回踩 / 偏反转（选其一）
[1-2 句具体描述，如"若放量突破 xxx 则上看 xxx；若跌破 xxx 则可能回踩 xxx"]

⚠️ 风险提示：[1-2 句]

置信度：xx%

规则：
1. 只选最重要的 2-3 个支撑位和 2-3 个阻力位
2. 置信度 60-90%，信号越一致越高，矛盾越多越低，并在最后加一句说明依据
3. 严格基于给出的数据，不编造
4. 语言简洁，去掉废话"""


def llm_analyze(client: OpenAI, ta_data: dict, model: str = "qwen-max") -> str:
    user_msg = (
        f"请分析以下市场数据：\n\n"
        f"```json\n{json.dumps(ta_data, ensure_ascii=False, indent=2)}\n```"
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content


# ─────────────────────────────────────────────
# 钉钉推送层
# ─────────────────────────────────────────────
def _dingtalk_sign(secret: str):
    """生成钉钉加签：timestamp + sign"""
    ts = str(round(time.time() * 1000))
    msg = f"{ts}\n{secret}"
    digest = hmac.new(secret.encode(), msg.encode(), digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(digest))
    return ts, sign


def _report_to_markdown(report: str, symbol: str, timeframe: str) -> str:
    """将 LLM 报告转为钉钉 Markdown（钉钉不支持部分 emoji，保留即可）"""
    # 钉钉 markdown title 不超过 20 字
    title = f"{symbol} {timeframe} 价位分析"
    # 钉钉 markdown text 第一行必须是 # 标题
    text = f"# {title}\n\n{report}"
    return title, text


def send_dingtalk(webhook: str, report: str, symbol: str, timeframe: str,
                  secret: str | None = None) -> None:
    """
    推送分析报告到钉钉群机器人。

    webhook: 钉钉机器人 Webhook URL
    secret:  加签密钥（在钉钉机器人「安全设置」中开启「加签」后获取）
    """
    title, text = _report_to_markdown(report, symbol, timeframe)

    url = webhook
    if secret:
        ts, sign = _dingtalk_sign(secret)
        url = f"{webhook}&timestamp={ts}&sign={sign}"

    payload = json.dumps({
        "msgtype": "markdown",
        "markdown": {"title": title, "text": text},
    }, ensure_ascii=False).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
        if result.get("errcode") != 0:
            raise RuntimeError(f"钉钉推送失败：{result}")
    print(f"📨 已推送到钉钉：{title}")


# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────
def run(symbol: str, timeframe: str, limit: int = 300,
        model: str = "qwen-max", verbose: bool = False,
        dingtalk_webhook: str = None, dingtalk_secret: str = None) -> str:
    print(f"\n⏳ 获取 {symbol} {timeframe} 数据中...")
    df = fetch_ohlcv(symbol, timeframe, limit)
    print(f"✅ {len(df)} 根 K 线，最新：{df.index[-1]}")

    print("🔬 计算技术指标...")
    ta_data = analyze(df, symbol, timeframe)

    if verbose:
        print("\n── 原始 TA 数据 ──")
        print(json.dumps(ta_data, ensure_ascii=False, indent=2))

    print("🤖 千问综合分析中...\n")
    client = get_qwen_client()
    report = llm_analyze(client, ta_data, model)

    print("=" * 60)
    print(report)
    print("=" * 60)

    # 钉钉推送（可选）
    webhook = dingtalk_webhook or os.getenv("DINGTALK_WEBHOOK")
    secret  = dingtalk_secret  or os.getenv("DINGTALK_SECRET")
    if webhook:
        send_dingtalk(webhook, report, symbol, timeframe, secret)

    return report


def main():
    parser = argparse.ArgumentParser(description="Quant Levels Agent — 支撑阻力位分析")
    parser.add_argument("symbol",    help="标的代码，如 BTC / ETH / AAPL / 600519")
    parser.add_argument("timeframe", choices=["15min", "1h", "4h", "日线"], help="K 线周期")
    parser.add_argument("--limit",   type=int, default=300, help="K 线数量（默认 300）")
    parser.add_argument("--model",   default="qwen-max",
                        help="千问模型：qwen-max / qwen-plus / qwen-turbo")
    parser.add_argument("--verbose", action="store_true", help="打印原始 TA 数据")
    parser.add_argument("--dingtalk-webhook",
                        help="钉钉机器人 Webhook URL（也可用环境变量 DINGTALK_WEBHOOK）")
    parser.add_argument("--dingtalk-secret",
                        help="钉钉加签密钥（也可用环境变量 DINGTALK_SECRET）")
    args = parser.parse_args()
    run(args.symbol, args.timeframe, args.limit, args.model, args.verbose,
        args.dingtalk_webhook, args.dingtalk_secret)


if __name__ == "__main__":
    main()
