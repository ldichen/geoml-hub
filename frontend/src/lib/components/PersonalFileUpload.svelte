<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { Upload, X, FileText, Image, Video, Music, Archive, Code, File } from 'lucide-svelte';
  import { api } from '$lib/utils/api.js';
  
  export let username: string;
  export let currentPath: string = '/';
  
  const dispatch = createEventDispatcher();
  
  let showUploadModal = false;
  let dragActive = false;
  let uploadFiles: File[] = [];
  let uploading = false;
  let uploadProgress: { [key: string]: number } = {};
  let uploadResults = {
    success: 0,
    failed: 0,
    total: 0
  };
  
  function openUploadModal() {
    showUploadModal = true;
    uploadFiles = [];
    uploadProgress = {};
    uploadResults = { success: 0, failed: 0, total: 0 };
  }
  
  function closeUploadModal() {
    showUploadModal = false;
    uploading = false;
  }
  
  function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target.files) {
      addFiles(Array.from(target.files));
    }
  }
  
  function handleDrop(event: DragEvent) {
    event.preventDefault();
    dragActive = false;
    
    if (event.dataTransfer?.files) {
      addFiles(Array.from(event.dataTransfer.files));
    }
  }
  
  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    dragActive = true;
  }
  
  function handleDragLeave() {
    dragActive = false;
  }
  
  function addFiles(files: File[]) {
    uploadFiles = [...uploadFiles, ...files];
  }
  
  function removeFile(index: number) {
    uploadFiles = uploadFiles.filter((_, i) => i !== index);
  }
  
  function getFileIcon(file: File) {
    const type = file.type.toLowerCase();
    if (type.startsWith('image/')) return Image;
    if (type.startsWith('video/')) return Video;
    if (type.startsWith('audio/')) return Music;
    if (type.includes('archive') || type.includes('zip')) return Archive;
    if (type.includes('text') || type.includes('json') || type.includes('xml')) return Code;
    if (type.includes('pdf') || type.includes('document')) return FileText;
    return File;
  }
  
  function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
  
  async function uploadFile(file: File, description: string = '', tags: string = '', isPublic: boolean = false): Promise<void> {
    try {
      // 第一步：获取上传URL
      const uploadData = await api.request(`/api/personal-files/${username}/upload-url?filename=${encodeURIComponent(file.name)}&file_size=${file.size}`, {
        method: 'POST'
      });
      
      // 第二步：上传文件到MinIO
      const uploadResponse = await fetch(uploadData.upload_url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type
        }
      });
      
      if (!uploadResponse.ok) {
        throw new Error('文件上传失败');
      }
      
      // 第三步：完成上传
      return await api.request(`/api/personal-files/${username}/complete-upload`, {
        method: 'POST',
        body: {
          file_key: uploadData.file_key,
          filename: file.name,
          file_path: currentPath, // 使用目录路径，而不是完整文件路径
          file_size: file.size,
          mime_type: file.type,
          description,
          tags,
          is_public: isPublic
        }
      });
    } catch (error) {
      console.error('Upload error:', error);
      throw error;
    }
  }
  
  async function handleUpload() {
    if (uploadFiles.length === 0) return;
    
    uploading = true;
    uploadResults = { success: 0, failed: 0, total: uploadFiles.length };
    
    const uploadPromises = uploadFiles.map(async (file, index) => {
      try {
        uploadProgress[file.name] = 0;
        uploadProgress = { ...uploadProgress };
        
        await uploadFile(file);
        
        uploadProgress[file.name] = 100;
        uploadProgress = { ...uploadProgress };
        uploadResults.success++;
        uploadResults = { ...uploadResults };
      } catch (error) {
        console.error(`Upload failed for ${file.name}:`, error);
        uploadProgress[file.name] = -1; // 错误状态
        uploadProgress = { ...uploadProgress };
        uploadResults.failed++;
        uploadResults = { ...uploadResults };
      }
    });
    
    await Promise.all(uploadPromises);
    uploading = false;
    
    // 通知父组件刷新文件列表
    dispatch('uploadComplete', {
      success: uploadResults.success,
      failed: uploadResults.failed,
      total: uploadResults.total
    });
    
    // 延长显示结果的时间，让用户看到上传结果
    setTimeout(() => {
      closeUploadModal();
    }, uploadResults.failed > 0 ? 3000 : 2000); // 有失败的情况显示更长时间
  }
