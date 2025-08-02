# GeoML-Hub v2.0 - mManager 集成指南

## 概述

GeoML-Hub v2.0 已完全重构为基于 mManager 的分布式 Docker 容器管理架构。本文档介绍了新架构的部署、配置和使用方法。

## 架构变更

### v1.0 架构（旧）
```
GeoML-Hub Backend → 直接调用 Docker API → 本地 Docker
```

### v2.0 架构（新）
```
GeoML-Hub Backend → mManager 集群 → 分布式 Docker 服务器
                    ↙        ↓        ↘
               GPU服务器   CPU服务器   边缘服务器
```

## 部署步骤

### 1. 部署 mManager 控制器

#### GPU 服务器 (192.168.1.10)
```bash
# 创建配置目录
mkdir -p /opt/mmanager/logs /opt/mmanager/data

# 部署 mManager
cd /opt/mmanager
cat > docker-compose.yml << EOF
version: '3.8'
services:
  mmanager:
    image: mmanager:latest
    container_name: mmanager-gpu-01
    ports:
      - "8001:8000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - MMANAGER_API_KEY=mmanager-secure-key-12345
      - SERVER_ID=mmanager-gpu-01
      - SERVER_TYPE=gpu
      - MAX_CONTAINERS=30
    restart: unless-stopped
    networks:
      - geoml-network

networks:
  geoml-network:
    external: true
EOF

docker-compose up -d
```

#### CPU 服务器 (192.168.1.11)
```bash
# 类似配置，修改相应参数
SERVER_ID=mmanager-cpu-01
SERVER_TYPE=cpu
MAX_CONTAINERS=50
PORT=8002
```

### 2. 更新 GeoML-Hub 后端配置

```python
# backend/app/config.py
mmanager_enabled = True
mmanager_api_key = "mmanager-secure-key-12345"
mmanager_controllers = [
    {
        "id": "mmanager-gpu-01",
        "url": "http://192.168.1.10:8001",
        "server_type": "gpu",
        "enabled": True,
        "priority": 1,
        "weight": 100
    },
    {
        "id": "mmanager-cpu-01", 
        "url": "http://192.168.1.11:8002",
        "server_type": "cpu",
        "enabled": True,
        "priority": 2,
        "weight": 80
    }
]
```

### 3. 运行数据库迁移

```bash
cd backend
alembic upgrade head
```

### 4. 重启 GeoML-Hub 服务

```bash
docker-compose restart backend
```

## 功能特性

### 智能调度

系统会根据以下因素自动选择最优的 mManager 控制器：

1. **硬件需求匹配**
   - GPU 模型自动分配到 GPU 服务器
   - CPU 模型优先分配到 CPU 服务器

2. **负载均衡**
   - 选择负载最低的控制器
   - 避免单点过载

3. **故障转移**
   - 自动检测控制器故障
   - 将故障服务器上的服务迁移到健康服务器

### 容器生命周期管理

```python
# 创建服务（自动选择控制器）
service = await model_service_manager.create_service(
    db, service_data, repository_id, user_id
)

# 启动服务（通过选定的控制器）
await model_service_manager.start_service(
    db, service_id, user_id
)

# 停止服务
await model_service_manager.stop_service(
    db, service_id, user_id
)

# 获取服务状态（包含控制器信息）
status = await model_service_manager.get_service_status(
    db, service_id
)
```

### 监控和日志

1. **控制器健康监控**
   ```bash
   # 检查所有控制器状态
   curl http://geoml-hub/api/admin/controllers/health
   ```

2. **容器日志收集**
   ```bash
   # 获取服务日志（自动路由到正确的控制器）
   curl http://geoml-hub/api/services/{service_id}/logs
   ```

3. **资源使用监控**
   ```bash
   # 查看资源使用情况
   curl http://geoml-hub/api/admin/resources/usage
   ```

## 配置选项

### 后端配置 (config.py)

```python
# mManager 基础配置
mmanager_enabled: bool = True
mmanager_api_key: str = "your-secure-api-key"

# 控制器列表
mmanager_controllers: List[dict] = [
    {
        "id": "controller-id",
        "url": "http://host:port",
        "server_type": "gpu|cpu|edge",
        "enabled": True,
        "priority": 1,  # 数值越小优先级越高
        "weight": 100   # 负载均衡权重
    }
]

# 服务配置
service_domain: str = "your-domain.com"
max_services_per_user: int = 5
service_idle_timeout: int = 30  # minutes
```

### mManager 配置

```bash
# 基础配置
MMANAGER_API_KEY=your-secure-api-key
SERVER_ID=unique-server-id
SERVER_TYPE=gpu|cpu|edge
MAX_CONTAINERS=100

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/app/logs/mmanager.log

# Docker 配置
DOCKER_HOST=unix:///var/run/docker.sock
DOCKER_TIMEOUT=60
```

## 数据库更改

### 新增表

1. **container_registry** - 容器注册表
   - 记录容器在哪个控制器上运行
   - 存储容器的基本信息和状态

2. **mmanager_controllers** - 控制器注册表
   - 记录所有 mManager 控制器信息
   - 监控控制器健康状态

