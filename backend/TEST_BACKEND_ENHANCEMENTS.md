# 后端补充功能测试指南

## ✅ 已完成的后端增强

### 1. 仓库详情API返回task_classifications

**端点**: `GET /api/repositories/{owner}/{repo_name}`

**修改文件**:
- `app/routers/repositories.py:280-292`

**新增返回字段**:
```json
{
  "id": 1,
  "name": "my-model",
  "owner": {...},
  "classification_path": ["Geosphere", "Geological Processes"],
  "task_classifications": [  // 新增字段
    {
      "id": 1,
      "name": "Recognition",
      "name_zh": "识别类",
      "description": "...",
      "sort_order": 1,
      "icon": "eye",
      "is_active": true
    }
  ],
  ...
}
```

**测试命令**:
```bash
# 获取仓库详情
curl http://localhost:8000/api/repositories/testuser/test-repo | jq '.task_classifications'

# 预期输出：
# [
#   {
#     "id": 1,
#     "name": "Recognition",
#     "name_zh": "识别类",
#     ...
#   }
# ]
```

---

### 2. Repository Schema新增字段

**修改文件**:
- `app/schemas/repository.py:5` - 导入TaskClassification
- `app/schemas/repository.py:66` - Repository类添加task_classifications字段
- `app/schemas/repository.py:97` - RepositoryListItem类添加task_classifications字段

**字段定义**:
```python
task_classifications: Optional[List[TaskClassification]] = []
```

**影响范围**:
- 所有返回Repository或RepositoryListItem的API
- 前端可以直接从仓库对象获取task_classifications

---

### 3. 仓库列表支持task分类过滤

**端点**: `GET /api/repositories?task_classification_id=1`

**修改文件**:
- `app/routers/repositories.py:73` - 添加task_classification_id参数
- `app/routers/repositories.py:149-155` - 添加过滤逻辑

**查询逻辑**:
```python
if task_classification_id:
    from app.models.repository import RepositoryTaskClassification
    task_subquery = select(RepositoryTaskClassification.repository_id).where(
        RepositoryTaskClassification.task_classification_id == task_classification_id
    )
    query = query.where(Repository.id.in_(task_subquery))
```

**测试命令**:
```bash
# 按task分类筛选仓库
curl "http://localhost:8000/api/repositories?task_classification_id=1&per_page=5" | jq '.items[].name'

# 预期输出：只返回有Recognition分类的仓库
```

---

## 🧪 完整测试流程

### 前置条件

1. 确保数据库已迁移：
```bash
cd /Users/liudichen/Documents/project/GeoML-hub/backend
alembic upgrade head
```

2. 确保task_classifications已导入：
```bash
python scripts/import_task_classifications.py
```

3. 后端服务运行中：
```bash
uvicorn app.main:app --reload
```

---

### 测试场景1：添加task分类后查看仓库详情

```bash
# 1. 创建测试仓库（假设已有testuser/test-repo）

# 2. 添加task分类
curl -X POST "http://localhost:8000/api/repositories/testuser/test-repo/task-classifications?task_classification_id=1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. 获取仓库详情
curl "http://localhost:8000/api/repositories/testuser/test-repo" | jq '.task_classifications'

# 预期结果：
# [
#   {
#     "id": 1,
#     "name": "Recognition",
#     "name_zh": "识别类",
#     "description": "Identification and classification of geographic features...",
#     "sort_order": 1,
#     "icon": "eye",
#     "is_active": true,
#     "created_at": "...",
#     "updated_at": "..."
#   }
# ]

# 4. 检查README是否自动同步
curl "http://localhost:8000/api/repositories/testuser/test-repo" | jq '.readme_content' | head -20

# 预期结果：README的YAML frontmatter包含task_classifications
# ---
# task_classifications:
#   - Recognition
# ---
```

---

### 测试场景2：按task分类筛选仓库列表

```bash
# 1. 为多个仓库添加不同的task分类
curl -X POST "http://localhost:8000/api/repositories/testuser/repo1/task-classifications?task_classification_id=1" \
  -H "Authorization: Bearer YOUR_TOKEN"

curl -X POST "http://localhost:8000/api/repositories/testuser/repo2/task-classifications?task_classification_id=2" \
  -H "Authorization: Bearer YOUR_TOKEN"

curl -X POST "http://localhost:8000/api/repositories/testuser/repo3/task-classifications?task_classification_id=1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. 筛选Recognition分类的仓库
curl "http://localhost:8000/api/repositories?task_classification_id=1" | jq '.items[] | {name, task_classifications}'

# 预期结果：只返回repo1和repo3

# 3. 筛选Monitoring分类的仓库
curl "http://localhost:8000/api/repositories?task_classification_id=2" | jq '.items[] | {name, task_classifications}'

# 预期结果：只返回repo2
```

---

### 测试场景3：移除task分类后查看仓库

