from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://geoml:password@localhost:5432/geoml_hub"
    database_pool_size: int = 20
    database_max_overflow: int = 30

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str = ""

    # Security
    secret_key: str = "your-super-secret-key-here"
    algorithm: str = "HS256"

    # CORS - 根据环境自动配置
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    cors_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_headers: List[str] = ["Content-Type", "Authorization"]

    # File upload
    upload_dir: str = "/app/uploads"
    max_file_size: int = 10485760  # 10MB
    allowed_extensions: List[str] = ["jpg", "jpeg", "png", "gif", "pdf", "md"]

    # JWT Authentication
    jwt_secret_key: str = "your-jwt-secret-key-change-in-production"
    external_auth_secret_key: str = "external-auth-secret-key-change-in-production"

    # OpenGMS User Server Configuration
    opengms_user_server_url: str = (
        "http://localhost:8080"  # 需要替换为实际的OpenGMS用户服务器地址
    )
    opengms_oauth2_client_id: str = "geoml-hub"  # 需要向OpenGMS团队申请
    opengms_oauth2_client_secret: str = "your-secret-key"  # 需要向OpenGMS团队申请
    opengms_auth_timeout: int = 30  # seconds

    # External Authentication Service (保留原有配置作为备用)
    external_auth_url: str = "https://auth.example.com"
    external_auth_timeout: int = 30  # seconds

    # Token Configuration
    refresh_token_expire_days: int = 7  # 7 days
    access_token_expire_minutes: int = (
        30  # Override the previous definition with more explicit name
    )

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    # Cache
    cache_ttl: int = 3600  # 1 hour
    cache_prefix: str = "geoml_hub:"

    # MinIO Storage
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_default_bucket: str = "geoml-hub"

    # File Storage
    max_file_size_mb: int = 500  # 500MB per file
    max_total_size_gb: int = 5  # 5GB per user
    chunk_size_mb: int = 5  # 5MB per chunk
    upload_session_expires_hours: int = 24

    # Model Service Management
    service_port_start: int = 7000  # 服务端口范围开始
    service_port_end: int = 8000  # 服务端口范围结束
    max_services_per_user: int = 20  # 每用户最大同时运行服务数
    max_services_per_repository: int = 3  # 每仓库最大服务数
    service_idle_timeout: int = 30  # 空闲超时时间(分钟)
    health_check_interval: int = 60  # 健康检查间隔(秒)
    service_startup_timeout: int = 300  # 服务启动超时(秒)
    service_shutdown_timeout: int = 30  # 服务关闭超时(秒)
    docker_image_name: str = "geoml-service:latest"  # 默认Docker镜像

    # Auto-start Configuration
    auto_start_on_visit: bool = True  # 访问仓库时自动启动服务
    startup_failure_retry_interval: int = 60  # 启动失败后重试间隔(秒)
    startup_priority_enabled: bool = True  # 是否启用优先级启动
    max_auto_start_retries: int = 3  # 最大自动启动重试次数
    exponential_backoff_enabled: bool = True  # 是否启用指数退避重试
    max_retry_delay: int = 3600  # 最大重试延迟时间(秒)，默认1小时

    # Docker Remote Connection
    docker_ms_host: str = (
        "unix:///var/run/docker.sock"  # Docker服务器地址，支持tcp://host:port, ssh://user@host, unix:///path/to/socket
    )
    docker_ms_tls_verify: bool = False  # 是否启用TLS验证
    docker_ms_cert_path: str = (
        ""  # TLS证书路径 (目录路径，包含ca.pem, cert.pem, key.pem)
    )
    docker_ms_ca_cert: str = ""  # CA证书文件路径
    docker_ms_client_cert: str = ""  # 客户端证书文件路径
    docker_ms_client_key: str = ""  # 客户端私钥文件路径
    docker_ms_timeout: int = 60  # Docker API超时时间(秒)

    # Model Service TLS Configuration
    service_tls_enabled: bool = False  # 是否为模型服务启用TLS
    service_tls_cert_path: str = ""  # 服务TLS证书文件路径
    service_tls_key_path: str = ""  # 服务TLS私钥文件路径
    service_domain: str = "localhost"  # 服务域名

    # Resource Limits
    default_cpu_limit: str = "0.3"  # 默认CPU限制
    default_memory_limit: str = "256Mi"  # 默认内存限制
    max_cpu_limit: str = "0.5"  # 最大CPU限制
    max_memory_limit: str = "512Mi"  # 最大内存限制

    class Config:
        env_file = ".env"
        extra = "ignore"  # 忽略额外的环境变量


settings = Settings()
