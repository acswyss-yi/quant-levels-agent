import sys
import pathlib

# 确保项目根目录在 sys.path，使 agent.py 可被 import
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routers import analysis, agent, dingtalk

app = FastAPI(title="Quant Levels Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router, prefix="/api")
app.include_router(agent.router,    prefix="/api")
app.include_router(dingtalk.router, prefix="/api")

# 生产环境：伺服前端静态文件
_dist = pathlib.Path(__file__).parent.parent / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="static")
