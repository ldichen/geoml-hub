# 分类自动同步系统 - 方案A实现指南

## 🎯 核心理念

**数据库是数据源（Single Source of Truth），README是显示层**

- 数据库 → README：**自动同步**（强制）
- README → 数据库：**可选同步**（辅助）

## 🏗️ 系统架构

```
┌─────────────────┐
│   Web界面/API   │  用户通过界面管理分类
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  数据库（主数据源）│  repository_classifications
│                 │  repository_task_classifications
└────────┬────────┘
         │
         ▼ 自动触发
┌─────────────────┐
│ ClassificationMi│  批量更新README
│ grationService  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  README.md文件  │  显示最新分类信息
│  (MinIO + DB)   │
└─────────────────┘
```

## 📦 实现组件

### 1. ClassificationMigrationService

**位置**: `app/services/classification_migration_service.py`

**核心功能**:
- `sync_repository_readme(repository_id)` - 同步单个仓库的README
- `batch_sync_readmes_for_sphere_classification(classification_id)` - 批量同步sphere分类
- `batch_sync_readmes_for_task_classification(task_classification_id)` - 批量同步task分类

**工作流程**:
```python
# 1. 从数据库读取最新分类
sphere_classifications = await _get_repository_sphere_classifications(repo_id)
task_classifications = await _get_repository_task_classifications(repo_id)

# 2. 解析现有README
metadata, content = yaml_parser.extract_content(readme_content)

# 3. 更新元数据
metadata["classifications"] = sphere_classifications
metadata["task_classifications"] = task_classifications

# 4. 重新生成README
updated_readme = yaml_parser.create_frontmatter(metadata, content)

# 5. 保存到数据库和MinIO
repository.readme_content = updated_readme
await update_readme_in_minio(repository, updated_readme)
```

### 2. MetadataSyncService（已增强）

**位置**: `app/services/metadata_sync_service.py`

**新增功能**:
- 支持task_classifications字段
- `_get_repository_task_classifications()` - 获取task分类列表
- `_find_task_classification_by_name()` - 根据名称查找task分类
- `_sync_classifications()` - 同步sphere和task两种分类

**README → 数据库同步**:
```yaml
---
classifications:
  - Geosphere
  - Hydrosphere
task_classifications:
  - Recognition
  - Monitoring
---
```
↓ 解析并同步到数据库

## 🔌 API端点集成

### Sphere分类管理

```http
POST /api/repositories/{owner}/{repo}/classifications
Query: classification_id=1
```

**处理流程**:
```python
# 1. 添加分类到数据库
await repo_service.add_repository_classification(repo_id, classification_id)

# 2. 自动同步README
migration_service = ClassificationMigrationService(db)
await migration_service.sync_repository_readme(repo_id)
await db.commit()

# 3. 返回结果
return {"message": "分类添加成功并已同步至README"}
```

### Task分类管理

```http
POST /api/repositories/{owner}/{repo}/task-classifications
Query: task_classification_id=1

DELETE /api/repositories/{owner}/{repo}/task-classifications/{task_id}

GET /api/repositories/{owner}/{repo}/task-classifications
```

**同样会自动触发README同步**

## 📤 文件上传集成

### 分片上传完成时检测README

**位置**: `app/services/file_upload_service.py:236-264`

```python
# 如果上传的是README.md
if session.file_path.lower() == "readme.md":
    # 1. 从MinIO获取内容
    content = await minio_service.get_file_content(...)

    # 2. 更新仓库readme_content字段
    repository.readme_content = content.decode('utf-8')

    # 3. 同步YAML frontmatter到数据库
    metadata_sync = MetadataSyncService(db)
    await metadata_sync.sync_readme_to_repository(repository, readme_content)
```

## 📝 YAML Frontmatter格式

### 完整示例

```yaml
---
license: mit
tags:
  - pytorch
  - machine-learning
base_model: bert-base-uncased

# Sphere分类（地球科学圈层分类）
classifications:
  - Geosphere
  - Hydrosphere
  - Atmosphere

# Task分类（任务类型分类）
task_classifications:
  - Recognition
  - Monitoring
  - Simulation & Prediction

# 其他元数据
model_type: text-classification
language:
  - en
datasets:
  - imdb
---

# My Geoscience Model

This is a machine learning model for geoscience applications...
```

## 🔄 使用场景

### 场景1：用户通过Web界面添加分类

```
1. 用户点击"添加分类" → 选择"Geosphere"
2. 前端调用：POST /api/repositories/user/repo/classifications?classification_id=1
3. 后端自动：
   - 添加到repository_classifications表
   - 调用migration_service.sync_repository_readme()
   - 更新README的YAML部分
   - 保存到MinIO
4. README自动变为：
   ---
   classifications:
     - Geosphere
   ---
```

