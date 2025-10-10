# Task Classifications System Guide

## 🎯 Overview

The Task Classifications system provides a single-level categorization for repositories based on the **type of task** they perform, independent of the sphere-based classifications.

## 📊 Task Categories

| # | English Name | Chinese Name | Description |
|---|--------------|--------------|-------------|
| 1 | Recognition | 识别类 | Identification and classification of geographic features |
| 2 | Monitoring | 监测类 | Continuous observation and tracking of phenomena |
| 3 | Retrieval | 反演类 | Inverse estimation of physical parameters |
| 4 | Simulation & Prediction | 模拟预测类 | Numerical modeling and forecasting |
| 5 | Assessment | 评估类 | Evaluation and quantification of conditions |
| 6 | Risk & Early Warning | 风险防控类 | Hazard identification and warning systems |
| 7 | Decision Support | 决策支持类 | Planning and decision-making tools |
| 8 | Model Analysis | 模型解析类 | Model interpretation and explanation |

## 🚀 Installation Steps

### 1. Run Database Migration

```bash
cd /Users/liudichen/Documents/project/GeoML-hub/backend
alembic upgrade head
```

This creates the tables:
- `task_classifications` - Task categories
- `repository_task_classifications` - Repository-to-task associations

### 2. Import Task Classifications

```bash
python scripts/import_task_classifications.py
```

This imports all 8 task categories.

### 3. Verify Installation

Start the backend server:
```bash
uvicorn app.main:app --reload
```

Access API docs: http://localhost:8000/docs

Test the endpoint:
```bash
curl http://localhost:8000/api/task-classifications
```

## 📡 API Endpoints

### Get All Task Classifications
```http
GET /api/task-classifications?active_only=true
```

**Response:**
```json
{
  "task_classifications": [
    {
      "id": 1,
      "name": "Recognition",
      "name_zh": "识别类",
      "description": "...",
      "sort_order": 1,
      "icon": "eye",
      "is_active": true,
      "created_at": "2025-10-09T...",
      "updated_at": "2025-10-09T..."
    }
  ],
  "total": 8
}
```

### Get Single Task Classification
```http
GET /api/task-classifications/{id}
```

### Create Task Classification (Admin Only)
```http
POST /api/task-classifications
Content-Type: application/json

{
  "name": "New Task",
  "name_zh": "新任务",
  "description": "Description",
  "sort_order": 9,
  "is_active": true
}
```

### Update Task Classification (Admin Only)
```http
PUT /api/task-classifications/{id}
Content-Type: application/json

{
  "name_zh": "Updated Name"
}
```

### Delete Task Classification (Admin Only)
```http
DELETE /api/task-classifications/{id}
```

### Get Repositories by Task
```http
GET /api/task-classifications/{id}/repositories?skip=0&limit=50
```

## 🔗 Repository Integration

### Add Task to Repository

Use the `TaskClassificationService`:

```python
from app.services.task_classification_service import TaskClassificationService

service = TaskClassificationService(db)

# Add task classification to repository
await service.add_to_repository(
    repository_id=1,
    task_classification_id=4  # Simulation & Prediction
)
```

### Get Repository's Tasks

```python
tasks = await service.get_repository_tasks(repository_id=1)
# Returns: [TaskClassification, TaskClassification, ...]
```

### Remove Task from Repository

```python
success = await service.remove_from_repository(
    repository_id=1,
    task_classification_id=4
)
```

## 📐 Database Schema

### task_classifications Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String(100) | English name (unique) |
| name_zh | String(100) | Chinese name |
| description | String(500) | Description (optional) |
| sort_order | Integer | Display order |
| icon | String(50) | Icon identifier (optional) |
| is_active | Boolean | Active status |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Update timestamp |

### repository_task_classifications Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| repository_id | Integer | Foreign key → repositories.id |
| task_classification_id | Integer | Foreign key → task_classifications.id |
| created_at | DateTime | Association timestamp |

**Unique Constraint:** `(repository_id, task_classification_id)`

## 🎨 Frontend Usage Example

```javascript
// Fetch all task classifications
const response = await api.get('/api/task-classifications');
const tasks = response.data.task_classifications;

// Display in UI
tasks.forEach(task => {
  console.log(`${task.name} (${task.name_zh})`);
});

// Add task to repository
await api.post(`/api/repositories/${repoId}/task-classifications`, {
  task_classification_id: taskId
});
```

## 🔄 Dual Classification System

Repositories can now have **two independent classification dimensions**:

1. **Sphere Classifications** (2-level hierarchy):
   - Geosphere → Geomorphological Processes
   - Hydrosphere → Surface Hydrology
   - etc.

2. **Task Classifications** (single level):
   - Recognition
   - Monitoring
   - etc.

### Example Repository

```json
{
  "repository": "flood-prediction-model",
  "sphere_classifications": [
    {
      "level1": "Hydrosphere",
      "level2": "Surface Hydrology"
    }
  ],
  "task_classifications": [
    "Monitoring",
    "Simulation & Prediction",
    "Risk & Early Warning"
  ]
}
```

## 🛠️ Maintenance

### Update Task Descriptions

```python
from app.services.task_classification_service import TaskClassificationService

service = TaskClassificationService(db)

await service.update(
    classification_id=1,
    data=TaskClassificationUpdate(
        description="New description"
    )
)
```

### Deactivate Task

```python
await service.update(
    classification_id=1,
    data=TaskClassificationUpdate(is_active=False)
)
```

### Add New Task

```python
await service.create(
    TaskClassificationCreate(
        name="New Task Type",
        name_zh="新任务类型",
        description="Description",
        sort_order=9
    )
)
```

## ✅ Testing Checklist

- [ ] Database migration runs successfully
- [ ] Import script imports 8 classifications
- [ ] GET /api/task-classifications returns all tasks
- [ ] Can add task to repository
- [ ] Can remove task from repository
- [ ] Can get repositories by task
- [ ] Admin can create/update/delete tasks
- [ ] Non-admin cannot modify tasks

## 📚 Related Files

**Models:**
- `app/models/task_classification.py`
- `app/models/repository.py` (RepositoryTaskClassification)

**Schemas:**
- `app/schemas/task_classification.py`

**Services:**
- `app/services/task_classification_service.py`

**Routers:**
- `app/routers/task_classifications.py`

**Migrations:**
- `alembic/versions/db1f3d67777c_add_task_classifications.py`

**Scripts:**
- `scripts/import_task_classifications.py`