3. **container_operations** - 容器操作记录
   - 记录所有容器操作的历史
   - 用于审计和故障排查

4. **service_deployment_history** - 服务部署历史
   - 记录服务的部署版本和配置
   - 支持服务版本回滚

### 模型变更

```python
# ModelService 新增字段
class ModelService(Base):
    # ... 原有字段 ...
    
    # 新增关联关系
    container_registry = relationship(
        "ContainerRegistry", 
        back_populates="service", 
        uselist=False
    )
```

## API 变更

### 保持兼容

所有现有的 API 接口保持不变，但底层实现已切换到 mManager：

```python
# 这些 API 接口不变
POST   /api/{username}/{repo}/services     # 创建服务
POST   /api/services/{id}/start            # 启动服务
POST   /api/services/{id}/stop             # 停止服务
GET    /api/services/{id}/status           # 获取状态
GET    /api/services/{id}/logs             # 获取日志
DELETE /api/services/{id}                  # 删除服务
```

### 新增管理接口

```python
# 控制器管理
GET    /api/admin/controllers              # 列出控制器
GET    /api/admin/controllers/{id}/health  # 控制器健康检查
POST   /api/admin/controllers/{id}/enable  # 启用控制器
POST   /api/admin/controllers/{id}/disable # 禁用控制器

# 容器管理
GET    /api/admin/containers               # 列出所有容器
GET    /api/admin/containers/{id}/migrate  # 迁移容器
GET    /api/admin/operations               # 操作历史
```

## 故障排除

### 常见问题

1. **控制器连接失败**
   ```bash
   # 检查网络连通性
   curl http://controller-host:port/health
   
   # 检查 API 密钥
   curl -H "Authorization: Bearer your-api-key" \
        http://controller-host:port/health
   ```

2. **服务启动失败**
   ```bash
   # 查看服务日志
   curl http://geoml-hub/api/services/{id}/logs
   
   # 查看控制器状态
   curl http://geoml-hub/api/admin/controllers
   ```

3. **容器找不到**
   ```bash
   # 检查容器注册表
   SELECT * FROM container_registry WHERE service_id = ?;
   
   # 检查控制器健康状态
   SELECT * FROM mmanager_controllers WHERE status = 'healthy';
   ```

### 日志位置

```bash
# GeoML-Hub 后端日志
docker logs geoml-hub-backend

# mManager 控制器日志
docker logs mmanager-gpu-01
docker exec mmanager-gpu-01 tail -f /app/logs/mmanager.log

# 数据库日志
tail -f /var/log/postgresql/postgresql.log
```

## 性能优化

### 负载均衡优化

```python
# 调整控制器权重
{
    "id": "high-performance-gpu",
    "weight": 150,  # 更高权重，承担更多负载
    "priority": 1
}

{
    "id": "backup-cpu",
    "weight": 50,   # 较低权重，作为备用
    "priority": 3
}
```

### 资源配额管理

```python
# 限制单用户最大服务数
max_services_per_user = 5

# 限制服务资源使用
{
    "memory_limit": "2GB",
    "cpu_limit": 2.0,
    "gpu_required": True
}
```

### 监控告警

```bash
# 设置 Prometheus 监控
# 监控指标：
# - mmanager_containers_running
# - mmanager_load_percentage  
# - mmanager_memory_usage_percent

# 告警规则示例
- alert: HighContainerLoad
  expr: mmanager_load_percentage > 90
  for: 5m
  annotations:
    summary: "mManager 负载过高"
```

## 迁移指南

### 从 v1.0 迁移到 v2.0

1. **备份现有数据**
   ```bash
   pg_dump geoml_hub > backup_v1.sql
   ```

2. **部署 mManager 控制器**
   ```bash
   # 在每台服务器上部署 mManager
   docker-compose -f mmanager/docker-compose.yml up -d
   ```

3. **更新后端配置**
   ```bash
   # 更新 config.py 中的 mManager 配置
   ```

4. **运行数据库迁移**
   ```bash
   alembic upgrade head
   ```

5. **重启服务**
   ```bash
   docker-compose restart
   ```

6. **验证功能**
   ```bash
   # 测试服务创建和启动
   curl -X POST http://geoml-hub/api/{user}/{repo}/services
   ```

### 回滚方案

如果需要回滚到 v1.0：

1. **恢复数据库**
   ```bash
   psql geoml_hub < backup_v1.sql
   ```

2. **切换到旧版代码**
   ```bash
   git checkout v1.0
   docker-compose up -d
   ```

## 最佳实践

1. **高可用部署**
   - 至少部署 2 个 mManager 控制器
   - 使用不同的物理服务器
   - 配置自动故障转移

2. **安全配置**
   - 使用强 API 密钥
   - 启用 HTTPS
   - 限制网络访问

3. **监控配置**
   - 配置 Prometheus 监控
   - 设置告警规则
   - 定期检查日志

4. **资源管理**
   - 合理配置资源限制
   - 监控资源使用情况
   - 定期清理未使用的容器

## 支持

如有问题，请：

1. 查看本文档的故障排除部分
2. 检查 GitHub Issues
3. 联系开发团队

---

**注意**: 本文档基于 GeoML-Hub v2.0 版本编写，如有更新请查看最新版本文档。