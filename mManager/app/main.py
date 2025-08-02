"""
mManager - GeoML Docker 控制器服务
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.config import settings
from app.middleware import AuthenticationMiddleware, LoggingMiddleware
from app.routers import containers, health, images
from app.services.docker_service import docker_service


# 配置日志
def setup_logging():
    """配置日志系统"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 创建日志目录
    os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)

    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format=log_format,
        handlers=[
            logging.StreamHandler(),  # 控制台输出
            logging.FileHandler(settings.log_file),  # 文件输出
        ],
    )

    # 设置Docker库的日志级别
    logging.getLogger("docker").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


# 设置日志
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("mManager 启动中...")

    try:
        # 初始化Docker服务
        await docker_service.get_system_info()  # 测试Docker连接
        logger.info(f"mManager ({settings.server_id}) 启动成功")
        logger.info(f"服务器类型: {settings.server_type}")
        logger.info(f"最大容器数: {settings.max_containers}")

        yield

    except Exception as e:
        logger.error(f"mManager 启动失败: {e}")
        raise
    finally:
        logger.info("mManager 关闭中...")


# 创建FastAPI应用
app = FastAPI(
    title="mManager",
    description="GeoML Docker 控制器服务 - 管理Docker容器的独立服务",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 添加自定义中间件
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthenticationMiddleware)

# 注册路由
app.include_router(health.router)
app.include_router(containers.router)
app.include_router(images.router)


@app.get("/")
async def root():
    """根路径信息"""
    return {
        "service": "mManager",
        "description": "GeoML Docker 控制器服务",
        "version": "1.0.0",
        "server_id": settings.server_id,
        "server_type": settings.server_type,
        "timestamp": datetime.now(datetime.timezone.utc).isoformat(),
        "status": "running",
        "endpoints": {
            "health": "/health",
            "containers": "/containers",
            "system": "/system",
            "capabilities": "/capabilities",
            "metrics": "/metrics",
            "docs": "/docs",
        },
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return HTTPException(status_code=500, detail=f"内部服务器错误: {str(exc)}")


if __name__ == "__main__":
    import uvicorn

    logger.info(f"启动 mManager 服务，监听 {settings.host}:{settings.port}")

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=False,  # 生产环境关闭热重载
        access_log=True,
    )
