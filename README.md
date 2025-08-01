# 🌍 GeoML-Hub v2.0

> **第一个专为地理科学设计的机器学习模型库 - 重构升级版**

GeoML-Hub v2.0 是一个全面重构的地理科学机器学习模型仓库平台，采用类似 Hugging Face 的架构设计，为地理空间 AI 模型的发现、共享、管理和部署提供现代化的用户体验。

## README update rule

1. 保持设计完整性
   - ✅ 应该做: 保留所有已规划的功能、API、前端页面和组件设计
   - ❌ 不应该做: 删除未实现但已设计的功能
2. 准确标注实现状态
   - ✅ 已实现 - 代码已写好、测试通过、可以使用
   - 🔄 部分实现 - 核心功能完成，但还需完善
   - ⚠️ 待实现 - 已设计但未开始编码
3. 实际文件与文档对应
   - 比如，如果创建了 file_version.py 包含多个模型 → 在文档中说明包含的具体内容
   - 比如，如果创建了 file_editor.py 实现了部分 API → 只标注实际实现的 API 为已完成
   - 如果合并了多个服务到一个文件 → 在文档中明确说明合并情况，并对该文件做一定程度上的改名。
4. 更新范围界定
   - 项目结构: 根据实际创建的文件更新，但保留设计中的文件结构
   - 数据库: 添加实际创建的表，更新表的结构，保留规划中的表
   - API 接口: 标注实际实现的接口状态，保留设计中的接口
   - 前端页面和组件：标注已经完成的页面和组件，以及完成的对应的 API。
5. 命名准确性
   - 文件名应该反映实际内容，如 file_version.py 实际包含版本、会话、权限、模板等
   - 可以重命名为更准确的名称，或在描述中详细说明包含内容

### 🎯 总结

README 是系统的设计蓝图和实现进度的结合体，应该既展示完整设计，又准确反映当前进度。

## 📁 项目结构

