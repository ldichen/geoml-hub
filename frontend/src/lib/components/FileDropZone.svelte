<script>
  import { createEventDispatcher } from 'svelte';
  import { Upload, FolderOpen } from 'lucide-svelte';

  const dispatch = createEventDispatcher();

  export let show = false;
  export let isUploading = false;

  let dragCounter = 0;
  let isDragOver = false;

  function handleDragEnter(e) {
    e.preventDefault();
    e.stopPropagation();
    dragCounter++;
    isDragOver = true;
  }

  function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    dragCounter--;
    if (dragCounter === 0) {
      isDragOver = false;
    }
  }

  function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    isDragOver = false;
    dragCounter = 0;

    const items = e.dataTransfer.items;
    const files = [];

    if (items) {
      // 处理拖拽的项目
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.kind === 'file') {
          const entry = item.webkitGetAsEntry();
          if (entry) {
            if (entry.isDirectory) {
              // 处理文件夹
              readDirectory(entry, files).then(() => {
                dispatch('filesSelected', { files, isFolder: true });
              });
              return;
            } else {
              // 处理文件
              files.push(item.getAsFile());
            }
          }
        }
      }
      
      if (files.length > 0) {
        dispatch('filesSelected', { files, isFolder: false });
      }
    }
  }

  async function readDirectory(directoryEntry, files) {
    const reader = directoryEntry.createReader();
    
    return new Promise((resolve) => {
      const readEntries = () => {
        reader.readEntries(async (entries) => {
          if (entries.length === 0) {
            resolve();
            return;
          }

          for (const entry of entries) {
            if (entry.isFile) {
              const file = await new Promise((fileResolve) => {
                entry.file((file) => {
                  // 设置相对路径
                  Object.defineProperty(file, 'webkitRelativePath', {
                    value: entry.fullPath.substring(1), // 去掉开头的 /
                    writable: false
                  });
                  fileResolve(file);
                });
              });
              files.push(file);
            } else if (entry.isDirectory) {
              await readDirectory(entry, files);
            }
          }
          
          readEntries(); // 递归读取更多条目
        });
      };
      
      readEntries();
    });
  }

  function handleFileInput(e) {
    const files = Array.from(e.target.files);
    const isFolder = files.some(file => file.webkitRelativePath);
    dispatch('filesSelected', { files, isFolder });
    e.target.value = ''; // 清空输入
  }

  function handleClose() {
    show = false;
    dispatch('close');
  }
</script>

{#if show}
  <!-- 全屏拖拽区域 -->
  <div 
    class="fixed inset-0 z-50 bg-gray-900 bg-opacity-95 flex items-center justify-center"
    on:click={handleClose}
    on:dragenter={handleDragEnter}
    on:dragleave={handleDragLeave}
    on:dragover={handleDragOver}
    on:drop={handleDrop}
  >
    <!-- 关闭按钮 -->
    <button
      class="absolute top-6 right-6 text-gray-400 hover:text-white transition-colors z-10"
      on:click={handleClose}
    >
      <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
      </svg>
    </button>

    <!-- 拖拽区域边框 -->
    <div 
      class="w-full max-w-4xl mx-6 h-64 border-4 border-dashed rounded-lg flex items-center justify-center transition-colors duration-200"
      class:border-blue-400={isDragOver}
      class:bg-blue-500={isDragOver}
      class:bg-opacity-10={isDragOver}
      class:border-gray-500={!isDragOver}
      on:click|stopPropagation
    >
      <div class="text-center text-white">
        <!-- 图标 -->
        <div class="flex justify-center space-x-4 mb-4">
          <div class="p-3 bg-white bg-opacity-20 rounded-full">
            <Upload class="h-8 w-8" />
          </div>
          <div class="p-3 bg-white bg-opacity-20 rounded-full">
            <FolderOpen class="h-8 w-8" />
          </div>
        </div>

        <!-- 主标题 -->
        <h3 class="text-xl font-semibold mb-2">
          {isDragOver ? '释放文件/文件夹到此处' : 'Drag files/folders here or click to browse from your computer.'}
        </h3>

        <!-- 描述 -->
        {#if !isDragOver}
          <p class="text-gray-300 mb-6 text-sm">
            支持所有文件格式，单个文件最大 10GB
          </p>

          <!-- 按钮组 -->
          <div class="flex justify-center space-x-4">
            <button
              class="inline-flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
              on:click={() => document.getElementById('file-input').click()}
              disabled={isUploading}
            >
              <Upload class="h-5 w-5 mr-2" />
              选择文件
            </button>
            
            <button
              class="inline-flex items-center px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
              on:click={() => document.getElementById('folder-input').click()}
              disabled={isUploading}
            >
              <FolderOpen class="h-5 w-5 mr-2" />
              选择文件夹
            </button>
          </div>
        {/if}
      </div>
    </div>

    <!-- 隐藏的文件输入 -->
    <input
      id="file-input"
      type="file"
      multiple
      class="hidden"
      on:change={handleFileInput}
    />
    
    <input
      id="folder-input"
      type="file"
      webkitdirectory
      multiple
      class="hidden"
      on:change={handleFileInput}
    />
  </div>
{/if}

<style>
  .border-dashed {
    border-style: dashed;
  }
</style>