<script>
  import { createEventDispatcher } from 'svelte';
  import { X, Save, Settings, Shield, Cpu, HardDrive, Upload, FileText, Package, FolderOpen, AlertCircle, Info } from 'lucide-svelte';
  import { api } from '$lib/utils/api';

  export let service;
  export let isOpen = false;
  export let loading = false;

  const dispatch = createEventDispatcher();

  // 资源配置预设
  const resourceConfigs = {
    'lightweight': { cpu: '1', memory: '1Gi', label: '轻量配置', icon: 'eco', color: 'green' },
    'recommended': { cpu: '2', memory: '2Gi', label: '推荐配置', icon: 'zap', color: 'blue' },
    'performance': { cpu: '4', memory: '4Gi', label: '性能配置', icon: 'rocket', color: 'purple' }
  };

  let formData = {
    resource_config: 'recommended', // 资源配置预设选择
    cpu_limit: '2',
    memory_limit: '2Gi',
    is_public: false
  };
  let errors = {};

  // 文件上传状态
  let mcJsonFile = null;
  let gogogoFile = null;
  let modelFile = null;
  let examplesFile = null;

  // File input references
  let mcJsonFileRef;
  let gogogoFileRef;
  let modelFileRef;
  let examplesFileRef;

  // Drag and drop states
  let isDragOverMcJson = false;
  let isDragOverGogogo = false;
  let isDragOverModel = false;
  let isDragOverExamples = false;

  // Reset form data when service changes
  $: if (service) {
    formData = {
      resource_config: getCurrentResourceConfig(service.cpu_limit, service.memory_limit),
      cpu_limit: service.cpu_limit || '2',
      memory_limit: service.memory_limit || '2Gi',
      is_public: service.is_public || false
    };
    errors = {};
    resetFiles();
  }

  function getCurrentResourceConfig(cpu, memory) {
    // 根据当前CPU和内存配置确定预设
    for (const [key, config] of Object.entries(resourceConfigs)) {
      if (config.cpu === cpu && config.memory === memory) {
        return key;
      }
    }
    return 'recommended'; // 默认推荐配置
  }

  function resetFiles() {
    mcJsonFile = null;
    gogogoFile = null;
    modelFile = null;
    examplesFile = null;
    if (mcJsonFileRef) mcJsonFileRef.value = '';
    if (gogogoFileRef) gogogoFileRef.value = '';
    if (modelFileRef) modelFileRef.value = '';
    if (examplesFileRef) examplesFileRef.value = '';
  }

  function handleClose() {
    if (loading) return;
    dispatch('close');
    resetForm();
  }

  function resetForm() {
    if (service) {
      formData = {
        resource_config: getCurrentResourceConfig(service.cpu_limit, service.memory_limit),
        cpu_limit: service.cpu_limit || '2',
        memory_limit: service.memory_limit || '2Gi',
        is_public: service.is_public || false
      };
    }
    errors = {};
    resetFiles();
  }

  // 处理资源配置变更
  function handleResourceConfigChange() {
    const config = resourceConfigs[formData.resource_config];
    if (config) {
      formData.cpu_limit = config.cpu;
      formData.memory_limit = config.memory;
    }
  }

  function validateForm() {
    errors = {};
    return Object.keys(errors).length === 0;
  }

  async function handleSave() {
    if (!validateForm()) {
      return;
    }

    try {
      loading = true;

      // 准备更新数据
      const updateData = new FormData();
      updateData.append('cpu_limit', formData.cpu_limit);
      updateData.append('memory_limit', formData.memory_limit);
      updateData.append('is_public', formData.is_public.toString());

      // 添加文件更新
      if (mcJsonFile) {
        updateData.append('mc_json', mcJsonFile);
      }
      if (gogogoFile) {
        updateData.append('gogogo_py', gogogoFile);
      }
      if (modelFile) {
        updateData.append('model_archive', modelFile);
      }
      if (examplesFile) {
        updateData.append('examples_archive', examplesFile);
      }

      await api.updateServiceFiles(service.id, updateData);
      
      dispatch('updated', { ...formData, id: service.id });
      handleClose();
    } catch (error) {
      console.error('Failed to update service:', error);
      alert(`更新服务失败: ${error.message}`);
    } finally {
      loading = false;
    }
  }

  function handleKeydown(event) {
    if (event.key === 'Escape' && !loading) {
      handleClose();
    }
  }

  // File handling functions
  function handleFileSelect(event, fileType) {
    const input = event.target;
    const file = input.files?.[0];
    
    if (!file) {
      setFile(fileType, null);
      return;
    }
    
    // Validate file based on type
    const validationResult = validateFile(file, fileType);
    if (!validationResult.isValid) {
      alert(validationResult.message);
      input.value = '';
      setFile(fileType, null);
      return;
    }
    
    setFile(fileType, file);
  }

  function validateFile(file, fileType) {
    switch (fileType) {
      case 'mcJson':
        if (!file.name.toLowerCase().endsWith('.json')) {
          return { isValid: false, message: 'mc.json 必须是JSON格式文件' };
        }
        if (file.size > 1024 * 1024) { // 1MB
          return { isValid: false, message: 'mc.json 文件大小不能超过1MB' };
        }
        break;
      case 'gogogo':
        if (!file.name.toLowerCase().endsWith('.py')) {
          return { isValid: false, message: 'gogogo.py 必须是Python文件' };
        }
        if (file.size > 10 * 1024 * 1024) { // 10MB
          return { isValid: false, message: 'gogogo.py 文件大小不能超过10MB' };
        }
        break;
      case 'model':
        const modelExtensions = ['.zip', '.tar', '.tar.gz', '.tgz'];
        const isValidModel = modelExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
        if (!isValidModel) {
          return { isValid: false, message: 'model 必须是压缩包格式 (zip, tar, tar.gz)' };
        }
        if (file.size > 2 * 1024 * 1024 * 1024) { // 2GB
          return { isValid: false, message: 'model 文件大小不能超过2GB' };
        }
        break;
      case 'examples':
        const exampleExtensions = ['.zip', '.tar', '.tar.gz', '.tgz'];
        const isValidExample = exampleExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
        if (!isValidExample) {
          return { isValid: false, message: 'examples 必须是压缩包格式 (zip, tar, tar.gz)' };
        }
        if (file.size > 100 * 1024 * 1024) { // 100MB
          return { isValid: false, message: 'examples 文件大小不能超过100MB' };
        }
        break;
    }
    return { isValid: true };
  }

  function setFile(fileType, file) {
    switch (fileType) {
      case 'mcJson':
        mcJsonFile = file;
        break;
      case 'gogogo':
        gogogoFile = file;
        break;
      case 'model':
        modelFile = file;
        break;
      case 'examples':
        examplesFile = file;
        break;
    }
  }

  function removeFile(fileType) {
    setFile(fileType, null);
    // Reset corresponding file input
    switch (fileType) {
      case 'mcJson':
        if (mcJsonFileRef) mcJsonFileRef.value = '';
        break;
      case 'gogogo':
        if (gogogoFileRef) gogogoFileRef.value = '';
        break;
      case 'model':
        if (modelFileRef) modelFileRef.value = '';
        break;
      case 'examples':
        if (examplesFileRef) examplesFileRef.value = '';
        break;
    }
  }

  function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // Drag and drop handlers
  function createDragHandlers(fileType) {
    return {
      handleDragEnter: (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragState(fileType, true);
      },
      handleDragLeave: (e) => {
        e.preventDefault();
        e.stopPropagation();
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX;
        const y = e.clientY;
        
        if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
          setDragState(fileType, false);
        }
      },
      handleDragOver: (e) => {
        e.preventDefault();
        e.stopPropagation();
      },
      handleDrop: (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragState(fileType, false);
        
        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0) {
          const file = files[0];
          const validationResult = validateFile(file, fileType);
          if (!validationResult.isValid) {
            alert(validationResult.message);
            return;
          }
          setFile(fileType, file);
        }
      }
    };
  }

  function setDragState(fileType, isDragging) {
    switch (fileType) {
      case 'mcJson':
        isDragOverMcJson = isDragging;
        break;
      case 'gogogo':
        isDragOverGogogo = isDragging;
        break;
      case 'model':
        isDragOverModel = isDragging;
        break;
      case 'examples':
        isDragOverExamples = isDragging;
        break;
    }
  }

  function getDragState(fileType) {
    switch (fileType) {
      case 'mcJson':
        return isDragOverMcJson;
      case 'gogogo':
        return isDragOverGogogo;
      case 'model':
        return isDragOverModel;
      case 'examples':
        return isDragOverExamples;
      default:
        return false;
    }
  }

  function getFile(fileType) {
    switch (fileType) {
      case 'mcJson':
        return mcJsonFile;
      case 'gogogo':
        return gogogoFile;
      case 'model':
        return modelFile;
      case 'examples':
        return examplesFile;
      default:
        return null;
    }
  }

  function getFileRef(fileType) {
    switch (fileType) {
      case 'mcJson':
        return mcJsonFileRef;
      case 'gogogo':
        return gogogoFileRef;
      case 'model':
        return modelFileRef;
      case 'examples':
        return examplesFileRef;
      default:
        return null;
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if isOpen}
  <!-- Backdrop with blur effect -->
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
    <!-- Modal Container -->
    <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden border border-gray-200 dark:border-gray-700">
      <!-- Header -->
      <div class="relative bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700 px-6 py-4 border-b border-gray-200 dark:border-gray-600">
        <div class="flex items-center space-x-3">
          <div class="flex items-center justify-center w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-xl">
            <Settings class="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 class="text-xl font-bold text-gray-900 dark:text-white">
              服务设置
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-300 mt-1">
              配置资源和更新服务文件 - {service?.service_name}
            </p>
          </div>
        </div>
        <button
          class="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-all duration-200"
          on:click={handleClose}
          disabled={loading}
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Form -->
      <form on:submit|preventDefault={handleSave}>
        <div class="overflow-y-auto max-h-[calc(90vh-140px)]">
          <div class="p-6 space-y-6">
            <!-- Resource Configuration Section -->
            <div class="bg-gray-50 dark:bg-gray-800/50 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
              <div class="flex items-center space-x-2 mb-4">
                <div class="flex items-center justify-center w-8 h-8 bg-purple-100 dark:bg-purple-900 rounded-lg">
                  <Settings class="w-4 h-4 text-purple-600 dark:text-purple-400" />
                </div>
                <h4 class="text-lg font-semibold text-gray-900 dark:text-white">资源配置</h4>
              </div>

              <div class="space-y-4">
                <!-- Resource Configuration Presets -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    资源配置 <span class="text-red-500">*</span>
                  </label>
                  <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    {#each Object.entries(resourceConfigs) as [key, config]}
                      <label class="relative">
                        <input
                          type="radio"
                          name="resource_config"
                          value={key}
                          bind:group={formData.resource_config}
                          on:change={handleResourceConfigChange}
                          class="sr-only"
                          disabled={loading}
                        />
                        <div class="flex flex-col p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md {formData.resource_config === key ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'}">
                          <div class="flex items-center justify-between mb-2">
                            <span class="font-medium text-sm text-gray-900 dark:text-white">{config.label}</span>
                            {#if key === 'recommended'}
                              <span class="text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 px-2 py-1 rounded-full">推荐</span>
                            {/if}
                          </div>
                          <div class="flex items-center space-x-3 text-xs text-gray-600 dark:text-gray-400">
                            <div class="flex items-center space-x-1">
                              <Cpu class="w-3 h-3" />
                              <span>{config.cpu}</span>
                            </div>
                            <div class="flex items-center space-x-1">
                              <HardDrive class="w-3 h-3" />
                              <span>{config.memory}</span>
                            </div>
                          </div>
                        </div>
                      </label>
                    {/each}
                  </div>
                  <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 mt-3">
                    <p class="text-sm text-blue-800 dark:text-blue-200 flex items-center space-x-2">
                      <Info class="w-4 h-4" />
                      <span>当前配置：CPU {formData.cpu_limit} cores，内存 {formData.memory_limit}</span>
                    </p>
                  </div>
                </div>

                <!-- Public Access -->
                <div class="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg p-4 border border-green-200 dark:border-green-700">
                  <div class="flex items-start space-x-3">
                    <input
                      type="checkbox"
                      id="is_public"
                      bind:checked={formData.is_public}
                      class="mt-1 h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded transition-colors"
                      disabled={loading}
                    />
                    <div class="flex-1">
                      <label for="is_public" class="block text-sm font-medium text-gray-900 dark:text-white">
                        <div class="flex items-center space-x-2">
                          <Shield class="w-4 h-4 text-green-600 dark:text-green-400" />
                          <span>公开访问</span>
                        </div>
                      </label>
                      <p class="text-xs text-gray-600 dark:text-gray-400">
                        允许任何人访问和使用此服务
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- File Modification Section -->
            <div class="bg-gray-50 dark:bg-gray-800/50 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
              <div class="flex items-center space-x-2 mb-4">
                <div class="flex items-center justify-center w-8 h-8 bg-orange-100 dark:bg-orange-900 rounded-lg">
                  <Upload class="w-4 h-4 text-orange-600 dark:text-orange-400" />
                </div>
                <h4 class="text-lg font-semibold text-gray-900 dark:text-white">文件更新</h4>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- mc.json Upload -->
                {#each [
                  { type: 'mcJson', title: 'mc.json', subtitle: '模型配置文件', icon: FileText, ref: mcJsonFileRef, accept: '.json' },
                  { type: 'gogogo', title: 'gogogo.py', subtitle: '服务启动脚本', icon: FileText, ref: gogogoFileRef, accept: '.py' },
                  { type: 'model', title: 'model', subtitle: '模型文件压缩包', icon: Package, ref: modelFileRef, accept: '.zip,.tar,.tar.gz,.tgz' },
                  { type: 'examples', title: 'examples', subtitle: '示例数据压缩包', icon: FolderOpen, ref: examplesFileRef, accept: '.zip,.tar,.tar.gz,.tgz' }
                ] as fileConfig}
                  <div class="space-y-2">
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      {fileConfig.title}
                    </label>
                    <p class="text-xs text-gray-500 dark:text-gray-400 mb-2">{fileConfig.subtitle}</p>
                    
                    {#if getFile(fileConfig.type)}
                      <!-- File selected -->
                      <div class="bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-3">
                        <div class="flex items-center justify-between">
                          <div class="flex items-center">
                            <div class="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mr-3">
                              <svelte:component this={fileConfig.icon} class="w-4 h-4 text-blue-600 dark:text-blue-400" />
                            </div>
                            <div>
                              <p class="text-sm font-medium text-gray-900 dark:text-white">{getFile(fileConfig.type).name}</p>
                              <p class="text-xs text-gray-500 dark:text-gray-400">{formatFileSize(getFile(fileConfig.type).size)}</p>
                            </div>
                          </div>
                          <button
                            type="button"
                            on:click={() => removeFile(fileConfig.type)}
                            class="text-red-500 hover:text-red-700 text-sm font-medium"
                            disabled={loading}
                          >
                            移除
                          </button>
                        </div>
                      </div>
                    {:else}
                      <!-- File selector with drag-and-drop -->
                      <div 
                        class="border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer {getDragState(fileConfig.type) ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'}"
                        on:click={() => getFileRef(fileConfig.type)?.click()}
                        on:dragenter={createDragHandlers(fileConfig.type).handleDragEnter}
                        on:dragleave={createDragHandlers(fileConfig.type).handleDragLeave}
                        on:dragover={createDragHandlers(fileConfig.type).handleDragOver}
                        on:drop={createDragHandlers(fileConfig.type).handleDrop}
                      >
                        <input
                          type="file"
                          accept={fileConfig.accept}
                          on:change={(e) => handleFileSelect(e, fileConfig.type)}
                          bind:this={fileConfig.ref}
                          class="hidden"
                          disabled={loading}
                        />
                        <svelte:component this={fileConfig.icon} class="mx-auto h-8 w-8 text-gray-400 dark:text-gray-500 mb-2" />
                        <button
                          type="button"
                          on:click={() => getFileRef(fileConfig.type)?.click()}
                          class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium text-sm"
                          disabled={loading}
                        >
                          {getDragState(fileConfig.type) ? '释放文件到此处' : `点击选择或拖拽${fileConfig.title}文件`}
                        </button>
                      </div>
                    {/if}
                  </div>
                {/each}
              </div>
            </div>
          </div>
        </div>

        <!-- Sticky Footer -->
        <div class="sticky bottom-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 px-6 py-4">
          <div class="flex items-center justify-between">
            <div class="text-sm text-gray-500 dark:text-gray-400">
              {#if loading}
                <div class="flex items-center space-x-2">
                  <div class="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                  <span>正在保存设置...</span>
                </div>
              {:else}
                配置资源选项和更新文件
              {/if}
            </div>
            <div class="flex space-x-3">
              <button
                type="button"
                class="px-6 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-600 hover:bg-gray-200 dark:hover:bg-gray-500 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                on:click={handleClose}
                disabled={loading}
              >
                取消
              </button>
              <button
                type="submit"
                class="px-6 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
                disabled={loading}
              >
                {#if loading}
                  <div class="flex items-center space-x-2">
                    <div class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
                    <span>保存中...</span>
                  </div>
                {:else}
                  <div class="flex items-center space-x-2">
                    <Save class="w-4 h-4" />
                    <span>保存设置</span>
                  </div>
                {/if}
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  </div>
{/if}

<style>
  /* Custom animations and transitions */
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-10px) scale(0.95);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  /* Modal enter animation */
  .fixed.inset-0 {
    animation: fadeIn 0.2s ease-out;
  }

  .fixed.inset-0 > div {
    animation: slideIn 0.3s ease-out;
  }

  /* Custom radio button styles */
  input[type="radio"]:checked + div {
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
  }

  /* Custom checkbox styles */
  input[type="checkbox"]:indeterminate {
    background-color: #3b82f6;
    border-color: #3b82f6;
  }

  /* Scrollbar styling for better UX */
  .overflow-y-auto::-webkit-scrollbar {
    width: 6px;
  }

  .overflow-y-auto::-webkit-scrollbar-track {
    background: transparent;
  }

  .overflow-y-auto::-webkit-scrollbar-thumb {
    background: rgba(156, 163, 175, 0.5);
    border-radius: 3px;
  }

  .overflow-y-auto::-webkit-scrollbar-thumb:hover {
    background: rgba(156, 163, 175, 0.7);
  }

  /* Dark mode scrollbar */
  .dark .overflow-y-auto::-webkit-scrollbar-thumb {
    background: rgba(75, 85, 99, 0.5);
  }

  .dark .overflow-y-auto::-webkit-scrollbar-thumb:hover {
    background: rgba(75, 85, 99, 0.7);
  }
</style>