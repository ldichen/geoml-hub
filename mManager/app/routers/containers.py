"""
容器管理路由
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional

from app.models.container import (
    ContainerCreateRequest,
    ContainerInfo,
    ContainerStatsResponse,
    ContainerLogsResponse,
    ContainerListResponse,
    ContainerOperationResponse
)
from app.services.docker_service import docker_service

router = APIRouter(prefix="/containers", tags=["containers"])

@router.post("/", response_model=ContainerOperationResponse)
async def create_container(config: ContainerCreateRequest):
    """创建新容器"""
    try:
        result = await docker_service.create_container(config)
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{container_id}/start", response_model=ContainerOperationResponse)
async def start_container(
    container_id: str = Path(..., description="容器ID")
):
    """启动容器"""
    try:
        result = await docker_service.start_container(container_id)
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{container_id}/stop", response_model=ContainerOperationResponse)
async def stop_container(
    container_id: str = Path(..., description="容器ID"),
    timeout: int = Query(10, description="停止超时时间(秒)")
):
    """停止容器"""
    try:
        result = await docker_service.stop_container(container_id, timeout)
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{container_id}", response_model=ContainerOperationResponse)
async def remove_container(
    container_id: str = Path(..., description="容器ID"),
    force: bool = Query(False, description="强制删除")
):
    """删除容器"""
    try:
        result = await docker_service.remove_container(container_id, force)
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{container_id}", response_model=ContainerInfo)
async def get_container_info(
    container_id: str = Path(..., description="容器ID")
):
    """获取容器详细信息"""
    try:
        return await docker_service.get_container_info(container_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{container_id}/stats", response_model=ContainerStatsResponse)
async def get_container_stats(
    container_id: str = Path(..., description="容器ID")
):
    """获取容器统计信息"""
    try:
        return await docker_service.get_container_stats(container_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{container_id}/logs", response_model=ContainerLogsResponse)
async def get_container_logs(
    container_id: str = Path(..., description="容器ID"),
    lines: int = Query(100, description="日志行数", ge=1, le=10000)
):
    """获取容器日志"""
    try:
        return await docker_service.get_container_logs(container_id, lines)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/", response_model=ContainerListResponse)
async def list_containers(
    all: bool = Query(False, description="显示所有容器（包括已停止的）")
):
    """列出容器"""
    try:
        return await docker_service.list_containers(all_containers=all)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{container_id}/restart", response_model=ContainerOperationResponse)
async def restart_container(
    container_id: str = Path(..., description="容器ID"),
    timeout: int = Query(10, description="停止超时时间(秒)")
):
    """重启容器"""
    try:
        # 先停止容器
        stop_result = await docker_service.stop_container(container_id, timeout)
        if not stop_result.success:
            return stop_result
        
        # 再启动容器
        start_result = await docker_service.start_container(container_id)
        if start_result.success:
            start_result.operation = "restart"
            start_result.message = "容器重启成功"
        
        return start_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))