```
GeoML-hub/
├── 📁 backend/                    # FastAPI 后端应用 (✅ 已实现)
│   ├── 📁 app/
│   │   ├── 📁 models/             # SQLAlchemy 数据模型 (✅ 已实现)
│   │   │   ├── user.py               # 用户模型 (✅ 已实现)
│   │   │   ├── repository.py         # 仓库模型 (✅ 已实现)
│   │   │   ├── file_storage.py       # 文件存储模型 (✅ 已实现)
│   │   │   ├── classification.py     # 分类系统模型 (✅ 已实现)
│   │   │   ├── file_editor.py        # 文件编辑器模型 (✅ 已实现)
│   │   │   │                        # 包含: FileVersion, FileEditSession, FileEditPermission, FileTemplate, FileDraft
│   │   │   ├── personal_files.py     # 个人文件管理模型 (✅ 已实现)
│   │   │   │                        # 包含: PersonalFile, PersonalFolder
│   │   │   └── service.py            # 模型服务管理模型 (✅ 已实现)
│   │   │   │                        # 包含: ModelService, ServiceInstance, ServiceLog, ServiceHealthCheck
│   │   ├── 📁 schemas/            # Pydantic 验证模式 (✅ 已实现)
│   │   │   ├── user.py               # 用户相关模式 (✅ 已实现)
│   │   │   ├── repository.py         # 仓库相关模式 (✅ 已实现)
│   │   │   ├── file_storage.py       # 文件存储模式 (✅ 已实现)
│   │   │   ├── classification.py     # 分类模式 (✅ 已实现)
│   │   │   ├── metadata.py           # 元数据管理模式 (✅ 已实现)
│   │   │   ├── file_editor.py        # 文件编辑器模式 (✅ 已实现)
│   │   │   │                        # 包含: FileVersionCreate, FileEditSessionCreate, FilePermissionCreate, FileTemplateCreate, FileDraftCreate 等
│   │   │   ├── personal_files.py     # 个人文件管理模式 (✅ 已实现)
│   │   │   │                        # 包含: PersonalFileBase, PersonalFolderBase, CreateFolderRequest, UpdateFolderRequest 等
│   │   │   ├── service.py            # 模型服务管理模式 (✅ 已实现)
│   │   │   │                        # 包含: ServiceCreate, ServiceUpdate, ServiceResponse, ServiceStatus, ServiceStartRequest, ServiceStopRequest, BatchServiceRequest 等
│   │   │   └── auth.py               # 认证模式 (✅ 已实现)
│   │   ├── 📁 routers/            # API 路由 (✅ 已实现)
│   │   │   ├── auth.py               # 认证API (✅ 已实现)
│   │   │   ├── users.py              # 用户API (✅ 已实现)
│   │   │   ├── repositories.py       # 仓库API (✅ 已实现)
│   │   │   ├── classifications.py    # 分类API (✅ 已实现)
│   │   │   ├── search.py             # 搜索API (✅ 已实现)
│   │   │   ├── files.py              # 文件管理API (✅ 已实现)
│   │   │   ├── metadata.py           # 元数据管理API (✅ 已实现)
│   │   │   ├── discover.py           # 发现功能API (✅ 已实现)
│   │   │   ├── system.py             # 系统配置API (✅ 已实现)
│   │   │   ├── admin.py              # 管理API (✅ 已实现)
│   │   │   ├── file_editor.py        # 文件编辑器API (✅ 已实现)
│   │   │   │                        # 包含: 版本管理、编辑会话、权限管理、草稿管理、模板管理 API
│   │   │   │                        # file_templates.py 已整合到 file_editor.py
│   │   │   ├── personal_files.py     # 个人文件管理API (✅ 已实现)
│   │   │   │                        # 包含: 个人文件上传、下载、删除、文件夹管理 API
│   │   │   └── services.py           # 模型服务管理API (✅ 已实现)
│   │   │   │                        # 包含: 服务CRUD、生命周期控制、健康检查、批量操作、监控统计 API
│   │   ├── 📁 services/           # 业务逻辑层 (✅ 已实现)
│   │   │   ├── auth_service.py       # 认证服务集成 (✅ 已实现)
│   │   │   ├── repository_service.py # 仓库管理服务 (✅ 已实现)
│   │   │   ├── user_service.py       # 用户管理服务 (✅ 已实现)
│   │   │   ├── minio_service.py      # MinIO 文件存储服务 (✅ 已实现)
│   │   │   ├── file_upload_service.py # 文件上传服务 (✅ 已实现)
│   │   │   ├── file_editor_service.py # 文件编辑服务 (✅ 已实现)
│   │   │   │                        # 包含: FileVersionService, FileEditSessionService, FilePermissionService, FileDraftService
│   │   │   │                        # draft_service.py 已整合到 file_editor_service.py
│   │   │   │                        # file_template_service.py 已整合到 file_editor_service.py
│   │   │   │                        # collaboration_service.py 已整合到 file_editor_service.py
│   │   │   ├── personal_files_service.py # 个人文件管理服务 (✅ 已实现)
│   │   │   │                        # 包含: 个人文件上传、下载、删除、文件夹管理服务
│   │   │   ├── metadata_service.py    # 元数据管理服务 (✅ 已实现)
│   │   │   ├── model_service.py      # 模型服务管理 (✅ 已实现)
│   │   │   │                        # 包含: 容器编排、资源管理、健康检查、自动清理、智能重试、批量操作
│   │   │   ├── service_scheduler.py  # 服务调度器 (✅ 已实现)
│   │   │   │                        # 包含: 定期健康检查、空闲清理、资源监控、失败重试循环
│   │   │   └── classification.py     # 分类服务 (✅ 已实现)
│   │   ├── 📁 utils/              # 工具函数 (✅ 已实现)
│   │   │   ├── yaml_parser.py        # YAML frontmatter 解析 (✅ 已实现)
│   │   │   └── resource_manager.py   # 资源管理工具 (✅ 已实现)
│   │   │       │                    # 包含: 端口分配、资源验证、系统监控、配额管理
│   │   ├── 📁 dependencies/       # 依赖注入 (✅ 已实现)
│   │   │   └── auth.py               # 认证依赖 (✅ 已实现)
│   │   ├── 📁 middleware/         # 中间件 (✅ 已实现)
│   │   │   └── error_handler.py      # 错误处理 (✅ 已实现)
│   │   ├── 📄 main.py             # 应用入口 (✅ 已实现)
│   │   ├── 📄 config.py           # 配置管理 (✅ 已实现)
│   │   └── 📄 database.py         # 数据库配置 (✅ 已实现)
│   ├── 📁 alembic/                # 数据库迁移 (✅ 已实现)
│   │   ├── 📁 versions/           # 迁移版本文件 (✅ 已实现)
│   │   └── 📄 env.py              # 迁移环境配置 (✅ 已实现)
│   ├── 📁 scripts/                # 初始化脚本 (✅ 已实现)
│   │   ├── init_classifications.py   # 分类初始化 (✅ 已实现)
│   │   └── create_admin_user.py      # 管理员创建 (✅ 已实现)
│   ├── 📄 package.json            # Node.js 配置 (✅ 已实现)
│   ├── 📄 package-lock.json       # 依赖锁定文件 (✅ 已实现)
│   ├── 📄 Dockerfile              # 容器构建配置 (✅ 已实现)
│   └── 📄 requirements.txt        # Python 依赖 (✅ 已实现)
├── 📁 frontend/                   # SvelteKit 前端应用 (🔄 部分实现)
│   ├── 📁 src/
│   │   ├── 📁 routes/             # 页面路由 (🔄 部分实现)
│   │   │   ├── 📄 +page.svelte        # 主页 (✅ 已实现)
│   │   │   ├── 📄 +layout.svelte      # 布局文件 (✅ 已实现)
│   │   │   ├── 📄 +layout.js          # 布局逻辑 (✅ 已实现)
│   │   │   ├── 📁 [username]/         # 用户空间 (🔄 部分实现)
│   │   │   │   ├── 📄 +page.svelte    # 用户主页 (✅ 已实现)
│   │   │   │   └── 📁 [repository]/   # 仓库页面 (🔄 部分实现)
│   │   │   │       ├── 📄 +page.svelte    # 仓库主页 (✅ 已实现)
│   │   │   │       ├── 📁 edit/           # 文件编辑 (✅ 已实现)
│   │   │   │       │   └── 📁 [...file_path]/ # 文件编辑页面 (✅ 已实现)
│   │   │   │       │       └── 📄 +page.svelte # 文件编辑器页面 (✅ 已实现)
│   │   │   │       ├── 📁 blob/           # 文件查看 (✅ 已实现)
│   │   │   │       │   └── 📁 [...file_path]/ # 文件查看页面 (✅ 已实现)
│   │   │   │       │       └── 📄 +page.svelte # 文件查看页面 (✅ 已实现)
│   │   │   │       ├── 📁 commits/        # 提交历史 (✅ 已实现)
│   │   │   │       │   └── 📄 +page.svelte    # 提交历史页面 (✅ 已实现)
│   │   │   │       ├── 📁 drafts/         # 草稿管理 (✅ 已实现)
│   │   │   │       │   └── 📄 +page.svelte    # 草稿列表页面 (✅ 已实现)
│   │   │   │       ├── 📁 services/       # 模型服务管理 (⚠️ 待实现)
│   │   │   │       │   ├── 📄 +page.svelte    # 服务列表页面 (⚠️ 待实现)
│   │   │   │       │   ├── 📁 create/         # 创建服务 (⚠️ 待实现)
│   │   │   │       │   │   └── 📄 +page.svelte # 创建服务页面 (⚠️ 待实现)
│   │   │   │       │   └── 📁 [service_id]/   # 服务详情 (⚠️ 待实现)
│   │   │   │       │       ├── 📄 +page.svelte    # 服务详情页面 (⚠️ 待实现)
│   │   │   │       │       ├── 📁 logs/           # 服务日志 (⚠️ 待实现)
│   │   │   │       │       │   └── 📄 +page.svelte # 日志查看页面 (⚠️ 待实现)
│   │   │   │       │       └── 📁 metrics/        # 服务监控 (⚠️ 待实现)
│   │   │   │       │           └── 📄 +page.svelte # 监控页面 (⚠️ 待实现)
│   │   │   │       └── 📁 upload/         # 文件上传 (✅ 已实现)
│   │   │   │           └── 📄 +page.svelte    # 文件上传页面 (✅ 已实现)
│   │   │   ├── 📁 login/              # 登录页面 (✅ 已实现)
│   │   │   │   └── 📄 +page.svelte    # 登录组件 (✅ 已实现)
│   │   │   ├── 📁 register/           # 注册页面 (✅ 已实现)
│   │   │   │   └── 📄 +page.svelte    # 注册组件 (✅ 已实现)
│   │   │   ├── 📁 new/                # 新建仓库 (✅ 已实现)
│   │   │   │   └── 📄 +page.svelte    # 新建仓库组件 (✅ 已实现)
│   │   │   ├── 📁 search/             # 搜索页面 (✅ 已实现)
│   │   │   │   └── 📄 +page.svelte    # 搜索组件 (✅ 已实现)
│   │   │   ├── 📁 trending/           # 趋势页面 (✅ 已实现)
│   │   │   │   └── 📄 +page.svelte    # 趋势组件 (✅ 已实现)
│   │   │   └── 📁 admin/              # 管理员控制台 (✅ 已实现)
│   │   │       ├── 📄 +page.svelte        # 管理员入口页面 (✅ 已实现)
│   │   │       ├── 📄 +layout.svelte      # 管理员布局 (✅ 已实现)
│   │   │       ├── 📁 dashboard/          # 管理员仪表板 (✅ 已实现)
│   │   │       │   └── 📄 +page.svelte    # 仪表板页面 (✅ 已实现)
│   │   │       ├── 📁 users/              # 用户管理 (✅ 已实现)
│   │   │       │   └── 📄 +page.svelte    # 用户管理页面 (✅ 已实现)
│   │   │       ├── 📁 repositories/       # 仓库管理 (✅ 已实现)
│   │   │       │   └── 📄 +page.svelte    # 仓库管理页面 (✅ 已实现)
│   │   │       ├── 📁 storage/            # 存储管理 (✅ 已实现)
│   │   │       │   └── 📄 +page.svelte    # 存储管理页面 (✅ 已实现)
│   │   │       ├── 📁 system/             # 系统监控 (✅ 已实现)
│   │   │       │   └── 📄 +page.svelte    # 系统监控页面 (✅ 已实现)
│   │   │       └── 📁 settings/           # 设置管理 (✅ 已实现)
│   │   │           └── 📄 +page.svelte    # 设置管理页面 (✅ 已实现)
│   │   └── 📁 lib/
│   │       ├── 📁 components/     # 可复用组件 (✅ 已实现)
│   │       │   ├── ActivityFeed.svelte       # 活动动态 (✅ 已实现)
│   │       │   ├── CategoryFilter.svelte     # 分类筛选器 (✅ 已实现)
│   │       │   ├── ClassificationFilter.svelte # 分类筛选器 (✅ 已实现)
│   │       │   ├── ClassificationSelector.svelte # 分类选择器 (✅ 已实现)
│   │       │   ├── CommentSection.svelte     # 评论区 (✅ 已实现)
│   │       │   ├── FileDropZone.svelte       # 文件拖放区 (✅ 已实现)
│   │       │   ├── FileManager.svelte        # 文件管理器 (✅ 已实现)
│   │       │   ├── FileTree.svelte          # 文件浏览器 (✅ 已实现)
│   │       │   ├── FileUpload.svelte        # 文件上传 (✅ 已实现)
│   │       │   ├── Footer.svelte            # 页脚 (✅ 已实现)
│   │       │   ├── Header.svelte            # 页头 (✅ 已实现)
│   │       │   ├── Loading.svelte           # 加载组件 (✅ 已实现)
│   │       │   ├── ModelCard.svelte         # 模型卡片 (✅ 已实现)
│   │       │   ├── NotificationCenter.svelte # 通知中心 (✅ 已实现)
│   │       │   ├── NotificationTrigger.svelte # 通知触发器 (✅ 已实现)
│   │       │   ├── Pagination.svelte        # 分页组件 (✅ 已实现)
│   │       │   ├── PersonalFileManager.svelte # 个人文件管理器 (✅ 已实现)
│   │       │   ├── PersonalFileUpload.svelte # 个人文件上传 (✅ 已实现)
│   │       │   ├── ReadmeViewer.svelte      # README查看器 (✅ 已实现)
│   │       │   ├── RepositoryCard.svelte    # 仓库卡片 (✅ 已实现)
│   │       │   ├── RepositoryHeader.svelte  # 仓库头部 (✅ 已实现)
│   │       │   ├── RepositoryStats.svelte   # 仓库统计 (✅ 已实现)
│   │       │   ├── RepositoryTabs.svelte    # 仓库选项卡 (✅ 已实现)
│   │       │   ├── SearchBar.svelte         # 搜索栏 (✅ 已实现)
│   │       │   ├── ServiceCard.svelte       # 服务卡片 (✅ 已实现)
│   │       │   ├── SocialButton.svelte      # 社交按钮 (✅ 已实现)
│   │       │   ├── StyleGuide.svelte        # 样式指南 (✅ 已实现)
│   │       │   ├── ToastContainer.svelte    # 提示容器 (✅ 已实现)
│   │       │   ├── UserAvatar.svelte        # 用户头像 (✅ 已实现)
│   │       │   ├── UserProfile.svelte       # 用户资料 (✅ 已实现)
│   │       │   ├── YAMLMetadataEditor.svelte # YAML编辑器 (✅ 已实现)
│   │       │   ├── 📁 admin/               # 管理员组件 (✅ 已实现)
│   │       │   │   └── (管理员相关组件)        # 包含仪表板、用户管理等组件 (✅ 已实现)
│   │       │   ├── 📁 collaboration/       # 协作组件 (✅ 已实现)
│   │       │   │   └── (协作相关组件)          # 包含协作编辑、会话管理等 (✅ 已实现)
│   │       │   ├── 📁 draft/               # 草稿管理组件 (✅ 已实现)
│   │       │   │   └── (草稿相关组件)          # 包含草稿管理、自动保存等 (✅ 已实现)
│   │       │   ├── 📁 editor/              # 文件编辑器组件 (✅ 已实现)
│   │       │   │   └── (编辑器相关组件)        # 包含编辑器、工具栏、状态栏等 (✅ 已实现)
│   │       │   ├── 📁 ui/                  # 基础UI组件 (✅ 已实现)
│   │       │   │   └── (基础UI组件)           # 包含按钮、输入框、模态框等 (✅ 已实现)
│   │       │   └── 📁 version/             # 版本控制组件 (✅ 已实现)
│   │       │       └── (版本控制相关组件)      # 包含版本历史、差异查看等 (✅ 已实现)
│   │       ├── 📁 utils/          # 工具函数 (✅ 已实现)
│   │       │   ├── accessibility.js       # 无障碍工具 (✅ 已实现)
│   │       │   ├── api.js                 # API 客户端 (✅ 已实现)
│   │       │   ├── auth.js                # 认证工具 (✅ 已实现)
│   │       │   ├── constants.js           # 常量定义 (✅ 已实现)
│   │       │   ├── form-validation.js     # 表单验证 (✅ 已实现)
│   │       │   └── toast.js               # 提示工具 (✅ 已实现)
│   │       ├── 📁 config/         # 配置文件 (✅ 已实现)
│   │       ├── 📁 i18n/           # 国际化文件 (✅ 已实现)
│   │       ├── 📁 stores/         # 状态管理 (✅ 已实现)
│   │       ├── 📁 styles/         # 样式文件 (✅ 已实现)
│   │       └── 📁 types/          # 类型定义 (✅ 已实现)
│   │       ├── 📁 i18n/           # 国际化 (✅ 已实现)
│   │       │   └── 📁 locales/        # 语言包 (✅ 已实现)
│   │       ├── 📁 styles/         # 样式文件 (✅ 已实现)
│   │       │   ├── editor.css             # 编辑器样式 (⚠️ 待实现)
│   │       │   ├── codemirror-themes.css  # CodeMirror 主题 (⚠️ 待实现)
│   │       │   ├── diff-viewer.css        # 差异查看器样式 (⚠️ 待实现)
│   │       │   └── file-manager.css       # 文件管理器样式 (⚠️ 待实现)
│   │       └── 📁 types/          # TypeScript 类型 (✅ 已实现)
│   │           ├── editor.ts              # 编辑器类型 (⚠️ 待实现)
│   │           ├── version.ts             # 版本类型 (⚠️ 待实现)
│   │           ├── session.ts             # 会话类型 (⚠️ 待实现)
│   │           ├── draft.ts               # 草稿类型 (⚠️ 待实现)
│   │           ├── template.ts            # 模板类型 (⚠️ 待实现)
│   │           └── collaboration.ts       # 协作类型 (⚠️ 待实现)
│   ├── 📁 static/                 # 静态文件 (✅ 已实现)
│   ├── 📄 app.html                # HTML模板 (✅ 已实现)
│   ├── 📄 app.css                 # 全局样式 (✅ 已实现)
│   ├── 📄 package.json            # Node.js 依赖 (✅ 已实现)
│   ├── 📄 tailwind.config.js      # 样式配置 (✅ 已实现)
│   ├── 📄 svelte.config.js        # Svelte 配置 (✅ 已实现)
│   ├── 📄 tsconfig.json           # TypeScript 配置 (✅ 已实现)
│   └── 📄 vite.config.js          # Vite 配置 (✅ 已实现)
├── 📄 docker-compose.yml          # 开发环境配置 (✅ 已实现)
├── 📄 docker-compose.prod.yml     # 生产环境配置 (✅ 已实现)
├── 📄 CLAUDE.md                  # AI 开发指南 (✅ 已实现)
├── 📄 README.md                  # 项目文档 (✅ 已实现)
└── 📄 DEPLOYMENT.md              # 部署文档 (✅ 已实现)
```

## 🔗 系统关系架构 v2.0

### 核心实体关系

```mermaid
erDiagram
    USER_PROFILES ||--o{ MODEL_REPOSITORIES : owns
    USER_PROFILES ||--o{ USER_FOLLOWS : follows
    USER_PROFILES ||--o{ REPOSITORY_STARS : stars
    USER_PROFILES ||--|| USER_STORAGE : has

    MODEL_REPOSITORIES ||--o{ REPOSITORY_FILES : contains
    MODEL_REPOSITORIES ||--o{ MODEL_CLASSIFICATIONS : categorized_by
    MODEL_REPOSITORIES ||--o{ REPOSITORY_STARS : receives_stars
    MODEL_REPOSITORIES ||--o{ REPOSITORY_VIEWS : receives_views

    CLASSIFICATIONS ||--o{ MODEL_CLASSIFICATIONS : used_in
    CLASSIFICATIONS ||--o{ CLASSIFICATIONS : parent_child

    REPOSITORY_FILES ||--o{ FILE_DOWNLOADS : downloaded
    REPOSITORY_FILES ||--|| FILE_UPLOAD_SESSIONS : uploaded_via
```

### 分层架构设计

#### 第一层：用户身份层