### 场景2：管理员重命名分类

```
1. 管理员修改分类：Geosphere → 地球圈
2. 调用：PUT /api/classifications/1 {"name": "地球圈"}
3. 后端：
   - 更新classifications表
   - 调用batch_sync_readmes_for_sphere_classification(1)
   - 自动更新所有使用该分类的仓库README
4. 所有156个仓库的README自动更新：
   classifications:
     - 地球圈  # 自动从"Geosphere"改为"地球圈"
```

### 场景3：用户直接上传README.md

```
1. 用户上传包含YAML的README.md：
   ---
   classifications:
     - Atmosphere
   task_classifications:
     - Monitoring
   ---
2. 分片上传完成后自动触发：
   - 解析YAML frontmatter
   - 查找"Atmosphere"和"Monitoring"分类
   - 更新repository_classifications和repository_task_classifications表
   - 数据库和README保持一致
```

### 场景4：用户直接编辑README

```
1. 用户在Web编辑器中修改README：
   PUT /api/repositories/user/repo/blob/README.md
   {
     "content": "---\nclassifications:\n  - Biosphere\n---\n..."
   }
2. 自动触发（repositories.py:997-1005）：
   - 更新repository.readme_content
   - 调用metadata_sync.sync_readme_to_repository()
   - 解析YAML并同步到数据库
```

## ⚙️ 关键配置

### README优先级规则

```python
# sync_readme_to_repository() - README → 数据库
# 只在以下情况触发：
1. 用户编辑README文件（PUT /blob/README.md）
2. 用户上传README文件（分片上传完成）
3. 手动调用 POST /metadata/{owner}/{repo}/parse-readme

# sync_repository_readme() - 数据库 → README
# 自动触发于：
1. 添加/删除sphere分类
2. 添加/删除task分类
3. 重命名分类（批量更新）
```

### 冲突处理

如果用户同时：
1. 在Web界面添加分类A
2. 直接编辑README添加分类B

**结果**:
- 数据库包含：A和B（README解析时会合并）
- README显示：A和B（自动同步会包含所有数据库中的分类）

## 🎯 优势总结

1. ✅ **用户无需手动修改README** - 通过界面管理，自动同步
2. ✅ **管理员可以自由重命名分类** - 自动批量更新所有README
3. ✅ **README始终保持最新** - 数据库修改后立即同步
4. ✅ **支持双分类系统** - Sphere和Task分类独立管理
5. ✅ **向下兼容** - 用户仍可直接编辑README，会同步到数据库
6. ✅ **Git友好** - README包含完整分类信息，可查看历史
7. ✅ **克隆友好** - 克隆仓库后README包含所有元数据

## 🚀 测试方法

### 1. 测试添加分类

```bash
# 添加sphere分类
curl -X POST "http://localhost:8000/api/repositories/testuser/test-repo/classifications?classification_id=1" \
  -H "Authorization: Bearer {token}"

# 检查README
curl "http://localhost:8000/api/repositories/testuser/test-repo" \
  | jq '.readme_content'

# 应该看到：
# ---
# classifications:
#   - Geosphere
# ---
```

### 2. 测试添加task分类

```bash
# 添加task分类
curl -X POST "http://localhost:8000/api/repositories/testuser/test-repo/task-classifications?task_classification_id=1" \
  -H "Authorization: Bearer {token}"

# 检查README
# 应该看到：
# ---
# classifications:
#   - Geosphere
# task_classifications:
#   - Recognition
# ---
```

### 3. 测试上传README

```bash
# 1. 初始化上传
curl -X POST "http://localhost:8000/api/repositories/testuser/test-repo/upload/init?file_name=README.md&file_size=500&file_path=README.md" \
  -H "Authorization: Bearer {token}"

# 2. 上传文件（包含YAML）
# ... 上传步骤 ...

# 3. 完成上传 - 应该自动解析YAML并同步到数据库
curl -X POST "http://localhost:8000/api/repositories/testuser/test-repo/upload/{session_id}/complete" \
  -H "Authorization: Bearer {token}"

# 4. 检查分类是否已同步到数据库
curl "http://localhost:8000/api/repositories/testuser/test-repo/classifications"
```

## 📋 TODO: 未来增强

- [ ] 添加分类重命名API端点（触发批量同步）
- [ ] 添加后台任务队列（大量仓库批量更新时异步处理）
- [ ] 添加同步失败重试机制
- [ ] 添加同步历史记录
- [ ] 前端显示同步状态（"正在同步README..."）
