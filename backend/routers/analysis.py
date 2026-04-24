import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException
from openai import OpenAI

from agent import fetch_ohlcv, analyze
from backend.schemas import AnalysisRequest, AnalysisResponse, OHLCVBar

QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

router = APIRouter()


@router.post("/analysis", response_model=AnalysisResponse)
async def run_analysis(req: AnalysisRequest):
    try:
        df = fetch_ohlcv(req.symbol, req.timeframe, req.limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"数据获取失败：{e}")

    ta_data = analyze(df, req.symbol, req.timeframe)

    df_reset = df.reset_index()
    ts_col = df_reset.columns[0]
    ohlcv = [
        OHLCVBar(
            ts=str(row[ts_col]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row["volume"]),
        )
        for _, row in df_reset.iterrows()
    ]

    return AnalysisResponse(
        symbol=req.symbol,
        timeframe=req.timeframe,
        kline_count=len(df),
        latest_ts=str(df.index[-1]),
        ta_data=ta_data,
        ohlcv=ohlcv,
    )
