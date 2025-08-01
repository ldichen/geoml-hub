# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GeoML-Hub v2.0 is a comprehensive geoscience machine learning model repository platform designed as the first ML model hub specifically for geographic sciences, rebuilt with a Hugging Face-style architecture. The platform provides user namespaces, social features, and modern file management for discovering, sharing, and deploying geospatial machine learning models.

## Architecture

### System Structure (v2.0)

- **Frontend**: SvelteKit with TypeScript and TailwindCSS
- **Backend**: FastAPI with SQLAlchemy 2.0 (async ORM)
- **Database**: PostgreSQL with user-repository architecture + three-level classification system
- **File Storage**: MinIO object storage for scalable file management
- **Authentication**: External authentication service integration
- **Containerization**: Docker with docker-compose for development
- **API**: RESTful API with Pydantic validation
- **Migration**: Alembic for database schema management

## 📖 Documentation Consistency Rule

**CRITICAL**: README.md must always reflect the current state of the codebase. This is a mandatory requirement for this project.

### 📋 Documentation Sync Requirements

Whenever you make changes to the codebase, you MUST update the README.md file to reflect:

1. **Project Structure Changes**
   - Add new directories/modules to the project structure section
   - Remove outdated directory references
   - Update file organization explanations

2. **Database Schema Updates**
   - Update database table definitions when models change
   - Add new relationships and constraints
   - Update migration information

3. **API Interface Changes**
   - Add new API endpoints with proper status indicators (✅/⚠️/🔄)
   - Update existing endpoint descriptions
   - Remove deprecated endpoints
   - Update request/response examples

4. **Frontend Components Updates**
   - Add new component documentation
   - Update component organization structure
   - Add usage examples for new components

5. **Configuration Changes**
   - Update environment variables
   - Add new deployment instructions
   - Update Docker configurations

### 🔄 Automatic Documentation Updates

You should automatically update README.md when:
- New API endpoints are implemented
- Database schema changes occur
- New components are created
- Project structure is modified
- Configuration requirements change

### 📊 Status Indicators

Always use these status indicators in API documentation:
- ✅ **已实现** (Implemented and tested)
- ⚠️ **待实现** (Designed but not implemented)
- 🔄 **部分实现** (Core functionality implemented, refinements needed)

### 🎯 Priority Sections

These sections require immediate updates when changed:
1. **API 接口 v2.0** - High priority
2. **项目结构** - High priority
3. **数据库架构 v2.0** - Medium priority
4. **核心组件** - Medium priority
5. **环境启动指南** - Low priority (unless major changes)

### 🚫 Documentation Rules

- README.md should never be outdated or incorrect
- All implemented features must be documented
- All API endpoints must have status indicators
- Code examples should be current and working
- Remove documentation for deprecated features

### 🔗 Documentation Synchronization Rule

**CRITICAL**: README.md的不同章节必须保持相互同步和联动。当修改任何一个章节时，必须检查并同步更新相关联的章节。

#### 同步规则：

1. **项目结构 ↔ 前端内容**
   - 项目结构中的目录变更必须同步到前端页面和组件列表
   - 前端组件新增/删除必须在项目结构中体现

2. **数据库架构 ↔ API接口**
   - 数据库表结构变更必须同步到相关API端点
   - 新增数据库字段必须在API响应格式中体现

3. **API接口 ↔ 前端内容**
   - **关键规则**: 前端内容中标注"未实现"的API，在API章节中必须存在且也标注为"未实现"
   - API端点状态变更（✅/⚠️/🔄）必须同步到使用该API的前端组件状态
   - 新增API端点必须在相关前端组件中体现使用关系

4. **前端内容 ↔ 项目结构**
   - 前端页面列表必须与 `frontend/src/routes/` 目录结构一致
   - 前端组件列表必须与 `frontend/src/lib/components/` 目录结构一致

#### 检查清单：

修改任何章节时，必须检查以下联动关系：
- [ ] 项目结构是否与实际目录一致
- [ ] API状态是否与前端组件使用状态一致
- [ ] 数据库字段是否与API响应格式一致
- [ ] 前端组件是否与项目结构目录一致
- [ ] 所有相关章节的状态指示符是否同步

