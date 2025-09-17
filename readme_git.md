# GeoML-Hub Git-Like版本控制系统设计文档

## 📋 项目概述

本文档描述了如何在GeoML-Hub中实现Git-Like的版本控制系统，采用**方案2：Git概念的数据库实现**。

### 核心理念
- 🎯 **借鉴Git概念**：用户熟悉的分支、提交、发布版本等概念
- 🏗️ **现代技术栈**：用数据库+MinIO对象存储实现，避免真实Git的复杂性
- 🖥️ **Web界面操作**：完全通过前端界面进行版本控制，无需命令行
- 📊 **适合ML场景**：优化大文件存储，支持模型文件的版本管理

## 🏗️ 后端架构设计

### 1. 核心服务重构

#### 1.1 服务层次划分

```python
# 第一层：底层文件存储 (保持现有逻辑，增强路径管理)
class FileUploadService:
    """纯粹的文件存储和传输机制"""

    async def initiate_upload_session(
        self,
        storage_path: str,      # 完整的存储路径 (由上层服务提供)
        file_name: str,
        file_size: int,
        content_type: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """初始化上传会话 - 不再自己生成路径"""
        # 使用传入的完整路径，不再自己生成时间戳路径
        object_key = storage_path
        # ... 其余分片上传逻辑保持不变

# 第二层：版本控制服务 (新增)
class VersionControlService:
    """Git-Like版本控制实现"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.file_upload_service = FileUploadService(db)

    async def create_snapshot(
        self,
        repository_id: int,
        files: List[FileUpload],
        message: str,
        author_id: int,
        branch: str = "main"
    ) -> Snapshot:
        """创建快照 (相当于Git commit)"""

        # 1. 生成快照ID
        snapshot_id = self._generate_snapshot_id()

        # 2. 为每个文件生成版本化路径
        uploaded_files = []
        for file_upload in files:
            storage_path = self._get_snapshot_path(
                repository_id, snapshot_id, file_upload.path
            )

            # 使用现有的分片上传逻辑
            file_record = await self.file_upload_service.upload_file(
                storage_path=storage_path,
                file_data=file_upload.content,
                file_size=file_upload.size
            )
            uploaded_files.append(file_record)

        # 3. 创建快照记录
        snapshot = Snapshot(
            id=snapshot_id,
            repository_id=repository_id,
            message=message,
            author_id=author_id,
            branch=branch,
            parent_snapshot_id=await self._get_branch_head(repository_id, branch),
            created_at=datetime.utcnow()
        )

        # 4. 创建文件关联记录
        for file_record in uploaded_files:
            snapshot_file = SnapshotFile(
                snapshot_id=snapshot_id,
                file_path=file_record.file_path,
                storage_path=file_record.minio_object_key,
                file_hash=file_record.file_hash,
                file_size=file_record.file_size
            )
            self.db.add(snapshot_file)

        # 5. 更新分支指针
        await self._update_branch_head(repository_id, branch, snapshot_id)

        self.db.add(snapshot)
        await self.db.commit()

        return snapshot

    def _get_snapshot_path(self, repo_id: int, snapshot_id: str, file_path: str) -> str:
        """生成统一的快照文件存储路径"""
        repo = await self._get_repository(repo_id)
        return f"users/{repo.owner.username}/repositories/{repo.name}/snapshots/{snapshot_id}/{file_path}"

    def _generate_snapshot_id(self) -> str:
        """生成类似Git commit hash的唯一ID"""
        import hashlib
        import time
        import random

        content = f"{time.time()}{random.random()}".encode()
        return hashlib.sha256(content).hexdigest()[:12]  # 12位短hash

# 第三层：仓库管理服务 (重构现有)
class RepositoryService:
    """面向用户的高级仓库操作"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.version_control = VersionControlService(db)
        self.metadata_sync = MetadataSyncService(db)
```

### 1.2 数据库模型设计

