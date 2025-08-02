#!/usr/bin/env python3
"""
本地mManager服务器 - 用于开发调试
"""

import asyncio
import os
import sys
import subprocess
import json
import psutil
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 配置
MMANAGER_PORT = int(os.getenv("MMANAGER_PORT", "8001"))
MMANAGER_API_KEY = os.getenv(
    "MMANAGER_API_KEY", "mmanager-secure-key-12345-change-in-production"
)
MMANAGER_SERVER_TYPE = os.getenv("MMANAGER_SERVER_TYPE", "cpu")
MAX_CONTAINERS = int(os.getenv("MMANAGER_MAX_CONTAINERS", "10"))

app = FastAPI(title="mManager Local Server", version="1.0.0")

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模拟容器存储
containers = {}
container_counter = 0


class ContainerConfig(BaseModel):
    image: str
    name: Optional[str] = None
    ports: Optional[Dict] = {}
    environment: Optional[Dict] = {}
    volumes: Optional[Dict] = {}
    command: Optional[str] = None


class ContainerInfo(BaseModel):
    id: str
    name: str
    image: str
    status: str
    created_at: str
    ports: Dict


def check_api_key(request: Request):
    """检查API密钥"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid authorization header"
        )

    token = auth_header[7:]  # Remove "Bearer "
    if token != MMANAGER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/health")
async def health_check():
    """健康检查"""
    # 获取系统资源信息
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "status": "healthy",
        "server_type": MMANAGER_SERVER_TYPE,
        "timestamp": datetime.utcnow().isoformat(),
        "containers": {
            "running": len(
                [c for c in containers.values() if c["status"] == "running"]
            ),
            "total": len(containers),
            "max_allowed": MAX_CONTAINERS,
        },
        "resources": {
            "cpu_cores": psutil.cpu_count(),
            "cpu_usage_percent": cpu_percent,
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "memory_usage_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_available_gb": round(disk.free / (1024**3), 2),
        },
        "load_percentage": round((cpu_percent + memory.percent) / 2, 2),
        "capabilities": {
            "gpu_support": False,  # 本地调试暂不支持GPU
            "max_memory_gb": round(memory.total / (1024**3), 2),
            "docker_support": True,
        },
    }


@app.post("/containers/")
async def create_container(config: ContainerConfig, request: Request):
    """创建容器"""
    check_api_key(request)

    global container_counter
    container_counter += 1

    # 生成容器ID和名称
    container_id = f"local_container_{container_counter}"
    container_name = config.name or f"mmanager_local_{container_counter}"

    # 模拟Docker run命令
    print(f"模拟创建容器: {config.image}")
    print(f"端口映射: {config.ports}")
    print(f"环境变量: {config.environment}")

    # 创建容器记录
    container_info = {
        "id": container_id,
        "name": container_name,
        "image": config.image,
        "status": "created",
        "created_at": datetime.utcnow().isoformat(),
        "ports": config.ports or {},
        "environment": config.environment or {},
        "command": config.command,
    }

    containers[container_id] = container_info

    return {
        "container_id": container_id,
        "name": container_name,
        "status": "created",
        "message": f"容器 {container_name} 创建成功",
    }


@app.post("/containers/{container_id}/start")
async def start_container(container_id: str, request: Request):
    """启动容器"""
    check_api_key(request)

    if container_id not in containers:
        raise HTTPException(status_code=404, detail="Container not found")

    container = containers[container_id]
    print(f"模拟启动容器: {container_id} ({container['name']})")

    # 更新状态
    container["status"] = "running"
    container["started_at"] = datetime.utcnow().isoformat()

    return {
        "container_id": container_id,
        "status": "running",
        "message": f"容器 {container['name']} 启动成功",
    }


@app.post("/containers/{container_id}/stop")
async def stop_container(container_id: str, request: Request, timeout: int = 10):
    """停止容器"""
    check_api_key(request)

    if container_id not in containers:
        raise HTTPException(status_code=404, detail="Container not found")

    container = containers[container_id]
    print(f"模拟停止容器: {container_id} ({container['name']})")

    # 更新状态
    container["status"] = "stopped"
    container["stopped_at"] = datetime.utcnow().isoformat()

    return {
        "container_id": container_id,
        "status": "stopped",
        "message": f"容器 {container['name']} 停止成功",
    }


@app.delete("/containers/{container_id}")
async def remove_container(container_id: str, request: Request, force: bool = True):
    """删除容器"""
    check_api_key(request)

    if container_id not in containers:
        raise HTTPException(status_code=404, detail="Container not found")

    container = containers[container_id]
    print(f"模拟删除容器: {container_id} ({container['name']})")

    # 删除容器记录
    del containers[container_id]

    return {
        "container_id": container_id,
        "message": f"容器 {container['name']} 删除成功",
    }


@app.get("/containers/{container_id}")
async def get_container_info(container_id: str, request: Request):
    """获取容器信息"""
    check_api_key(request)

    if container_id not in containers:
        raise HTTPException(status_code=404, detail="Container not found")

    return containers[container_id]


@app.get("/containers/{container_id}/stats")
async def get_container_stats(container_id: str, request: Request):
    """获取容器统计信息"""
    check_api_key(request)

    if container_id not in containers:
        raise HTTPException(status_code=404, detail="Container not found")

    # 模拟统计数据
    return {
        "container_id": container_id,
        "cpu_usage": "0.5%",
        "memory_usage": "128MB / 256MB",
        "memory_percentage": "50%",
        "network_io": "1KB / 2KB",
        "block_io": "0B / 0B",
    }


@app.get("/containers/{container_id}/logs")
async def get_container_logs(container_id: str, request: Request, lines: int = 100):
    """获取容器日志"""
    check_api_key(request)

    if container_id not in containers:
        raise HTTPException(status_code=404, detail="Container not found")

    # 模拟日志
    container = containers[container_id]
    logs = [
        f"[{datetime.utcnow().isoformat()}] Container {container['name']} started",
        f"[{datetime.utcnow().isoformat()}] Service initializing...",
        f"[{datetime.utcnow().isoformat()}] Service ready on port 7860",
    ]

    return {"container_id": container_id, "logs": logs[-lines:], "lines": len(logs)}


@app.get("/containers/")
async def list_containers(request: Request, all_containers: bool = False):
    """列出容器"""
    check_api_key(request)

    if all_containers:
        result_containers = list(containers.values())
    else:
        result_containers = [c for c in containers.values() if c["status"] == "running"]

    return {"containers": result_containers, "total": len(result_containers)}


if __name__ == "__main__":
    print(f"启动本地mManager服务器...")
    print(f"端口: {MMANAGER_PORT}")
    print(f"服务器类型: {MMANAGER_SERVER_TYPE}")
    print(f"API密钥: {MMANAGER_API_KEY}")
    print(f"最大容器数: {MAX_CONTAINERS}")
    print(f"访问地址: http://localhost:{MMANAGER_PORT}")
    print(f"API文档: http://localhost:{MMANAGER_PORT}/docs")

    uvicorn.run(app, host="0.0.0.0", port=MMANAGER_PORT, reload=False)