**示例**：
- 如果前端组件标注使用 `GET /api/notifications` (⚠️ 待实现)
- 那么API章节必须包含该端点并标注为 (⚠️ 待实现)
- 如果该API涉及通知功能，数据库章节也应包含相关表结构

**Remember**: Documentation is not optional - it's a core requirement for this project's maintainability and usability.

# Summary Instructions for Custom Compacting

When using `/compact`, please apply the following strategy to summarize conversation history efficiently and accurately:

## 🧱 1. System Structure

- Summarize the v2.0 architecture (user namespaces, repositories, MinIO storage)
- Retain directory/module structure explanations for new components
- Keep key interactions between components (backend ↔ MinIO, auth service integration)

## 🧠 2. Design Decisions

- Preserve Hugging Face-style architecture choices
- Keep reasoning behind user namespace and repository structure
- Include social features and metadata-driven approach rationale

## 🧰 3. Code Changes and Fixes

- Keep v2.0 refactoring changes (new models, services, APIs)
- Retain MinIO integration and YAML parsing implementations
- Include migration strategies and backward compatibility solutions

## 📦 4. Database & Models

- Preserve v2.0 database schema changes and new table structures
- Include user-repository relationship patterns
- Keep MinIO integration and file storage patterns

## ✅ 5. Final Outputs

- Retain v2.0 backend implementation (models, services, APIs)
- Include MinIO service and YAML parser utilities
- Keep updated configuration and deployment instructions

---

## 🚫 Avoid including in summary:

- v1.0-only implementation details (unless for compatibility context)
- Redundant backend refactoring trial-and-error
- Minor configuration tweaks unless critical for v2.0 functionality
- Console logs or verbose output unless relevant to v2.0 debugging

---

## V2.0 Page Development Guidelines

### Page Naming Conventions

- **User Pages**: `/{username}` pattern for all user-related pages
- **Repository Pages**: `/{username}/{repo_name}` pattern for repository-related pages
- **System Pages**: `/admin/*`, `/settings/*` for system management
- **Auth Pages**: `/login`, `/register`, `/auth/*` for authentication

### Component Organization

```
src/lib/components/
├── layout/              # Layout components
│   ├── Header.svelte
│   ├── Sidebar.svelte
│   └── Footer.svelte
├── user/               # User-related components
│   ├── UserProfile.svelte
│   ├── UserAvatar.svelte
│   └── UserStats.svelte
├── repository/         # Repository components
│   ├── RepositoryCard.svelte
│   ├── RepositoryHeader.svelte
│   └── FileTree.svelte
├── social/             # Social interaction components
│   ├── StarButton.svelte
│   ├── FollowButton.svelte
│   └── SocialStats.svelte
├── file/               # File management components
│   ├── FileUpload.svelte
│   ├── FilePreview.svelte
│   └── DropZone.svelte
└── common/             # Shared components
    ├── LoadingSpinner.svelte
    ├── Modal.svelte
    └── Toast.svelte
```

### API Integration Patterns

```javascript
// API client usage pattern
import { api } from "$lib/utils/api.js";

// Repository operations
const repository = await api.repositories.get(username, repoName);
const files = await api.repositories.getFiles(username, repoName);

// User operations
const user = await api.users.get(username);
const repositories = await api.users.getRepositories(username);

// Social operations
await api.repositories.star(username, repoName);
await api.users.follow(username);

// File operations
const uploadSession = await api.files.initiateUpload(repositoryId, fileInfo);
const downloadUrl = await api.files.getDownloadUrl(fileId);
```

### State Management Guidelines

- Use Svelte stores for global state (user auth, theme, etc.)
- Use component state for local UI state
- Use URL parameters for shareable state (filters, pagination)
- Cache frequently accessed data (user profiles, classifications)

### Performance Considerations

- Implement lazy loading for large file lists
- Use virtual scrolling for long lists
- Optimize images with proper sizing and formats
- Implement progressive loading for repository content
- Cache API responses where appropriate

# important-instruction-reminders

Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (\*.md) or README files. Only create documentation files if explicitly requested by the User.
