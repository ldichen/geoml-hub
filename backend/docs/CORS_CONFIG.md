# CORS 配置指南

## 概述

CORS (Cross-Origin Resource Sharing) 配置根据部署环境的不同需要进行相应调整。本指南说明了在不同环境中如何正确配置 CORS 设置。

## 环境配置

### 1. 开发环境 (Development)

```env
# .env 文件
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
CORS_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_HEADERS=["Content-Type", "Authorization"]
```

**说明**:
- `http://localhost:5173` - SvelteKit 开发服务器默认端口
- `http://localhost:3000` - React/Next.js 开发服务器常用端口
- 允许所有必要的 HTTP 方法和头部

### 2. 测试环境 (Testing/Staging)

```env
# .env.testing 文件
CORS_ORIGINS=["https://test.geoml-hub.com","https://staging.geoml-hub.com"]
CORS_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_HEADERS=["Content-Type", "Authorization"]
```

**说明**:
- 仅允许测试域名的 HTTPS 访问
- 保持与生产环境相同的安全级别

### 3. 生产环境 (Production)

```env
# .env.production 文件
CORS_ORIGINS=["https://geoml-hub.com","https://www.geoml-hub.com"]
CORS_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_HEADERS=["Content-Type", "Authorization"]
```

**说明**:
- 仅允许生产域名的 HTTPS 访问
- 严格限制跨域访问来源

## 安全考虑

### ❌ 不要在生产环境中使用

```python
# 危险 - 允许所有来源
allow_origins=["*"]

# 危险 - 混合 HTTP 和 HTTPS
CORS_ORIGINS=["http://example.com","https://example.com"]
```

### ✅ 推荐的安全实践

1. **明确指定域名**: 不要使用通配符 `*`
2. **使用 HTTPS**: 生产环境必须使用 HTTPS
3. **最小权限原则**: 只允许必要的方法和头部
4. **环境隔离**: 不同环境使用不同的配置

## Docker 部署配置

### docker-compose.yml

```yaml
version: '3.8'
services:
  backend:
    build: .
    environment:
      - CORS_ORIGINS=["https://your-domain.com"]
      - CORS_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
      - CORS_HEADERS=["Content-Type", "Authorization"]
    ports:
      - "8000:8000"
```

### Kubernetes 配置

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
data:
  CORS_ORIGINS: '["https://your-domain.com"]'
  CORS_METHODS: '["GET", "POST", "PUT", "DELETE", "OPTIONS"]'
  CORS_HEADERS: '["Content-Type", "Authorization"]'
```

## 常见问题

### 1. 跨域错误

**错误信息**: `Access to fetch at 'http://localhost:8000/api/...' from origin 'http://localhost:5173' has been blocked by CORS policy`

**解决方案**:
- 确保 `CORS_ORIGINS` 包含前端地址
- 重启后端服务器
- 检查端口号是否正确

### 2. 认证问题

**错误信息**: `Cannot use credentials with "*"`

**解决方案**:
- 不要在 `allow_origins` 中使用 `["*"]`
- 明确指定允许的域名

### 3. 预检请求失败

**错误信息**: `OPTIONS` 请求失败

**解决方案**:
- 确保 `CORS_METHODS` 包含 `"OPTIONS"`
- 检查 `CORS_HEADERS` 是否包含所需头部

## 验证配置

### 测试 CORS 配置

```bash
# 测试预检请求
curl -H "Origin: http://localhost:5173" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:8000/api/auth/login

# 测试实际请求
curl -H "Origin: http://localhost:5173" \
     -H "Content-Type: application/json" \
     -X POST \
     -d '{"test": "data"}' \
     http://localhost:8000/api/auth/login
```

### 检查响应头

正确的 CORS 响应应该包含以下头部:

```
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

## 更新配置

修改 CORS 配置后，需要：

1. 更新 `.env` 文件
2. 重启后端服务器
3. 清除浏览器缓存
4. 测试跨域请求

## 监控和日志

可以通过以下方式监控 CORS 问题：

```python
# 在 main.py 中添加日志
import logging

logger = logging.getLogger(__name__)

@app.middleware("http")
async def cors_debug_middleware(request, call_next):
    origin = request.headers.get("origin")
    logger.info(f"Request from origin: {origin}")
    
    response = await call_next(request)
    
    if origin:
        logger.info(f"CORS headers: {response.headers}")
    
    return response
```

这样可以更好地调试 CORS 问题。