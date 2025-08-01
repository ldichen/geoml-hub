<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { Upload, X, CheckCircle, AlertCircle, File, Image, Archive } from 'lucide-svelte';
  import { api } from '$lib/utils/api';
  import type { UploadProgress } from '$lib/types';

  const dispatch = createEventDispatcher<{
    upload: { files: FileList };
    complete: { files: File[] };
    error: { error: string };
  }>();

  export let owner: string;
  export let repository: string;
  export let accept: string = '*/*';
  export let maxFileSize: number = 500 * 1024 * 1024; // 500MB
  export let multiple: boolean = true;
  export let disabled: boolean = false;

  let dragOver = false;
  let uploading = false;
  let uploadProgress: UploadProgress[] = [];
  let fileInput: HTMLInputElement;

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    dragOver = true;
  }

  function handleDragLeave(event: DragEvent) {
    event.preventDefault();
    dragOver = false;
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    dragOver = false;
    
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      handleFiles(files);
    }
  }

  function handleFileInput(event: Event) {
    const target = event.target as HTMLInputElement;
    const files = target.files;
    if (files && files.length > 0) {
      handleFiles(files);
    }
  }

  function handleFiles(files: FileList) {
    if (disabled || uploading) return;

    // Validate file sizes
    const oversizedFiles = Array.from(files).filter(file => file.size > maxFileSize);
    if (oversizedFiles.length > 0) {
      dispatch('error', { 
        error: `以下文件超过大小限制 (${formatFileSize(maxFileSize)}): ${oversizedFiles.map(f => f.name).join(', ')}`
      });
      return;
    }

    dispatch('upload', { files });
    uploadFiles(files);
  }

  async function uploadFiles(files: FileList) {
    uploading = true;
    uploadProgress = Array.from(files).map(file => ({
      filename: file.name,
      progress: 0,
      status: 'uploading'
    }));

    const uploadPromises = Array.from(files).map(async (file, index) => {
      try {
        const result = await api.uploadRepositoryFile(
          owner,
          repository,
          file,
          (progress) => {
            uploadProgress[index] = {
              ...uploadProgress[index],
              progress
            };
            uploadProgress = [...uploadProgress];
          }
        );

        uploadProgress[index] = {
          ...uploadProgress[index],
          status: 'completed',
          progress: 100
        };
        uploadProgress = [...uploadProgress];

        return result;
      } catch (error) {
        uploadProgress[index] = {
          ...uploadProgress[index],
          status: 'failed',
          error: error instanceof Error ? error.message : 'Upload failed'
        };
        uploadProgress = [...uploadProgress];
        throw error;
      }
    });

    try {
      const results = await Promise.all(uploadPromises);
      dispatch('complete', { files: results });
      
      // Clear progress after a delay
      setTimeout(() => {
        uploadProgress = [];
      }, 3000);
    } catch (error) {
      dispatch('error', { 
        error: error instanceof Error ? error.message : 'Upload failed'
      });
    } finally {
      uploading = false;
    }
  }

  function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  function getFileIcon(filename: string) {
    const extension = filename.split('.').pop()?.toLowerCase();
    
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(extension || '')) {
      return Image;
    } else if (['zip', 'rar', '7z', 'tar', 'gz'].includes(extension || '')) {
      return Archive;
    } else {
      return File;
    }
  }

  function removeProgressItem(index: number) {
    uploadProgress = uploadProgress.filter((_, i) => i !== index);
  }
</script>

<div class="w-full">
  <!-- Drop Zone -->
  <div
    class="relative border-2 border-dashed rounded-lg p-8 text-center transition-colors
           {dragOver 
             ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20' 
             : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'}"
    class:opacity-50={disabled}
    role="button"
    tabindex="0"
    on:dragover={handleDragOver}
    on:dragleave={handleDragLeave}
    on:drop={handleDrop}
    on:click={() => fileInput.click()}
    on:keydown={(e) => e.key === 'Enter' && fileInput.click()}
  >
    <input
      bind:this={fileInput}
      type="file"
      {accept}
      {multiple}
      {disabled}
      class="hidden"
      on:change={handleFileInput}
    />

    <div class="space-y-4">
      <div class="flex justify-center">
        <Upload class="h-12 w-12 text-gray-400 dark:text-gray-500" />
      </div>
      
      <div>
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
          {dragOver ? '放开以上传文件' : '拖拽文件到这里上传'}
        </h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
          或者
          <button
            class="text-blue-600 dark:text-blue-400 hover:underline"
            {disabled}
            on:click={() => fileInput.click()}
          >
            点击选择文件
          </button>
        </p>
        
        <div class="text-xs text-gray-400 dark:text-gray-500">
          <p>支持的文件类型: {accept === '*/*' ? '所有类型' : accept}</p>
          <p>最大文件大小: {formatFileSize(maxFileSize)}</p>
          {#if multiple}
            <p>支持多文件上传</p>
          {/if}
        </div>
      </div>
    </div>
  </div>

  <!-- Upload Progress -->
  {#if uploadProgress.length > 0}
    <div class="mt-4 space-y-2">
      <h4 class="text-sm font-medium text-gray-900 dark:text-white">上传进度</h4>
      {#each uploadProgress as progress, index}
        <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <svelte:component 
                this={getFileIcon(progress.filename)} 
                class="h-5 w-5 text-gray-400 dark:text-gray-500" 
              />
              <div>
                <p class="text-sm font-medium text-gray-900 dark:text-white">
                  {progress.filename}
                </p>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {progress.status === 'uploading' ? `上传中 ${progress.progress}%` : 
                   progress.status === 'completed' ? '上传完成' : '上传失败'}
                </p>
              </div>
            </div>
            
            <div class="flex items-center space-x-2">
              {#if progress.status === 'uploading'}
                <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              {:else if progress.status === 'completed'}
                <CheckCircle class="h-5 w-5 text-green-500" />
              {:else if progress.status === 'failed'}
                <AlertCircle class="h-5 w-5 text-red-500" />
              {/if}
              
              <button
                class="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-400"
                on:click={() => removeProgressItem(index)}
              >
                <X class="h-4 w-4" />
              </button>
            </div>
          </div>
          
          <!-- Progress Bar -->
          {#if progress.status === 'uploading'}
            <div class="mt-2 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                class="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style="width: {progress.progress}%"
              ></div>
            </div>
          {/if}
          
          <!-- Error Message -->
          {#if progress.status === 'failed' && progress.error}
            <p class="mt-2 text-xs text-red-600 dark:text-red-400">
              {progress.error}
            </p>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .animate-spin {
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
</style>