```
👤 外部认证服务 (JWT Token + 用户信息同步)
    ↓
👥 用户资料管理 (user_profiles)
    ↓
📁 用户个人空间 (/{username} 命名空间)
```

#### 第二层：仓库管理层

```
📁 用户空间 (所有权关系)
    ↓
📦 模型仓库 (model_repositories)
    ├── 📝 README.md → 🔧 YAML元数据解析
    ├── 📄 仓库文件 (repository_files)
    ├── 🗂️ 分类标签 (model_classifications)
    └── 📈 社交统计 (stars, views, downloads)
```

#### 第三层：内容组织层

```
📦 仓库内容
    ├── 📁 文件管理 → 💾 MinIO对象存储
    ├── 🏷️ 智能分类 → 📊 三级分类体系
    ├── 👥 社区功能 → ⭐ 收藏、关注、统计
    └── 🔍 搜索发现 → 🎯 多维度筛选
```

## 🗄️ 数据库架构 v2.0

### 核心表结构 (✅ 已实现)

```sql
-- 用户表 (✅ 已实现)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,                     -- 内部用户ID
    external_user_id VARCHAR(255) NOT NULL UNIQUE, -- 外部认证系统用户ID
    username VARCHAR(100) NOT NULL UNIQUE,     -- 用户名 (唯一)
    email VARCHAR(255) NOT NULL UNIQUE,        -- 邮箱
    full_name VARCHAR(255),                     -- 全名
    avatar_url VARCHAR(500),                    -- 头像URL
    bio TEXT,                                   -- 个人简介
    website VARCHAR(500),                       -- 个人网站
    location VARCHAR(255),                      -- 地理位置

    -- 社交统计
    followers_count INTEGER DEFAULT 0,         -- 粉丝数
    following_count INTEGER DEFAULT 0,         -- 关注数
    public_repos_count INTEGER DEFAULT 0,      -- 公开仓库数

    -- 存储配额
    storage_quota BIGINT DEFAULT 5368709120,   -- 5GB 默认配额
    storage_used BIGINT DEFAULT 0,             -- 已使用存储

    -- 账户状态
    is_active BOOLEAN DEFAULT TRUE,            -- 是否激活
    is_verified BOOLEAN DEFAULT FALSE,         -- 是否验证
    is_admin BOOLEAN DEFAULT FALSE,            -- 是否管理员

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 用户存储统计表 (✅ 已实现)
CREATE TABLE user_storage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    total_files INTEGER DEFAULT 0,                 -- 总文件数
    total_size BIGINT DEFAULT 0,                   -- 总大小

    -- 按文件类型统计
    model_files_count INTEGER DEFAULT 0,
    model_files_size BIGINT DEFAULT 0,
    dataset_files_count INTEGER DEFAULT 0,
    dataset_files_size BIGINT DEFAULT 0,
    image_files_count INTEGER DEFAULT 0,
    image_files_size BIGINT DEFAULT 0,
    document_files_count INTEGER DEFAULT 0,
    document_files_size BIGINT DEFAULT 0,
    other_files_count INTEGER DEFAULT 0,
    other_files_size BIGINT DEFAULT 0,

    last_calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 个人文件表 (✅ 已实现)
CREATE TABLE personal_files (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,                    -- 文件名
    original_filename VARCHAR(255) NOT NULL,          -- 原始文件名
    file_path VARCHAR(1000) NOT NULL,                 -- 文件在个人空间中的路径
    file_size BIGINT NOT NULL DEFAULT 0,              -- 文件大小
    file_type VARCHAR(100),                           -- 文件类型
    mime_type VARCHAR(200),                           -- MIME类型
    file_hash VARCHAR(128),                           -- 文件哈希

    -- MinIO存储信息
    minio_bucket VARCHAR(255) NOT NULL,
    minio_object_key VARCHAR(1000) NOT NULL,

    -- 元数据
    description TEXT,                                  -- 文件描述
    tags TEXT,                                        -- 标签（逗号分隔）
    is_public BOOLEAN DEFAULT FALSE,                  -- 是否公开
    is_deleted BOOLEAN DEFAULT FALSE,                 -- 是否删除
    upload_status VARCHAR(20) DEFAULT 'completed',    -- 上传状态

    -- 统计信息
    download_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(user_id, file_path)
);

-- 个人文件夹表 (✅ 已实现)
CREATE TABLE personal_folders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,                       -- 文件夹名
    path VARCHAR(1000) NOT NULL,                      -- 文件夹路径
    parent_id INTEGER REFERENCES personal_folders(id) ON DELETE CASCADE,
    description TEXT,                                  -- 描述
    color VARCHAR(7),                                 -- 文件夹颜色
    is_public BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id, path)
);

-- 个人文件下载记录表 (✅ 已实现)
CREATE TABLE personal_file_downloads (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES personal_files(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    ip_address VARCHAR(45),                           -- 下载者IP
    user_agent VARCHAR(500),                          -- User Agent
    download_size BIGINT,                             -- 下载字节数
    download_status VARCHAR(20) DEFAULT 'completed',
    downloaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 用户关注关系表 (✅ 已实现)
CREATE TABLE user_follows (
    id SERIAL PRIMARY KEY,
    follower_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    following_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(follower_id, following_id),
    CHECK (follower_id != following_id)
);

-- 仓库表 (✅ 已实现)
CREATE TABLE repositories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,             -- 仓库名称
    full_name VARCHAR(512) NOT NULL UNIQUE, -- owner/repo_name
    description TEXT,                       -- 仓库描述

    -- 所有者信息
    owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    -- 仓库类型和可见性
    repo_type VARCHAR(50) DEFAULT 'model',  -- model, dataset, space
    visibility VARCHAR(20) DEFAULT 'public', -- public, private

    -- README.md 解析的元数据
    repo_metadata JSON,                     -- YAML frontmatter 解析结果
    readme_content TEXT,                    -- README.md 内容

    -- 标签和分类
    tags TEXT[],                           -- 标签数组
    license VARCHAR(100),                   -- 许可证

    -- 统计信息
    stars_count INTEGER DEFAULT 0,         -- 星标数
    downloads_count INTEGER DEFAULT 0,     -- 下载次数
    views_count INTEGER DEFAULT 0,         -- 查看次数
    forks_count INTEGER DEFAULT 0,         -- Fork数

    -- 文件和存储信息
    total_files INTEGER DEFAULT 0,
    total_size BIGINT DEFAULT 0,

    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_commit_at TIMESTAMP WITH TIME ZONE
);

-- 仓库文件表 (✅ 已实现)
CREATE TABLE repository_files (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER REFERENCES repositories(id) ON DELETE CASCADE,

    -- 文件信息
    filename VARCHAR(500) NOT NULL,          -- 文件名
    file_path VARCHAR(1000) NOT NULL,        -- 仓库内相对路径
    file_type VARCHAR(100),                  -- 文件类型分类
    mime_type VARCHAR(200),                  -- MIME类型
    file_size BIGINT NOT NULL,               -- 文件大小
    file_hash VARCHAR(128),                  -- SHA256哈希

    -- MinIO 存储信息
    minio_bucket VARCHAR(255) NOT NULL,      -- MinIO桶名
    minio_object_key VARCHAR(1000) NOT NULL, -- MinIO对象键

    -- 版本和状态
    version VARCHAR(50) DEFAULT 'latest',
    is_deleted BOOLEAN DEFAULT FALSE,

    -- 下载统计
    download_count INTEGER DEFAULT 0,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(repository_id, file_path)
);

-- 文件上传会话表 (✅ 已实现)
CREATE TABLE file_upload_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    repository_id INTEGER REFERENCES repositories(id) ON DELETE CASCADE,

    -- 文件信息
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(200),
    file_hash VARCHAR(128),

    -- 分块上传信息
    chunk_size INTEGER DEFAULT 5242880,     -- 5MB 默认块大小
    total_chunks INTEGER NOT NULL,
    uploaded_chunks INTEGER DEFAULT 0,
    chunk_status JSON,                      -- 记录每个块的上传状态

    -- MinIO 信息
    minio_bucket VARCHAR(255),
    minio_object_key VARCHAR(1000),
    minio_upload_id VARCHAR(255),           -- MultipartUpload ID

    -- 状态和进度
    status VARCHAR(20) DEFAULT 'pending',   -- pending/uploading/completed/failed/cancelled
    progress_percentage INTEGER DEFAULT 0,
    error_message TEXT,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- 文件下载记录表 (✅ 已实现)
CREATE TABLE file_downloads (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES repository_files(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- 下载信息
    ip_address VARCHAR(45),                 -- IPv6 支持
    user_agent TEXT,
    referer VARCHAR(1000),
    download_method VARCHAR(50) DEFAULT 'direct', -- direct, git, api

    -- 下载状态
    bytes_downloaded BIGINT DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,

    -- 时间戳
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 仓库星标关系表 (✅ 已实现)
CREATE TABLE repository_stars (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    repository_id INTEGER REFERENCES repositories(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, repository_id)
);

-- 仓库访问记录表 (✅ 已实现)
CREATE TABLE repository_views (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER REFERENCES repositories(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    ip_address VARCHAR(45),                 -- IPv6 支持
    user_agent TEXT,
    referer VARCHAR(1000),

    -- 访问详情
    view_type VARCHAR(50) DEFAULT 'page_view', -- page_view, file_view, download
    target_path VARCHAR(1000),              -- 访问的具体路径或文件

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 文件版本历史表 (⚠️ 待实现)
CREATE TABLE file_versions (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES repository_files(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    version_hash VARCHAR(64) NOT NULL,           -- 内容哈希 (SHA256前16位)

    -- 内容存储
    content_preview TEXT,                        -- 文本文件内容预览 (前1000字符)
    minio_object_key VARCHAR(1000) NOT NULL,     -- MinIO 中的版本文件路径

    -- 变更信息
    commit_message TEXT,
    diff_summary JSON,                           -- 变更摘要 {added_lines: 10, deleted_lines: 5}
    file_size BIGINT NOT NULL,

    -- 操作信息
    author_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 索引
    UNIQUE(file_id, version_number)
);

-- 文件编辑会话表 (✅ 已实现)
CREATE TABLE file_edit_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    file_id INTEGER REFERENCES repository_files(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    -- 编辑状态
    is_active BOOLEAN DEFAULT TRUE,
    content_draft TEXT,                          -- 草稿内容
    last_cursor_position JSON,                   -- 光标位置

    -- 时间管理
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,         -- 会话过期时间

    INDEX(file_id, is_active),
    INDEX(user_id, is_active)
);

-- 文件编辑权限表 (✅ 已实现)
CREATE TABLE file_edit_permissions (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES repository_files(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    permission_type VARCHAR(20) DEFAULT 'read', -- read, write, admin
    granted_by INTEGER REFERENCES users(id),
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(file_id, user_id)
);

-- 文件草稿表 (✅ 已实现)
CREATE TABLE file_drafts (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES repository_files(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    base_version_id INTEGER REFERENCES file_versions(id) ON DELETE CASCADE,

    -- 草稿内容
    draft_content TEXT,
    title VARCHAR(255),
    description TEXT,

    -- 编辑状态
    cursor_position JSON,
    selection_range JSON,
    is_auto_saved BOOLEAN DEFAULT TRUE,
    auto_save_count INTEGER DEFAULT 0,

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_access TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(file_id, user_id)
);

-- 文件模板表 (✅ 已实现)
CREATE TABLE file_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    file_extension VARCHAR(50),
    template_content TEXT NOT NULL,
    variables JSON,                              -- 模板变量定义
    category VARCHAR(100),
    is_system BOOLEAN DEFAULT FALSE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 扩展现有表字段 (⚠️ 待实现)
-- ALTER TABLE repository_files ADD COLUMN current_version INTEGER DEFAULT 1;
-- ALTER TABLE repository_files ADD COLUMN last_edit_session_id VARCHAR(255);
-- ALTER TABLE repository_files ADD COLUMN is_text_file BOOLEAN DEFAULT FALSE;
-- ALTER TABLE repository_files ADD COLUMN encoding VARCHAR(20) DEFAULT 'utf-8';
-- ALTER TABLE repositories ADD COLUMN total_commits INTEGER DEFAULT 0;
-- ALTER TABLE repositories ADD COLUMN last_commit_message TEXT;

-- 分类表 (✅ 已实现)
CREATE TABLE classifications (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    level INTEGER NOT NULL,                  -- 1=一级, 2=二级, 3=三级
    parent_id INTEGER REFERENCES classifications(id),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CHECK ((level = 1 AND parent_id IS NULL) OR (level > 1 AND parent_id IS NOT NULL)),
    UNIQUE(name, parent_id)
);

-- 仓库分类关联表 (✅ 已实现)
CREATE TABLE repository_classifications (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER REFERENCES repositories(id) ON DELETE CASCADE,
    classification_id INTEGER REFERENCES classifications(id) ON DELETE CASCADE,
    level INTEGER NOT NULL,                  -- 记录选择的级别
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(repository_id, classification_id)
);

-- 系统存储统计表 (✅ 已实现)
CREATE TABLE system_storage (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP WITH TIME ZONE NOT NULL UNIQUE,

    -- 总体统计
    total_users INTEGER DEFAULT 0,
    total_repositories INTEGER DEFAULT 0,
    total_files INTEGER DEFAULT 0,
    total_size BIGINT DEFAULT 0,

    -- 按类型统计
    public_repos INTEGER DEFAULT 0,
    private_repos INTEGER DEFAULT 0,
    model_repos INTEGER DEFAULT 0,
    dataset_repos INTEGER DEFAULT 0,

    -- 按文件类型统计
    model_files_size BIGINT DEFAULT 0,
    dataset_files_size BIGINT DEFAULT 0,
    image_files_size BIGINT DEFAULT 0,
    document_files_size BIGINT DEFAULT 0,
    other_files_size BIGINT DEFAULT 0,

    -- 活跃度统计
    daily_downloads INTEGER DEFAULT 0,
    daily_uploads INTEGER DEFAULT 0,
    daily_views INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- MinIO 服务健康状态表 (✅ 已实现)
CREATE TABLE minio_service_health (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(500) NOT NULL,

    -- 健康状态
    is_healthy BOOLEAN DEFAULT TRUE,
    response_time_ms INTEGER,
    error_message TEXT,

    -- 存储信息
    available_space BIGINT,
    used_space BIGINT,
    total_space BIGINT,

    -- 检查时间
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 统计信息
    total_buckets INTEGER DEFAULT 0,
    total_objects INTEGER DEFAULT 0
);

-- 模型服务表 (✅ 已实现)
CREATE TABLE model_services (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER REFERENCES repositories(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    -- 服务基本信息
    service_name VARCHAR(255) NOT NULL,        -- 服务名称
    model_id VARCHAR(255) NOT NULL,            -- 模型标识符
    model_ip VARCHAR(255) NOT NULL,            -- 模型服务器IP地址
    description TEXT,                          -- 服务描述

    -- 服务配置
    example_data_path VARCHAR(1000),           -- 示例数据路径
    gradio_port INTEGER,                       -- Gradio端口
    service_url VARCHAR(500),                  -- 服务访问URL

    -- 资源配置
    cpu_limit VARCHAR(50) DEFAULT '0.2',       -- CPU限制（默认0.2核）
    memory_limit VARCHAR(50) DEFAULT '256Mi',  -- 内存限制（默认256Mi）

    -- 访问控制
    is_public BOOLEAN DEFAULT FALSE,           -- 是否公开访问
    access_token VARCHAR(255),                 -- 访问令牌

    -- 服务状态
    status VARCHAR(50) DEFAULT 'created',      -- created, starting, running, stopping, stopped, error, idle
    container_id VARCHAR(255),                 -- 容器ID

    -- 服务优先级和重试机制 (V2.0 新增)
    priority INTEGER DEFAULT 100,             -- 启动优先级，数值越小优先级越高
    last_health_check TIMESTAMP WITH TIME ZONE, -- 最后健康检查时间
    auto_start_retry_count INTEGER DEFAULT 0, -- 自动启动重试次数
    last_failure_reason TEXT,                 -- 最后一次失败原因
    failure_type VARCHAR(50),                 -- 失败类型: temporary, permanent, unknown

    -- 统计信息
    access_count INTEGER DEFAULT 0,           -- 访问次数
    start_count INTEGER DEFAULT 0,            -- 启动次数
    total_runtime_minutes INTEGER DEFAULT 0,  -- 总运行时间(分钟)

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    last_started_at TIMESTAMP WITH TIME ZONE,
    last_stopped_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT uq_repo_service_name UNIQUE(repository_id, service_name)
);

-- 服务实例表 (✅ 已实现)
CREATE TABLE service_instances (
    id SERIAL PRIMARY KEY,
    service_id INTEGER REFERENCES model_services(id) ON DELETE CASCADE,

    -- 容器信息
    container_id VARCHAR(255) NOT NULL UNIQUE,
    container_name VARCHAR(255),
    image_name VARCHAR(255),

    -- 网络配置
    host_port INTEGER,                         -- 主机端口
    container_port INTEGER DEFAULT 7860,      -- 容器端口

    -- 实例状态
    status VARCHAR(50) DEFAULT 'created',     -- created, starting, running, stopping, stopped, error
    pid INTEGER,                              -- 进程ID

    -- 资源使用
    cpu_usage_percent DECIMAL(5,2),           -- CPU使用率
    memory_usage_bytes BIGINT,                -- 内存使用量

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    stopped_at TIMESTAMP WITH TIME ZONE,
    last_heartbeat TIMESTAMP WITH TIME ZONE
);

-- 服务日志表 (✅ 已实现)
CREATE TABLE service_logs (
    id SERIAL PRIMARY KEY,
    service_id INTEGER REFERENCES model_services(id) ON DELETE CASCADE,

    -- 日志信息
    log_level VARCHAR(20) NOT NULL,           -- info, warning, error, debug
    message TEXT NOT NULL,                    -- 日志消息
    event_type VARCHAR(50),                   -- create, start, stop, access, error, health_check

    -- 上下文信息
    user_id INTEGER REFERENCES users(id),    -- 操作用户
    ip_address INET,                          -- 操作IP
    user_agent TEXT,                          -- 用户代理

    -- 元数据
    metadata JSONB,                           -- 额外的日志数据

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 服务健康监控表 (✅ 已实现)
CREATE TABLE service_health_checks (
    id SERIAL PRIMARY KEY,
    service_id INTEGER REFERENCES model_services(id) ON DELETE CASCADE,

    -- 健康状态
    status VARCHAR(50) NOT NULL,              -- healthy, unhealthy, unknown, timeout
    response_time_ms INTEGER,                 -- 响应时间(ms)

    -- 检查详情
    check_type VARCHAR(50) DEFAULT 'http',    -- http, tcp, process
    endpoint VARCHAR(500),                    -- 检查端点
    http_status_code INTEGER,                 -- HTTP状态码

    -- 错误信息
    error_message TEXT,                       -- 错误信息
    error_code VARCHAR(50),                   -- 错误代码

    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


-- 创建索引以优化查询性能 (✅ 已实现)
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_external_user_id ON users(external_user_id);
CREATE INDEX idx_repositories_owner ON repositories(owner_id);
CREATE INDEX idx_repositories_visibility ON repositories(visibility);
CREATE INDEX idx_repositories_tags ON repositories USING GIN(tags);
CREATE INDEX idx_repositories_full_name ON repositories(full_name);
CREATE INDEX idx_repositories_search ON repositories USING GIN(
    to_tsvector('english', name || ' ' || COALESCE(description, '') || ' ' || array_to_string(tags, ' '))
);
CREATE INDEX idx_repository_files_repo ON repository_files(repository_id);
CREATE INDEX idx_repository_files_type ON repository_files(file_type);
CREATE INDEX idx_repository_stars_user ON repository_stars(user_id);
CREATE INDEX idx_repository_stars_repo ON repository_stars(repository_id);
CREATE INDEX idx_user_follows_follower ON user_follows(follower_id);
CREATE INDEX idx_user_follows_following ON user_follows(following_id);
CREATE INDEX idx_classifications_level ON classifications(level);
CREATE INDEX idx_classifications_parent ON classifications(parent_id);
CREATE INDEX idx_file_upload_sessions_session_id ON file_upload_sessions(session_id);

-- 文件编辑和版本控制相关索引 (✅ 已实现)
CREATE INDEX idx_file_versions_file_id ON file_versions(file_id);
CREATE INDEX idx_file_versions_version ON file_versions(file_id, version_number DESC);
CREATE INDEX idx_file_versions_author ON file_versions(author_id);
CREATE INDEX idx_file_edit_sessions_file ON file_edit_sessions(file_id, is_active);
CREATE INDEX idx_file_edit_sessions_user ON file_edit_sessions(user_id, is_active);
CREATE INDEX idx_file_edit_sessions_session ON file_edit_sessions(session_id);
CREATE INDEX idx_file_edit_permissions_file ON file_edit_permissions(file_id);
CREATE INDEX idx_file_edit_permissions_user ON file_edit_permissions(user_id);
CREATE INDEX idx_file_templates_category ON file_templates(category);
CREATE INDEX idx_file_templates_extension ON file_templates(file_extension);
CREATE INDEX idx_repository_classifications_repo ON repository_classifications(repository_id);
CREATE INDEX idx_repository_classifications_class ON repository_classifications(classification_id);
CREATE INDEX idx_model_services_repo ON model_services(repository_id);
CREATE INDEX idx_model_services_user ON model_services(user_id);
CREATE INDEX idx_model_services_status ON model_services(status);
CREATE INDEX idx_model_services_model_id ON model_services(model_id);
CREATE INDEX idx_model_services_priority ON model_services(priority);
CREATE INDEX idx_model_services_failure_type ON model_services(failure_type);
CREATE INDEX idx_service_instances_service ON service_instances(service_id);
CREATE INDEX idx_service_instances_container ON service_instances(container_id);
CREATE INDEX idx_service_logs_service ON service_logs(service_id);
CREATE INDEX idx_service_logs_user ON service_logs(user_id);
CREATE INDEX idx_service_logs_event_type ON service_logs(event_type);
CREATE INDEX idx_service_health_checks_service ON service_health_checks(service_id);
```

