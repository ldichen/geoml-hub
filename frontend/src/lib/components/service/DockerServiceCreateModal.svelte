<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { api } from '$lib/utils/api.js';
  import { showToast } from '$lib/utils/toast.js';
  
  export let repository: any;
  export let show = false;
  
  const dispatch = createEventDispatcher();
  
  let creating = false;
  let formData = {
    service_name: '',
    docker_image: '',
    description: '',
    gradio_port: 7860,
    cpu_limit: '2',
    memory_limit: '2Gi',
    is_public: false,
    priority: 2
  };
  
  let examplesFile: File | null = null;
  let fileInputRef: HTMLInputElement;
  
  const resourceConfigs = {
    lightweight: { cpu: '1', memory: '1Gi', label: '轻量 (1 核, 1Gi)' },
    recommended: { cpu: '2', memory: '2Gi', label: '推荐 (2 核, 2Gi)' },
    performance: { cpu: '4', memory: '5Gi', label: '性能 (4 核, 4Gi)' }
  };
  
  const priorityOptions = [
    { value: 0, label: '0 (最高优先级)' },
    { value: 1, label: '1 (高优先级)' },
    { value: 2, label: '2 (默认优先级)' },
    { value: 3, label: '3 (低优先级)' }
  ];
  
  let selectedResourceConfig = 'recommended';
  
  $: {
    // 当资源配置改变时更新表单数据
    const config = resourceConfigs[selectedResourceConfig as keyof typeof resourceConfigs];
    formData.cpu_limit = config.cpu;
    formData.memory_limit = config.memory;
  }
  
  function handleFileSelect(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    
    if (!file) {
      examplesFile = null;
      return;
    }
    
    // 验证文件大小 (最大10GB)
    const maxSize = 10 *1024 * 1024 * 1024;
    if (file.size > maxSize) {
      showToast('示例数据文件大小不能超过10GB', 'error');
      input.value = '';
      examplesFile = null;
      return;
    }
    
    // 验证文件格式
    const allowedExtensions = ['.zip', '.tar', '.tar.gz', '.tgz'];
    const fileName = file.name.toLowerCase();
    const isValidFormat = allowedExtensions.some(ext => fileName.endsWith(ext));
    
    if (!isValidFormat) {
      showToast('示例数据必须是压缩包格式 (zip, tar, tar.gz)', 'error');
      input.value = '';
      examplesFile = null;
      return;
    }
    
    examplesFile = file;
  }
  
  function removeExamplesFile() {
    examplesFile = null;
    if (fileInputRef) {
      fileInputRef.value = '';
    }
  }
  
  function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
  
  function validateDockerImage(image: string): boolean {
    // 基本的Docker镜像名称验证
    const dockerImagePattern = /^[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\/[a-z0-9]+([\-\.\_]{1}[a-z0-9]+)*(:[a-zA-Z0-9\-\.\_]+)?$|^[a-z0-9]+([\-\.\_]{1}[a-z0-9]+)*(:[a-zA-Z0-9\-\.\_]+)?$/;
    return dockerImagePattern.test(image) || image.includes('localhost') || image.includes('127.0.0.1');
  }
  
  async function handleSubmit() {
    // 验证必填字段
    if (!formData.service_name.trim()) {
      showToast('请输入服务名称', 'error');
      return;
    }
    
    if (!formData.docker_image.trim()) {
      showToast('请输入Docker镜像名称', 'error');
      return;
    }
    
    // 验证服务名称格式
    if (!/^[a-zA-Z0-9\-_]+$/.test(formData.service_name)) {
      showToast('服务名称只能包含字母、数字、下划线和连字符', 'error');
      return;
    }
    
    if (formData.service_name.length > 30) {
      showToast('服务名称不能超过30个字符', 'error');
      return;
    }
    
    // 验证Docker镜像名称
    if (!validateDockerImage(formData.docker_image)) {
      showToast('请输入有效的Docker镜像名称', 'error');
      return;
    }
    
    // 验证端口范围
    if (formData.gradio_port < 1024 || formData.gradio_port > 65535) {
      showToast('端口号必须在1024-65535之间', 'error');
      return;
    }
    
    creating = true;
    
    try {
      const submitFormData = new FormData();
      
      // 添加表单数据
      Object.entries(formData).forEach(([key, value]) => {
        submitFormData.append(key, value.toString());
      });
      
      // 添加仓库信息
      submitFormData.append('username', repository.owner.username);
      submitFormData.append('repo_name', repository.name);
      
      // 添加示例文件（如果有）
      if (examplesFile) {
        submitFormData.append('examples_archive', examplesFile);
      }
      
      const response = await api.createServiceWithImage(submitFormData);
      
      showToast('Docker服务创建成功！', 'success');
      dispatch('created', response);
      handleClose();
      
    } catch (error: any) {
      console.error('创建Docker服务失败:', error);
      showToast(`创建失败: ${error.message || '未知错误'}`, 'error');
    } finally {
      creating = false;
    }
  }
  
  function handleClose() {
    show = false;
    // 重置表单
    formData = {
      service_name: '',
      docker_image: '',
      description: '',
      gradio_port: 7860,
      cpu_limit: '2',
      memory_limit: '2Gi',
      is_public: false,
      priority: 2
    };
    selectedResourceConfig = 'recommended';
    examplesFile = null;
    if (fileInputRef) {
      fileInputRef.value = '';
    }
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
          <h2 class="text-xl font-semibold text-gray-900">创建Docker模型服务</h2>
          <p class="text-sm text-gray-600 mt-1">仓库: {repository?.owner?.username}/{repository?.name}</p>
        </div>
        <button 
          on:click={handleClose}
          class="text-gray-400 hover:text-gray-600 transition-colors"
          disabled={creating}
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
      
      <!-- Body -->
      <form on:submit|preventDefault={handleSubmit} class="p-6 space-y-6">
        <!-- 重要说明 -->
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div class="flex">
            <svg class="w-5 h-5 text-blue-400 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
            </svg>
            <div>
              <h3 class="text-sm font-medium text-blue-800">Docker镜像要求</h3>
              <div class="text-sm text-blue-700 mt-1 space-y-1">
                <p>您的Docker镜像必须包含以下文件结构：</p>
                <ul class="list-disc list-inside ml-2 space-y-1">
                  <li><code class="bg-blue-100 px-1 rounded">gogogo.py</code> - 模型服务启动文件</li>
                  <li><code class="bg-blue-100 px-1 rounded">mc.json</code> - 配置文件</li>
                  <li><code class="bg-blue-100 px-1 rounded">model/</code> - 模型文件目录</li>
                </ul>
                <p class="mt-2">可选上传 <code class="bg-blue-100 px-1 rounded">examples/</code> 示例数据目录。</p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 基本信息 -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label for="service_name" class="block text-sm font-medium text-gray-700 mb-2">
              服务名称 <span class="text-red-500">*</span>
            </label>
            <input
              id="service_name"
              type="text"
              bind:value={formData.service_name}
              placeholder="输入服务名称"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              maxlength="30"
              required
              disabled={creating}
            />
            <p class="text-xs text-gray-500 mt-1">只能包含字母、数字、下划线和连字符，最长30字符</p>
          </div>
          
          <div>
            <label for="docker_image" class="block text-sm font-medium text-gray-700 mb-2">
              Docker镜像 <span class="text-red-500">*</span>
            </label>
            <input
              id="docker_image"
              type="text"
              bind:value={formData.docker_image}
              placeholder="例如: my-model:latest"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
              disabled={creating}
            />
            <p class="text-xs text-gray-500 mt-1">完整的Docker镜像名称和标签</p>
          </div>
        </div>
        
        <!-- 服务描述 -->
        <div>
          <label for="description" class="block text-sm font-medium text-gray-700 mb-2">
            服务描述
          </label>
          <textarea
            id="description"
            bind:value={formData.description}
            placeholder="描述您的模型服务功能..."
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            disabled={creating}
          ></textarea>
        </div>
        
        <!-- 配置选项 -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label for="gradio_port" class="block text-sm font-medium text-gray-700 mb-2">
              Gradio端口
            </label>
            <input
              id="gradio_port"
              type="number"
              bind:value={formData.gradio_port}
              min="1024"
              max="65535"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={creating}
            />
            <p class="text-xs text-gray-500 mt-1">1024-65535范围内的端口号</p>
          </div>
          
          <div>
            <label for="priority" class="block text-sm font-medium text-gray-700 mb-2">
              启动优先级
            </label>
            <select
              id="priority"
              bind:value={formData.priority}
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={creating}
            >
              {#each priorityOptions as option}
                <option value={option.value}>{option.label}</option>
              {/each}
            </select>
          </div>
        </div>
        
        <!-- 资源配置 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-3">资源配置</label>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
            {#each Object.entries(resourceConfigs) as [key, config]}
              <label class="relative">
                <input
                  type="radio"
                  bind:group={selectedResourceConfig}
                  value={key}
                  class="sr-only"
                  disabled={creating}
                />
                <div class="border-2 rounded-lg p-3 cursor-pointer transition-all {
                  selectedResourceConfig === key 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:border-gray-300'
                }">
                  <div class="text-sm font-medium text-gray-900">{config.label}</div>
                </div>
              </label>
            {/each}
          </div>
        </div>
        
        <!-- 访问设置 -->
        <div>
          <label class="flex items-center">
            <input
              type="checkbox"
              bind:checked={formData.is_public}
              class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              disabled={creating}
            />
            <span class="ml-2 text-sm text-gray-700">允许公开访问（未登录用户可以使用此服务）</span>
          </label>
        </div>
        
        <!-- 示例数据上传 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-3">
            示例数据 <span class="text-gray-500">(可选)</span>
          </label>
          
          {#if examplesFile}
            <!-- 已选择文件显示 -->
            <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div class="flex items-center justify-between">
                <div class="flex items-center">
                  <svg class="w-5 h-5 text-gray-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 0v12h8V6H8V4H6z" clip-rule="evenodd"></path>
                  </svg>
                  <div>
                    <p class="text-sm font-medium text-gray-900">{examplesFile.name}</p>
                    <p class="text-xs text-gray-500">{formatFileSize(examplesFile.size)}</p>
                  </div>
                </div>
                <button
                  type="button"
                  on:click={removeExamplesFile}
                  class="text-red-500 hover:text-red-700 text-sm"
                  disabled={creating}
                >
                  移除
                </button>
              </div>
            </div>
          {:else}
            <!-- 文件选择器 -->
            <div class="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
              <input
                type="file"
                accept=".zip,.tar,.tar.gz,.tgz"
                on:change={handleFileSelect}
                bind:this={fileInputRef}
                class="hidden"
                disabled={creating}
              />
              <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <div class="mt-4">
                <button
                  type="button"
                  on:click={() => fileInputRef?.click()}
                  class="text-blue-600 hover:text-blue-800 font-medium"
                  disabled={creating}
                >
                  点击选择示例数据压缩包
                </button>
                <p class="text-sm text-gray-500 mt-2">支持 ZIP, TAR, TAR.GZ 格式，最大10GB</p>
              </div>
            </div>
          {/if}
        </div>
      </form>
      
      <!-- Footer -->
      <div class="flex items-center justify-end space-x-3 p-6 border-t bg-gray-50">
        <button
          type="button"
          on:click={handleClose}
          class="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
          disabled={creating}
        >
          取消
        </button>
        <button
          type="submit"
          on:click={handleSubmit}
          disabled={creating || !formData.service_name.trim() || !formData.docker_image.trim()}
          class="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
        >
          {#if creating}
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            创建中...
          {:else}
            创建服务
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}