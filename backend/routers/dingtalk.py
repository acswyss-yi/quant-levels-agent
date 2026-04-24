import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from fastapi import APIRouter
from agent import send_dingtalk
from backend.schemas import DingTalkRequest, DingTalkResponse

router = APIRouter()


@router.post("/dingtalk", response_model=DingTalkResponse)
async def push_dingtalk(req: DingTalkRequest):
    webhook = f"https://oapi.dingtalk.com/robot/send?access_token={req.webhook_token}"
    try:
        send_dingtalk(webhook, req.report, req.symbol, req.timeframe, secret=req.secret)
        return DingTalkResponse(success=True)
    except Exception as e:
        return DingTalkResponse(success=False, error=str(e))
