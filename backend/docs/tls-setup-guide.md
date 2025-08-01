# TLS证书配置指南

本指南将帮助您为GeoML-Hub配置TLS证书，包括Docker远程连接和模型服务的HTTPS支持。

## 1. Docker远程连接TLS配置

### 1.1 生成Docker TLS证书

如果您的Docker守护进程在远程主机上运行，需要配置TLS证书来安全连接。

#### 在Docker主机上生成证书：

```bash
# 创建证书目录
mkdir -p /etc/docker/certs
cd /etc/docker/certs

# 生成CA私钥
openssl genrsa -aes256 -out ca-key.pem 4096

# 生成CA证书
openssl req -new -x509 -days 365 -key ca-key.pem -sha256 -out ca.pem

# 生成服务器私钥
openssl genrsa -out server-key.pem 4096

# 生成服务器证书签名请求
openssl req -subj "/CN=your-docker-host" -sha256 -new -key server-key.pem -out server.csr

# 配置扩展属性
echo subjectAltName = DNS:your-docker-host,IP:your-docker-host-ip,IP:127.0.0.1 >> extfile.cnf
echo extendedKeyUsage = serverAuth >> extfile.cnf

# 生成服务器证书
openssl x509 -req -days 365 -sha256 -in server.csr -CA ca.pem -CAkey ca-key.pem -out server-cert.pem -extfile extfile.cnf -CAcreateserial

# 生成客户端私钥
openssl genrsa -out key.pem 4096

# 生成客户端证书签名请求
openssl req -subj '/CN=client' -new -key key.pem -out client.csr

# 配置客户端扩展属性
echo extendedKeyUsage = clientAuth > extfile-client.cnf

# 生成客户端证书
openssl x509 -req -days 365 -sha256 -in client.csr -CA ca.pem -CAkey ca-key.pem -out cert.pem -extfile extfile-client.cnf -CAcreateserial

# 设置权限
chmod -v 400 ca-key.pem key.pem server-key.pem
chmod -v 444 ca.pem server-cert.pem cert.pem
```

#### 启动Docker守护进程（在Docker主机上）：

```bash
dockerd \
    --tlsverify \
    --tlscacert=ca.pem \
    --tlscert=server-cert.pem \
    --tlskey=server-key.pem \
    -H=0.0.0.0:2376
```

### 1.2 配置GeoML-Hub客户端

将客户端证书文件（ca.pem, cert.pem, key.pem）复制到GeoML-Hub后端服务器，然后在`.env`文件中配置：

```bash
# Docker远程连接配置
DOCKER_MS_HOST=tcp://your-docker-host:2376
DOCKER_MS_TLS_VERIFY=true
DOCKER_MS_CERT_PATH=/path/to/docker/certs  # 包含ca.pem, cert.pem, key.pem的目录
```

## 2. 模型服务HTTPS配置

### 2.1 生成服务TLS证书

为模型服务生成SSL证书：

```bash
# 创建服务证书目录
mkdir -p /etc/geoml/certs
cd /etc/geoml/certs

# 生成私钥
openssl genrsa -out service-key.pem 2048

# 生成证书签名请求
openssl req -new -key service-key.pem -out service.csr

# 生成自签名证书（用于测试）
openssl x509 -req -days 365 -in service.csr -signkey service-key.pem -out service-cert.pem

# 或者使用已有的CA签名证书（生产环境推荐）
# openssl x509 -req -days 365 -in service.csr -CA ca.pem -CAkey ca-key.pem -out service-cert.pem -CAcreateserial
```

### 2.2 配置服务TLS

在`.env`文件中配置：

```bash
# 模型服务TLS配置
SERVICE_TLS_ENABLED=true
SERVICE_TLS_CERT_PATH=/etc/geoml/certs/service-cert.pem
SERVICE_TLS_KEY_PATH=/etc/geoml/certs/service-key.pem
SERVICE_DOMAIN=your-domain.com  # 您的服务域名
```

## 3. 完整配置示例

```bash
# =============================================================================
# Docker Remote Connection with TLS
# =============================================================================
DOCKER_MS_HOST=tcp://192.168.1.100:2376
DOCKER_MS_TLS_VERIFY=true
DOCKER_MS_CERT_PATH=/etc/docker/certs
DOCKER_MS_TIMEOUT=60

# =============================================================================
# Model Service TLS Configuration
# =============================================================================
SERVICE_TLS_ENABLED=true
SERVICE_TLS_CERT_PATH=/etc/geoml/certs/service-cert.pem
SERVICE_TLS_KEY_PATH=/etc/geoml/certs/service-key.pem
SERVICE_DOMAIN=ml.yourdomain.com

# =============================================================================
# Service Configuration
# =============================================================================
SERVICE_PORT_START=7000
SERVICE_PORT_END=8000
DOCKER_IMAGE_NAME=geoml-service:latest
```

## 4. 验证配置

### 4.1 测试Docker连接

```bash
# 启动GeoML-Hub后端服务，检查日志
docker-compose logs backend | grep -i "docker"

# 应该看到类似以下成功消息：
# Docker TLS连接初始化成功，连接到: tcp://192.168.1.100:2376
# Docker客户端连接测试成功
```

### 4.2 测试模型服务

1. 创建一个模型服务
2. 启动服务
3. 检查生成的服务URL是否为HTTPS
4. 访问服务URL验证TLS证书

## 5. 故障排除

### 5.1 常见错误

1. **证书验证失败**
   - 检查证书文件路径是否正确
   - 确认证书文件权限（建议644）
   - 验证证书是否过期

2. **连接被拒绝**
   - 检查Docker主机防火墙设置
   - 确认Docker守护进程正在监听指定端口
   - 验证网络连通性

3. **TLS握手失败**
   - 检查客户端和服务器证书是否匹配
   - 确认CA证书正确

### 5.2 调试命令

```bash
# 测试Docker连接
openssl s_client -connect your-docker-host:2376 -cert cert.pem -key key.pem -CAfile ca.pem

# 检验证书信息
openssl x509 -in cert.pem -text -noout

# 验证证书链
openssl verify -CAfile ca.pem cert.pem
```

## 6. 安全建议

1. 使用强密码保护私钥
2. 定期更新证书
3. 限制证书文件访问权限
4. 使用受信任的CA签发证书（生产环境）
5. 启用防火墙规则限制访问
6. 定期备份证书文件

## 7. 生产环境部署

在生产环境中，建议：

1. 使用Let's Encrypt或商业CA签发的证书
2. 配置反向代理（如Nginx）处理TLS终端
3. 使用秘密管理系统（如Vault）存储证书
4. 设置证书自动更新机制
5. 启用证书透明度监控

## 8. 联系支持

如果遇到配置问题，请：

1. 检查日志文件获取详细错误信息
2. 验证配置文件语法
3. 参考Docker官方TLS文档
4. 联系系统管理员获取帮助