```python
# 新增表结构
class Snapshot(Base):
    """快照表 (对应Git的commit)"""
    __tablename__ = "snapshots"

    id = Column(String(12), primary_key=True)  # 短hash ID
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    message = Column(Text, nullable=False)  # 提交信息
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    branch = Column(String(255), default="main")  # 所属分支
    parent_snapshot_id = Column(String(12), nullable=True)  # 父快照
    created_at = Column(DateTime, default=func.now())

    # 关联关系
    repository = relationship("Repository", back_populates="snapshots")
    author = relationship("User")
    files = relationship("SnapshotFile", back_populates="snapshot")

class Branch(Base):
    """分支表"""
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    name = Column(String(255), nullable=False)  # 分支名称
    head_snapshot_id = Column(String(12), ForeignKey("snapshots.id"))  # 最新快照
    is_default = Column(Boolean, default=False)  # 是否为默认分支
    created_at = Column(DateTime, default=func.now())

    # 关联关系
    repository = relationship("Repository")
    head_snapshot = relationship("Snapshot")

class Release(Base):
    """发布版本表"""
    __tablename__ = "releases"

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    tag_name = Column(String(100), nullable=False)  # v1.0, v2.0
    snapshot_id = Column(String(12), ForeignKey("snapshots.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    is_prerelease = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    # 关联关系
    repository = relationship("Repository")
    snapshot = relationship("Snapshot")

class SnapshotFile(Base):
    """快照文件关联表"""
    __tablename__ = "snapshot_files"

    snapshot_id = Column(String(12), ForeignKey("snapshots.id"), primary_key=True)
    file_path = Column(String(1000), primary_key=True)  # 文件在仓库中的路径
    storage_path = Column(String(1000), nullable=False)  # 在MinIO中的实际路径
    file_hash = Column(String(64))  # 文件内容hash (SHA-256)
    file_size = Column(BigInteger)
    content_type = Column(String(200))

    # 关联关系
    snapshot = relationship("Snapshot", back_populates="files")

# 扩展现有Repository模型
class Repository(Base):
    # ... 现有字段保持不变 ...

    # 新增关联关系
    snapshots = relationship("Snapshot", back_populates="repository")
    branches = relationship("Branch")
    releases = relationship("Release")
```

### 1.3 API路由设计

```python
# 新增版本控制相关API
@router.post("/{username}/{repo_name}/upload")
async def upload_files_with_commit(
    username: str,
    repo_name: str,
    files: List[UploadFile] = File(...),
    commit_message: str = Form(...),
    branch: str = Form(default="main"),
    current_user: User = Depends(get_current_active_user)
):
    """上传文件并创建新快照"""

    repository = await repository_service.get_repository_by_full_name(f"{username}/{repo_name}")
    if not repository:
        raise HTTPException(404, "仓库不存在")

    # 创建快照
    snapshot = await version_control_service.create_snapshot(
        repository_id=repository.id,
        files=files,
        message=commit_message,
        author_id=current_user.id,
        branch=branch
    )

    return {"snapshot_id": snapshot.id, "message": "文件上传成功"}

@router.get("/{username}/{repo_name}/snapshots")
async def get_repository_snapshots(
    username: str,
    repo_name: str,
    branch: Optional[str] = "main",
    page: int = 1,
    limit: int = 20
):
    """获取仓库快照历史"""

    snapshots = await version_control_service.get_snapshots(
        repository_full_name=f"{username}/{repo_name}",
        branch=branch,
        page=page,
        limit=limit
    )

    return {"snapshots": snapshots}

@router.post("/{username}/{repo_name}/branches")
async def create_branch(
    username: str,
    repo_name: str,
    branch_data: BranchCreate,
    current_user: User = Depends(get_current_active_user)
):
    """创建新分支"""

    branch = await version_control_service.create_branch(
        repository_full_name=f"{username}/{repo_name}",
        branch_name=branch_data.name,
        source_branch=branch_data.source_branch,
        creator_id=current_user.id
    )

    return {"branch": branch}

@router.post("/{username}/{repo_name}/releases")
async def create_release(
    username: str,
    repo_name: str,
    release_data: ReleaseCreate,
    current_user: User = Depends(get_current_active_user)
):
    """创建发布版本"""

    release = await version_control_service.create_release(
        repository_full_name=f"{username}/{repo_name}",
        tag_name=release_data.tag_name,
        snapshot_id=release_data.snapshot_id,
        title=release_data.title,
        description=release_data.description,
        creator_id=current_user.id
    )

    return {"release": release}

@router.get("/{username}/{repo_name}/download/{snapshot_id}")
async def download_snapshot(
    username: str,
    repo_name: str,
    snapshot_id: str,
    format: str = "zip"  # zip, tar.gz
):
    """下载特定快照的所有文件"""

    download_url = await version_control_service.create_snapshot_archive(
        repository_full_name=f"{username}/{repo_name}",
        snapshot_id=snapshot_id,
        format=format
    )

    return {"download_url": download_url}

@router.post("/{username}/{repo_name}/rollback")
async def rollback_to_snapshot(
    username: str,
    repo_name: str,
    rollback_data: RollbackRequest,
    current_user: User = Depends(get_current_active_user)
):
    """回滚到指定快照"""

    new_snapshot = await version_control_service.rollback_to_snapshot(
        repository_full_name=f"{username}/{repo_name}",
        target_snapshot_id=rollback_data.target_snapshot_id,
        rollback_message=rollback_data.message,
        author_id=current_user.id
    )

    return {"new_snapshot_id": new_snapshot.id}
```

