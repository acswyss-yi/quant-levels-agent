import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

import json
import queue
import asyncio
import functools

from fastapi import APIRouter
from openai import OpenAI
from sse_starlette.sse import EventSourceResponse

from agent import run_agent
from backend.schemas import AgentStreamRequest

QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

router = APIRouter()


@router.post("/agent/stream")
async def agent_stream(req: AgentStreamRequest):
    q: queue.Queue = queue.Queue()

    def on_tool_call(sym: str, tf: str):
        q.put({"symbol": sym, "timeframe": tf})

    async def event_generator():
        client = OpenAI(api_key=req.api_key, base_url=QWEN_BASE_URL)
        loop = asyncio.get_running_loop()   # 3.10+ 正确用法

        future = loop.run_in_executor(
            None,
            functools.partial(
                run_agent,
                req.symbol,
                req.timeframe,
                req.limit,
                req.model,
                client,
                on_tool_call=on_tool_call,
            ),
        )

        step = 0
        ping_counter = 0
        while not future.done():
            try:
                item = q.get_nowait()
                step += 1
                yield {
                    "event": "tool_call",
                    "data": json.dumps({"step": step, **item}, ensure_ascii=False),
                }
            except queue.Empty:
                await asyncio.sleep(0.1)
                ping_counter += 1
                # 每 5 秒发一次心跳，防止 LLM 等待期间连接被断开
                if ping_counter >= 50:
                    ping_counter = 0
                    yield {"event": "ping", "data": "{}"}

        # 排空队列中残余的 tool_call 事件
        while not q.empty():
            item = q.get_nowait()
            step += 1
            yield {
                "event": "tool_call",
                "data": json.dumps({"step": step, **item}, ensure_ascii=False),
            }

        try:
            report = await future
            yield {
                "event": "report",
                "data": json.dumps({"content": report}, ensure_ascii=False),
            }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)}, ensure_ascii=False),
            }

        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(event_generator())
