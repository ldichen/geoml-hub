<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { api } from '$lib/utils/api.js';
  import { showToast } from '$lib/utils/toast.js';
  
  export let service: any;
  export let show = false;
  
  const dispatch = createEventDispatcher();
  
  let updating = false;
  let selectedFiles: { [key: string]: File | null } = {
    gogogo: null,
    mc_config: null,
    model: null,
    examples: null
  };
  
  let fileInputRefs: { [key: string]: HTMLInputElement } = {};
  
  const fileTypes = {
    gogogo: {
      accept: '.py',
      label: '启动脚本 (gogogo.py)',
      description: 'Python模型服务启动文件',
      maxSize: 10 * 1024 * 1024 // 10MB
    },
    mc_config: {
      accept: '.json',
      label: '配置文件 (mc.json)',
      description: 'JSON格式配置文件',
      maxSize: 1 * 1024 * 1024 // 1MB
    },
    model: {
      accept: '.zip,.tar,.tar.gz,.tgz',
      label: '模型文件',
      description: '模型目录压缩包 (支持zip, tar, tar.gz)',
      maxSize: 1 * 1024 * 1024 * 1024 // 1GB
    },
    examples: {
      accept: '.zip,.tar,.tar.gz,.tgz',
      label: '示例数据',
      description: '示例数据目录压缩包 (支持zip, tar, tar.gz)',
      maxSize: 100 * 1024 * 1024 // 100MB
    }
  };
  
  function handleFileSelect(fileType: string, event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    
    if (!file) {
      selectedFiles[fileType] = null;
      return;
    }
    
    // 验证文件大小
    const maxSize = fileTypes[fileType as keyof typeof fileTypes].maxSize;
    if (file.size > maxSize) {
      showToast(`文件大小超过限制 (${formatFileSize(maxSize)})`, 'error');
      input.value = '';
      selectedFiles[fileType] = null;
      return;
    }
    
    // 验证文件扩展名
    const acceptedExtensions = fileTypes[fileType as keyof typeof fileTypes].accept
      .split(',')
      .map(ext => ext.trim().toLowerCase());
    
    const fileName = file.name.toLowerCase();
    const isValidExtension = acceptedExtensions.some(ext => 
      fileName.endsWith(ext.replace('.', ''))
    );
    
    if (!isValidExtension) {
      showToast(`不支持的文件格式，请选择: ${fileTypes[fileType as keyof typeof fileTypes].accept}`, 'error');
      input.value = '';
      selectedFiles[fileType] = null;
      return;
    }
    
    selectedFiles[fileType] = file;
  }
  
  function removeFile(fileType: string) {
    selectedFiles[fileType] = null;
    if (fileInputRefs[fileType]) {
      fileInputRefs[fileType].value = '';
    }
  }
  
  function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
  
  async function handleUpdate() {
    // 检查是否至少选择了一个文件
    const hasFiles = Object.values(selectedFiles).some(file => file !== null);
    if (!hasFiles) {
      showToast('请至少选择一个文件进行更新', 'error');
      return;
    }
    
    updating = true;
    
    try {
      const formData = new FormData();
      
      // 添加选中的文件
      Object.entries(selectedFiles).forEach(([fileType, file]) => {
        if (file) {
          const fieldName = fileType === 'mc_config' ? 'mc_config_file' : 
                           fileType === 'gogogo' ? 'gogogo_file' :
                           fileType === 'model' ? 'model_archive' : 'examples_archive';
          formData.append(fieldName, file);
        }
      });
      
      const response = await api.updateServiceFiles(service.id, formData);
      
      if (response.result?.overall_success) {
        showToast('文件更新成功，服务正在重启...', 'success');
        
        // 等待一下再检查服务状态
        setTimeout(async () => {
          try {
            await checkServiceStatus();
          } catch (error) {
            console.error('检查服务状态失败:', error);
          }
        }, 3000);
        
        dispatch('updated', response);
        handleClose();
      } else {
        const failedUpdates = Object.entries(response.result?.updates || {})
          .filter(([_, result]: [string, any]) => !result.success)
          .map(([fileType, result]: [string, any]) => `${fileType}: ${result.error}`)
          .join('; ');
        
        showToast(`部分文件更新失败: ${failedUpdates}`, 'error');
      }
      
    } catch (error: any) {
      console.error('文件更新失败:', error);
      showToast(`更新失败: ${error.message || '未知错误'}`, 'error');
    } finally {
      updating = false;
    }
  }
  
  async function checkServiceStatus() {
    try {
      const containerInfo = await api.getServiceContainerInfo(service.id);
      
      if (containerInfo.health_status === 'unhealthy') {
        showToast(`服务环境存在问题: ${containerInfo.error_message}`, 'warning');
      } else if (containerInfo.health_status === 'healthy') {
        showToast('服务更新完成，运行正常', 'success');
      }
      
    } catch (error) {
      console.error('获取容器信息失败:', error);
    }
  }
  
  function handleClose() {
    show = false;
    // 清理文件选择
    selectedFiles = {
      gogogo: null,
      mc_config: null,
      model: null,
      examples: null
    };
    Object.values(fileInputRefs).forEach(input => {
      if (input) input.value = '';
    });
  }
  
  function handleBackdropClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      handleClose();
    }
  }
