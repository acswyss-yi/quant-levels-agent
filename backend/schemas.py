from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


# ── 请求模型 ──────────────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    symbol: str
    timeframe: str
    limit: int = 300
    api_key: str


class AgentStreamRequest(BaseModel):
    symbol: str
    timeframe: str
    limit: int = 300
    model: str = "qwen-max"
    api_key: str


class DingTalkRequest(BaseModel):
    webhook_token: str
    report: str
    symbol: str
    timeframe: str
    secret: Optional[str] = None


# ── 响应子模型 ────────────────────────────────────────────────────────────────

class OHLCVBar(BaseModel):
    ts: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class AnalysisResponse(BaseModel):
    symbol: str
    timeframe: str
    kline_count: int
    latest_ts: str
    ta_data: dict
    ohlcv: list[OHLCVBar]


class DingTalkResponse(BaseModel):
    success: bool
    error: Optional[str] = None
