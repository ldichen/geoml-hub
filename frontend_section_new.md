## 前端
### 🖥️ 技术栈架构
- **框架**: SvelteKit (SSR/SPA)
- **样式**: TailwindCSS + 自定义 CSS
- **状态管理**: Svelte Stores (auth, theme, toast)
- **类型检查**: TypeScript
- **构建工具**: Vite
- **国际化**: 内置 i18n 支持 (中文/英文)
- **图标**: Lucide Svelte
- **代码编辑器**: CodeMirror 6

### 📁 项目结构
```
frontend/src/
├── lib/
│   ├── components/           # 组件库
│   │   ├── ui/              # 基础 UI 组件
│   │   ├── admin/           # 管理员专用组件
│   │   ├── service/         # 模型服务相关组件
│   │   ├── editor/          # 文件编辑器组件
│   │   ├── draft/           # 草稿管理组件
│   │   ├── version/         # 版本控制组件
│   │   └── collaboration/   # 协作功能组件
│   ├── stores/              # 状态管理
│   │   ├── auth.js         # 用户认证状态
│   │   ├── theme.js        # 主题切换
│   │   └── toast.js        # 消息提示
│   ├── utils/               # 工具函数
│   │   ├── api.js          # API 客户端
│   │   ├── auth.js         # 认证工具
│   │   ├── constants.js    # 常量定义
│   │   └── imagePreloader.js # 图片预加载
│   ├── types/               # TypeScript 类型定义
│   └── i18n/               # 国际化配置
└── routes/                  # 页面路由
    ├── (app)/              # 主应用布局
    ├── admin/              # 管理员页面
    └── [username]/         # 用户空间
```

### 🖥️ 页面架构 (SvelteKit)

#### 🏠 核心页面
- **主页** (`/`) - 仓库展示与筛选 (✅ 已实现)
  - 使用 API: `GET /api/repositories`, `GET /api/classifications`, `GET /api/search/trending`
  - 核心组件: `RepositoryCard`, `ClassificationFilter`, `SearchBar`, `CategoryFilter`
  - 功能特性: 
    - 🔍 智能搜索与分类筛选
    - 🏷️ 三级分类体系导航
    - 📈 热门仓库推荐
    - 📄 分页加载与无限滚动
    - 🎯 实时搜索建议

- **用户主页** (`/{username}`) - 个人空间中心 (✅ 已实现)
  - 使用 API: `GET /api/users/{username}`, `GET /api/users/{username}/repositories`, `GET /api/users/{username}/starred`, `GET /api/users/{username}/storage`
  - 核心组件: `UserProfile`, `UserAvatar`, `RepositoryCard`, `PersonalFileManager`
  - 功能特性:
    - 👤 用户信息展示与编辑
    - 📚 个人仓库管理 (创建、删除、设置)
    - ⭐ 星标仓库展示 (✅ 最新实现)
    - 👥 关注/粉丝系统
    - 💾 存储空间监控
    - 📁 **个人数据空间**: 文件上传下载、文件夹管理、权限控制

- **仓库页面** (`/{username}/{repository}`) - 仓库详情中心 (✅ 已实现)
  - 使用 API: `GET /api/repositories/{owner}/{repo}`, `GET /api/repositories/{owner}/{repo}/files`
  - 核心组件: `RepositoryHeader`, `FileTree`, `ReadmeViewer`, `ServiceList`
  - 功能特性:
    - 📋 Model Card (README) 渲染
    - 📁 文件树浏览与管理
    - ⚡ **模型服务管理**: 创建、启动、监控、日志查看
    - 📊 仓库统计与分析
    - ⭐ 社交功能 (星标、下载统计)
    - 🔒 权限控制 (编辑、删除)

