#!/usr/bin/env python3
"""
Quant Levels Agent — Streamlit UI
运行: streamlit run app.py
"""

import os
import json
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from main import (
    fetch_ohlcv, analyze, get_qwen_client, send_dingtalk,
    SYSTEM_PROMPT,
)

# ─────────────────────────────────────────────
# 页面配置
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Quant Levels Agent",
    page_icon="🕯",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRESET_SYMBOLS = ["BTC", "ETH", "SOL", "AAPL", "NVDA", "TSLA", "600519", "00700"]
TIMEFRAMES     = ["15min", "1h", "4h", "日线"]
MODELS         = ["qwen-max", "qwen-plus", "qwen-turbo"]


# ─────────────────────────────────────────────
# 侧边栏：参数输入
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("🕯 Quant Levels Agent")
    st.divider()

    st.subheader("📊 分析参数")
    symbol_select = st.selectbox("标的", PRESET_SYMBOLS + ["自定义..."])
    if symbol_select == "自定义...":
        symbol = st.text_input("输入标的代码", placeholder="如 MSFT / 000001")
    else:
        symbol = symbol_select

    timeframe = st.radio("K 线周期", TIMEFRAMES, index=2, horizontal=True)
    limit     = st.slider("K 线数量", min_value=100, max_value=500, value=300, step=50)
    model     = st.selectbox("千问模型", MODELS)

    st.divider()
    st.subheader("📨 钉钉推送")
    enable_dingtalk = st.checkbox("启用推送")
    dingtalk_webhook, dingtalk_secret = None, None
    if enable_dingtalk:
        dingtalk_webhook = st.text_input(
            "Webhook URL",
            value=os.getenv("DINGTALK_WEBHOOK", ""),
            type="password",
            placeholder="https://oapi.dingtalk.com/robot/send?access_token=xxx",
        )
        dingtalk_secret = st.text_input(
            "加签密钥（可选）",
            value=os.getenv("DINGTALK_SECRET", ""),
            type="password",
            placeholder="SECxxx",
        )

    st.divider()
    run_btn = st.button("▶ 开始分析", type="primary", use_container_width=True)