### 关键特性

- **用户空间管理**: 完整的用户系统，支持个人空间和社交功能
- **存储配额管理**: 用户存储空间管理，支持配额控制和使用统计
- **仓库版本控制**: 类似 GitHub 的仓库管理，支持分支和文件版本
- **文件对象存储**: 与 MinIO 集成，支持大文件和分块上传
- **YAML 元数据**: 自动解析 README.md 中的 frontmatter，构建搜索索引
- **社交功能**: 星标、关注、访问统计等社区功能
- **分类兼容**: 保持原有的三级分类体系，同时支持标签检索
- **高级搜索**: 全文搜索、多维度筛选和智能推荐
- **服务集成**: 支持模型推理、训练、部署服务的集成与监控 (设计中)
- **独立文件管理**: 跨仓库的文件管理和操作功能 (设计中)
- **元数据标准化**: 完整的元数据模式定义和验证系统 (设计中)
- **性能优化**: 针对用户查询、文件检索和元数据搜索的索引优化

## 🔌 API 接口 v2.0

### 📋 接口实现状态

- ✅ **已实现**: 接口已在 backend 中完整实现
- ⚠️ **待实现**: 接口已设计但尚未实现
- 🔄 **部分实现**: 接口核心功能已实现，部分细节待完善

### 认证 API

