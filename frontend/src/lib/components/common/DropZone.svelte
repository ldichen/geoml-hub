<script>
  import { createEventDispatcher } from 'svelte';
  import { Upload } from 'lucide-svelte';

  export let accept = '*'; // 接受的文件类型
  export let multiple = false; // 是否允许多文件
  export let disabled = false; // 是否禁用
  export let maxSize = null; // 最大文件大小(字节)
  export let dropText = '拖拽文件到这里或点击选择文件';
  export let dragText = '释放文件进行上传';
  
  const dispatch = createEventDispatcher();
  
  let isDragOver = false;
  let fileInput;
  
  function handleDragOver(event) {
    if (disabled) return;
    event.preventDefault();
    isDragOver = true;
  }
  
  function handleDragLeave(event) {
    if (disabled) return;
    event.preventDefault();
    isDragOver = false;
  }
  
  function handleDrop(event) {
    if (disabled) return;
    event.preventDefault();
    isDragOver = false;
    
    const files = Array.from(event.dataTransfer.files);
    handleFiles(files);
  }
  
  function handleFileSelect(event) {
    if (disabled) return;
    const files = Array.from(event.target.files);
    handleFiles(files);
  }
  
  function handleFiles(files) {
    if (!multiple) {
      files = files.slice(0, 1);
    }
    
    // 文件大小验证
    if (maxSize) {
      const oversizedFiles = files.filter(file => file.size > maxSize);
      if (oversizedFiles.length > 0) {
        dispatch('error', {
          type: 'size_exceeded',
          files: oversizedFiles,
          maxSize
        });
        return;
      }
    }
    
    if (files.length > 0) {
      dispatch('files', { files });
    }
  }
  
  function triggerFileSelect() {
    if (disabled) return;
    fileInput?.click();
  }
</script>

<div
  class="dropzone border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 cursor-pointer
    {isDragOver ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-600'}
    {disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-blue-400 hover:bg-gray-50 dark:hover:bg-gray-800'}
  "
  on:dragover={handleDragOver}
  on:dragleave={handleDragLeave}
  on:drop={handleDrop}
  on:click={triggerFileSelect}
  on:keydown={(e) => e.key === 'Enter' && triggerFileSelect()}
  role="button"
  tabindex="0"
  aria-label="文件上传区域"
>
  <input
    bind:this={fileInput}
    type="file"
    {accept}
    {multiple}
    {disabled}
    on:change={handleFileSelect}
    class="hidden"
  />
  
  <div class="flex flex-col items-center space-y-4">
    <div class="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
      <Upload class="w-6 h-6 text-gray-400" />
    </div>
    
    <div class="space-y-2">
      <p class="text-lg font-medium text-gray-900 dark:text-white">
        {isDragOver ? dragText : dropText}
      </p>
      
      {#if maxSize}
        <p class="text-sm text-gray-500 dark:text-gray-400">
          最大文件大小: {(maxSize / 1024 / 1024).toFixed(1)}MB
        </p>
      {/if}
      
      {#if accept !== '*'}
        <p class="text-sm text-gray-500 dark:text-gray-400">
          支持格式: {accept}
        </p>
      {/if}
    </div>
  </div>
</div>

<style>
  .dropzone {
    min-height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
</style>