#### 📝 文件管理与编辑
- **文件编辑页面** (`/{username}/{repository}/edit/{...file_path}`) - 在线代码编辑器 (✅ 已实现)
  - 使用 API: `GET /api/file-editor/files/{file_id}/versions`, `POST /api/file-editor/files/{file_id}/versions`
  - 核心组件: `FileEditor`, `EditorToolbar`, `EditorStatusBar`, `EditorSidebar`
  - 功能特性:
    - 💻 CodeMirror 6 编辑器 (语法高亮、自动补全)
    - 💾 自动保存与草稿恢复
    - 📝 版本提交与消息记录
    - 👥 实时协作状态显示
    - 🔍 搜索替换功能

- **文件查看页面** (`/{username}/{repository}/blob/{...file_path}`) - 文件内容展示 (✅ 已实现)
  - 使用 API: `GET /api/repositories/{owner}/{repo}/blob/{file_path}`
  - 核心组件: `FileViewer`, `SyntaxHighlighter`
  - 功能特性:
    - 🎨 多语言语法高亮
    - 📥 文件下载功能
    - ✏️ 快速编辑跳转 (所有者权限)
    - 🔍 行号与搜索定位

- **文件历史页面** (`/{username}/{repository}/commits/{...file_path}`) - 版本控制 (✅ 已实现)
  - 使用 API: `GET /api/file-editor/files/{file_id}/versions`
  - 核心组件: `VersionHistory`, `VersionDiff`
  - 功能特性:
    - 📜 完整版本历史记录
    - 🔄 版本间差异对比
    - ⏪ 版本回滚功能
    - 👤 提交者信息展示

- **草稿管理页面** (`/{username}/{repository}/drafts`) - 草稿中心 (✅ 已实现)
  - 使用 API: `GET /api/repositories/{owner}/{repo}/drafts`
  - 核心组件: `DraftManager`, `DraftRecovery`, `DraftAutoSaver`
  - 功能特性:
    - 📝 草稿列表管理
    - 🔄 快速恢复编辑
    - 🗑️ 批量删除清理
    - ⏰ 自动保存机制

#### 🔍 功能页面
- **搜索页面** (`/search`) - 全局搜索中心 (✅ 已实现)
  - 使用 API: `GET /api/search/repositories`, `GET /api/search/users`, `GET /api/search/suggestions`
  - 核心组件: `SearchBar`, `RepositoryCard`, `UserProfile`, `Pagination`
  - 功能特性:
    - 🔍 仓库与用户搜索
    - 🏷️ 高级筛选条件
    - 💡 搜索建议与自动补全
    - 📄 结果分页展示

- **趋势页面** (`/trending`) - 热门发现 (✅ 已实现)
  - 使用 API: `GET /api/search/trending`
  - 核心组件: `RepositoryCard`, `CategoryFilter`
  - 功能特性:
    - 📈 热门仓库排行
    - 📅 时间范围筛选
    - 🏷️ 分类趋势分析

- **新建仓库页面** (`/new`) - 仓库创建向导 (✅ 已实现)
  - 使用 API: `POST /api/repositories`, `GET /api/classifications`
  - 核心组件: `ClassificationSelector`, `YAMLMetadataEditor`, `FormField`
  - 功能特性:
    - 📝 仓库基本信息配置
    - 🏷️ 三级分类选择
    - 📄 YAML 元数据编辑
    - 🔒 可见性设置

#### 🔐 认证页面
- **登录页面** (`/login`) - 用户登录 (✅ 已实现)
  - 使用 API: `POST /api/auth/login`, `POST /api/auth/login/credentials`
  - 核心组件: `FormField`, `Button`, `Input`
  - 功能特性:
    - 📧 邮箱密码登录
    - 🔗 外部认证支持
    - 💾 登录状态保持
    - 🔒 安全验证

- **注册页面** (`/register`) - 用户注册 (✅ 已实现)
  - 使用 API: `POST /api/auth/register`
  - 核心组件: `FormField`, `Button`, `Input`
  - 功能特性:
    - 📝 用户信息注册
    - ✉️ 邮箱验证
    - 🔐 密码强度检查