```http
# 用户认证 (✅ 已实现)
POST   /api/auth/login                          # 用户登录
POST   /api/auth/logout                         # 用户登出
POST   /api/auth/refresh                        # 刷新访问token

# 用户信息 (✅ 已实现)
GET    /api/auth/me                             # 获取当前用户信息
POST   /api/auth/verify                         # 验证JWT Token
POST   /api/auth/sync                           # 同步用户信息

# 服务状态 (✅ 已实现)
GET    /api/auth/health                         # 认证服务健康检查
```

### 用户管理 API

```http
# 用户列表和创建 (✅ 已实现)
GET    /api/users                               # 获取用户列表
POST   /api/users                               # 创建用户（管理员）

# 用户资料 (✅ 已实现)
GET    /api/users/{username}                    # 获取用户资料
PUT    /api/users/{username}                    # 更新用户资料（需认证）
GET    /api/users/{username}/repositories       # 获取用户仓库列表
GET    /api/users/{username}/followers          # 获取用户粉丝列表
GET    /api/users/{username}/following          # 获取用户关注列表

# 用户关注 (✅ 已实现)
POST   /api/users/{username}/follow             # 关注用户
DELETE /api/users/{username}/follow             # 取消关注用户

# 用户统计和存储 (✅ 已实现)
GET    /api/users/{username}/stats              # 获取用户统计信息 (✅ 已实现)
GET    /api/users/{username}/starred            # 获取用户收藏的仓库 (✅ 已实现)
GET    /api/users/{username}/storage            # 获取存储使用情况 (✅ 已实现)
```

### 仓库管理 API

```http
# 仓库基本操作 (✅ 已实现)
GET    /api/repositories                        # 浏览所有公开仓库 (✅ 已实现)
POST   /api/repositories                        # 创建仓库 (✅ 已实现)
GET    /api/{username}/{repo_name}              # 获取仓库详情 (✅ 已实现)
PUT    /api/{username}/{repo_name}              # 更新仓库信息 (✅ 已实现)
DELETE /api/{username}/{repo_name}              # 删除仓库 (✅ 已实现)

# 仓库设置 (✅ 已实现)
GET    /api/{username}/{repo_name}/settings     # 获取仓库设置 (✅ 已实现)
PUT    /api/{username}/{repo_name}/settings     # 更新仓库设置 (✅ 已实现)

# 仓库分类 (✅ 已实现)
GET    /api/{username}/{repo_name}/classifications    # 获取仓库分类
POST   /api/{username}/{repo_name}/classifications    # 添加仓库分类 (自动关联父级)
DELETE /api/{username}/{repo_name}/classifications    # 移除所有仓库分类

# 仓库文件管理 (✅ 已实现)
GET    /api/{username}/{repo_name}/files        # 获取仓库文件列表
GET    /api/{username}/{repo_name}/blob/{file_path} # 获取文件内容
GET    /api/{username}/{repo_name}/download/{file_path} # 下载文件

# 仓库社交功能 (✅ 已实现)
POST   /api/{username}/{repo_name}/star         # 收藏仓库
DELETE /api/{username}/{repo_name}/star         # 取消收藏仓库
GET    /api/{username}/{repo_name}/stars        # 获取收藏者列表

# 仓库统计 (✅ 已实现)
GET    /api/{username}/{repo_name}/stats        # 获取仓库统计信息 (✅ 已实现)
GET    /api/{username}/{repo_name}/analytics    # 获取详细分析数据 (✅ 已实现)
```

### 文件管理 API

```http
# 仓库文件浏览 (✅ 已实现)
GET    /api/{username}/{repo_name}/tree/main             # 获取文件树 (✅ 已实现)
GET    /api/{username}/{repo_name}/tree/main/{path}      # 获取指定路径文件 (✅ 已实现)
GET    /api/{username}/{repo_name}/blob/{file_path}      # 获取文件内容 (✅ 已实现)
GET    /api/{username}/{repo_name}/files                 # 获取仓库文件列表 (✅ 已实现)

# 文件上传 (✅ 已实现)
POST   /api/{username}/{repo_name}/upload               # 上传单个文件 (✅ 已实现)
POST   /api/{username}/{repo_name}/upload/batch         # 批量上传文件 (✅ 已实现)
POST   /api/{username}/{repo_name}/upload/init          # 初始化分块上传 (✅ 已实现)
POST   /api/{username}/{repo_name}/upload/{session_id}/chunk/{chunk_number} # 上传分片 (✅ 已实现)
POST   /api/{username}/{repo_name}/upload/{session_id}/complete # 完成分块上传 (✅ 已实现)
DELETE /api/{username}/{repo_name}/upload/{session_id}  # 取消分块上传 (✅ 已实现)
GET    /api/{username}/{repo_name}/upload/{session_id}/status # 获取上传状态 (✅ 已实现)

# 文件下载 (✅ 已实现)
GET    /api/{username}/{repo_name}/download/{file_path} # 下载文件 (✅ 已实现)
GET    /api/files/{file_id}/download                    # 通过文件ID下载 (✅ 已实现)

# 独立文件管理 API (✅ 已实现)
GET    /api/files                                       # 获取所有文件列表 (管理员) (✅ 已实现)
GET    /api/files/{file_id}                             # 获取文件详细信息 (✅ 已实现)
PUT    /api/files/{file_id}                             # 更新文件信息 (✅ 已实现)
DELETE /api/files/{file_id}                             # 删除文件 (✅ 已实现)
GET    /api/files/{file_id}/stats                       # 获取文件统计信息 (✅ 已实现)
POST   /api/files/{file_id}/move                        # 移动文件 (✅ 已实现)
POST   /api/files/{file_id}/copy                        # 复制文件 (✅ 已实现)
GET    /api/files/search                                # 搜索文件 (✅ 已实现)
```

### 个人数据空间 API

```http
# 个人空间统计 (✅ 已实现)
GET    /api/personal-files/{username}/stats             # 获取个人空间统计信息 (✅ 已实现)
GET    /api/personal-files/{username}/browse            # 浏览个人空间文件 (✅ 已实现)
GET    /api/personal-files/{username}/search            # 搜索个人文件 (✅ 已实现)

# 文件夹管理 (✅ 已实现)
POST   /api/personal-files/{username}/folders           # 创建文件夹 (✅ 已实现)

# 文件上传与管理 (✅ 已实现)
POST   /api/personal-files/{username}/upload-url        # 获取上传URL (✅ 已实现)
POST   /api/personal-files/{username}/complete-upload   # 完成文件上传 (✅ 已实现)
GET    /api/personal-files/files/{file_id}              # 获取文件信息 (✅ 已实现)
GET    /api/personal-files/files/{file_id}/download     # 下载个人文件 (✅ 已实现)
DELETE /api/personal-files/files/{file_id}              # 删除个人文件 (✅ 已实现)
```

### 文件编辑和版本控制 API

```http
# 文件编辑器核心 API (✅ 已实现)
GET    /api/file-editor/files/{file_id}/versions              # 获取文件版本历史 (✅ 已实现)
GET    /api/file-editor/files/{file_id}/versions/{version_id}/content # 获取指定版本内容 (✅ 已实现)
POST   /api/file-editor/files/{file_id}/versions              # 创建新版本 (✅ 已实现)
GET    /api/file-editor/files/{file_id}/versions/{old_version_id}/diff/{new_version_id} # 获取版本差异 (✅ 已实现)
DELETE /api/editor/{username}/{repo_name}/file/{file_path}     # 删除文件 (⚠️ 待实现)

# 编辑会话管理 API (✅ 已实现)
POST   /api/file-editor/files/{file_id}/edit-session          # 创建编辑会话 (✅ 已实现)
PUT    /api/file-editor/edit-sessions/{session_id}           # 更新编辑会话内容 (✅ 已实现)
GET    /api/file-editor/files/{file_id}/collaboration        # 获取文件协作状态 (✅ 已实现)
DELETE /api/file-editor/edit-sessions/{session_id}         # 关闭编辑会话 (✅ 已实现)

# 权限管理 API (✅ 已实现)
POST   /api/file-editor/files/{file_id}/permissions           # 授予文件权限 (✅ 已实现)
GET    /api/file-editor/files/{file_id}/permissions/check     # 检查文件权限 (✅ 已实现)

# 草稿管理 API (✅ 已实现)
POST   /api/file-editor/files/{file_id}/drafts                 # 保存文件草稿 (✅ 已实现)
GET    /api/file-editor/files/{file_id}/drafts                 # 获取文件草稿 (✅ 已实现)
PUT    /api/file-editor/drafts/{draft_id}                      # 更新文件草稿 (✅ 已实现)
DELETE /api/file-editor/drafts/{draft_id}                      # 删除文件草稿 (✅ 已实现)
GET    /api/file-editor/drafts                                 # 获取用户所有草稿 (✅ 已实现)

# 模板管理 API (✅ 已实现)
GET    /api/file-editor/templates                              # 获取文件模板列表 (✅ 已实现)
POST   /api/file-editor/templates                              # 创建文件模板 (✅ 已实现)

# 批量操作 API (⚠️ 待实现)
POST   /api/editor/{username}/{repo_name}/batch/commit          # 批量提交多个文件 (⚠️ 待实现)
GET    /api/editor/{username}/{repo_name}/tree/edit             # 获取可编辑文件树 (⚠️ 待实现)

# 文件模板 API (✅ 已实现)
GET    /api/editor/templates                                    # 获取文件模板列表 (✅ 已实现)
POST   /api/editor/{username}/{repo_name}/file/from-template    # 从模板创建文件 (✅ 已实现)

# 仓库级别 API 扩展 (⚠️ 待实现)
GET    /api/{username}/{repo_name}/commits                      # 获取仓库提交历史 (⚠️ 待实现)
GET    /api/{username}/{repo_name}/commit/{commit_id}           # 获取特定提交详情 (⚠️ 待实现)
GET    /api/{username}/{repo_name}/stats/edits                  # 获取编辑统计 (⚠️ 待实现)
```

### 社区功能 API

```http
# 收藏功能 (✅ 已实现)
POST   /api/{username}/{repo_name}/star         # 收藏仓库
DELETE /api/{username}/{repo_name}/star         # 取消收藏
GET    /api/{username}/{repo_name}/stars        # 获取收藏者列表

# 访问统计 (✅ 已实现)
GET    /api/{username}/{repo_name}/views        # 获取访问统计 (✅ 已实现)
POST   /api/{username}/{repo_name}/view         # 记录访问（自动调用）(✅ 已实现)
```

### 元数据 API

```http
# YAML元数据管理 (✅ 已实现)
GET    /api/{username}/{repo_name}/metadata           # 获取YAML元数据 (✅ 已实现)
PUT    /api/{username}/{repo_name}/metadata           # 更新元数据 (✅ 已实现)
POST   /api/{username}/{repo_name}/parse-readme       # 解析README.md元数据 (✅ 已实现)
GET    /api/{username}/{repo_name}/model-card         # 获取Model Card (✅ 已实现)

# 元数据字段管理 (✅ 已实现)
GET    /api/metadata/schema                           # 获取元数据模式定义 (✅ 已实现)
POST   /api/metadata/validate                         # 验证元数据格式 (✅ 已实现)
GET    /api/metadata/templates                        # 获取元数据模板 (✅ 已实现)
POST   /api/metadata/templates                        # 创建元数据模板 (✅ 已实现)

# 元数据搜索 (✅ 已实现)
GET    /api/metadata/search                           # 搜索元数据 (✅ 已实现)
GET    /api/metadata/stats                            # 元数据统计信息 (✅ 已实现)
```