</script>

{#if show}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" on:click={handleBackdropClick}>
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b">
        <div>
          <h2 class="text-xl font-semibold text-gray-900">更新服务文件</h2>
          <p class="text-sm text-gray-600 mt-1">服务: {service.service_name}</p>
        </div>
        <button 
          on:click={handleClose}
          class="text-gray-400 hover:text-gray-600 transition-colors"
          disabled={updating}
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
      
      <!-- Body -->
      <div class="p-6 space-y-6">
        <!-- 重要提示 -->
        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div class="flex">
            <svg class="w-5 h-5 text-yellow-400 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
            </svg>
            <div>
              <h3 class="text-sm font-medium text-yellow-800">重要提示</h3>
              <p class="text-sm text-yellow-700 mt-1">
                文件更新后将重启整个容器。如果更新的文件存在问题，服务可能无法正常启动。
              </p>
            </div>
          </div>
        </div>
        
        <!-- 文件上传区域 -->
        <div class="space-y-4">
          {#each Object.entries(fileTypes) as [fileType, config]}
            <div class="border border-gray-200 rounded-lg p-4">
              <div class="flex items-start justify-between mb-3">
                <div>
                  <h3 class="text-sm font-medium text-gray-900">{config.label}</h3>
                  <p class="text-xs text-gray-600 mt-1">{config.description}</p>
                  <p class="text-xs text-gray-500 mt-1">
                    支持格式: {config.accept} | 最大: {formatFileSize(config.maxSize)}
                  </p>
                </div>
                
                {#if selectedFiles[fileType]}
                  <button
                    on:click={() => removeFile(fileType)}
                    class="text-red-500 hover:text-red-700 text-sm"
                    disabled={updating}
                  >
                    移除
                  </button>
                {/if}
              </div>
              
              {#if selectedFiles[fileType]}
                <!-- 已选择文件显示 -->
                <div class="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <div class="flex items-center">
                    <svg class="w-4 h-4 text-gray-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 0v12h8V6H8V4H6z" clip-rule="evenodd"></path>
                    </svg>
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium text-gray-900 truncate">
                        {selectedFiles[fileType]?.name}
                      </p>
                      <p class="text-xs text-gray-500">
                        {formatFileSize(selectedFiles[fileType]?.size || 0)}
                      </p>
                    </div>
                  </div>
                </div>
              {:else}
                <!-- 文件选择器 -->
                <div class="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-gray-400 transition-colors">
                  <input
                    type="file"
                    accept={config.accept}
                    on:change={(e) => handleFileSelect(fileType, e)}
                    bind:this={fileInputRefs[fileType]}
                    class="hidden"
                    disabled={updating}
                  />
                  <button
                    on:click={() => fileInputRefs[fileType]?.click()}
                    class="text-sm text-blue-600 hover:text-blue-800 font-medium"
                    disabled={updating}
                  >
                    点击选择文件
                  </button>
                  <p class="text-xs text-gray-500 mt-1">或拖拽文件到此处</p>
                </div>
              {/if}
            </div>
          {/each}
        </div>
        
        <!-- 当前服务状态 -->
        {#if service.health_status}
          <div class="bg-gray-50 rounded-lg p-4">
            <h3 class="text-sm font-medium text-gray-900 mb-2">当前服务状态</h3>
            <div class="flex items-center space-x-4 text-sm">
              <span class="flex items-center">
                <span class="w-2 h-2 rounded-full mr-2 {
                  service.health_status === 'healthy' ? 'bg-green-500' :
                  service.health_status === 'unhealthy' ? 'bg-red-500' :
                  'bg-yellow-500'
                }"></span>
                健康状态: {service.health_status}
              </span>
              <span>运行状态: {service.status}</span>
            </div>
            {#if service.error_message}
              <p class="text-xs text-red-600 mt-2">{service.error_message}</p>
            {/if}
          </div>
        {/if}
      </div>
      
      <!-- Footer -->
      <div class="flex items-center justify-end space-x-3 p-6 border-t bg-gray-50">
        <button
          on:click={handleClose}
          class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
          disabled={updating}
        >
          取消
        </button>
        <button
          on:click={handleUpdate}
          disabled={updating || !Object.values(selectedFiles).some(file => file !== null)}
          class="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
        >
          {#if updating}
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            更新中...
          {:else}
            更新文件
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  /* 拖拽样式增强 */
  .drag-over {
    @apply border-blue-400 bg-blue-50;
  }
</style>