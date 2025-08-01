# GeoML-Hub 部署指南

## 📋 目录结构

```
GeoML-hub/
├── .env                    # Docker Compose环境变量
├── .env.example           # Docker Compose环境变量示例
├── docker-compose.yml     # 开发环境配置
├── docker-compose.prod.yml # 生产环境配置
├── backend/
│   ├── .env              # 后端应用配置
│   ├── .env.example      # 后端应用配置示例
│   ├── Dockerfile        # 开发环境Dockerfile
│   └── Dockerfile.prod   # 生产环境Dockerfile
└── frontend/
    ├── Dockerfile        # 开发环境Dockerfile
    └── Dockerfile.prod   # 生产环境Dockerfile
```

## 🛠️ 环境准备

### 系统要求
- Docker 20.10+
- Docker Compose 2.0+
- Node.js 18+ (本地开发)
- Python 3.12+ (本地开发)

### 配置文件设置
1. 复制环境变量示例文件：
   ```bash
   cp .env.example .env
   cp backend/.env.example backend/.env
   ```

2. 根据您的环境修改配置文件

## 🚀 开发环境启动

### 方法1：使用Docker Compose（推荐）

```bash
# 1. 启动所有服务
docker-compose up -d

# 2. 查看服务状态
docker-compose ps

# 3. 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 4. 停止服务
docker-compose down
```

### 方法2：本地开发

```bash
# 1. 启动基础服务（PostgreSQL, Redis, MinIO）
docker-compose up -d postgres redis minio

# 2. 后端开发
cd backend
pip install -r requirements.txt
alembic upgrade head
python scripts/init_classifications.py  # 初始化分类数据
python scripts/init_sample_data.py     # 初始化示例数据
uvicorn app.main:app --reload

# 3. 前端开发（新终端）
cd frontend
npm install
npm run dev
```

### 服务访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:5173 | SvelteKit开发服务器 |
| 后端API | http://localhost:8000 | FastAPI应用 |
| API文档 | http://localhost:8000/docs | Swagger UI |
| PostgreSQL | localhost:5432 | 数据库 |
| Redis | localhost:6379 | 缓存 |
| MinIO | http://localhost:9000 | 对象存储 |
| MinIO控制台 | http://localhost:9001 | Web管理界面 |

### MinIO访问凭证（开发环境）
- 用户名: `minioadmin`
- 密码: `minioadmin123`

## 🏭 生产环境部署

### 1. 环境准备

```bash
# 创建生产环境配置
cp .env.example .env.prod
cp backend/.env.example backend/.env.prod

# 修改生产环境配置
# 注意：生产环境必须修改所有密码和密钥
```

### 2. 生产环境启动

```bash
# 使用生产环境配置启动
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 3. 数据库初始化

```bash
# 进入后端容器
docker-compose -f docker-compose.prod.yml exec backend bash

# 运行数据库迁移
alembic upgrade head

# 初始化数据（仅首次部署）
python scripts/init_classifications.py
python scripts/init_sample_data.py
```

### 4. SSL证书配置（生产环境）

```bash
# 创建SSL证书目录
mkdir -p nginx/ssl

# 将SSL证书放入该目录
# - nginx/ssl/cert.pem
# - nginx/ssl/key.pem
```

### 5. 域名配置

修改 `nginx/nginx.conf` 文件，替换域名：
```nginx
server_name your-domain.com;
```

## 📊 监控和维护

### 日志查看

```bash
# 开发环境
docker-compose logs -f [service_name]

# 生产环境
docker-compose -f docker-compose.prod.yml logs -f [service_name]
```

### 数据备份

```bash
# 数据库备份
docker-compose exec postgres pg_dump -U geoml geoml_hub > backup.sql

# MinIO数据备份
docker-compose exec minio mc mirror /data ./minio-backup/
```

### 服务重启

```bash
# 重启单个服务
docker-compose restart backend

# 重启所有服务
docker-compose restart
```

## 🔧 常见问题

### 1. 端口冲突
如果端口被占用，修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - "5433:5432"  # 将PostgreSQL端口改为5433
```

### 2. 数据库连接失败
检查环境变量配置，确保：
- 数据库密码正确
- 数据库服务已启动
- 防火墙允许访问

### 3. MinIO连接失败
确保：
- MinIO服务正常运行
- 访问凭证正确
- 网络连接正常

### 4. 前端无法访问API
检查：
- 后端服务是否运行正常
- CORS配置是否正确
- API_BASE_URL配置是否正确

## 📚 相关命令

### Docker命令
```bash
# 查看容器状态
docker-compose ps

# 进入容器
docker-compose exec backend bash
docker-compose exec frontend sh

# 查看容器日志
docker-compose logs -f backend

# 重建镜像
docker-compose build --no-cache

# 清理资源
docker-compose down -v  # 删除volume
docker system prune -a  # 清理所有未使用资源
```

### 数据库命令
```bash
# 进入数据库
docker-compose exec postgres psql -U geoml -d geoml_hub

# 数据库迁移
docker-compose exec backend alembic upgrade head

# 创建迁移文件
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### MinIO管理
```bash
# 创建存储桶
docker-compose exec minio mc mb local/geoml-hub

# 查看存储桶
docker-compose exec minio mc ls local/

# 设置存储桶策略
docker-compose exec minio mc policy set public local/geoml-hub
```

---

## 🚨 安全注意事项

1. **生产环境必须修改所有默认密码**
2. **使用HTTPS协议**
3. **定期备份数据**
4. **监控资源使用情况**
5. **及时更新依赖包**
6. **配置防火墙规则**

## 📞 技术支持

如果遇到问题，请：
1. 查看日志文件
2. 检查环境变量配置
3. 参考本文档的常见问题部分
4. 联系开发团队