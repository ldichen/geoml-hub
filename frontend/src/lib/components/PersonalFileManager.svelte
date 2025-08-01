<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import { Folder, File, Download, Trash2, Eye, EyeOff, Plus, FolderPlus, ArrowLeft, MoreVertical } from 'lucide-svelte';
  import PersonalFileUpload from './PersonalFileUpload.svelte';
  import { api } from '$lib/utils/api.js';

  export let username: string;
  export let currentUser: any;

  const dispatch = createEventDispatcher();

  let currentPath = '/';
  let files: any[] = [];
  let folders: any[] = [];
  let loading = false;
  let error = '';
  let showCreateFolderModal = false;
  let newFolderName = '';
  let selectedFiles: Set<number> = new Set();
  let showBulkActions = false;
  let creatingFolder = false;
  let operationInProgress = false;
  let successMessage = '';

  interface FileItem {
    id: number;
    filename: string;
    file_path: string;
    file_size: number;
    mime_type: string;
    is_public: boolean;
    download_count: number;
    created_at: string;
    updated_at: string;
  }

  interface FolderItem {
    id: number;
    name: string;
    path: string;
    is_public: boolean;
    file_count: number;
    created_at: string;
  }

  onMount(() => {
    loadFiles();
  });

  async function loadFiles() {
    loading = true;
    error = '';
    
    try {
      const data = await api.request(`/api/personal-files/${username}/browse?path=${encodeURIComponent(currentPath)}`);
      files = data.files || [];
      folders = data.folders || [];
    } catch (err) {
      error = err instanceof Error ? err.message : '加载文件失败';
      console.error('Load files error:', err);
    } finally {
      loading = false;
    }
  }

  async function navigateToFolder(folderPath: string) {
    currentPath = folderPath;
    await loadFiles();
  }

  async function navigateUp() {
    if (currentPath === '/') return;
    const parts = currentPath.split('/').filter(p => p);
    parts.pop();
    currentPath = parts.length > 0 ? '/' + parts.join('/') : '/';
    await loadFiles();
  }

  async function createFolder() {
    if (!newFolderName.trim() || creatingFolder) return;
    
    const requestData = {
      name: newFolderName.trim(),
      parent_path: currentPath,
      is_public: false
    };
    
    creatingFolder = true;
    error = '';
    
    try {
      await api.request(`/api/personal-files/${username}/folders`, {
        method: 'POST',
        body: requestData
      });
      
      newFolderName = '';
      showCreateFolderModal = false;
      await loadFiles();
      successMessage = '文件夹创建成功';
      setTimeout(() => successMessage = '', 3000);
    } catch (err) {
      error = err instanceof Error ? err.message : '创建文件夹失败';
      console.error('Create folder error:', err);
    } finally {
      creatingFolder = false;
    }
  }

  async function deleteFile(fileId: number) {
    if (!confirm('确定要删除这个文件吗？') || operationInProgress) return;
    
    operationInProgress = true;
    error = '';
    
    try {
      await api.request(`/api/personal-files/${username}/files/${fileId}`, {
        method: 'DELETE'
      });
      
      await loadFiles();
    } catch (err) {
      error = err instanceof Error ? err.message : '删除文件失败';
      console.error('Delete file error:', err);
    } finally {
      operationInProgress = false;
    }
  }

  async function deleteFolder(folderId: number) {
    if (!confirm('确定要删除这个文件夹吗？文件夹内的所有文件也会被删除。')) return;
    
    try {
      await api.request(`/api/personal-files/${username}/folders/${folderId}`, {
        method: 'DELETE'
      });
      
      await loadFiles();
    } catch (err) {
      error = err instanceof Error ? err.message : '删除文件夹失败';
      console.error('Delete folder error:', err);
    }
  }

  async function toggleFileVisibility(fileId: number, isPublic: boolean) {
    try {
      await api.request(`/api/personal-files/${username}/files/${fileId}`, {
        method: 'PUT',
        body: {
          is_public: !isPublic
        }
      });
      
      await loadFiles();
    } catch (err) {
      error = err instanceof Error ? err.message : '更新文件设置失败';
      console.error('Toggle visibility error:', err);
    }
  }

  async function toggleFolderVisibility(folderId: number, isPublic: boolean) {
    try {
      await api.request(`/api/personal-files/${username}/folders/${folderId}`, {
        method: 'PUT',
        body: {
          is_public: !isPublic
        }
      });
      
      await loadFiles();
      successMessage = '文件夹可见性更新成功';
      setTimeout(() => successMessage = '', 3000);
    } catch (err) {
      error = err instanceof Error ? err.message : '更新文件夹设置失败';
      console.error('Toggle folder visibility error:', err);
    }
  }

  async function downloadFile(fileId: number, filename: string) {
    try {
      const data = await api.request(`/api/personal-files/${username}/files/${fileId}/download`);
      
      // 创建临时链接下载
      const a = document.createElement('a');
      a.href = data.download_url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (err) {
      error = err instanceof Error ? err.message : '下载文件失败';
      console.error('Download file error:', err);
    }
  }

  function toggleFileSelection(fileId: number) {
    if (selectedFiles.has(fileId)) {
      selectedFiles.delete(fileId);
    } else {
      selectedFiles.add(fileId);
    }
    selectedFiles = new Set(selectedFiles);
    showBulkActions = selectedFiles.size > 0;
  }

  function selectAllFiles() {
    selectedFiles = new Set(files.map(f => f.id));
    showBulkActions = true;
  }

  function clearSelection() {
    selectedFiles.clear();
    selectedFiles = new Set();
    showBulkActions = false;
  }

  async function bulkDelete() {
    if (selectedFiles.size === 0) return;
    if (!confirm(`确定要删除选中的 ${selectedFiles.size} 个文件吗？`)) return;
    
    const deletePromises = Array.from(selectedFiles).map(fileId => 
      api.request(`/api/personal-files/${username}/files/${fileId}`, {
        method: 'DELETE'
      })
    );
    
    try {
      await Promise.all(deletePromises);
      clearSelection();
      await loadFiles();
    } catch (err) {
      error = '批量删除失败';
      console.error('Bulk delete error:', err);
    }
  }

  function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('zh-CN');
  }

  function getFileIcon(mimeType: string) {
    if (mimeType.startsWith('image/')) return '🖼️';
    if (mimeType.startsWith('video/')) return '🎥';
    if (mimeType.startsWith('audio/')) return '🎵';
    if (mimeType.includes('pdf')) return '📄';
    if (mimeType.includes('text')) return '📝';
    if (mimeType.includes('json')) return '📋';
    if (mimeType.includes('csv')) return '📊';
    if (mimeType.includes('archive') || mimeType.includes('zip')) return '📦';
    if (mimeType.includes('python')) return '🐍';
    if (mimeType.includes('javascript')) return '📜';
    return '📄';
  }

  function handleUploadComplete(event) {
    const { success, failed, total } = event.detail || { success: 0, failed: 0, total: 0 };
    
    // 刷新文件列表
    loadFiles();
    
    // 显示上传结果消息
    if (success > 0) {
      successMessage = `成功上传 ${success} 个文件${failed > 0 ? `，${failed} 个失败` : ''}`;
      setTimeout(() => successMessage = '', 4000);
    } else if (failed > 0) {
      error = `上传失败 ${failed} 个文件`;
      setTimeout(() => error = '', 4000);
    }
  }