</script>

<!-- 上传按钮 -->
<button
  class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
  on:click={openUploadModal}
>
  <Upload class="h-4 w-4 mr-2" />
  上传文件
</button>

<!-- 上传模态框 -->
{#if showUploadModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[80vh] overflow-y-auto">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">上传文件</h3>
        <button
          class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          on:click={closeUploadModal}
        >
          <X class="h-5 w-5" />
        </button>
      </div>
      
      <div class="text-sm text-gray-600 dark:text-gray-400 mb-4">
        上传到: {currentPath}
      </div>
      
      <!-- 拖拽上传区域 -->
      <div
        class="border-2 border-dashed rounded-lg p-8 text-center transition-colors {dragActive ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-600'}"
        on:drop={handleDrop}
        on:dragover={handleDragOver}
        on:dragleave={handleDragLeave}
      >
        <Upload class="h-12 w-12 mx-auto mb-4 text-gray-400" />
        <p class="text-lg font-medium text-gray-900 dark:text-white mb-2">
          拖拽文件到这里上传
        </p>
        <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
          或者点击选择文件
        </p>
        <input
          type="file"
          multiple
          class="hidden"
          id="file-upload"
          on:change={handleFileSelect}
        />
        <label
          for="file-upload"
          class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer transition-colors"
        >
          选择文件
        </label>
      </div>
      
      <!-- 文件列表 -->
      {#if uploadFiles.length > 0}
        <div class="mt-6">
          <h4 class="text-md font-medium text-gray-900 dark:text-white mb-3">
            待上传文件 ({uploadFiles.length})
          </h4>
          <div class="space-y-3 max-h-60 overflow-y-auto">
            {#each uploadFiles as file, index}
              <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div class="flex items-center space-x-3 flex-1 min-w-0">
                  <svelte:component this={getFileIcon(file)} class="h-5 w-5 text-gray-400 flex-shrink-0" />
                  <div class="flex-1 min-w-0">
                    <div class="font-medium text-gray-900 dark:text-white truncate">
                      {file.name}
                    </div>
                    <div class="text-sm text-gray-500 dark:text-gray-400">
                      {formatFileSize(file.size)}
                    </div>
                    
                    <!-- 上传进度 -->
                    {#if uploading && uploadProgress[file.name] !== undefined}
                      <div class="mt-2">
                        {#if uploadProgress[file.name] === -1}
                          <div class="text-sm text-red-600 dark:text-red-400">上传失败</div>
                        {:else if uploadProgress[file.name] === 100}
                          <div class="text-sm text-green-600 dark:text-green-400">上传完成</div>
                        {:else}
                          <div class="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                            <div 
                              class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                              style="width: {uploadProgress[file.name]}%"
                            ></div>
                          </div>
                        {/if}
                      </div>
                    {/if}
                  </div>
                </div>
                
                {#if !uploading}
                  <button
                    class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 ml-2"
                    on:click={() => removeFile(index)}
                  >
                    <X class="h-4 w-4" />
                  </button>
                {/if}
              </div>
            {/each}
          </div>
        </div>
      {/if}
      
      <!-- 上传结果显示 -->
      {#if !uploading && uploadResults.total > 0}
        <div class="mt-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <h4 class="text-md font-medium text-gray-900 dark:text-white mb-2">上传结果</h4>
          <div class="space-y-2">
            {#if uploadResults.success > 0}
              <div class="flex items-center text-green-600 dark:text-green-400">
                <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                </svg>
                成功上传 {uploadResults.success} 个文件
              </div>
            {/if}
            {#if uploadResults.failed > 0}
              <div class="flex items-center text-red-600 dark:text-red-400">
                <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                </svg>
                上传失败 {uploadResults.failed} 个文件
              </div>
            {/if}
          </div>
        </div>
      {/if}
      
      <!-- 操作按钮 -->
      <div class="flex justify-end space-x-3 mt-6">
        <button
          class="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
          on:click={closeUploadModal}
          disabled={uploading}
        >
          取消
        </button>
        <button
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          on:click={handleUpload}
          disabled={uploadFiles.length === 0 || uploading}
        >
          {#if uploading}
            上传中...
          {:else}
            开始上传
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}