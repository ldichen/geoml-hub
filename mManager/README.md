# mManager - GeoML Docker 控制器

mManager 是 GeoML-Hub 的独立 Docker 容器管理服务，专门负责管理和调度 Docker 容器。

## 架构概述

```
GeoML-Hub 主服务
       ↓
   负载均衡器
   ↙    ↓    ↘
mManager-1  mManager-2  mManager-3
    ↓         ↓         ↓
 服务器A     服务器B    服务器C
```

## 主要特性

- **独立部署**：完全独立的 Docker 控制器服务
- **分布式管理**：支持多个 mManager 实例管理不同服务器
- **负载均衡**：智能选择最优控制器进行容器部署
- **健康监控**：实时监控容器和控制器健康状态
- **故障恢复**：自动处理控制器故障和容器迁移
- **资源感知**：支持 GPU/CPU 等硬件资源的智能调度

## 快速开始

### 1. 构建镜像

```bash
cd mManager
docker build -t mmanager:latest .
```

### 2. 启动服务

```bash
# 使用 docker-compose 启动
docker-compose up -d

# 或直接运行
docker run -d \
  --name mmanager \
  -p 8001:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e MMANAGER_API_KEY=your-secure-api-key \
  -e SERVER_TYPE=gpu \
  mmanager:latest
```

### 3. 验证服务

```bash
# 健康检查
curl http://localhost:8001/health

# 查看系统信息
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8001/system

# 列出容器
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8001/containers/
```

## 配置参数

### 环境变量

| 变量名             | 默认值                        | 说明                     |
| ------------------ | ----------------------------- | ------------------------ |
| `MMANAGER_API_KEY` | `mmanager-default-key`        | API 访问密钥             |
| `SERVER_ID`        | `mmanager-default`            | 服务器唯一标识           |
| `SERVER_TYPE`      | `cpu`                         | 服务器类型：cpu/gpu/edge |
| `MAX_CONTAINERS`   | `100`                         | 最大容器数量             |
| `LOG_LEVEL`        | `INFO`                        | 日志级别                 |
| `DOCKER_HOST`      | `unix:///var/run/docker.sock` | Docker 连接              |

### 服务器类型配置

```python
# CPU 服务器
SERVER_TYPE=cpu
MAX_CONTAINERS=50

# GPU 服务器
SERVER_TYPE=gpu
MAX_CONTAINERS=30

# 边缘服务器
SERVER_TYPE=edge
MAX_CONTAINERS=20
```

## API 接口

### 健康检查

```http
GET /health
```

### 容器管理

```http
POST   /containers/              # 创建容器
POST   /containers/{id}/start    # 启动容器
POST   /containers/{id}/stop     # 停止容器
DELETE /containers/{id}          # 删除容器
GET    /containers/{id}          # 获取容器信息
GET    /containers/{id}/stats    # 获取容器统计
GET    /containers/{id}/logs     # 获取容器日志
GET    /containers/              # 列出所有容器
```

### 系统信息

```http
GET /system        # 系统信息
GET /capabilities  # 服务器能力
GET /metrics       # Prometheus 指标
```

## 容器配置示例

```json
{
  "name": "geoml-service-example",
  "image": "tensorflow/tensorflow:latest-gpu",
  "command": "python app.py",
  "working_dir": "/app",
  "environment": {
    "MODEL_ID": "my-model",
    "GRADIO_SERVER_PORT": "7860"
  },
  "ports": {
    "7860/tcp": 7860
  },
  "volumes": {
    "/host/data": "/app/data"
  },
  "memory_limit": "2GB",
  "cpu_limit": 2.0,
  "restart_policy": "unless-stopped"
}
```

## 监控指标

mManager 提供以下 Prometheus 指标：

- `mmanager_containers_total` - 容器总数
- `mmanager_containers_running` - 运行中容器数
- `mmanager_memory_usage_bytes` - 内存使用量
- `mmanager_cpu_cores` - CPU 核心数
- `mmanager_load_percentage` - 负载百分比

## 故障排除

### 常见问题

1. **Docker 连接失败**

   ```bash
   # 检查 Docker socket 权限
   sudo chmod 666 /var/run/docker.sock

   # 或添加用户到 docker 组
   sudo usermod -aG docker $USER
   ```

2. **API 认证失败**

   ```bash
   # 检查 API 密钥是否正确
   curl -H "Authorization: Bearer correct-api-key" \
        http://localhost:8001/health
   ```

3. **容器创建失败**

   ```bash
   # 检查镜像是否存在
   docker images | grep your-image

   # 检查资源限制
   curl -H "Authorization: Bearer your-api-key" \
        http://localhost:8001/system
   ```

### 日志查看

```bash
# 查看容器日志
docker logs mmanager

# 查看详细日志
docker exec mmanager tail -f /app/logs/mmanager.log
```

## 生产部署

### 多服务器部署

1. **GPU 服务器部署**

```yaml
# docker-compose.gpu.yml
version: "3.8"
services:
  mmanager-gpu:
    image: mmanager:latest
    environment:
      - SERVER_ID=mmanager-gpu-01
      - SERVER_TYPE=gpu
      - MAX_CONTAINERS=30
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    ports:
      - "8001:8000"
```

2. **CPU 服务器部署**

```yaml
# docker-compose.cpu.yml
version: "3.8"
services:
  mmanager-cpu:
    image: mmanager:latest
    environment:
      - SERVER_ID=mmanager-cpu-01
      - SERVER_TYPE=cpu
      - MAX_CONTAINERS=50
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    ports:
      - "8002:8000"
```

### 高可用配置

```yaml
# docker-compose.ha.yml
version: "3.8"
services:
  mmanager:
    image: mmanager:latest
    deploy:
      replicas: 2
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

## 开发指南

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# 运行测试
pytest tests/
```

### 添加新功能

1. 在 `app/models/` 添加数据模型
2. 在 `app/services/` 添加业务逻辑
3. 在 `app/routers/` 添加 API 路由
4. 更新 `app/main.py` 注册新路由

## 安全考虑

1. **API 密钥管理**

   - 使用强密钥
   - 定期轮换密钥
   - 不要在代码中硬编码

2. **网络安全**

   - 使用 HTTPS（生产环境）
   - 限制访问来源 IP
   - 使用防火墙保护

3. **容器安全**
   - 使用非 root 用户运行容器
   - 限制容器权限
   - 定期更新基础镜像

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。