### 分类管理 API (保持兼容)

```http
# 分类查询 (✅ 已实现)
GET    /api/classifications/tree                # 获取分类树结构
GET    /api/classifications                     # 获取分类列表
GET    /api/classifications/{id}                # 获取分类详情
GET    /api/classifications/{id}/children       # 获取子分类
GET    /api/classifications/{id}/path           # 获取分类路径

# 分类管理 (✅ 已实现)
POST   /api/classifications                     # 创建分类（管理员）
PUT    /api/classifications/{id}                # 更新分类（管理员）
DELETE /api/classifications/{id}                # 删除分类（管理员）
```

### 搜索和发现 API

```http
# 搜索功能 (✅ 已实现)
GET    /api/search/repositories                 # 搜索仓库
GET    /api/search/users                        # 搜索用户
GET    /api/search/suggestions                  # 搜索建议
GET    /api/search/stats                        # 搜索统计

# 发现功能 (✅ 已实现)
GET    /api/search/trending                     # 热门仓库 (✅ 已实现)
GET    /api/trending                            # 热门仓库 (✅ 已实现)
GET    /api/featured                            # 推荐仓库 (✅ 已实现)
GET    /api/recent                              # 最新仓库 (✅ 已实现)
GET    /api/popular                             # 受欢迎仓库 (✅ 已实现)
```

### 通知系统 API

```http
# 通知管理 (⚠️ 待实现)
GET    /api/notifications                               # 获取通知列表
POST   /api/notifications/{id}/read                     # 标记通知为已读
GET    /api/notifications/unread-count                  # 获取未读通知数量
DELETE /api/notifications/{id}                          # 删除通知
POST   /api/notifications/read-all                      # 标记所有通知为已读
```

### 评论系统 API

```http
# 评论管理 (⚠️ 待实现)
GET    /api/comments                                    # 获取评论列表
POST   /api/comments                                    # 创建评论
PUT    /api/comments/{id}                               # 更新评论
DELETE /api/comments/{id}                               # 删除评论
POST   /api/comments/{id}/like                          # 点赞评论
DELETE /api/comments/{id}/like                          # 取消点赞评论
```

### 活动动态 API

```http
# 活动管理 (⚠️ 待实现)
GET    /api/activities                                  # 获取活动动态列表
GET    /api/activities/{user_id}                        # 获取用户活动动态
```

### 模型服务管理 API

```http
# 服务CRUD操作 (✅ 已实现)
GET    /api/{username}/{repo_name}/services             # 获取仓库服务列表，支持自动启动
POST   /api/{username}/{repo_name}/services             # 创建模型服务
GET    /api/services/{service_id}                       # 获取服务详情
PUT    /api/services/{service_id}                       # 更新服务配置
DELETE /api/services/{service_id}                       # 删除服务

# 服务生命周期控制 (✅ 已实现)
POST   /api/services/{service_id}/start                 # 启动服务（支持强制重启）
POST   /api/services/{service_id}/stop                  # 停止服务（支持强制停止）
POST   /api/services/{service_id}/restart               # 重启服务
GET    /api/services/{service_id}/status                # 获取服务状态和资源使用情况
GET    /api/services/{service_id}/logs                  # 获取服务日志（支持级别和事件类型筛选）

# 服务访问管理 (✅ 已实现)
GET    /api/services/{service_id}/demo                  # 访问Gradio界面（自动重定向）
POST   /api/services/{service_id}/access-token          # 重新生成访问令牌
PUT    /api/services/{service_id}/visibility            # 更新服务可见性

# 服务监控和健康检查 (✅ 已实现)
GET    /api/services/{service_id}/health                # 获取服务健康检查历史
POST   /api/services/{service_id}/health-check          # 手动触发健康检查
GET    /api/services/{service_id}/metrics               # 获取服务性能指标
GET    /api/services/{service_id}/resource-usage        # 获取实时资源使用情况

# 批量操作 (✅ 已实现)
POST   /api/{username}/{repo_name}/services/batch/start # 批量启动服务（异步执行）
POST   /api/{username}/{repo_name}/services/batch/stop  # 批量停止服务（异步执行）
DELETE /api/{username}/{repo_name}/services/batch       # 批量删除服务（异步执行）

# 系统管理和监控 (✅ 已实现)
GET    /api/admin/services/statistics                   # 获取系统资源和服务统计信息
GET    /api/admin/services/overview                     # 获取服务概览信息
POST   /api/admin/services/maintenance                  # 执行系统维护任务
GET    /api/services/health-summary                     # 获取服务健康状态摘要
POST   /api/services/cleanup-idle                       # 手动触发空闲服务清理
```

### 系统管理 API

```http
# 管理员仪表板 (✅ 已实现)
GET    /api/admin/dashboard                     # 管理员仪表板数据
GET    /api/admin/users                         # 用户管理列表（分页、搜索、筛选）
PUT    /api/admin/users/{user_id}/status        # 更新用户状态（激活/验证/管理员权限）

# 仓库管理 (✅ 已实现)
GET    /api/admin/repositories                  # 管理员仓库列表（包括软删除，高级搜索）
PUT    /api/admin/repositories/{repository_id}/status # 更新仓库状态（激活/推荐/可见性）
POST   /api/admin/repositories/{repository_id}/restore # 恢复软删除的仓库
DELETE /api/admin/repositories/{repository_id}/hard-delete # 永久删除仓库（硬删除）
GET    /api/admin/repositories/stats            # 仓库统计信息（概览、类型分布、热门排行）

# 存储管理 (✅ 已实现)
GET    /api/admin/storage/stats                 # 存储统计信息（用户存储、文件类型、MinIO桶使用）
POST   /api/admin/storage/cleanup               # 存储清理（过期会话、孤儿文件）

# 系统监控 (✅ 已实现)
GET    /api/admin/system/health                 # 系统健康检查（数据库、MinIO、磁盘空间）
GET    /api/admin/logs                          # 获取系统日志（级别筛选、分页查看）

# 系统配置 (✅ 已实现)
GET    /api/system/config                       # 获取系统配置 (✅ 已实现)
PUT    /api/system/config                       # 更新系统配置 (✅ 已实现)
GET    /api/system/health                       # 系统健康检查 (✅ 已实现)
GET    /api/system/info                         # 获取系统信息 (✅ 已实现)
POST   /api/system/maintenance                  # 切换维护模式 (✅ 已实现)
POST   /api/system/restart                      # 重启系统组件 (✅ 已实现)
```

## 前端

### 🖥️ 页面架构 (SvelteKit)

#### 核心页面

- **主页** (`/`) - 展示仓库列表和分类筛选 (✅ 已实现)
  - 使用 API: `GET /api/repositories`, `GET /api/classifications`
  - 组件: `RepositoryCard`, `ClassificationFilter`, `SearchBar`
- **用户主页** (`/{username}`) - 用户个人空间 (✅ 已实现)

  - 使用 API: `GET /api/users/{username}`, `GET /api/users/{username}/repositories`, `GET /api/users/{username}/storage`, `GET /api/personal-files/{username}/stats`
  - 组件: `UserProfile`, `RepositoryCard`, `UserAvatar`, `PersonalFileManager`, `PersonalFileUpload`
  - 功能: 用户信息展示、仓库列表、关注功能、存储空间管理、**个人数据空间** (✅ 已实现)
  - **个人数据空间功能**: 文件上传下载、文件夹创建管理、公开/私有设置、文件删除、上传进度跟踪

- **仓库页面** (`/{username}/{repository}`) - 仓库详情展示 (✅ 已实现)

  - 使用 API: `GET /api/{username}/{repository}`, `GET /api/{username}/{repository}/files`, `GET /api/{username}/{repository}/analytics`
  - 组件: `RepositoryHeader`, `FileTree`, `ReadmeViewer`, `RepositoryStats`

- **文件上传页面** (`/{username}/{repository}/upload`) - 文件上传界面 (✅ 已实现)
  - 使用 API: `POST /api/{username}/{repository}/upload`
  - 组件: `FileUpload`, `FileManager`
  - 功能: 多文件上传、上传进度显示、文件拖拽上传

#### 功能页面

- **登录页面** (`/login`) - 用户登录 (✅ 已实现)

  - 使用 API: `POST /api/auth/login`
  - 组件: `Button`, `Input`, `FormField`

- **注册页面** (`/register`) - 用户注册 (🔄 部分实现)

  - 使用 API: `POST /api/auth/register` (⚠️ 注意：API 在 backend 未实现)
  - 组件: `Button`, `Input`, `FormField`

- **新建仓库页面** (`/new`) - 创建新仓库 (✅ 已实现)

  - 使用 API: `POST /api/repositories`, `GET /api/classifications`
  - 组件: `Button`, `Input`, `Dropdown`, `ClassificationFilter`

- **搜索页面** (`/search`) - 搜索仓库和用户 (✅ 已实现)

  - 使用 API: `GET /api/search/repositories`, `GET /api/search/users`
  - 组件: `SearchBar`, `RepositoryCard`, `UserProfile`, `Pagination`

- **趋势页面** (`/trending`) - 展示热门仓库 (✅ 已实现)
  - 使用 API: `GET /api/search/trending`
  - 组件: `RepositoryCard`, `CategoryFilter`

#### 文件编辑与版本控制页面 (✅ 已实现)

- **文件编辑页面** (`/{username}/{repository}/edit/{file_path}`) - 在线文件编辑器 (✅ 已实现)

  - 使用 API: `GET /api/file-editor/files/{file_id}/versions/{version_id}/content`, `POST /api/file-editor/files/{file_id}/versions`
  - 组件: `FileEditor`, `EditorToolbar`, `EditorStatusBar`, `EditorSidebar`
  - 功能: CodeMirror 6 编辑器、语法高亮、自动保存、版本提交、协作状态

- **文件查看页面** (`/{username}/{repository}/blob/{file_path}`) - 文件内容查看 (✅ 已实现)

  - 使用 API: `GET /api/files/{username}/{repository}/blob/{file_path}`
  - 组件: `FileViewer`, `SyntaxHighlighter`, `FileActions`
  - 功能: 语法高亮、版本切换、下载、编辑跳转

- **文件历史页面** (`/{username}/{repository}/commits/{file_path}`) - 文件版本历史 (✅ 已实现)

  - 使用 API: `GET /api/file-editor/files/{file_id}/versions`
  - 组件: `VersionHistory`, `VersionDiff`
  - 功能: 版本列表、版本比较、回滚操作、差异对比

- **草稿管理页面** (`/{username}/{repository}/drafts`) - 草稿管理中心 (✅ 已实现)
  - 使用 API: `GET /api/repositories/{username}/{repository}/drafts`
  - 组件: `DraftManager`, `DraftRecovery`, `DraftAutoSaver`
  - 功能: 草稿列表、恢复编辑、批量管理、自动保存

#### 管理员页面 ✅ 已实现

- **管理员入口页面** (`/admin`) - 管理员访问控制和重定向 (✅ 已实现)

  - 使用 API: `GET /api/auth/me`
  - 组件: `AdminHeader`, `AdminSidebar`

- **管理员仪表板** (`/admin/dashboard`) - 系统概览和统计信息 (✅ 已实现)

  - 使用 API: `GET /api/admin/dashboard`, `GET /api/admin/system/health`
  - 组件: `DashboardCard`, `SystemHealthCard`, `AdminSidebar`

