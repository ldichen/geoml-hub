-- 快速清理所有相关数据的SQL脚本
-- 警告：此脚本将删除所有images、model_services相关数据，不可恢复！

-- 1. 清理service相关表（注意顺序，先清理外键关联的表）
DELETE FROM service_health_checks;
DELETE FROM service_logs;
DELETE FROM service_instances;
DELETE FROM container_operations;
DELETE FROM container_registry;
DELETE FROM model_services;

-- 2. 清理image相关表
DELETE FROM image_build_logs;
DELETE FROM images;

-- 3. 重置序列（如果使用PostgreSQL）
ALTER SEQUENCE images_id_seq RESTART WITH 1;
ALTER SEQUENCE model_services_id_seq RESTART WITH 1;
ALTER SEQUENCE service_instances_id_seq RESTART WITH 1;
ALTER SEQUENCE service_logs_id_seq RESTART WITH 1;
ALTER SEQUENCE service_health_checks_id_seq RESTART WITH 1;
ALTER SEQUENCE container_registry_id_seq RESTART WITH 1;
ALTER SEQUENCE container_operations_id_seq RESTART WITH 1;
ALTER SEQUENCE image_build_logs_id_seq RESTART WITH 1;

-- 4. 可选：清理mManager控制器记录（如果需要重置控制器状态）
-- DELETE FROM mmanager_controllers;
-- ALTER SEQUENCE mmanager_controllers_id_seq RESTART WITH 1;

-- 查看清理结果
SELECT 'images' as table_name, COUNT(*) as remaining_records FROM images
UNION ALL
SELECT 'model_services', COUNT(*) FROM model_services
UNION ALL
SELECT 'service_instances', COUNT(*) FROM service_instances
UNION ALL
SELECT 'service_logs', COUNT(*) FROM service_logs
UNION ALL
SELECT 'service_health_checks', COUNT(*) FROM service_health_checks
UNION ALL
SELECT 'container_registry', COUNT(*) FROM container_registry
UNION ALL
SELECT 'container_operations', COUNT(*) FROM container_operations
UNION ALL
SELECT 'image_build_logs', COUNT(*) FROM image_build_logs;