## 🎨 前端界面设计

### 2.1 仓库主页改进

```svelte
<!-- src/routes/[username]/[repository]/+page.svelte -->
<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { api } from '$lib/utils/api.js';

  // 新增版本控制相关状态
  let currentBranch = 'main';
  let branches = [];
  let snapshots = [];
  let releases = [];
  let showVersionPanel = false;

  // 加载版本控制数据
  async function loadVersionData() {
    const { username, repository: repoName } = $page.params;

    try {
      // 并行加载分支、快照、发布版本
      const [branchesRes, snapshotsRes, releasesRes] = await Promise.all([
        api.getRepositoryBranches(username, repoName),
        api.getRepositorySnapshots(username, repoName, currentBranch),
        api.getRepositoryReleases(username, repoName)
      ]);

      branches = branchesRes.branches;
      snapshots = snapshotsRes.snapshots;
      releases = releasesRes.releases;
    } catch (error) {
      console.error('Failed to load version data:', error);
    }
  }

  // 切换分支
  async function switchBranch(branchName) {
    currentBranch = branchName;
    await loadVersionData();
    // 重新加载文件列表
    await loadRepositoryFiles();
  }

  onMount(() => {
    loadVersionData();
  });
</script>

<!-- 在现有仓库页面添加版本控制区域 -->
<div class="repository-header">
  <!-- 现有的仓库信息保持不变 -->

  <!-- 新增：版本控制面板 -->
  <div class="version-control-panel">
    <!-- 分支选择器 -->
    <div class="branch-selector">
      <select bind:value={currentBranch} on:change={() => switchBranch(currentBranch)}>
        {#each branches as branch}
          <option value={branch.name}>
            📋 {branch.name}
            {#if branch.is_default}(默认){/if}
          </option>
        {/each}
      </select>
    </div>

    <!-- 版本控制操作按钮 -->
    <div class="version-actions">
      <button
        class="btn-secondary"
        on:click={() => showVersionPanel = !showVersionPanel}
      >
        📚 版本历史 ({snapshots.length})
      </button>

      <button class="btn-secondary">
        🏷️ 发布版本 ({releases.length})
      </button>

      {#if $currentUser && repository.owner?.username === $currentUser.username}
        <button class="btn-primary">
          ⬆️ 上传文件
        </button>
      {/if}
    </div>
  </div>
</div>

<!-- 版本历史面板 -->
{#if showVersionPanel}
  <div class="version-history-panel">
    <div class="panel-header">
      <h3>📈 版本历史 - {currentBranch}分支</h3>
      <button on:click={() => showVersionPanel = false}>✕</button>
    </div>

    <div class="snapshots-list">
      {#each snapshots as snapshot}
        <div class="snapshot-item">
          <div class="snapshot-info">
            <span class="snapshot-hash">
              🔗 {snapshot.id.slice(0, 8)}
            </span>
            <span class="snapshot-message">
              {snapshot.message}
            </span>
            <span class="snapshot-date">
              {new Date(snapshot.created_at).toLocaleString()}
            </span>
            <span class="snapshot-author">
              👤 {snapshot.author.username}
            </span>
          </div>

          <div class="snapshot-actions">
            <button
              class="btn-sm btn-outline"
              on:click={() => downloadSnapshot(snapshot.id)}
            >
              ⬇️ 下载
            </button>

            <button
              class="btn-sm btn-outline"
              on:click={() => viewSnapshotFiles(snapshot.id)}
            >
              📁 浏览文件
            </button>

            {#if $currentUser && repository.owner?.username === $currentUser.username}
              <button
                class="btn-sm btn-warning"
                on:click={() => rollbackToSnapshot(snapshot.id)}
              >
                ↩️ 回滚
              </button>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  </div>
{/if}
```