- **用户管理页面** (`/admin/users`) - 用户列表、搜索、状态管理 (✅ 已实现)

  - 使用 API: `GET /api/admin/users`, `PUT /api/admin/users/{user_id}/status`
  - 组件: `SearchBar`, `Pagination`, `Modal`

- **仓库管理页面** (`/admin/repositories`) - 仓库列表、状态管理、软删除恢复 (✅ 已实现)

  - 使用 API: `GET /api/admin/repositories`, `PUT /api/admin/repositories/{repository_id}/status`, `POST /api/admin/repositories/{repository_id}/restore`, `DELETE /api/admin/repositories/{repository_id}/hard-delete`, `GET /api/admin/repositories/stats`
  - 组件: `RepositoryCard`, `Modal`, `Alert`

- **存储管理页面** (`/admin/storage`) - 存储统计、清理工具 (✅ 已实现)

  - 使用 API: `GET /api/admin/storage/stats`, `POST /api/admin/storage/cleanup`
  - 组件: `StorageMonitor`, `DashboardCard`, `Button`

- **系统监控页面** (`/admin/system`) - 健康检查、日志查看 (✅ 已实现)

  - 使用 API: `GET /api/admin/system/health`, `GET /api/admin/logs`, `GET /api/system/info`
  - 组件: `SystemHealthCard`, `LogViewer`, `Alert`

- **设置管理页面** (`/admin/settings`) - 系统配置管理 (✅ 已实现)
  - 使用 API: `GET /api/system/config`, `PUT /api/system/config`, `GET /api/system/info`, `POST /api/system/maintenance`
  - 组件: `FormField`, `Input`, `Button`, `Alert`

### 🧩 组件系统

#### 布局组件

- **Header.svelte** - 顶部导航栏 (✅ 已实现)

  - 功能: 导航菜单、用户登录状态、搜索框
  - 使用 API: `GET /api/auth/me`

- **Footer.svelte** - 底部信息栏 (✅ 已实现)
  - 功能: 版权信息、链接、统计数据

#### 用户相关组件

- **UserProfile.svelte** - 用户资料展示 (✅ 已实现)

  - 使用 API: `GET /api/users/{username}`, `GET /api/users/{username}/stats`, `GET /api/users/{username}/storage`
  - 功能: 用户信息、关注/取消关注、统计数据、存储使用情况

- **UserAvatar.svelte** - 用户头像 (✅ 已实现)
  - 功能: 头像展示、默认头像生成

#### 仓库相关组件

- **RepositoryCard.svelte** - 仓库卡片 (✅ 已实现)

  - 使用 API: `POST /api/{username}/{repository}/star`, `DELETE /api/{username}/{repository}/star`
  - 功能: 仓库信息展示、点赞/取消点赞

- **RepositoryHeader.svelte** - 仓库头部 (✅ 已实现)

  - 功能: 仓库名称、描述、统计信息、操作按钮

- **RepositoryStats.svelte** - 仓库统计 (✅ 已实现)

  - 功能: 点赞数、下载数、观看数、Fork 数

- **RepositoryTabs.svelte** - 仓库选项卡 (✅ 已实现)
  - 功能: 文件、README、设置等选项卡切换

#### 文件管理组件

- **FileTree.svelte** - 文件浏览器 (✅ 已实现)

  - 使用 API: `GET /api/{username}/{repository}/tree/main`
  - 功能: 文件目录树展示、文件下载

- **FileUpload.svelte** - 文件上传 (✅ 已实现)

  - 使用 API: `POST /api/{username}/{repository}/upload`
  - 功能: 拖拽上传、进度显示、文件预览、多文件上传、上传状态管理

- **FileManager.svelte** - 文件管理器 (✅ 已实现)

  - 功能: 文件批量操作、文件夹管理、文件下载、文件删除

#### 个人数据空间组件

- **PersonalFileManager.svelte** - 个人文件管理器 (✅ 已实现)

  - 使用 API: `GET /api/personal-files/{username}/browse`, `DELETE /api/personal-files/files/{file_id}`, `PUT /api/personal-files/{username}/folders/{folder_id}`
  - 功能: 个人文件浏览、文件夹管理、文件删除、文件下载、公开/私有设置

- **PersonalFileUpload.svelte** - 个人文件上传 (✅ 已实现)

  - 使用 API: `POST /api/personal-files/{username}/upload-url`, `POST /api/personal-files/{username}/complete-upload`
  - 功能: 个人文件上传、文件夹选择、上传进度跟踪、上传完成提示

- **ReadmeViewer.svelte** - README 查看器 (✅ 已实现)
  - 功能: Markdown 渲染、YAML frontmatter 展示

#### 搜索和分类组件

- **SearchBar.svelte** - 搜索栏 (✅ 已实现)

  - 使用 API: `GET /api/search/repositories`, `GET /api/search/users`
  - 功能: 实时搜索、搜索建议、搜索历史

- **ClassificationFilter.svelte** - 分类筛选器 (✅ 已实现)

  - 使用 API: `GET /api/classifications`
  - 功能: 三级分类筛选、分类树展示

- **CategoryFilter.svelte** - 分类筛选器 (✅ 已实现)
  - 功能: 快速分类筛选、标签管理

#### 社交和通知组件

- **SocialButton.svelte** - 社交按钮 (✅ 已实现)

  - 使用 API: `POST /api/users/{username}/follow`, `DELETE /api/users/{username}/follow`
  - 功能: 关注/取消关注、点赞/取消点赞

- **NotificationCenter.svelte** - 通知中心 (⚠️ 待实现)

  - 使用 API: `GET /api/notifications`, `POST /api/notifications/{id}/read` (⚠️ API 未实现)
  - 功能: 通知列表、标记已读、通知删除

- **NotificationTrigger.svelte** - 通知触发器 (⚠️ 待实现)

  - 使用 API: `GET /api/notifications/unread-count` (⚠️ API 未实现)
  - 功能: 未读通知数量、通知弹出

- **CommentSection.svelte** - 评论区 (⚠️ 待实现)
  - 使用 API: `GET /api/comments`, `POST /api/comments`, `POST /api/comments/{id}/like` (⚠️ API 未实现)
  - 功能: 评论展示、发表评论、点赞评论

#### 数据展示组件

- **ActivityFeed.svelte** - 活动动态 (⚠️ 待实现)

  - 使用 API: `GET /api/activities` (⚠️ API 未实现)
  - 功能: 用户活动流、操作历史

- **ModelCard.svelte** - 模型卡片 (✅ 已实现)

  - 功能: 模型信息展示、模型类型标识

- **ServiceCard.svelte** - 服务卡片 (⚠️ 待实现)
  - 使用 API: `GET /api/{username}/{repository}/services` (⚠️ API 未实现)
  - 功能: 服务状态展示、服务操作

#### 编辑器组件

- **YAMLMetadataEditor.svelte** - YAML 编辑器 (🔄 部分实现)
  - 使用 API: `GET /api/{username}/{repository}/metadata`, `PUT /api/{username}/{repository}/metadata` (⚠️ API 未实现)
  - 功能: YAML 编辑、语法高亮、实时预览

#### 文件编辑与版本控制组件 (✅ 已实现)

- **FileEditor.svelte** - 主文件编辑器 (✅ 已实现)

  - 使用 API: `GET /api/file-editor/files/{file_id}/versions/{version_id}/content`, `POST /api/file-editor/files/{file_id}/versions`
  - 功能: CodeMirror 6 编辑器、语法高亮、自动保存、多语言支持、主题切换

- **EditorToolbar.svelte** - 编辑器工具栏 (✅ 已实现)

  - 功能: 保存、撤销、重做、格式化、预览、视图切换

- **EditorStatusBar.svelte** - 编辑器状态栏 (✅ 已实现)

  - 功能: 光标位置、字数统计、语言显示、保存状态

- **EditorSidebar.svelte** - 编辑器侧边栏 (✅ 已实现)

  - 功能: 文件树、版本历史、协作者状态

- **VersionHistory.svelte** - 文件版本历史 (✅ 已实现)

  - 使用 API: `GET /api/file-editor/files/{file_id}/versions`
  - 功能: 版本列表、提交信息、作者信息、版本对比、恢复操作

- **VersionDiff.svelte** - 版本差异查看器 (✅ 已实现)

  - 使用 API: `GET /api/file-editor/files/{file_id}/versions/{old_version_id}/diff/{new_version_id}`
  - 功能: 分屏/统一视图、语法高亮差异、行号显示、统计信息

- **CollaborationStatus.svelte** - 协作状态组件 (✅ 已实现)

  - 使用 API: `GET /api/file-editor/files/{file_id}/collaboration`
  - 功能: 活跃用户列表、编辑状态、权限显示、实时轮询

- **DraftManager.svelte** - 草稿管理器 (✅ 已实现)

  - 使用 API: `GET /api/file-editor/files/{file_id}/drafts`, `POST /api/file-editor/files/{file_id}/drafts`
  - 功能: 草稿列表、预览、恢复、删除、批量操作

- **DraftAutoSaver.svelte** - 自动保存组件 (✅ 已实现)

  - 使用 API: `POST /api/file-editor/files/{file_id}/drafts`
  - 功能: 定时自动保存、状态指示、错误处理

- **DraftRecovery.svelte** - 草稿恢复组件 (✅ 已实现)
  - 使用 API: `GET /api/file-editor/files/{file_id}/drafts`
  - 功能: 启动时恢复提示、智能推荐、批量恢复

## 🔧 开发指南

### 数据库迁移

```bash
# 1. 修改模型后生成迁移
cd backend
alembic revision --autogenerate -m "Add new field"

# 2. 检查生成的迁移文件
# 编辑 alembic/versions/xxx_add_new_field.py

# 3. 应用迁移
alembic upgrade head

# 4. 回滚迁移 (如需要)
alembic downgrade -1
```

### 前端组件开发

```javascript
// 创建新组件
// src/lib/components/NewComponent.svelte

<script>
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  // 组件逻辑
</script>

<!-- 组件模板 -->
<div class="component-class">
  <!-- HTML结构 -->
</div>

<style>
  /* 组件样式 */
</style>
```

## 🚀 环境启动指南

### 📋 系统要求

**基础环境**

- **Node.js** 18.0+
- **Python** 3.12+
- **Docker** 20.10+ & **Docker Compose** 2.0+
- **PostgreSQL** 15+
- **Redis** 7.0+
- **MinIO** (对象存储)

**系统资源**

- **内存**: 最少 4GB，推荐 8GB+
- **存储**: 最少 10GB 可用空间
- **网络**: 稳定的互联网连接

### 🛠️ 开发环境启动

#### 1. 克隆项目并设置

```bash
# 克隆仓库
git clone https://github.com/your-username/GeoML-hub.git
cd GeoML-hub

# 检查系统要求
node --version    # 应该 >= 18.0
python --version  # 应该 >= 3.12
docker --version  # 应该 >= 20.10
```

#### 2. 启动基础服务

```bash
# 启动数据库和缓存服务
docker-compose up -d postgres redis minio

# 等待服务完全启动
sleep 10

# 验证服务状态
docker-compose ps
```

#### 3. 后端服务设置

```bash
cd backend

# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量 (开发环境)
export DATABASE_URL="postgresql://geoml:password@localhost:5432/geoml_hub"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="dev-secret-key-change-in-production"
export MINIO_ENDPOINT="localhost:9000"
export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="minioadmin"
export MINIO_SECURE="false"

# 数据库初始化
alembic upgrade head                    # 确保包含最新的 is_admin 字段迁移
python scripts/init_classifications.py

# 创建管理员用户 (可选)
# python scripts/create_admin_user.py

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. 前端服务设置

```bash
# 新终端窗口
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local
# 编辑 .env.local 设置 API 地址

