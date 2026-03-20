#!/usr/bin/env python3
"""
Quant Levels Agent — Streamlit UI
运行: streamlit run app.py
"""

import json
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from openai import OpenAI

from agent import (
    fetch_ohlcv, analyze, send_dingtalk,
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

# IBM Carbon 风格全局样式（白灰蓝）
st.markdown("""
<style>
/* 隐藏 Deploy 按钮 */
[data-testid='stToolbar'] {display: none;}

/* 全局背景 */
.stApp { background-color: #F9FAFB; }

/* 侧边栏 */
[data-testid='stSidebar'] {
    background-color: #FFFFFF;
    border-right: 1px solid #E0E0E0;
}
[data-testid='stSidebar'] * { color: #161616 !important; }
[data-testid='stSidebarContent'] .stButton > button {
    background-color: #0F62FE;
    color: #ffffff;
    border: none;
    border-radius: 2px;
    font-weight: 600;
    transition: background 0.2s;
}
[data-testid='stSidebarContent'] .stButton > button:hover {
    background-color: #0043CE;
}

/* 主区域文字 */
.stApp, .stMarkdown, p, span, label { color: #161616; }

/* 指标卡片背景 */
[data-testid='stMetric'] {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 2px;
    padding: 12px 16px !important;
}
[data-testid='stMetricLabel'] { color: #8D8D8D !important; font-size: 12px !important; }
[data-testid='stMetricValue'] {
    color: #161616 !important;
    font-size: 22px !important;
    font-variant-numeric: tabular-nums;
}
[data-testid='stMetricDelta'] { font-size: 12px !important; }

/* 分割线 */
hr { border-color: #E0E0E0 !important; }

/* expander */
[data-testid='stExpander'] {
    background-color: #FFFFFF;
    border: 1px solid #E0E0E0;
    border-radius: 2px;
}

/* 代码块 */
.stCode, [data-testid='stCode'] {
    background-color: #F4F4F4 !important;
    border: 1px solid #E0E0E0 !important;
    border-radius: 2px !important;
    color: #161616 !important;
}

/* info / error 提示 */
[data-testid='stAlert'] { border-radius: 2px; }

/* Token 弹框居中缩小 */
[data-testid='stDialog'] > div {
    max-width: 360px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    position: fixed !important;
    left: 0 !important;
    right: 0 !important;
}

/* 主要按钮 */
.stButton > button[kind='primary'] {
    background-color: #0F62FE !important;
    border: none !important;
    color: #fff !important;
    font-weight: 600;
    border-radius: 2px;
}
.stButton > button[kind='primary']:hover {
    background-color: #0043CE !important;
}

/* 价格 header 区域 */
.price-header {
    display: flex;
    align-items: baseline;
    gap: 16px;
    padding: 12px 0 8px 0;
    border-bottom: 1px solid #E0E0E0;
    margin-bottom: 12px;
}
.price-symbol {
    font-size: 20px;
    font-weight: 700;
    color: #161616;
    letter-spacing: 0.5px;
}
.price-value {
    font-size: 30px;
    font-weight: 700;
    color: #161616;
    font-variant-numeric: tabular-nums;
}
.price-up   { color: #24A148; font-size: 15px; font-weight: 600; }
.price-down { color: #DA1E28; font-size: 15px; font-weight: 600; }
.price-meta { color: #8D8D8D; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

PRESET_SYMBOLS = ["BTC", "ETH", "SOL", "AAPL", "NVDA", "TSLA", "600519", "00700"]
TIMEFRAMES     = ["15min", "1h", "4h", "日线"]
MODELS         = ["qwen-max", "qwen-plus", "qwen-turbo"]

QWEN_BASE_URL  = "https://dashscope.aliyuncs.com/compatible-mode/v1"


# ─────────────────────────────────────────────
# 千问 Token 弹框（首次启动时显示）
# ─────────────────────────────────────────────
@st.dialog("配置千问 API Token")
def qwen_token_dialog():
    st.markdown("""
<div style="text-align:center;padding:8px 0 16px 0;">
  <div style="font-size:32px;margin-bottom:8px;">🔑</div>
  <div style="font-size:13px;color:#525252;line-height:1.6;">
    输入阿里云百炼平台 API Key<br>
    <a href="https://bailian.console.aliyun.com/" target="_blank"
       style="color:#0F62FE;font-size:12px;">前往控制台获取 →</a>
  </div>
</div>
""", unsafe_allow_html=True)
    token = st.text_input(
        "DASHSCOPE_API_KEY",
        type="password",
        placeholder="sk-xxxxxxxxxxxx",
        label_visibility="collapsed",
    )
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("确认", type="primary", use_container_width=True):
        if not token.strip():
            st.warning("Token 不能为空")
        else:
            st.session_state["qwen_api_key"] = token.strip()
            st.rerun()


if "qwen_api_key" not in st.session_state:
    qwen_token_dialog()
    st.stop()


# ─────────────────────────────────────────────
# 侧边栏：参数输入
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🕯 Quant Levels Agent")
    st.divider()

    st.markdown("**📊 分析参数**")
    symbol_select = st.selectbox("标的", PRESET_SYMBOLS + ["自定义..."])
    if symbol_select == "自定义...":
        symbol = st.text_input("输入标的代码", placeholder="如 MSFT / 000001")
    else:
        symbol = symbol_select

    timeframe = st.radio("K 线周期", TIMEFRAMES, index=2, horizontal=True)
    limit     = st.slider("K 线数量", min_value=100, max_value=500, value=300, step=50)
    model     = st.selectbox("千问模型", MODELS)

    st.divider()
    run_btn = st.button("▶ 开始分析", type="primary", use_container_width=True)


# ─────────────────────────────────────────────
# K 线图（含 S/R 叠加）
# ─────────────────────────────────────────────
CHART_BG    = "#131722"
CHART_PANEL = "#1e222d"
CHART_GRID  = "#2a2e39"
COLOR_UP    = "#24A148"
COLOR_DOWN  = "#DA1E28"
COLOR_BLUE  = "#0F62FE"

def build_chart(df, ta_data: dict) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.02,
    )

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["open"], high=df["high"],
        low=df["low"],   close=df["close"],
        name="K线",
        increasing_line_color=COLOR_UP,
        decreasing_line_color=COLOR_DOWN,
        increasing_fillcolor=COLOR_UP,
        decreasing_fillcolor=COLOR_DOWN,
    ), row=1, col=1)

    colors = [COLOR_UP if c >= o else COLOR_DOWN
              for c, o in zip(df["close"], df["open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["volume"],
        marker_color=colors, name="成交量", opacity=0.5,
    ), row=2, col=1)

    current = ta_data["current_price"]
    x0, x1  = df.index[0], df.index[-1]

    fig.add_hline(y=current, line_color=COLOR_BLUE, line_width=1.5,
                  line_dash="dot", row=1, col=1)

    for lv in ta_data["resistance_levels"]:
        price = lv["price"]
        fig.add_shape(type="line", x0=x0, x1=x1, y0=price, y1=price,
                      line=dict(color=COLOR_DOWN, width=1, dash="dash"), row=1, col=1)
        fig.add_annotation(x=x1, y=price, text=f"  R {price:,.2f}",
                           showarrow=False, xanchor="left",
                           font=dict(color=COLOR_DOWN, size=11), row=1, col=1)

    for lv in ta_data["support_levels"]:
        price = lv["price"]
        fig.add_shape(type="line", x0=x0, x1=x1, y0=price, y1=price,
                      line=dict(color=COLOR_UP, width=1, dash="dash"), row=1, col=1)
        fig.add_annotation(x=x1, y=price, text=f"  S {price:,.2f}",
                           showarrow=False, xanchor="left",
                           font=dict(color=COLOR_UP, size=11), row=1, col=1)

    fig.update_layout(
        height=580,
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_PANEL,
        font=dict(color="#525252", family="Inter, sans-serif"),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        margin=dict(l=10, r=90, t=8, b=8),
    )
    fig.update_xaxes(gridcolor=CHART_GRID, zeroline=False, linecolor=CHART_GRID)
    fig.update_yaxes(gridcolor=CHART_GRID, zeroline=False, linecolor=CHART_GRID)
    return fig


# ─────────────────────────────────────────────
# 价格 Header
# ─────────────────────────────────────────────
def render_price_header(symbol: str, timeframe: str, ta_data: dict, kline_count: int, latest_ts):
    current = ta_data["current_price"]
    ind     = ta_data["indicators"]
    ma20    = ind.get("price_vs_ma20_pct")
    pct_str = f"{ma20:+.2f}% vs MA20" if ma20 is not None else ""
    color_cls = "price-up" if (ma20 or 0) >= 0 else "price-down"
    arrow     = "▲" if (ma20 or 0) >= 0 else "▼"

    st.markdown(f"""
<div class="price-header">
  <span class="price-symbol">{symbol}</span>
  <span class="price-meta">{timeframe}</span>
  <span class="price-value">{current:,.4g}</span>
  <span class="{color_cls}">{arrow} {pct_str}</span>
  <span class="price-meta" style="margin-left:auto">{kline_count} 根K线 &nbsp;·&nbsp; 最新 {latest_ts}</span>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 指标卡片
# ─────────────────────────────────────────────
def render_metrics(ta_data: dict):
    ind = ta_data["indicators"]
    rsi       = ind["rsi"]
    macd_hist = ind["macd_histogram"]
    vol_ratio = ind["volume_ratio_5_20"]
    ma20_pct  = ind.get("price_vs_ma20_pct")

    rsi_label  = "超买" if rsi > 70 else ("超卖" if rsi < 30 else "中性")
    rsi_delta  = f"{'⚠ ' if rsi > 70 or rsi < 30 else ''}{rsi_label}"
    macd_label = "多头" if macd_hist > 0 else "空头"
    vol_label  = "放量" if vol_ratio > 1.2 else ("缩量" if vol_ratio < 0.8 else "正常")
    ma_label   = f"{'↑' if ma20_pct and ma20_pct > 0 else '↓'} MA20" if ma20_pct else "N/A"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("RSI (14)",    f"{rsi}",             rsi_delta)
    c2.metric("MACD 柱",     f"{macd_hist:+.4f}",  macd_label)
    c3.metric("量比 5/20",   f"{vol_ratio}x",       vol_label)
    c4.metric("MA20 偏离",   f"{ma20_pct:+.2f}%" if ma20_pct else "N/A", ma_label)


# ─────────────────────────────────────────────
# 流式 LLM 输出
# ─────────────────────────────────────────────
def stream_report(ta_data: dict, model: str):
    client = OpenAI(
        api_key=st.session_state["qwen_api_key"],
        base_url=QWEN_BASE_URL,
    )
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
if not run_btn:
    st.markdown("""
<div style="display:flex;align-items:center;gap:12px;padding:48px 0 16px 0;">
  <span style="font-size:36px;">🕯</span>
  <span style="font-size:24px;font-weight:700;color:#161616;">Quant Levels Agent</span>
</div>
<p style="color:#8D8D8D;">← 在左侧设置参数后点击「开始分析」</p>
""", unsafe_allow_html=True)
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

# 2. TA 计算
ta_data = analyze(df, symbol, timeframe)

# 3. 价格 Header
render_price_header(symbol, timeframe, ta_data, len(df), df.index[-1])

# 4. K 线图
st.plotly_chart(build_chart(df, ta_data), use_container_width=True)

# 5. 指标卡片
render_metrics(ta_data)

st.divider()

# 6. LLM 流式报告
st.markdown("#### 🤖 千问分析报告")
report_placeholder = st.empty()
full_report = ""
try:
    with st.spinner("千问分析中..."):
        for chunk in stream_report(ta_data, model):
            full_report += chunk
            report_placeholder.markdown(full_report + "▌")
    report_placeholder.markdown(full_report)
except Exception as e:
    st.error(f"千问调用失败：{e}")
    st.stop()

st.divider()

# 7. 操作区
col_copy, col_push = st.columns([3, 2])

with col_copy:
    st.code(full_report, language=None)

with col_push:
    with st.expander("📨 推送到钉钉"):
        dingtalk_token = st.text_input(
            "钉钉机器人 Token",
            type="password",
            placeholder="粘贴 access_token",
        )
        if st.button("发送", type="primary", use_container_width=True, disabled=not full_report):
            if not dingtalk_token:
                st.warning("请先输入 Token")
            else:
                webhook = f"https://oapi.dingtalk.com/robot/send?access_token={dingtalk_token}"
                with st.spinner("推送中..."):
                    try:
                        send_dingtalk(webhook, full_report, symbol, timeframe)
                        st.success("推送成功！")
                    except Exception as e:
                        st.error(f"推送失败：{e}")

# 8. 原始 TA 数据（折叠）
with st.expander("🔬 查看原始 TA 数据"):
    st.json(ta_data)