### 2.2 文件上传组件增强

```svelte
<!-- src/lib/components/FileUploadWithCommit.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';
  import { api } from '$lib/utils/api.js';

  export let repository;
  export let currentBranch = 'main';

  const dispatch = createEventDispatcher();

  let uploadFiles = [];
  let commitMessage = '';
  let uploading = false;
  let dragOver = false;

  // 拖拽上传处理
  function handleDrop(event) {
    event.preventDefault();
    dragOver = false;

    const files = Array.from(event.dataTransfer.files);
    uploadFiles = [...uploadFiles, ...files];
  }

  // 提交文件上传
  async function commitFiles() {
    if (!commitMessage.trim() || uploadFiles.length === 0) {
      alert('请填写提交信息并选择文件');
      return;
    }

    uploading = true;

    try {
      const formData = new FormData();

      // 添加文件
      uploadFiles.forEach(file => {
        formData.append('files', file);
      });

      // 添加提交信息
      formData.append('commit_message', commitMessage);
      formData.append('branch', currentBranch);

      const result = await api.uploadFilesWithCommit(
        repository.owner.username,
        repository.name,
        formData
      );

      // 通知父组件刷新
      dispatch('uploaded', {
        snapshotId: result.snapshot_id,
        message: commitMessage
      });

      // 重置表单
      uploadFiles = [];
      commitMessage = '';

      alert(`文件上传成功！快照ID: ${result.snapshot_id}`);

    } catch (error) {
      console.error('Upload failed:', error);
      alert('上传失败: ' + error.message);
    } finally {
      uploading = false;
    }
  }
</script>

<div class="file-upload-commit">
  <!-- 拖拽上传区域 -->
  <div
    class="drop-zone {dragOver ? 'drag-over' : ''}"
    on:dragenter|preventDefault={() => dragOver = true}
    on:dragleave|preventDefault={() => dragOver = false}
    on:dragover|preventDefault
    on:drop={handleDrop}
  >
    {#if uploadFiles.length === 0}
      <div class="drop-zone-content">
        <div class="upload-icon">📤</div>
        <p>拖拽文件到此处或点击选择文件</p>
        <input
          type="file"
          multiple
          on:change={(e) => uploadFiles = Array.from(e.target.files)}
          style="display: none;"
          bind:this={fileInput}
        />
        <button on:click={() => fileInput.click()}>选择文件</button>
      </div>
    {:else}
      <div class="selected-files">
        <h4>已选择 {uploadFiles.length} 个文件:</h4>
        {#each uploadFiles as file, index}
          <div class="file-item">
            <span class="file-name">📄 {file.name}</span>
            <span class="file-size">({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
            <button
              class="remove-file"
              on:click={() => uploadFiles = uploadFiles.filter((_, i) => i !== index)}
            >
              ✕
            </button>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- 提交信息输入 -->
  <div class="commit-section">
    <label for="commit-message">提交信息:</label>
    <textarea
      id="commit-message"
      bind:value={commitMessage}
      placeholder="描述这次提交的变更内容..."
      rows="3"
    ></textarea>

    <div class="commit-info">
      <span>将提交到: <strong>{currentBranch}</strong> 分支</span>
    </div>

    <button
      class="btn-primary commit-btn"
      disabled={uploading || !commitMessage.trim() || uploadFiles.length === 0}
      on:click={commitFiles}
    >
      {#if uploading}
        ⏳ 上传中...
      {:else}
        🚀 提交文件
      {/if}
    </button>
  </div>
</div>

<style>
  .drop-zone {
    border: 2px dashed #ccc;
    border-radius: 10px;
    padding: 40px;
    text-align: center;
    margin-bottom: 20px;
    transition: all 0.3s ease;
  }

  .drop-zone.drag-over {
    border-color: #007bff;
    background-color: rgba(0, 123, 255, 0.1);
  }

  .commit-section {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
  }

  .commit-btn {
    width: 100%;
    margin-top: 15px;
  }

  .file-item {
    display: flex;
    align-items: center;
    padding: 8px;
    background: white;
    border-radius: 4px;
    margin: 5px 0;
  }

  .file-name {
    flex: 1;
  }

  .remove-file {
    background: #dc3545;
    color: white;
    border: none;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    cursor: pointer;
  }
</style>
```

