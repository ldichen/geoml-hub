# 数据清理工具

这里提供了几种清理images、model_services和Harbor数据的方法，用于重新测试自动服务名称生成功能。

⚠️ **警告：所有清理操作都是不可恢复的，请确认你真的需要清理数据！**

## 方法1：完整清理脚本（推荐）

使用Python脚本清理所有相关数据：

```bash
cd /Users/liudichen/Documents/project/GeoML-hub/backend
python cleanup_all_data.py
```

这个脚本会：
- 清理数据库中的所有相关表
- 清理Harbor中的所有镜像
- 清理mManager控制器中的容器
- 重置数据库序列

## 方法2：只清理数据库

如果你只需要清理数据库数据，可以直接执行SQL：

```bash
psql -h localhost -U your_username -d your_database -f quick_cleanup.sql
```

或者在数据库客户端中执行 `quick_cleanup.sql` 文件的内容。

## 方法3：只清理Harbor

如果你只需要清理Harbor中的镜像：

```bash
cd /Users/liudichen/Documents/project/GeoML-hub/backend
python harbor_cleanup.py
```

## 方法4：手动清理

### 清理数据库
```sql
-- 按顺序执行，注意外键约束
DELETE FROM service_health_checks;
DELETE FROM service_logs;
DELETE FROM service_instances;
DELETE FROM container_operations;
DELETE FROM container_registry;
DELETE FROM model_services;
DELETE FROM image_build_logs;
DELETE FROM images;

-- 重置序列
ALTER SEQUENCE images_id_seq RESTART WITH 1;
ALTER SEQUENCE model_services_id_seq RESTART WITH 1;
-- ... 其他序列
```

### 清理Harbor
使用Harbor Web UI或通过API删除所有镜像。

## 验证清理结果

清理完成后，可以通过以下SQL验证：

```sql
SELECT 'images' as table_name, COUNT(*) as remaining_records FROM images
UNION ALL
SELECT 'model_services', COUNT(*) FROM model_services
UNION ALL
SELECT 'service_instances', COUNT(*) FROM service_instances;
```

应该看到所有计数都是0。

## 重新测试

清理完成后，你可以：

1. **测试tar包上传创建服务**：
   ```bash
   curl -X POST "http://localhost:8000/api/services/create-with-tar" \
     -F "username=your_username" \
     -F "repo_name=your_repo" \
     -F "docker_tar=@your_image.tar" \
     -F "description=测试服务" \
     -H "Authorization: Bearer your_token"
   ```

2. **测试基于镜像创建服务**：
   ```bash
   curl -X POST "http://localhost:8000/api/images/{image_id}/services/create" \
     -F "description=测试服务" \
     -F "cpu_limit=0.5" \
     -F "memory_limit=512m" \
     -H "Authorization: Bearer your_token"
   ```

3. **验证自动生成的服务名称格式**：
   - 应该看到格式如：`redis-123-a1b2c3d4`
   - 其中 `redis` 是镜像名，`123` 是镜像ID，`a1b2c3d4` 是8位UUID

## 注意事项

- 清理前请确保备份重要数据
- 清理过程中不要进行其他操作
- 如果Harbor清理失败，可能需要手动清理
- 清理后需要重启应用以确保缓存清空

## 问题排查

如果清理过程中遇到问题：

1. **数据库连接问题**：检查数据库配置和连接
2. **Harbor连接问题**：检查Harbor配置和网络
3. **权限问题**：确保数据库用户有删除权限
4. **外键约束问题**：按照脚本顺序清理表

清理完成后，系统应该是干净的状态，可以重新测试自动服务名称生成功能。