```bash
# 1. 移除task分类
curl -X DELETE "http://localhost:8000/api/repositories/testuser/test-repo/task-classifications/1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. 查看仓库详情
curl "http://localhost:8000/api/repositories/testuser/test-repo" | jq '.task_classifications'

# 预期结果：空数组 []

# 3. 检查README是否自动更新
curl "http://localhost:8000/api/repositories/testuser/test-repo" | jq '.readme_content' | head -20

# 预期结果：README的task_classifications字段为空数组
# ---
# task_classifications: []
# ---
```

---

### 测试场景4：结合sphere分类和task分类筛选

```bash
# 1. 为仓库同时添加sphere和task分类
curl -X POST "http://localhost:8000/api/repositories/testuser/test-repo/classifications?classification_id=1" \
  -H "Authorization: Bearer YOUR_TOKEN"

curl -X POST "http://localhost:8000/api/repositories/testuser/test-repo/task-classifications?task_classification_id=1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. 只按sphere分类筛选
curl "http://localhost:8000/api/repositories?classification_id=1" | jq '.total'

# 3. 只按task分类筛选
curl "http://localhost:8000/api/repositories?task_classification_id=1" | jq '.total'

# 4. 同时按两种分类筛选
curl "http://localhost:8000/api/repositories?classification_id=1&task_classification_id=1" | jq '.total'

# 预期结果：第4个查询返回的数量 <= min(第2个, 第3个)
```

---

### 测试场景5：获取仓库的task分类列表

```bash
# 获取仓库的所有task分类
curl "http://localhost:8000/api/repositories/testuser/test-repo/task-classifications"

# 预期输出：
# {
#   "task_classifications": [
#     {
#       "id": 1,
#       "name": "Recognition",
#       "name_zh": "识别类",
#       ...
#     }
#   ]
# }
```

---

## 📊 数据验证

### 检查数据库

```sql
-- 查看仓库的task分类关联
SELECT
    r.name as repository_name,
    tc.name as task_classification,
    tc.name_zh as task_classification_zh
FROM repositories r
JOIN repository_task_classifications rtc ON r.id = rtc.repository_id
JOIN task_classifications tc ON rtc.task_classification_id = tc.id
WHERE r.name = 'test-repo';

-- 查看某个task分类下的所有仓库
SELECT
    r.name,
    r.full_name,
    tc.name as task_name
FROM repositories r
JOIN repository_task_classifications rtc ON r.id = rtc.repository_id
JOIN task_classifications tc ON rtc.task_classification_id = tc.id
WHERE tc.id = 1;
```

---

## ✅ 验收标准

所有功能正常工作的标志：

1. ✅ **仓库详情包含task_classifications字段**
   - GET /repositories/{owner}/{repo} 返回task_classifications数组
   - 数组包含完整的TaskClassification对象

2. ✅ **仓库列表支持task分类筛选**
   - GET /repositories?task_classification_id=1 只返回对应仓库
   - 筛选结果正确

3. ✅ **添加task分类自动同步README**
   - POST /repositories/{owner}/{repo}/task-classifications
   - README的YAML frontmatter自动更新
   - MinIO和数据库的README内容一致

4. ✅ **删除task分类自动同步README**
   - DELETE /repositories/{owner}/{repo}/task-classifications/{id}
   - README自动移除该task分类

5. ✅ **Schema正确返回**
   - Repository和RepositoryListItem都包含task_classifications字段
   - 前端可以直接使用

---

## 🔧 故障排查

### 问题1：task_classifications字段为空

**检查步骤**:
```bash
# 1. 确认仓库有task分类关联
curl "http://localhost:8000/api/repositories/testuser/test-repo/task-classifications"

# 2. 如果为空，手动添加
curl -X POST "http://localhost:8000/api/repositories/testuser/test-repo/task-classifications?task_classification_id=1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. 再次检查仓库详情
curl "http://localhost:8000/api/repositories/testuser/test-repo" | jq '.task_classifications'
```

### 问题2：过滤不返回结果

**检查步骤**:
```bash
# 1. 确认task_classification_id正确
curl "http://localhost:8000/api/task-classifications/"

# 2. 确认有仓库使用该分类
curl "http://localhost:8000/api/task-classifications/1/repositories"

# 3. 检查SQL查询
# 查看日志中的SQL语句是否包含task_classification_id条件
```

### 问题3：Schema验证错误

**可能原因**:
- TaskClassification导入失败
- Pydantic版本不兼容

**解决方案**:
```bash
# 检查import
python -c "from app.schemas.task_classification import TaskClassification; print('OK')"

# 重启后端服务
# uvicorn会自动重新加载schemas
```

---

## 📝 后续TODO（前端集成）

后端已准备好，前端需要：

1. **仓库详情页显示task分类**
   ```javascript
   const repo = await api.get(`/repositories/${owner}/${repo}`);
   // repo.task_classifications 数组可直接使用
   ```

2. **仓库设置页管理task分类**
   ```javascript
   // 添加
   await api.post(`/repositories/${owner}/${repo}/task-classifications`, {
     task_classification_id: 1
   });

   // 删除
   await api.delete(`/repositories/${owner}/${repo}/task-classifications/1`);
   ```

3. **首页按task分类筛选**
   ```javascript
   const repos = await api.get('/repositories', {
     params: { task_classification_id: 1 }
   });
   ```