### 2.3 版本管理面板

```svelte
<!-- src/lib/components/VersionManagementPanel.svelte -->
<script>
  import { createEventDispatcher } from 'svelte';
  import { api } from '$lib/utils/api.js';

  export let repository;
  export let snapshots = [];
  export let branches = [];
  export let releases = [];

  const dispatch = createEventDispatcher();

  let activeTab = 'commits'; // commits, branches, releases
  let showCreateBranch = false;
  let showCreateRelease = false;

  // 分支管理
  let newBranchName = '';
  let sourceBranch = 'main';

  // 发布版本管理
  let newTagName = '';
  let releaseTitle = '';
  let releaseDescription = '';
  let selectedSnapshot = '';

  // 创建分支
  async function createBranch() {
    try {
      const branchData = {
        name: newBranchName,
        source_branch: sourceBranch
      };

      await api.createBranch(
        repository.owner.username,
        repository.name,
        branchData
      );

      dispatch('branchCreated', { branchName: newBranchName });

      // 重置表单
      newBranchName = '';
      showCreateBranch = false;

    } catch (error) {
      alert('创建分支失败: ' + error.message);
    }
  }

  // 创建发布版本
  async function createRelease() {
    try {
      const releaseData = {
        tag_name: newTagName,
        snapshot_id: selectedSnapshot,
        title: releaseTitle,
        description: releaseDescription
      };

      await api.createRelease(
        repository.owner.username,
        repository.name,
        releaseData
      );

      dispatch('releaseCreated', { tagName: newTagName });

      // 重置表单
      newTagName = '';
      releaseTitle = '';
      releaseDescription = '';
      selectedSnapshot = '';
      showCreateRelease = false;

    } catch (error) {
      alert('创建发布版本失败: ' + error.message);
    }
  }

  // 回滚到指定快照
  async function rollbackToSnapshot(snapshotId) {
    const confirmed = confirm(
      `确定要回滚到快照 ${snapshotId.slice(0, 8)} 吗？这将创建一个新的提交。`
    );

    if (confirmed) {
      try {
        const rollbackData = {
          target_snapshot_id: snapshotId,
          message: `回滚到快照 ${snapshotId.slice(0, 8)}`
        };

        await api.rollbackToSnapshot(
          repository.owner.username,
          repository.name,
          rollbackData
        );

        dispatch('rollbackCompleted', { snapshotId });
        alert('回滚成功！');

      } catch (error) {
        alert('回滚失败: ' + error.message);
      }
    }
  }
</script>

<div class="version-management-panel">
  <!-- 标签页导航 -->
  <div class="tab-navigation">
    <button
      class="tab-btn {activeTab === 'commits' ? 'active' : ''}"
      on:click={() => activeTab = 'commits'}
    >
      📝 提交历史 ({snapshots.length})
    </button>

    <button
      class="tab-btn {activeTab === 'branches' ? 'active' : ''}"
      on:click={() => activeTab = 'branches'}
    >
      🌿 分支管理 ({branches.length})
    </button>

    <button
      class="tab-btn {activeTab === 'releases' ? 'active' : ''}"
      on:click={() => activeTab = 'releases'}
    >
      🏷️ 发布版本 ({releases.length})
    </button>
  </div>

  <!-- 提交历史标签页 -->
  {#if activeTab === 'commits'}
    <div class="tab-content">
      <div class="commits-list">
        {#each snapshots as snapshot}
          <div class="commit-card">
            <div class="commit-header">
              <span class="commit-hash">🔗 {snapshot.id.slice(0, 8)}</span>
              <span class="commit-date">
                {new Date(snapshot.created_at).toLocaleDateString()}
              </span>
            </div>

            <div class="commit-message">
              {snapshot.message}
            </div>

            <div class="commit-author">
              👤 {snapshot.author.username}
            </div>

            <div class="commit-actions">
              <button
                class="btn-sm btn-outline"
                on:click={() => dispatch('downloadSnapshot', { snapshotId: snapshot.id })}
              >
                ⬇️ 下载
              </button>

              <button
                class="btn-sm btn-outline"
                on:click={() => dispatch('browseSnapshot', { snapshotId: snapshot.id })}
              >
                📁 浏览
              </button>

              <button
                class="btn-sm btn-warning"
                on:click={() => rollbackToSnapshot(snapshot.id)}
              >
                ↩️ 回滚
              </button>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- 分支管理标签页 -->
  {#if activeTab === 'branches'}
    <div class="tab-content">
      <div class="section-header">
        <h3>🌿 分支管理</h3>
        <button
          class="btn-primary"
          on:click={() => showCreateBranch = true}
        >
          ➕ 创建分支
        </button>
      </div>

      <!-- 创建分支表单 -->
      {#if showCreateBranch}
        <div class="create-form">
          <h4>创建新分支</h4>

          <div class="form-group">
            <label>分支名称:</label>
            <input
              type="text"
              bind:value={newBranchName}
              placeholder="例如: feature/new-model"
            />
          </div>

          <div class="form-group">
            <label>基于分支:</label>
            <select bind:value={sourceBranch}>
              {#each branches as branch}
                <option value={branch.name}>{branch.name}</option>
              {/each}
            </select>
          </div>

          <div class="form-actions">
            <button class="btn-primary" on:click={createBranch}>
              创建
            </button>
            <button
              class="btn-secondary"
              on:click={() => showCreateBranch = false}
            >
              取消
            </button>
          </div>
        </div>
      {/if}

      <!-- 分支列表 -->
      <div class="branches-list">
        {#each branches as branch}
          <div class="branch-card">
            <div class="branch-info">
              <span class="branch-name">
                🌿 {branch.name}
                {#if branch.is_default}
                  <span class="default-badge">默认</span>
                {/if}
              </span>
              <span class="branch-commit">
                最新: {branch.head_snapshot_id?.slice(0, 8) || 'N/A'}
              </span>
            </div>

            <div class="branch-actions">
              <button class="btn-sm btn-outline">
                🔄 切换
              </button>
              {#if !branch.is_default}
                <button class="btn-sm btn-danger">
                  🗑️ 删除
                </button>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- 发布版本标签页 -->
  {#if activeTab === 'releases'}
    <div class="tab-content">
      <div class="section-header">
        <h3>🏷️ 发布版本</h3>
        <button
          class="btn-primary"
          on:click={() => showCreateRelease = true}
        >
          ➕ 创建发布版本
        </button>
      </div>

      <!-- 创建发布版本表单 -->
      {#if showCreateRelease}
        <div class="create-form">
          <h4>创建发布版本</h4>

          <div class="form-group">
            <label>版本标签:</label>
            <input
              type="text"
              bind:value={newTagName}
              placeholder="例如: v1.0.0"
            />
          </div>

          <div class="form-group">
            <label>基于快照:</label>
            <select bind:value={selectedSnapshot}>
              <option value="">选择快照...</option>
              {#each snapshots as snapshot}
                <option value={snapshot.id}>
                  {snapshot.id.slice(0, 8)} - {snapshot.message}
                </option>
              {/each}
            </select>
          </div>

          <div class="form-group">
            <label>版本标题:</label>
            <input
              type="text"
              bind:value={releaseTitle}
              placeholder="例如: 首个稳定版本"
            />
          </div>

          <div class="form-group">
            <label>版本描述:</label>
            <textarea
              bind:value={releaseDescription}
              placeholder="描述这个版本的主要功能和改进..."
              rows="4"
            ></textarea>
          </div>

          <div class="form-actions">
            <button class="btn-primary" on:click={createRelease}>
              创建发布版本
            </button>
            <button
              class="btn-secondary"
              on:click={() => showCreateRelease = false}
            >
              取消
            </button>
          </div>
        </div>
      {/if}

      <!-- 发布版本列表 -->
      <div class="releases-list">
        {#each releases as release}
          <div class="release-card">
            <div class="release-header">
              <h4 class="release-title">
                🏷️ {release.tag_name} - {release.title}
              </h4>
              <span class="release-date">
                {new Date(release.created_at).toLocaleDateString()}
              </span>
            </div>

            <div class="release-description">
              {release.description}
            </div>

            <div class="release-actions">
              <button
                class="btn-sm btn-primary"
                on:click={() => dispatch('downloadRelease', { releaseId: release.id })}
              >
                ⬇️ 下载 ZIP
              </button>

              <button
                class="btn-sm btn-outline"
                on:click={() => dispatch('browseRelease', { releaseId: release.id })}
              >
                📁 浏览文件
              </button>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .version-management-panel {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  .tab-navigation {
    display: flex;
    border-bottom: 2px solid #e9ecef;
    margin-bottom: 20px;
  }

  .tab-btn {
    background: none;
    border: none;
    padding: 12px 20px;
    cursor: pointer;
    border-bottom: 3px solid transparent;
    transition: all 0.3s ease;
  }

  .tab-btn.active {
    border-bottom-color: #007bff;
    color: #007bff;
    font-weight: bold;
  }

  .commit-card,
  .branch-card,
  .release-card {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    margin-bottom: 15px;
    border-left: 4px solid #007bff;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .create-form {
    background: #e9ecef;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
  }

  .form-group {
    margin-bottom: 15px;
  }

  .form-group label {
    display: block;
    font-weight: bold;
    margin-bottom: 5px;
  }

  .form-group input,
  .form-group select,
  .form-group textarea {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ccc;
    border-radius: 4px;
  }

  .form-actions {
    display: flex;
    gap: 10px;
  }
</style>
```