# ─────────────────────────────────────────────
# K 线图（含 S/R 叠加）
# ─────────────────────────────────────────────
def build_chart(df, ta_data: dict) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.03,
    )

    # K 线
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["open"], high=df["high"],
        low=df["low"],   close=df["close"],
        name="K线",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
    ), row=1, col=1)

    # 成交量
    colors = ["#26a69a" if c >= o else "#ef5350"
              for c, o in zip(df["close"], df["open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["volume"],
        marker_color=colors, name="成交量", opacity=0.6,
    ), row=2, col=1)

    current = ta_data["current_price"]
    x0, x1  = df.index[0], df.index[-1]

    # 当前价线
    fig.add_hline(y=current, line_color="#FF8C00", line_width=1.5,
                  line_dash="dot", row=1, col=1)

    # 阻力位（红色虚线）
    for lv in ta_data["resistance_levels"]:
        price = lv["price"]
        fig.add_shape(type="line", x0=x0, x1=x1, y0=price, y1=price,
                      line=dict(color="#ef5350", width=1, dash="dash"), row=1, col=1)
        fig.add_annotation(x=x1, y=price, text=f"  阻力 {price:,.2f}",
                           showarrow=False, xanchor="left",
                           font=dict(color="#ef5350", size=11), row=1, col=1)

    # 支撑位（蓝色虚线）
    for lv in ta_data["support_levels"]:
        price = lv["price"]
        fig.add_shape(type="line", x0=x0, x1=x1, y0=price, y1=price,
                      line=dict(color="#42a5f5", width=1, dash="dash"), row=1, col=1)
        fig.add_annotation(x=x1, y=price, text=f"  支撑 {price:,.2f}",
                           showarrow=False, xanchor="left",
                           font=dict(color="#42a5f5", size=11), row=1, col=1)

    fig.update_layout(
        height=560,
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        font=dict(color="#fafafa"),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        margin=dict(l=10, r=80, t=10, b=10),
    )
    fig.update_xaxes(gridcolor="#1e2130", zeroline=False)
    fig.update_yaxes(gridcolor="#1e2130", zeroline=False)
    return fig


# ─────────────────────────────────────────────
# 指标卡片
# ─────────────────────────────────────────────
def render_metrics(ta_data: dict):
    ind = ta_data["indicators"]
    rsi = ind["rsi"]
    macd_hist = ind["macd_histogram"]
    vol_ratio = ind["volume_ratio_5_20"]
    ma20_pct  = ind.get("price_vs_ma20_pct")

    rsi_label  = "超买" if rsi > 70 else ("超卖" if rsi < 30 else "中性")
    rsi_delta  = f"{'⚠ ' if rsi > 70 or rsi < 30 else ''}{rsi_label}"
    macd_label = "多头" if macd_hist > 0 else "空头"
    vol_label  = "放量" if vol_ratio > 1.2 else ("缩量" if vol_ratio < 0.8 else "正常")
    ma_label   = f"{'↑' if ma20_pct and ma20_pct > 0 else '↓'} MA20" if ma20_pct else "N/A"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("RSI (14)",     f"{rsi}",           rsi_delta)
    c2.metric("MACD 柱",      f"{macd_hist:+.4f}", macd_label)
    c3.metric("量比 (5/20)",  f"{vol_ratio}x",     vol_label)
    c4.metric("MA20 偏离",    f"{ma20_pct:+.2f}%" if ma20_pct else "N/A", ma_label)


# ─────────────────────────────────────────────
# 流式 LLM 输出
# ─────────────────────────────────────────────
def stream_report(client, ta_data: dict, model: str):
    user_msg = (
        f"请分析以下市场数据：\n\n"
        f"```json\n{json.dumps(ta_data, ensure_ascii=False, indent=2)}\n```"
    )
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        temperature=0.3,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


# ─────────────────────────────────────────────
# 主区域
# ─────────────────────────────────────────────
st.markdown(f"## {symbol or '—'} · {timeframe}" if symbol else "## Quant Levels Agent")

if not run_btn:
    st.info("← 在左侧设置参数后点击「开始分析」")
    st.stop()

if not symbol:
    st.error("请输入标的代码")
    st.stop()

# 1. 获取数据
with st.spinner(f"获取 {symbol} {timeframe} 数据..."):
    try:
        df = fetch_ohlcv(symbol, timeframe, limit)
    except Exception as e:
        st.error(f"数据获取失败：{e}")
        st.stop()

st.caption(f"共 {len(df)} 根 K 线 · 最新：{df.index[-1]}")

# 2. TA 计算
ta_data = analyze(df, symbol, timeframe)

# 3. K 线图（立即渲染）
st.plotly_chart(build_chart(df, ta_data), use_container_width=True)

# 4. 指标卡片
render_metrics(ta_data)

st.divider()

# 5. LLM 流式报告
st.subheader("🤖 千问分析报告")
try:
    client = get_qwen_client()
except EnvironmentError as e:
    st.error(str(e))
    st.stop()

report_placeholder = st.empty()
full_report = ""
with st.spinner("千问分析中..."):
    for chunk in stream_report(client, ta_data, model):
        full_report += chunk
        report_placeholder.markdown(full_report + "▌")
report_placeholder.markdown(full_report)

# 6. 操作按钮
st.divider()
col_copy, col_push = st.columns([1, 1])

with col_copy:
    st.code(full_report, language=None)

with col_push:
    if enable_dingtalk and dingtalk_webhook:
        if st.button("📨 推送到钉钉", use_container_width=True):
            with st.spinner("推送中..."):
                try:
                    send_dingtalk(dingtalk_webhook, full_report, symbol, timeframe,
                                  dingtalk_secret or None)
                    st.success("推送成功！")
                except Exception as e:
                    st.error(f"推送失败：{e}")
    else:
        st.info("在侧边栏启用钉钉推送后可点击发送")

# 7. 原始 TA 数据（折叠）
with st.expander("🔬 查看原始 TA 数据"):
    st.json(ta_data)