</script>

<div class="space-y-6">
  <!-- 顶部工具栏 -->
  <div class="flex items-center justify-between">
    <div class="flex items-center space-x-4">
      <!-- 路径导航 -->
      <div class="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
        <button 
          class="hover:text-blue-600 dark:hover:text-blue-400"
          on:click={() => navigateToFolder('/')}
        >
          个人文件
        </button>
        {#each currentPath.split('/').filter(p => p) as part, index}
          <span>/</span>
          <button 
            class="hover:text-blue-600 dark:hover:text-blue-400"
            on:click={() => navigateToFolder('/' + currentPath.split('/').filter(p => p).slice(0, index + 1).join('/'))}
          >
            {part}
          </button>
        {/each}
      </div>
      
      {#if currentPath !== '/'}
        <button
          class="inline-flex items-center px-2 py-1 text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
          on:click={navigateUp}
        >
          <ArrowLeft class="h-4 w-4 mr-1" />
          返回上级
        </button>
      {/if}
    </div>

    <div class="flex items-center space-x-3">
      <!-- 批量操作 -->
      {#if showBulkActions}
        <div class="flex items-center space-x-2 bg-blue-50 dark:bg-blue-900/20 px-3 py-2 rounded-lg">
          <span class="text-sm text-blue-700 dark:text-blue-300">
            已选择 {selectedFiles.size} 个文件
          </span>
          <button
            class="text-sm text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
            on:click={bulkDelete}
          >
            批量删除
          </button>
          <button
            class="text-sm text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-300"
            on:click={clearSelection}
          >
            取消选择
          </button>
        </div>
      {/if}

      <!-- 创建文件夹 -->
      <button
        class="inline-flex items-center px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
        on:click={() => showCreateFolderModal = true}
      >
        <FolderPlus class="h-4 w-4 mr-2" />
        新建文件夹
      </button>

      <!-- 上传文件 -->
      <PersonalFileUpload 
        {username} 
        {currentPath} 
        on:uploadComplete={handleUploadComplete}
      />
    </div>
  </div>

  <!-- 错误提示 -->
  {#if error}
    <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
      <p class="text-red-700 dark:text-red-300">{error}</p>
    </div>
  {/if}

  <!-- 成功提示 -->
  {#if successMessage}
    <div class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
      <p class="text-green-700 dark:text-green-300">{successMessage}</p>
    </div>
  {/if}

  <!-- 加载状态 -->
  {#if loading}
    <div class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  {:else}
    <!-- 文件和文件夹列表 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      <div class="p-4 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-medium text-gray-900 dark:text-white">
            文件列表
          </h3>
          {#if files.length > 0}
            <button
              class="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
              on:click={selectAllFiles}
            >
              全选
            </button>
          {/if}
        </div>
      </div>

      <div class="divide-y divide-gray-200 dark:divide-gray-700">
        <!-- 文件夹列表 -->
        {#each folders as folder}
          <div class="p-4 hover:bg-gray-50 dark:hover:bg-gray-700">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3 flex-1 min-w-0">
                <Folder class="h-5 w-5 text-blue-500 flex-shrink-0" />
                <div class="flex-1 min-w-0">
                  <button
                    class="font-medium text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 truncate block"
                    on:click={() => navigateToFolder(folder.path)}
                  >
                    {folder.name}
                  </button>
                  <div class="text-sm text-gray-500 dark:text-gray-400">
                    {folder.file_count || 0} 个文件 • 创建于 {formatDate(folder.created_at)}
                    {#if folder.is_public}
                      <span class="ml-2 px-2 py-0.5 bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300 text-xs rounded-full">
                        公开
                      </span>
                    {:else}
                      <span class="ml-2 px-2 py-0.5 bg-gray-100 dark:bg-gray-900/20 text-gray-700 dark:text-gray-300 text-xs rounded-full">
                        私有
                      </span>
                    {/if}
                  </div>
                </div>
              </div>
              
              <div class="flex items-center space-x-2">
                <button
                  class="text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-300 p-1"
                  on:click={() => toggleFolderVisibility(folder.id, folder.is_public)}
                  title={folder.is_public ? '设为私有' : '设为公开'}
                >
                  {#if folder.is_public}
                    <Eye class="h-4 w-4" />
                  {:else}
                    <EyeOff class="h-4 w-4" />
                  {/if}
                </button>
                <button
                  class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 p-1"
                  on:click={() => deleteFolder(folder.id)}
                  title="删除文件夹"
                >
                  <Trash2 class="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        {/each}

        <!-- 文件列表 -->
        {#each files as file}
          <div class="p-4 hover:bg-gray-50 dark:hover:bg-gray-700">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3 flex-1 min-w-0">
                <input
                  type="checkbox"
                  class="rounded border-gray-300 dark:border-gray-600"
                  checked={selectedFiles.has(file.id)}
                  on:change={() => toggleFileSelection(file.id)}
                />
                <span class="text-xl flex-shrink-0">{getFileIcon(file.mime_type)}</span>
                <div class="flex-1 min-w-0">
                  <div class="font-medium text-gray-900 dark:text-white truncate">
                    {file.filename}
                  </div>
                  <div class="text-sm text-gray-500 dark:text-gray-400">
                    {formatFileSize(file.file_size)} • {formatDate(file.created_at)} • {file.download_count} 次下载
                    {#if file.is_public}
                      <span class="ml-2 px-2 py-0.5 bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-300 text-xs rounded-full">
                        公开
                      </span>
                    {:else}
                      <span class="ml-2 px-2 py-0.5 bg-gray-100 dark:bg-gray-900/20 text-gray-700 dark:text-gray-300 text-xs rounded-full">
                        私有
                      </span>
                    {/if}
                  </div>
                </div>
              </div>
              
              <div class="flex items-center space-x-2">
                <button
                  class="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 p-1"
                  on:click={() => downloadFile(file.id, file.filename)}
                  title="下载文件"
                >
                  <Download class="h-4 w-4" />
                </button>
                <button
                  class="text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-300 p-1"
                  on:click={() => toggleFileVisibility(file.id, file.is_public)}
                  title={file.is_public ? '设为私有' : '设为公开'}
                >
                  {#if file.is_public}
                    <Eye class="h-4 w-4" />
                  {:else}
                    <EyeOff class="h-4 w-4" />
                  {/if}
                </button>
                <button
                  class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 p-1"
                  on:click={() => deleteFile(file.id)}
                  title="删除文件"
                >
                  <Trash2 class="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        {/each}

        <!-- 空状态 -->
        {#if files.length === 0 && folders.length === 0}
          <div class="p-12 text-center">
            <Folder class="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p class="text-lg font-medium text-gray-900 dark:text-white mb-2">
              这里还没有任何文件
            </p>
            <p class="text-gray-600 dark:text-gray-400 mb-4">
              开始上传文件或创建文件夹来组织您的数据
            </p>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<!-- 创建文件夹模态框 -->
{#if showCreateFolderModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        创建新文件夹
      </h3>
      
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            文件夹名称
          </label>
          <input
            type="text"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            placeholder="输入文件夹名称"
            bind:value={newFolderName}
            on:keypress={(e) => e.key === 'Enter' && !creatingFolder && createFolder()}
            on:keydown={(e) => e.key === 'Escape' && (showCreateFolderModal = false)}
            disabled={creatingFolder}
            autofocus
          />
        </div>
        
        <div class="text-sm text-gray-600 dark:text-gray-400">
          将在 <span class="font-mono">{currentPath}</span> 下创建文件夹
        </div>
      </div>
      
      <div class="flex justify-end space-x-3 mt-6">
        <button
          class="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
          on:click={() => { showCreateFolderModal = false; newFolderName = ''; }}
        >
          取消
        </button>
        <button
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          on:click={createFolder}
          disabled={!newFolderName.trim() || creatingFolder}
        >
          {#if creatingFolder}
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            创建中...
          {:else}
            创建
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}