#### ⚙️ 管理员后台 (✅ 已实现)
- **管理员仪表板** (`/admin/dashboard`) - 系统概览
  - 使用 API: `GET /api/admin/dashboard`, `GET /api/admin/system/health`
  - 核心组件: `DashboardCard`, `SystemHealthCard`, `AdminSidebar`
  - 功能特性:
    - 📊 系统统计数据
    - 🏥 服务健康监控
    - 📈 使用趋势图表
    - ⚠️ 异常警报展示

- **用户管理** (`/admin/users`) - 用户管理中心
  - 使用 API: `GET /api/admin/users`, `PUT /api/admin/users/{user_id}/status`
  - 功能特性: 用户列表、搜索、状态管理、权限分配

- **仓库管理** (`/admin/repositories`) - 仓库管理中心
  - 使用 API: `GET /api/admin/repositories`, 仓库状态管理 API
  - 功能特性: 仓库审核、软删除恢复、统计分析

- **存储管理** (`/admin/storage`) - 存储空间管理
  - 使用 API: `GET /api/admin/storage/stats`, `POST /api/admin/storage/cleanup`
  - 核心组件: `StorageMonitor`
  - 功能特性: 存储统计、清理工具、空间监控

- **系统设置** (`/admin/settings`) - 系统配置管理
  - 使用 API: 系统配置相关 API
  - 功能特性: 系统参数配置、维护模式切换

### 🧩 核心组件库

#### 🎨 基础 UI 组件 (`src/lib/components/ui/`)
```javascript
// 完整的设计系统组件
Button      // 按钮组件 (多种样式、大小、状态)
Input       // 输入框组件 (验证、错误提示)
FormField   // 表单字段包装器
Card        // 卡片容器
Modal       // 模态对话框
Dropdown    // 下拉菜单
Tabs        // 标签页切换
Badge       // 标签徽章
Alert       // 警告提示
Toast       // 消息提示
Pagination  // 分页组件
```

#### 📱 业务组件
```javascript
// 用户相关
UserAvatar         // 用户头像 (多尺寸、加载状态)
UserProfile        // 用户资料卡片
SocialButton       // 社交按钮 (关注、星标)

// 仓库相关
RepositoryCard     // 仓库卡片 (统计信息、标签)
RepositoryHeader   // 仓库头部 (标题、描述、操作)
RepositoryStats    // 仓库统计信息
FileTree          // 文件树展示
ReadmeViewer      // Markdown 渲染器

// 搜索相关
SearchBar         // 搜索栏 (自动补全、历史记录)
ClassificationFilter  // 分类筛选器
CategoryFilter    // 类别筛选器

// 文件管理
FileUpload        // 文件上传 (拖拽、进度条、批量)
FileManager       // 文件管理器
FileDropZone      // 拖拽上传区域
PersonalFileManager   // 个人文件管理
```

#### ⚙️ 专业功能组件
```javascript
// 编辑器相关
FileEditor        // CodeMirror 6 编辑器
EditorToolbar     // 编辑器工具栏
EditorStatusBar   // 编辑器状态栏
EditorSidebar     // 编辑器侧边栏

// 版本控制
VersionHistory    // 版本历史列表
VersionDiff       // 版本差异对比
DraftManager      // 草稿管理器
DraftAutoSaver    // 自动保存器

// 模型服务
ServiceList       // 服务列表
ServiceCard       // 服务卡片
ServiceCreateModal    // 服务创建弹窗
ServiceMonitor    // 服务监控
ServiceLogs       // 服务日志查看器
ServiceSettings   // 服务设置

// 管理员专用
AdminHeader       // 管理员页头
AdminSidebar      // 管理员侧边栏
DashboardCard     // 仪表板卡片
SystemHealthCard  // 系统健康卡片
StorageMonitor    // 存储监控器
LogViewer         // 日志查看器
```

