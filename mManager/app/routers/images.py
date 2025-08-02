"""
mManager镜像管理路由
处理镜像的拉取、删除、清理等操作
"""
import asyncio
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.services.docker_service import docker_service
from app.middleware import verify_api_key
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class ImagePullRequest(BaseModel):
    """镜像拉取请求"""
    image: str
    auth: Optional[Dict] = None
    platform: Optional[str] = None


class ImageInfo(BaseModel):
    """镜像信息"""
    id: str
    repository: str
    tag: str
    size: int
    created: str


@router.post("/images/pull")
async def pull_image(
    request: ImagePullRequest,
    _: str = Depends(verify_api_key)
):
    """
    拉取Docker镜像
    """
    try:
        logger.info(f"开始拉取镜像: {request.image}")
        
        # 构建Docker命令
        pull_cmd = f"docker pull {request.image}"
        
        # 如果有认证信息，先登录
        if request.auth:
            username = request.auth.get("username")
            password = request.auth.get("password")
            registry = request.image.split('/')[0]
            
            if username and password:
                login_cmd = f"echo '{password}' | docker login {registry} -u {username} --password-stdin"
                process = await asyncio.create_subprocess_shell(
                    login_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Docker登录失败: {stderr.decode()}"
                    )
        
        # 执行拉取命令
        process = await asyncio.create_subprocess_shell(
            pull_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode()
            logger.error(f"镜像拉取失败: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=f"镜像拉取失败: {error_msg}"
            )
        
        output = stdout.decode()
        logger.info(f"镜像拉取成功: {request.image}")
        
        return {
            "status": "success",
            "image": request.image,
            "message": "镜像拉取成功",
            "output": output
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"拉取镜像异常: {e}")
        raise HTTPException(status_code=500, detail=f"内部错误: {str(e)}")


@router.get("/images/")
async def list_images(
    all_images: bool = Query(False, description="是否包含所有镜像"),
    _: str = Depends(verify_api_key)
):
    """
    列出本地Docker镜像
    """
    try:
        # 构建命令
        if all_images:
            cmd = "docker images --format 'table {{.ID}}\\t{{.Repository}}\\t{{.Tag}}\\t{{.Size}}\\t{{.CreatedAt}}'"
        else:
            cmd = "docker images --filter 'dangling=false' --format 'table {{.ID}}\\t{{.Repository}}\\t{{.Tag}}\\t{{.Size}}\\t{{.CreatedAt}}'"
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode()
            logger.error(f"列出镜像失败: {error_msg}")
            raise HTTPException(status_code=500, detail=f"列出镜像失败: {error_msg}")
        
        output = stdout.decode()
        lines = output.strip().split('\n')[1:]  # 跳过表头
        
        images = []
        for line in lines:
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 5:
                    images.append({
                        "id": parts[0],
                        "repository": parts[1],
                        "tag": parts[2],
                        "size": parts[3],
                        "created": parts[4]
                    })
        
        return {
            "images": images,
            "total": len(images)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"列出镜像异常: {e}")
        raise HTTPException(status_code=500, detail=f"内部错误: {str(e)}")


@router.get("/images/{image_name:path}")
async def get_image_info(
    image_name: str,
    _: str = Depends(verify_api_key)
):
    """
    获取镜像详细信息
    """
    try:
        # URL解码镜像名称
        import urllib.parse
        image_name = urllib.parse.unquote(image_name)
        
        cmd = f"docker inspect {image_name}"
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode()
            if "No such image" in error_msg:
                raise HTTPException(status_code=404, detail="镜像不存在")
            else:
                raise HTTPException(status_code=500, detail=f"获取镜像信息失败: {error_msg}")
        
        import json
        image_info = json.loads(stdout.decode())[0]
        
        return {
            "id": image_info["Id"],
            "repository_tags": image_info.get("RepoTags", []),
            "size": image_info["Size"],
            "created": image_info["Created"],
            "config": image_info.get("Config", {}),
            "architecture": image_info.get("Architecture"),
            "os": image_info.get("Os")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取镜像信息异常: {e}")
        raise HTTPException(status_code=500, detail=f"内部错误: {str(e)}")


@router.delete("/images/{image_name:path}")
async def remove_image(
    image_name: str,
    force: bool = Query(False, description="强制删除"),
    _: str = Depends(verify_api_key)
):
    """
    删除Docker镜像
    """
    try:
        # URL解码镜像名称
        import urllib.parse
        image_name = urllib.parse.unquote(image_name)
        
        # 构建删除命令
        cmd = f"docker rmi {image_name}"
        if force:
            cmd += " --force"
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode()
            if "No such image" in error_msg:
                raise HTTPException(status_code=404, detail="镜像不存在")
            elif "image is being used by running container" in error_msg:
                raise HTTPException(status_code=409, detail="镜像正在被容器使用")
            else:
                raise HTTPException(status_code=400, detail=f"删除镜像失败: {error_msg}")
        
        output = stdout.decode()
        logger.info(f"镜像删除成功: {image_name}")
        
        return {
            "status": "success",
            "image": image_name,
            "message": "镜像删除成功",
            "output": output
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除镜像异常: {e}")
        raise HTTPException(status_code=500, detail=f"内部错误: {str(e)}")


@router.post("/images/prune")
async def prune_images(
    all_images: bool = Query(False, description="删除所有未使用的镜像"),
    _: str = Depends(verify_api_key)
):
    """
    清理未使用的镜像
    """
    try:
        # 构建清理命令
        cmd = "docker image prune -f"
        if all_images:
            cmd = "docker image prune -a -f"
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode()
            logger.error(f"镜像清理失败: {error_msg}")
            raise HTTPException(status_code=500, detail=f"镜像清理失败: {error_msg}")
        
        output = stdout.decode()
        logger.info("镜像清理完成")
        
        # 解析清理结果
        freed_space = "0B"
        for line in output.split('\n'):
            if "Total reclaimed space:" in line:
                freed_space = line.split(":")[-1].strip()
                break
        
        return {
            "status": "success",
            "message": "镜像清理完成",
            "freed_space": freed_space,
            "output": output
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"镜像清理异常: {e}")
        raise HTTPException(status_code=500, detail=f"内部错误: {str(e)}")


@router.get("/images/stats")
async def get_images_stats(
    _: str = Depends(verify_api_key)
):
    """
    获取镜像统计信息
    """
    try:
        # 获取镜像总数
        count_cmd = "docker images -q | wc -l"
        process = await asyncio.create_subprocess_shell(
            count_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        total_images = int(stdout.decode().strip()) if process.returncode == 0 else 0
        
        # 获取悬空镜像数量
        dangling_cmd = "docker images -f 'dangling=true' -q | wc -l"
        process = await asyncio.create_subprocess_shell(
            dangling_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        dangling_images = int(stdout.decode().strip()) if process.returncode == 0 else 0
        
        # 获取总大小
        size_cmd = "docker system df --format 'table {{.Type}}\\t{{.Total}}\\t{{.Active}}\\t{{.Size}}\\t{{.Reclaimable}}' | grep Images"
        process = await asyncio.create_subprocess_shell(
            size_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        size_info = "未知"
        reclaimable = "未知"
        if process.returncode == 0:
            output = stdout.decode().strip()
            if output:
                parts = output.split('\t')
                if len(parts) >= 5:
                    size_info = parts[3]
                    reclaimable = parts[4]
        
        return {
            "total_images": total_images,
            "dangling_images": dangling_images,
            "total_size": size_info,
            "reclaimable_size": reclaimable
        }
        
    except Exception as e:
        logger.error(f"获取镜像统计异常: {e}")
        raise HTTPException(status_code=500, detail=f"内部错误: {str(e)}")