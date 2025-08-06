from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routers import (
    auth,
    classifications,
    users,
    repositories,
    search,
    admin,
    files,
    metadata,
    discover,
    system,
    file_editor,
    personal_files,
    services,
    images,
)
from app.middleware.error_handler import add_exception_handlers
from app.services.model_service import service_manager
from app.database import get_async_db
import logging
import asyncio

# Configure logging
from app.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


# 应用启动事件
async def startup_event():
    """应用启动时初始化服务"""
    logger.info("初始化 GeoML-Hub v2.0 服务...")

    # 初始化服务管理器和mManager客户端
    async for db in get_async_db():
        try:
            await service_manager.initialize(db)
            logger.info("服务管理器初始化成功")
            break
        except Exception as e:
            logger.error(f"服务管理器初始化失败: {e}")
        finally:
            await db.close()


# Create FastAPI app
app = FastAPI(
    title="GeoML-Hub API v2.0",
    description="地理科学机器学习模型仓库平台 API - Hugging Face 风格架构",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    on_startup=[startup_event],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add exception handlers
add_exception_handlers(app)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(
    classifications.router, prefix="/api/classifications", tags=["classifications"]
)
# v2.0 核心路由
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(
    repositories.router, prefix="/api/repositories", tags=["repositories"]
)
# 搜索和发现
app.include_router(search.router, prefix="/api/search", tags=["search"])
# 顶级发现端点
app.include_router(discover.router, prefix="/api", tags=["discover"])
# 文件管理
app.include_router(files.router, prefix="/api/files", tags=["files"])
# 个人文件空间
app.include_router(personal_files.router, tags=["personal-files"])
# 文件编辑与版本控制
app.include_router(file_editor.router, prefix="/api", tags=["file-editor"])
# 元数据管理
app.include_router(metadata.router, prefix="/api/metadata", tags=["metadata"])
# 系统管理
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
# 系统配置
app.include_router(system.router, prefix="/api/system", tags=["system"])
# 模型服务管理
app.include_router(services.router, prefix="/api/services", tags=["services"])
# 镜像管理
app.include_router(images.router, prefix="/api/images", tags=["images"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to GeoML-Hub API v2.0",
        "description": "地理科学机器学习模型仓库平台 - Hugging Face 风格架构",
        "version": "2.0.0",
        "features": [
            "用户个人空间与仓库管理",
            "JWT认证与外部认证集成",
            "社交功能（点赞、关注、收藏）",
            "README.md 驱动的元数据解析",
            "MinIO 对象存储与大文件分片上传",
            "三级分类体系与全文搜索",
            "趋势发现与搜索建议",
            "系统管理与监控面板",
        ],
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "GeoML-Hub API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