# 启动开发服务器
npm run dev
```

#### 5. 访问应用

- **前端应用**: http://localhost:5173
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **MinIO 控制台**: http://localhost:9001 (minioadmin/minioadmin)

### 🏭 生产环境部署

#### 1. 环境变量配置

```bash
# 创建生产环境配置文件
cat > .env.production << EOF
# 数据库配置
DATABASE_URL=postgresql://geoml_user:secure_password@db.example.com:5432/geoml_hub_prod
REDIS_URL=redis://redis.example.com:6379/0

# 安全配置
SECRET_KEY=your-super-secure-random-secret-key-here
JWT_SECRET_KEY=another-secure-jwt-secret

# 服务配置
CORS_ORIGINS=https://geoml-hub.example.com,https://api.geoml-hub.example.com
ALLOWED_HOSTS=geoml-hub.example.com,api.geoml-hub.example.com

# 对象存储配置
MINIO_ENDPOINT=storage.example.com:9000
MINIO_ACCESS_KEY=your_production_access_key
MINIO_SECRET_KEY=your_production_secret_key
MINIO_SECURE=true
MINIO_DEFAULT_BUCKET=geoml-hub-prod

# 外部认证服务
EXTERNAL_AUTH_URL=https://auth.example.com
EXTERNAL_AUTH_CLIENT_ID=your_client_id
EXTERNAL_AUTH_CLIENT_SECRET=your_client_secret

# 模型服务管理配置 (V2.0 新增)
SERVICE_PORT_START=7000
SERVICE_PORT_END=8000
MAX_SERVICES_PER_USER=20
MAX_SERVICES_PER_REPOSITORY=3
SERVICE_IDLE_TIMEOUT=30
HEALTH_CHECK_INTERVAL=60
DEFAULT_CPU_LIMIT=0.2
DEFAULT_MEMORY_LIMIT=256Mi
MAX_CPU_LIMIT=0.5
MAX_MEMORY_LIMIT=1Gi
AUTO_START_ON_VISIT=true
MAX_AUTO_START_RETRIES=3
EXPONENTIAL_BACKOFF_ENABLED=true
DOCKER_MS_HOST=unix:///var/run/docker.sock
DOCKER_IMAGE_NAME=geoml-service:latest

# 性能配置
MAX_FILE_SIZE_MB=500
MAX_TOTAL_SIZE_GB=100
UPLOAD_SESSION_EXPIRES_HOURS=24
WORKER_PROCESSES=4

# 监控配置
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
LOG_LEVEL=INFO
ENABLE_METRICS=true
EOF
```

#### 2. 数据库准备

```bash
# 生产数据库初始化
cd backend

# 加载生产环境变量
source .env.production

# 运行数据库迁移 (包含最新的用户权限字段)
alembic upgrade head

# 初始化基础数据
python scripts/init_classifications.py

# 创建管理员账户 (交互式)
python scripts/create_admin_user.py

# 验证数据库连接
python -c "from app.database import get_async_db; print('Database connection successful')"
```

#### 3. Docker 生产部署

```bash
# 构建生产镜像
docker-compose -f docker-compose.prod.yml build

# 启动生产服务
docker-compose -f docker-compose.prod.yml up -d

# 检查服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f api
```

#### 4. 传统服务器部署

```bash
# 后端生产启动
cd backend

# 使用 Gunicorn 启动
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --keep-alive 5 \
  --access-logfile /var/log/geoml-hub/access.log \
  --error-logfile /var/log/geoml-hub/error.log

# 前端生产构建
cd frontend
npm run build

# 使用 Nginx 服务静态文件
sudo cp -r build/* /var/www/geoml-hub/
sudo systemctl reload nginx
```

### 🔧 管理脚本

#### 管理员用户管理

```bash
# 创建管理员用户 (交互式)
cd backend
python scripts/create_admin_user.py

# 列出现有管理员用户
python scripts/create_admin_user.py --list

# 查看帮助信息
python scripts/create_admin_user.py --help
```

#### 数据库初始化脚本

```bash
# 初始化分类数据
python scripts/init_classifications.py

# 创建管理员用户 (交互式)
python scripts/create_admin_user.py
```

### 🔧 开发工具和调试

#### 开发服务器命令

```bash
# 后端开发服务器 (热重载)
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端开发服务器 (热重载)
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173

# 数据库控制台
cd backend
python -c "from app.database import get_async_db; import asyncio; asyncio.run(get_async_db().__anext__())"

# MinIO 控制台
open http://localhost:9001
```

#### 调试工具

```bash
# 查看数据库表结构
cd backend
alembic current
alembic history

# 查看 API 文档
open http://localhost:8000/docs

# 检查代码格式
cd backend
black . --check
flake8 .

cd frontend
npm run lint
npm run format
```

### 📊 性能监控

#### 健康检查端点

```bash
# 系统健康检查
curl http://localhost:8000/health

# 数据库连接检查
curl http://localhost:8000/health/db

# MinIO 连接检查
curl http://localhost:8000/health/storage

# 详细系统信息
curl http://localhost:8000/health/detailed
```

#### 日志监控

```bash
# 应用日志
tail -f /var/log/geoml-hub/app.log

# Nginx 访问日志
tail -f /var/log/nginx/access.log

# Docker 容器日志
docker-compose logs -f api
docker-compose logs -f frontend
```

### 🔒 安全配置

#### SSL/TLS 配置

```bash
# 使用 Let's Encrypt 自动证书
sudo certbot --nginx -d geoml-hub.example.com

# 手动证书配置
sudo cp cert.pem /etc/ssl/certs/geoml-hub.crt
sudo cp key.pem /etc/ssl/private/geoml-hub.key
```

#### 防火墙配置

```bash
# 开放必要端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

#### 重启服务

```bash
# 重启开发环境
docker-compose restart
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev

# 重启生产环境
sudo systemctl restart geoml-hub-api
sudo systemctl restart nginx
docker-compose -f docker-compose.prod.yml restart
```

## 📦 快速部署

### Docker 一键部署 (推荐)

```bash
# 生产环境一键启动
git clone https://github.com/your-username/GeoML-hub.git
cd GeoML-hub
cp .env.example .env.production
# 编辑 .env.production 设置生产环境变量
docker-compose -f docker-compose.prod.yml up -d
```

### 开发环境快速启动

```bash
# 克隆并启动开发环境
git clone https://github.com/your-username/GeoML-hub.git
cd GeoML-hub
docker-compose up -d postgres redis minio
cd backend && pip install -r requirements.txt
alembic upgrade head && python scripts/init_classifications.py
python scripts/create_admin_user.py  # 创建管理员用户（可选）
uvicorn app.main:app --reload &
cd ../frontend && npm install && npm run dev
```

## tls 证书（若需要）

```bash
  # 创建证书目录
  mkdir -p /etc/docker/certs
  cd /etc/docker/certs

  # 1. 清理所有旧证书
  rm -f *.pem *.csr *.cnf *.srl

  # 2. 生成CA私钥
  openssl genrsa -out ca-key.pem 4096

  # 3. 生成CA证书（10年有效期）
  openssl req -new -x509 -days 3650 -key ca-key.pem -sha256 -out ca.pem -subj
  "/C=CN/ST=Beijing/L=Beijing/O=GeoML/OU=Docker/CN=CA"

  # 4. 生成服务器私钥
  openssl genrsa -out server-key.pem 4096

  # 5. 生成服务器证书签名请求
  openssl req -subj
  "/C=CN/ST=Beijing/L=Beijing/O=GeoML/OU=Docker/CN=172.21.252.231" -sha256 -new
  -key server-key.pem -out server.csr

  # 6. 创建SAN扩展文件
  cat > server-extfile.cnf <<EOF
  subjectAltName = IP:172.21.252.231,IP:127.0.0.1,DNS:localhost
  extendedKeyUsage = serverAuth
  EOF

  # 7. 使用CA签发服务器证书
  openssl x509 -req -days 3650 -sha256 -in server.csr -CA ca.pem -CAkey
  ca-key.pem -out server-cert.pem -extfile server-extfile.cnf -CAcreateserial

  # 8. 生成客户端私钥
  openssl genrsa -out key.pem 4096

  # 9. 生成客户端证书签名请求
  openssl req -subj "/C=CN/ST=Beijing/L=Beijing/O=GeoML/OU=Client/CN=client"
  -new -key key.pem -out client.csr

  # 10. 创建客户端扩展文件
  cat > client-extfile.cnf <<EOF
  extendedKeyUsage = clientAuth
  EOF

  # 11. 使用CA签发客户端证书
  openssl x509 -req -days 3650 -sha256 -in client.csr -CA ca.pem -CAkey
  ca-key.pem -out cert.pem -extfile client-extfile.cnf -CAcreateserial

  # 12. 验证证书是否正确生成
  echo "验证CA证书和私钥匹配："
  openssl x509 -noout -modulus -in ca.pem | openssl md5
  openssl rsa -noout -modulus -in ca-key.pem | openssl md5

  echo "验证服务器证书："
  openssl verify -CAfile ca.pem server-cert.pem

  echo "验证客户端证书："
  openssl verify -CAfile ca.pem cert.pem

  echo "查看服务器证书SAN："
  openssl x509 -in server-cert.pem -text -noout | grep -A 3 "Subject Alternative
   Name"

  # 13. 清理临时文件
  rm server.csr client.csr server-extfile.cnf client-extfile.cnf

  # 设置权限
  chmod 400 *-key.pem key.pem
  chmod 444 *.pem

  ca.pem, cert.pem, key.pem 放置合适的位置

  ⏺ # 1. 创建或编辑Docker守护进程配置
  sudo mkdir -p /etc/docker
  sudo bash -c 'cat > /etc/docker/daemon.json <<EOF
  {
    "hosts": ["fd://", "tcp://0.0.0.0:2376"],
    "tls": true,
    "tlscert": "/etc/docker/certs/server-cert.pem",
    "tlskey": "/etc/docker/certs/server-key.pem",
    "tlsverify": true,
    "tlscacert": "/etc/docker/certs/ca.pem"
  }
  EOF'

  # 2. 创建systemd服务覆盖文件
  sudo mkdir -p /etc/systemd/system/docker.service.d
  sudo bash -c 'cat >
  /etc/systemd/system/docker.service.d/override.conf <<EOF
  [Service]
  ExecStart=
  ExecStart=/usr/bin/dockerd
  EOF'

  # 3. 重新加载systemd并重启Docker
  sudo systemctl daemon-reload
  sudo systemctl restart docker

  # 4. 验证Docker TLS是否启用
  sudo systemctl status docker
  sudo netstat -tlnp | grep :2376

  步骤3: 复制客户端证书到你的应用机器

  # 3. 设置正确的权限
  sudo chown -R $(whoami):$(whoami) /tls/docker/certs
  chmod 444 /tls/docker/certs/ca.pem /tls/docker/certs/cert.pem
  chmod 400 /tls/docker/certs/key.pem

  2. 更新你的应用配置

  在你的 .env 文件中：

  # Docker TLS配置
  DOCKER_MS_HOST=tcp://你的Docker服务器IP:2376
  DOCKER_MS_TLS_VERIFY=true
  DOCKER_MS_CERT_PATH=/tls/docker/certs
  DOCKER_MS_TIMEOUT=60

  3. 测试TLS连接

  # 在应用服务器上测试连接
  docker --tlsverify \
      --tlscacert=/tls/docker/certs/ca.pem \
      --tlscert=/tls/docker/certs/cert.pem \
      --tlskey=/tls/docker/certs/key.pem \
      -H=tcp://你的Docker服务器IP:2376 \
      version
```