## 🚀 实施计划

### 阶段1: 数据库迁移 (1-2天)
1. 创建新的数据表 (`snapshots`, `branches`, `releases`, `snapshot_files`)
2. 为现有 `Repository` 模型添加关联关系
3. 编写数据库迁移脚本

### 阶段2: 后端核心服务 (3-5天)
1. 重构 `FileUploadService` - 支持自定义存储路径
2. 创建 `VersionControlService` - 核心版本控制逻辑
3. 重构 `RepositoryService` - 集成版本控制
4. 添加新的API路由

### 阶段3: 前端基础功能 (2-3天)
1. 修改仓库主页，添加版本控制面板
2. 创建文件上传组件（带提交信息）
3. 实现快照历史浏览功能

### 阶段4: 高级功能 (3-4天)
1. 分支管理界面
2. 发布版本管理
3. 文件下载和版本对比
4. 一键回滚功能

### 阶段5: 测试和优化 (2-3天)
1. 单元测试和集成测试
2. 性能优化
3. 用户体验调优

## 📝 开发注意事项

### 兼容性考虑
- 保持现有API的向后兼容性
- 现有文件可以通过数据迁移脚本转换为快照格式
- 渐进式部署，新功能可以逐步开启

### 性能优化
- 大文件使用现有的分片上传机制
- 快照文件去重（相同hash的文件只存储一份）
- 分页加载历史记录

### 用户体验
- 提供清晰的操作反馈
- 支持批量操作
- 错误处理和恢复机制

### 安全考虑
- 权限验证（只有仓库所有者可以创建快照）
- 输入验证和过滤
- 操作审计日志

## 🎯 预期效果

实施完成后，用户将能够：

1. **📤 通过Web界面上传文件并创建版本快照**
2. **🌿 创建和管理分支，支持并行开发**
3. **🏷️ 创建发布版本，标记重要里程碑**
4. **📚 浏览完整的版本历史记录**
5. **⬇️ 下载任意历史版本的文件**
6. **↩️ 一键回滚到之前的稳定版本**
7. **🔄 对比不同版本之间的文件变化**

这将使GeoML-Hub具备与GitHub类似的版本控制能力，但专门为ML模型和大文件优化！

---

*本文档会随着开发进展持续更新。如有疑问或建议，请及时沟通。*