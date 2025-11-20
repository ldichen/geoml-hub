# Skopeo 推送工具使用指南

本项目支持两种方式使用Skopeo推送镜像到Harbor:

1. **Docker容器方式** (推荐) - 适合生产环境,性能好
2. **原生Skopeo方式** - 适合开发环境,需要系统安装skopeo

## 方案一: Docker容器方式 (推荐)

### 优点
- ✅ 不需要在宿主机安装skopeo
- ✅ 使用常驻容器,性能好
- ✅ 容器隔离,不污染宿主机环境
- ✅ 跨平台支持 (Linux/macOS/Windows)

### 配置步骤

#### 1. 启动Skopeo容器

```bash
# 创建共享目录
mkdir -p /tmp/geoml-skopeo

# 启动Skopeo容器
docker run -d \
  --name skopeo-service \
  --restart unless-stopped \
  -v /tmp/geoml-skopeo:/tmp/skopeo \
  quay.io/skopeo/stable \
  tail -f /dev/null
```

#### 2. 验证容器运行

```bash
# 检查容器状态
docker ps | grep skopeo-service

# 验证skopeo可用
docker exec skopeo-service skopeo --version
```

#### 3. 配置环境变量 (可选)

在 `backend/.env` 中添加:

```bash
# Skopeo配置
SKOPEO_SHARED_DIR=/tmp/geoml-skopeo  # 默认值,可不配置
```

#### 4. 使用代码

```python
from app.utils.skopeo_pusher import skopeo_push_to_harbor

# 自动使用Docker容器方式 (prefer_docker=True是默认值)
result = await skopeo_push_to_harbor(
    tar_file=tar_file,
    harbor_url="https://harbor.example.com",
    username="admin",
    password="password",
    project="my-project",
    repository="my-repo",
    tag="latest",
    prefer_docker=True  # 优先使用Docker方式
)
```

### 容器管理

```bash
# 停止容器
docker stop skopeo-service

# 启动容器
docker start skopeo-service

# 重启容器
docker restart skopeo-service

# 查看容器日志
docker logs skopeo-service

# 删除容器
docker rm -f skopeo-service
```

---

## 方案二: 原生Skopeo方式

### 优点
- ✅ 不需要Docker
- ✅ 直接使用系统命令,调试方便

### 配置步骤

#### 1. 安装Skopeo

**macOS:**
```bash
brew install skopeo
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install skopeo
```

**CentOS/RHEL:**
```bash
sudo yum install skopeo
```

**从源码编译 (所有平台):**
```bash
git clone https://github.com/containers/skopeo
cd skopeo
make bin/skopeo
sudo cp bin/skopeo /usr/local/bin/
```

#### 2. 验证安装

```bash
skopeo --version
```

#### 3. 使用代码

```python
from app.utils.skopeo_pusher import skopeo_push_to_harbor

# 使用原生skopeo方式
result = await skopeo_push_to_harbor(
    tar_file=tar_file,
    harbor_url="https://harbor.example.com",
    username="admin",
    password="password",
    project="my-project",
    repository="my-repo",
    tag="latest",
    prefer_docker=False  # 不使用Docker方式
)
```

---

## 自动回退机制

代码内置了智能回退机制:

1. **优先尝试Docker方式** (如果 `prefer_docker=True`)
   - 检查容器是否运行
   - 检查容器内skopeo是否可用

2. **自动回退到原生方式** (如果Docker方式不可用)
   - 检查系统skopeo是否安装
   - 使用原生skopeo执行推送

3. **返回错误** (如果两种方式都不可用)

### 示例代码

```python
# 自动选择最佳方式
result = await skopeo_push_to_harbor(
    tar_file=tar_file,
    harbor_url="https://harbor.example.com",
    username="admin",
    password="password",
    project="my-project",
    repository="my-repo",
    tag="latest",
    prefer_docker=True  # 优先Docker,失败自动回退到原生
)

if result['status'] == 'success':
    print(f"推送成功: {result['image']}")
    print(f"使用方法: {result['method']}")  # 'docker' 或 'native'
else:
    print(f"推送失败: {result['message']}")
```

---

## 高级用法

### 直接使用SkopeoPusher类

```python
from app.utils.skopeo_pusher import SkopeoPusher

# 创建Docker模式推送器
pusher = SkopeoPusher(use_docker=True, container_name="skopeo-service")

# 检查可用性
if await pusher.check_skopeo_available():
    # 执行推送
    result = await pusher.push_from_tar(
        tar_file=tar_file,
        harbor_url="https://harbor.example.com",
        username="admin",
        password="password",
        project="my-project",
        repository="my-repo",
        tag="latest",
        progress_callback=my_progress_callback  # 可选的进度回调
    )
```

### 进度回调

```python
async def progress_callback(percent: int, message: str):
    print(f"[{percent}%] {message}")

result = await skopeo_push_to_harbor(
    tar_file=tar_file,
    harbor_url="https://harbor.example.com",
    username="admin",
    password="password",
    project="my-project",
    repository="my-repo",
    tag="latest",
    progress_callback=progress_callback
)
```

---

## 故障排查

### Docker方式问题

**问题: 容器未运行**
```bash
# 解决方案
docker start skopeo-service
```

**问题: 权限不足**
```bash
# 确保Docker可以访问共享目录
chmod 755 /tmp/geoml-skopeo
```

**问题: 容器不存在**
```bash
# 重新创建容器
docker run -d \
  --name skopeo-service \
  -v /tmp/geoml-skopeo:/tmp/skopeo \
  quay.io/skopeo/stable \
  tail -f /dev/null
```

### 原生方式问题

**问题: skopeo命令找不到**
```bash
# 检查安装
which skopeo

# 重新安装
brew install skopeo  # macOS
# 或
sudo apt-get install skopeo  # Ubuntu
```

**问题: TLS证书验证失败**
- 代码已经自动使用 `--dest-tls-verify=false` 参数
- 如果还有问题,检查Harbor服务器配置

---

## 性能对比

| 特性 | Docker方式 (常驻容器) | 原生方式 |
|------|---------------------|---------|
| 首次推送 | ~5s | ~3s |
| 后续推送 | ~3s (复用容器) | ~3s |
| 内存占用 | ~50MB (容器) | ~0MB |
| 部署复杂度 | 低 (只需Docker) | 中 (需安装skopeo) |
| 跨平台支持 | 优秀 | 一般 |

---

## 最佳实践

1. **生产环境**: 使用Docker容器方式,配合自动重启
2. **开发环境**: 根据个人喜好选择,两种都可以
3. **CI/CD环境**: 推荐Docker方式,更容易标准化
4. **Windows环境**: 必须使用Docker方式

---

## 环境变量总结

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `SKOPEO_SHARED_DIR` | `/tmp/geoml-skopeo` | Docker模式的共享目录 |

---

## 相关资源

- Skopeo官方文档: https://github.com/containers/skopeo
- Docker Hub: https://quay.io/repository/skopeo/stable
- Harbor文档: https://goharbor.io/docs/
