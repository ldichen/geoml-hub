# Docker容器管理功能更新

## 概述

此次更新为GeoML-Hub添加了完整的Docker容器管理功能，允许用户上传Docker镜像并管理模型服务的文件更新。

## 功能特性

### 1. Docker镜像管理
- 支持用户上传完整的Docker镜像来创建模型服务
- 镜像必须包含标准文件结构：`gogogo.py`、`mc.json`、`model/`目录
- 支持可选的`examples/`示例数据目录上传

### 2. 容器文件更新
- 支持单文件更新：`gogogo.py`、`mc.json`
- 支持目录更新：`model/`、`examples/`（通过压缩包）
- 自动解压和嵌套目录检测
- 更新后自动重启容器

### 3. 环境验证
- 自动检查容器环境完整性
- 识别缺失的依赖和文件
- 标记有问题的容器状态

## 数据库模型更新

### ModelService表新增字段
```sql
-- Docker镜像名称
docker_image VARCHAR(500) COMMENT 'Docker镜像名称'

-- 健康状态
health_status VARCHAR(50) DEFAULT 'unknown' COMMENT '健康状态: healthy, unhealthy, unknown, timeout'

-- 错误信息
error_message TEXT COMMENT '错误信息'

-- 最后更新时间
last_updated TIMESTAMP WITH TIME ZONE DEFAULT now() COMMENT '最后更新时间'
```

## API端点

### 新增端点

#### 1. 文件更新
```
POST /api/services/{service_id}/files/update
```
- 支持多文件上传：`gogogo_file`, `mc_config_file`, `model_archive`, `examples_archive`
- 自动处理压缩包解压
- 重启容器并验证健康状态

#### 2. Docker镜像服务创建
```
POST /api/services/create-with-image
```
- 使用Docker镜像创建服务
- 支持可选的examples文件上传
- 自动配置容器环境

#### 3. 容器信息获取
```
GET /api/services/{service_id}/container-info
```
- 获取容器详细信息
- 包含健康状态和错误信息

#### 4. 环境验证
```
POST /api/services/{service_id}/validate-environment
```
- 验证容器环境完整性
- 检查必需文件和Python环境

## 前端组件

### 新增组件

#### 1. ServiceUpdateModal.svelte
- 文件更新界面
- 支持拖拽上传
- 文件格式和大小验证
- 实时更新状态反馈

#### 2. DockerServiceCreateModal.svelte
- Docker镜像服务创建界面
- 资源配置选择
- 示例数据上传
- 表单验证

## 服务层

### 新增服务

#### ContainerFileUpdateService
- 文件更新核心逻辑
- 压缩包处理
- 容器操作管理
- 健康检查集成

## 使用流程

### 1. 创建Docker服务
1. 用户上传Docker镜像
2. 配置服务参数（CPU、内存、优先级等）
3. 可选上传examples文件
4. 系统创建服务并验证环境

### 2. 更新服务文件
1. 用户选择要更新的文件类型
2. 上传对应文件（单文件或压缩包）
3. 系统验证并处理文件
4. 自动重启容器
5. 执行健康检查并反馈状态

### 3. 容器管理策略
- **重启策略**：文件更新后重启整个容器（推荐）
- **健康检查**：自动验证服务可用性
- **错误处理**：标记环境问题并提供详细错误信息

## 重要注意事项

### Docker镜像要求
```
/app/
├── gogogo.py      # 必需：服务启动脚本
├── mc.json        # 必需：配置文件
├── model/         # 必需：模型文件目录
└── examples/      # 可选：示例数据目录
```

### 支持的文件格式
- **Python文件**：`.py`
- **配置文件**：`.json`
- **压缩包**：`.zip`, `.tar`, `.tar.gz`, `.tgz`

### 文件大小限制
- **单文件**：最大10MB
- **模型压缩包**：最大1GB
- **示例数据**：最大100MB

## 安全考虑

### 文件验证
- Python文件语法检查
- JSON文件格式验证
- 压缩包安全解压
- 嵌套目录检测和处理

### 权限控制
- 用户只能操作自己的服务
- 容器隔离和资源限制
- 文件系统权限控制

## 向后兼容性

此更新保持向后兼容：
- 现有服务继续正常工作
- 旧的API端点仍然可用
- 数据库迁移不影响现有数据

## 故障排除

### 常见问题
1. **容器启动失败**：检查Docker镜像是否包含必需文件
2. **文件更新失败**：验证文件格式和大小限制
3. **健康检查失败**：检查Python环境和依赖

### 错误状态处理
- `health_status: "unhealthy"` - 环境有问题
- `error_message` - 具体错误描述
- 自动重试机制（根据错误类型）