### 🔧 状态管理 (Svelte Stores)
```javascript
// src/lib/stores/auth.js - 用户认证状态
export const user = writable(null);           // 当前用户信息
export const isAuthenticated = derived(...);  // 登录状态
export const isAdmin = derived(...);          // 管理员状态

// src/lib/stores/theme.js - 主题切换
export const theme = writable('light');       // 当前主题
export const toggleTheme = () => {...};       // 主题切换函数

// src/lib/stores/toast.js - 消息提示
export const toasts = writable([]);           // 消息队列
export const addToast = (message) => {...};   // 添加消息
```

### 🌐 API 客户端 (`src/lib/utils/api.js`)
```javascript
// 完整的 RESTful API 客户端
class ApiClient {
  // 认证相关
  auth: {
    login(), register(), logout(), 
    getCurrentUser(), refreshToken()
  }
  
  // 用户相关
  users: {
    get(), list(), update(), 
    getRepositories(), getStarred(), // ✅ 最新实现
    follow(), unfollow()
  }
  
  // 仓库相关
  repositories: {
    get(), list(), create(), update(), delete(),
    getFiles(), uploadFile(), star(), unstar()
  }
  
  // 搜索相关
  search: {
    repositories(), users(), suggestions(),
    trending(), getStats()
  }
  
  // 管理员相关
  admin: {
    getDashboard(), getUsers(), getRepositories(),
    getStorageStats(), performCleanup()
  }
}
```

### 🎨 样式设计系统
```css
/* src/lib/styles/design-system.css */
:root {
  /* 颜色系统 */
  --color-primary: #3b82f6;      /* 主品牌色 */
  --color-secondary: #64748b;    /* 次要颜色 */
  --color-success: #10b981;      /* 成功状态 */
  --color-warning: #f59e0b;      /* 警告状态 */
  --color-error: #ef4444;        /* 错误状态 */
  
  /* 字体系统 */
  --font-sans: 'Inter', system-ui;
  --font-mono: 'Fira Code', monospace;
  
  /* 间距系统 */
  --spacing-xs: 0.25rem;         /* 4px */
  --spacing-sm: 0.5rem;          /* 8px */
  --spacing-md: 1rem;            /* 16px */
  --spacing-lg: 1.5rem;          /* 24px */
  --spacing-xl: 2rem;            /* 32px */
  
  /* 圆角系统 */
  --radius-sm: 0.25rem;          /* 4px */
  --radius-md: 0.5rem;           /* 8px */
  --radius-lg: 0.75rem;          /* 12px */
}
```

### 🌍 国际化支持
```javascript
// src/lib/i18n/locales/zh-CN.json
{
  "nav": {
    "home": "首页",
    "search": "搜索",
    "trending": "趋势",
    "new": "新建仓库"
  },
  "repository": {
    "star": "星标",
    "download": "下载",
    "view": "查看",
    "edit": "编辑"
  }
}
```

### 📱 响应式设计
- **断点系统**: `sm: 640px`, `md: 768px`, `lg: 1024px`, `xl: 1280px`
- **移动优先**: 所有组件支持移动端适配
- **触摸友好**: 按钮、链接等交互元素支持触摸操作
- **性能优化**: 图片懒加载、组件按需加载

### 🔧 开发工具与构建
```bash
# 开发命令
npm run dev          # 启动开发服务器 (热重载)
npm run build        # 生产构建
npm run preview      # 预览构建结果
npm run lint         # 代码检查
npm run format       # 代码格式化
npm run type-check   # TypeScript 类型检查
```

### 📈 性能优化
- **代码分割**: 路由级别的自动代码分割
- **图片优化**: 智能图片预加载和缓存 (`imagePreloader.js`)
- **懒加载**: 组件和图片的按需加载
- **缓存策略**: API 响应缓存和离线支持
- **Bundle 优化**: Tree-shaking 和压缩优化