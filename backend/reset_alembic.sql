-- 删除错误的版本记录
DELETE FROM alembic_version WHERE version_num = 'mmanager_001';

-- 插入正确的版本记录（如果需要）
-- INSERT INTO alembic_version (version_num) VALUES ('add_image_management_support');