<script>
  import { createEventDispatcher } from 'svelte';
  import { X, AlertCircle, Info, Settings, Zap, Shield, Cpu, HardDrive } from 'lucide-svelte';

  export let isOpen = false;
  export let loading = false;
  export let progress = 0; // 服务创建进度 (0-100)
  export let availableImages = []; // 可用的镜像列表

  const dispatch = createEventDispatcher();

  // 创建方式选择：'docker-upload' 或 'existing-image'
  let creationMode = 'docker-upload';

  let formElement;
  // 资源配置预设
  const resourceConfigs = {
    'lightweight': { cpu: '1', memory: '1Gi', label: '轻量配置', icon: 'eco', color: 'green' },
    'recommended': { cpu: '2', memory: '2Gi', label: '推荐配置', icon: 'zap', color: 'blue' },
    'performance': { cpu: '4', memory: '4Gi', label: '性能配置', icon: 'rocket', color: 'purple' }
  };

  // 优先级选项
  const priorityOptions = [
    { value: 1, label: '1 (最高)' },
    { value: 2, label: '2 (默认)' },
    { value: 3, label: '3 (最低)' }
  ];

  let formData = {
    description: '',
    resource_config: 'recommended', // 资源配置预设选择
    cpu_limit: '2',
    memory_limit: '2Gi',
    is_public: false,
    priority: 2,
    selected_image_id: null // 当选择已有镜像时使用
  };

  let dockerTarFile = null;
  let dockerFileInputRef;
  let examplesFile = null;
  let fileInputRef;

  let errors = {};
  
  // Drag and drop states
  let isDragOverDocker = false;
  let isDragOverExamples = false;

  function handleClose() {
    if (loading) return;
    dispatch('close');
    resetForm();
  }

  function resetForm() {
    formData = {
      description: '',
      resource_config: 'recommended',
      cpu_limit: '2',
      memory_limit: '2Gi',
      is_public: false,
      priority: 2,
      selected_image_id: null
    };
    errors = {};
    examplesFile = null;
    dockerTarFile = null;
    creationMode = 'docker-upload';
    if (fileInputRef) {
      fileInputRef.value = '';
    }
    if (dockerFileInputRef) {
      dockerFileInputRef.value = '';
    }
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

    if (creationMode === 'docker-upload') {
      // Docker tar包是必须的
      if (!dockerTarFile) {
        errors.docker_tar = 'Docker镜像tar包是必填项';
      }
    } else if (creationMode === 'existing-image') {
      // 必须选择一个镜像
      if (!formData.selected_image_id) {
        errors.selected_image = '请选择一个镜像';
      }
    }

    // Priority validation
    if (![1, 2, 3].includes(formData.priority)) {
      errors.priority = '优先级必须选择1、2或3';
    }

    return Object.keys(errors).length === 0;
  }

  function handleSubmit() {
    if (!validateForm()) {
      return;
    }

    if (creationMode === 'docker-upload') {
      // 传统方式：构建FormData以支持文件上传
      const submitFormData = new FormData();
      
      // 添加Docker tar包（必需）
      submitFormData.append('docker_tar', dockerTarFile);
      
      // 添加表单数据
      Object.entries(formData).forEach(([key, value]) => {
        if (key !== 'resource_config' && key !== 'selected_image_id') { // 不包含resource_config和selected_image_id
          submitFormData.append(key, value.toString());
        }
      });
      
      // 添加示例文件（如果有）
      if (examplesFile) {
        submitFormData.append('examples_archive', examplesFile);
      }

      dispatch('create', { type: 'docker-upload', data: submitFormData });
    } else if (creationMode === 'existing-image') {
      // 新方式：基于已有镜像创建服务，支持示例文件上传
      const submitFormData = new FormData();
      
      // 添加表单数据
      submitFormData.append('image_id', formData.selected_image_id.toString());
      submitFormData.append('description', formData.description || '');
      submitFormData.append('cpu_limit', formData.cpu_limit);
      submitFormData.append('memory_limit', formData.memory_limit);
      submitFormData.append('is_public', formData.is_public.toString());
      submitFormData.append('priority', formData.priority.toString());
      
      // 添加示例文件（如果有）
      if (examplesFile) {
        submitFormData.append('examples_archive', examplesFile);
      }

      dispatch('create', { type: 'existing-image', data: submitFormData });
    }
  }

  function handleKeydown(event) {
    if (event.key === 'Escape' && !loading) {
      handleClose();
    }
  }

  // CPU limit presets
  const cpuPresets = [
    { value: '1', label: '1 cores (轻量)' },
    { value: '2', label: '2 cores (推荐)' },
    { value: '4', label: '4 cores' },
    { value: '8', label: '8 cores' }
  ];

  // Memory limit presets
  const memoryPresets = [
    { value: '1Gi', label: '1Gi (最小)' },
    { value: '2Gi', label: '2Gi (推荐)' },
    { value: '4Gi', label: '4Gi' },
    { value: '8Gi', label: '8Gi' }
  ];

  // 处理Docker tar文件选择
  function handleDockerFileSelect(event) {
    const input = event.target;
    const file = input.files?.[0];
    
    if (!file) {
      dockerTarFile = null;
      return;
    }
    
    // 验证文件大小 (最大2GB)
    const maxSize = 20 * 1024 * 1024 * 1024;
    if (file.size > maxSize) {
      alert('Docker镜像tar包大小不能超过20GB');
      input.value = '';
      dockerTarFile = null;
      return;
    }
    
    // 验证文件格式
    const allowedExtensions = ['.tar', '.tar.gz', '.tgz'];
    const fileName = file.name.toLowerCase();
    const isValidFormat = allowedExtensions.some(ext => fileName.endsWith(ext));
    
    if (!isValidFormat) {
      alert('Docker镜像必须是tar包格式 (tar, tar.gz, tgz)');
      input.value = '';
      dockerTarFile = null;
      return;
    }
    
    dockerTarFile = file;
  }

  function removeDockerFile() {
    dockerTarFile = null;
    if (dockerFileInputRef) {
      dockerFileInputRef.value = '';
    }
  }

  // 处理examples文件选择
  function handleFileSelect(event) {
    const input = event.target;
    const file = input.files?.[0];
    
    if (!file) {
      examplesFile = null;
      return;
    }
    
    // 验证文件大小 (最大10GB)
    const maxSize = 10 * 1024 * 1024 * 1024;
    if (file.size > maxSize) {
      alert('示例数据文件大小不能超过10GB');
      input.value = '';
      examplesFile = null;
      return;
    }
    
    // 验证文件格式
    const allowedExtensions = ['.zip', '.tar', '.tar.gz', '.tgz'];
    const fileName = file.name.toLowerCase();
    const isValidFormat = allowedExtensions.some(ext => fileName.endsWith(ext));
    
    if (!isValidFormat) {
      alert('示例数据必须是压缩包格式 (zip, tar, tar.gz)');
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

  function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // Drag and drop handlers for Docker tar file
  function handleDockerDragEnter(e) {
    e.preventDefault();
    e.stopPropagation();
    isDragOverDocker = true;
  }

  function handleDockerDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX;
    const y = e.clientY;
    
    if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
      isDragOverDocker = false;
    }
  }

  function handleDockerDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  function handleDockerDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    isDragOverDocker = false;
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      const file = files[0];
      
      // Validate file size (max 2GB)
      const maxSize = 20 * 1024 * 1024 * 1024;
      if (file.size > maxSize) {
        alert('Docker镜像tar包大小不能超过20GB');
        return;
      }
      
      // Validate file format
      const allowedExtensions = ['.tar', '.tar.gz', '.tgz'];
      const fileName = file.name.toLowerCase();
      const isValidFormat = allowedExtensions.some(ext => fileName.endsWith(ext));
      
      if (!isValidFormat) {
        alert('Docker镜像必须是tar包格式 (tar, tar.gz, tgz)');
        return;
      }
      
      dockerTarFile = file;
    }
  }

  // Drag and drop handlers for examples file
  function handleExamplesDragEnter(e) {
    e.preventDefault();
    e.stopPropagation();
    isDragOverExamples = true;
  }

  function handleExamplesDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX;
    const y = e.clientY;
    
    if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
      isDragOverExamples = false;
    }
  }

  function handleExamplesDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  function handleExamplesDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    isDragOverExamples = false;
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      const file = files[0];
      
      // Validate file size (max 10GB)
      const maxSize = 10 * 1024 * 1024 * 1024;
      if (file.size > maxSize) {
        alert('示例数据文件大小不能超过10GB');
        return;
      }
      
      // Validate file format
      const allowedExtensions = ['.zip', '.tar', '.tar.gz', '.tgz'];
      const fileName = file.name.toLowerCase();
      const isValidFormat = allowedExtensions.some(ext => fileName.endsWith(ext));
      
      if (!isValidFormat) {
        alert('示例数据必须是压缩包格式 (zip, tar, tar.gz)');
        return;
      }
      
      examplesFile = file;
    }
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if isOpen}
  <!-- Backdrop with blur effect -->
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
    <!-- Modal Container -->
    <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-3xl w-full mx-4 max-h-[100vh] overflow-hidden border border-gray-200 dark:border-gray-700">
      <!-- Header -->
      <div class="relative bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700 px-6 py-4 border-b border-gray-200 dark:border-gray-600">
        <div class="flex items-center space-x-3">
          <div class="flex items-center justify-center w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-xl">
            <Settings class="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 class="text-xl font-bold text-gray-900 dark:text-white">
              创建模型服务
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-300 mt-1">
              配置并部署您的机器学习模型服务
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
      <form bind:this={formElement} on:submit|preventDefault={handleSubmit}>
        <div class="overflow-y-auto max-h-[calc(90vh-120px)]">
          <div class="p-4 space-y-4">
            <!-- Creation Mode Selector -->
            <div class="bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-gray-800 dark:to-gray-700 rounded-xl p-4 border border-indigo-200 dark:border-gray-600">
              <h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">选择创建方式</h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <!-- Docker Upload Option -->
                <label class="relative">
                  <input
                    type="radio"
                    name="creationMode"
                    value="docker-upload"
                    bind:group={creationMode}
                    class="sr-only"
                    disabled={loading}
                  />
                  <div class="flex flex-col p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md {creationMode === 'docker-upload' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'}">
                    <div class="flex items-center justify-between mb-2">
                      <span class="font-medium text-sm text-gray-900 dark:text-white">上传模型镜像</span>
                      <span class="text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 px-2 py-1 rounded-full">手动部署</span>
                    </div>
                    <p class="text-xs text-gray-600 dark:text-gray-400">直接上传模型镜像tar包创建服务</p>
                  </div>
                </label>

                <!-- Existing Image Option -->
                <label class="relative">
                  <input
                    type="radio"
                    name="creationMode"
                    value="existing-image"
                    bind:group={creationMode}
                    class="sr-only"
                    disabled={loading || availableImages.length === 0}
                  />
                  <div class="flex flex-col p-4 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md {creationMode === 'existing-image' ? 'border-green-500 bg-green-50 dark:bg-green-900/20' : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'} {availableImages.length === 0 ? 'opacity-50 cursor-not-allowed' : ''}">
                    <div class="flex items-center justify-between mb-2">
                      <span class="font-medium text-sm text-gray-900 dark:text-white">使用已有镜像</span>
                      <span class="text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 px-2 py-1 rounded-full">推荐</span>
                    </div>
                    <p class="text-xs text-gray-600 dark:text-gray-400">
                      {availableImages.length > 0 ? `从 ${availableImages.length} 个可用镜像中选择` : '暂无可用镜像'}
                    </p>
                  </div>
                </label>
              </div>
            </div>

            <!-- Docker Requirements Notice (仅在docker-upload模式显示) -->
            {#if creationMode === 'docker-upload'}
            <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-xl p-4">
              <div class="flex items-start space-x-3">
                <div class="flex-shrink-0">
                  <Info class="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
                </div>
                <div class="flex-1">
                  <h4 class="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
                    Docker镜像要求
                  </h4>
                  <div class="text-sm text-blue-800 dark:text-blue-200 space-y-2">
                    <p>您的Docker镜像必须包含以下文件结构（位于镜像的根目录）：</p>
                    <ul class="list-disc list-inside ml-2 space-y-1">
                      <li><code class="bg-blue-100 dark:bg-blue-800 px-1.5 py-0.5 rounded text-xs font-mono">gogogo.py</code> - 模型服务的启动文件</li>
                      <li><code class="bg-blue-100 dark:bg-blue-800 px-1.5 py-0.5 rounded text-xs font-mono">mc.json</code> - 配置文件</li>
                      <li><code class="bg-blue-100 dark:bg-blue-800 px-1.5 py-0.5 rounded text-xs font-mono">model/</code> - 模型文件夹</li>
                    </ul>
                    <p class="mt-2">可选文件：</p>
                    <ul class="list-disc list-inside ml-2">
                      <li><code class="bg-blue-100 dark:bg-blue-800 px-1.5 py-0.5 rounded text-xs font-mono">examples/</code> - 用于展示的样例数据文件夹（可后续上传）</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
            {/if}

            <!-- Image Selection (仅在existing-image模式显示) -->
            {#if creationMode === 'existing-image'}
            <div class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-xl p-6">
              <div class="flex items-center space-x-2 mb-4">
                <div class="flex items-center justify-center w-8 h-8 bg-green-100 dark:bg-green-900 rounded-lg">
                  <svg class="w-4 h-4 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2h4a1 1 0 011 1v1a1 1 0 01-1 1v9a2 2 0 01-2 2H5a2 2 0 01-2-2V7a1 1 0 01-1-1V5a1 1 0 011-1h4z"></path>
                  </svg>
                </div>
                <h4 class="text-lg font-semibold text-gray-900 dark:text-white">选择镜像</h4>
              </div>
              
              <div class="space-y-3">
                
                {#if availableImages.length > 0}
                  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {#each availableImages as image (image.id)}
                      <label class="relative">
                        <input
                          type="radio"
                          name="selectedImage"
                          value={image.id}
                          bind:group={formData.selected_image_id}
                          class="sr-only"
                          disabled={loading || image.status !== 'ready'}
                        />
                        <div class="flex flex-col p-3 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md {formData.selected_image_id === image.id ? 'border-green-500 bg-green-50 dark:bg-green-900/20' : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'} {image.status !== 'ready' ? 'opacity-50 cursor-not-allowed' : ''} min-h-[120px]">
                          <div class="flex items-center justify-between mb-2">
                            <div class="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                              <svg class="w-4 h-4 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                              </svg>
                            </div>
                            <span class="text-xs px-2 py-1 rounded-full {image.status === 'ready' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'}">
                              {image.status === 'ready' ? '就绪' : image.status === 'uploading' ? '上传中' : '不可用'}
                            </span>
                          </div>
                          <div class="flex-1">
                            <h4 class="font-medium text-sm text-gray-900 dark:text-white mb-1 truncate">{image.name}:{image.tag}</h4>
                            {#if image.description}
                              <p class="text-xs text-gray-600 dark:text-gray-400 mb-2 line-clamp-2">{image.description}</p>
                            {/if}
                            <div class="flex flex-col space-y-1 text-xs text-gray-500 dark:text-gray-400">
                              <div class="flex items-center justify-between">
                                <span>服务: {image.service_count || 0}/2</span>
                                <span>ID: {image.id}</span>
                              </div>
                              {#if image.harbor_size}
                                <span>大小: {Math.round(image.harbor_size / 1024 / 1024)}MB</span>
                              {/if}
                            </div>
                          </div>
                        </div>
                      </label>
                    {/each}
                  </div>
                {:else}
                  <div class="text-center py-8 text-gray-500 dark:text-gray-400">
                    <p>暂无可用镜像，请先<a href="#" class="text-blue-600 hover:underline">上传镜像</a></p>
                  </div>
                {/if}
                
                {#if errors.selected_image}
                  <p class="text-sm text-red-600 dark:text-red-400 flex items-center space-x-1">
                    <AlertCircle class="w-4 h-4" />
                    <span>{errors.selected_image}</span>
                  </p>
                {/if}
              </div>
            </div>
            {/if}

            <!-- Basic Information Section -->
            <div class="bg-gray-50 dark:bg-gray-800/50 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
              <div class="flex items-center space-x-2 mb-2">
                <div class="flex items-center justify-center w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg">
                  <Info class="w-4 h-4 text-blue-600 dark:text-blue-400" />
                </div>
                <h4 class="text-lg font-semibold text-gray-900 dark:text-white">基本信息</h4>
              </div>
              
              <!-- Docker Tar Package Upload (仅在docker-upload模式显示) -->
              {#if creationMode === 'docker-upload'}
              <div class="space-y-3">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Docker镜像tar包 <span class="text-red-500">*</span>
                </label>
                
                {#if dockerTarFile}
                  <!-- 已选择文件显示 -->
                  <div class="bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center">
                        <div class="flex-shrink-0 w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mr-3">
                          <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                          </svg>
                        </div>
                        <div>
                          <p class="text-sm font-medium text-gray-900 dark:text-white">{dockerTarFile.name}</p>
                          <p class="text-xs text-gray-500 dark:text-gray-400">{formatFileSize(dockerTarFile.size)}</p>
                        </div>
                      </div>
                      <button
                        type="button"
                        on:click={removeDockerFile}
                        class="text-red-500 hover:text-red-700 text-sm font-medium"
                        disabled={loading}
                      >
                        移除
                      </button>
                    </div>
                  </div>
                {:else}
                  <!-- Docker镜像tar包选择器 with drag-and-drop -->
                  <div 
                    class="border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer {isDragOverDocker ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20' : errors.docker_tar ? 'border-red-500' : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'}"
                    on:click={() => dockerFileInputRef?.click()}
                    on:dragenter={handleDockerDragEnter}
                    on:dragleave={handleDockerDragLeave}
                    on:dragover={handleDockerDragOver}
                    on:drop={handleDockerDrop}
                  >
                    <input
                      type="file"
                      accept=".tar,.tar.gz,.tgz"
                      on:change={handleDockerFileSelect}
                      bind:this={dockerFileInputRef}
                      class="hidden"
                      disabled={loading}
                    />
                    <svg class="mx-auto h-16 w-16 text-gray-400 dark:text-gray-500" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                      <path d="M24 8v24m8-12l-8-8-8 8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                    <div class="mt-4">
                      <button
                        type="button"
                        on:click={() => dockerFileInputRef?.click()}
                        class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium text-base"
                        disabled={loading}
                      >
                        {isDragOverDocker ? '释放文件到此处' : '点击选择或拖拽Docker镜像tar包'}
                      </button>
                      <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">支持 TAR, TAR.GZ, TGZ 格式</p>
                      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">最大文件大小: 20GB</p>
                    </div>
                  </div>
                  {#if errors.docker_tar}
                    <p class="text-sm text-red-600 dark:text-red-400 flex items-center space-x-1">
                      <AlertCircle class="w-4 h-4" />
                      <span>{errors.docker_tar}</span>
                    </p>
                  {/if}
                {/if}
              </div>
              {/if}

              <!-- Description -->
              <div class="md:col-span-3 space-y-2">
                <label for="description" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  服务描述
                </label>
                <textarea
                  id="description"
                  bind:value={formData.description}
                  rows="3"
                  class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white transition-all duration-200 resize-none"
                  placeholder="描述这个服务的功能和用途..."
                  disabled={loading}
                ></textarea>
              </div>

              <!-- Examples File Upload (所有创建模式都显示) -->
              <div class="md:col-span-3 space-y-2">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  示例数据 <span class="text-gray-500">(可选)</span>
                </label>
                
                {#if examplesFile}
                  <!-- 已选择文件显示 -->
                  <div class="bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center">
                        <div class="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mr-3">
                          <svg class="w-4 h-4 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 0v12h8V6H8V4H6z" clip-rule="evenodd"></path>
                          </svg>
                        </div>
                        <div>
                          <p class="text-sm font-medium text-gray-900 dark:text-white">{examplesFile.name}</p>
                          <p class="text-xs text-gray-500 dark:text-gray-400">{formatFileSize(examplesFile.size)}</p>
                        </div>
                      </div>
                      <button
                        type="button"
                        on:click={removeExamplesFile}
                        class="text-red-500 hover:text-red-700 text-sm font-medium"
                        disabled={loading}
                      >
                        移除
                      </button>
                    </div>
                  </div>
                {:else}
                  <!-- 文件选择器 with drag-and-drop -->
                  <div 
                    class="border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer {isDragOverExamples ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'}"
                    on:click={() => fileInputRef?.click()}
                    on:dragenter={handleExamplesDragEnter}
                    on:dragleave={handleExamplesDragLeave}
                    on:dragover={handleExamplesDragOver}
                    on:drop={handleExamplesDrop}
                  >
                    <input
                      type="file"
                      accept=".zip,.tar,.tar.gz,.tgz"
                      on:change={handleFileSelect}
                      bind:this={fileInputRef}
                      class="hidden"
                      disabled={loading}
                    />
                    <svg class="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                      <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                    <div class="mt-4">
                      <button
                        type="button"
                        on:click={() => fileInputRef?.click()}
                        class="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium text-sm"
                        disabled={loading}
                      >
                        {isDragOverExamples ? '释放文件到此处' : '点击选择或拖拽示例数据压缩包'}
                      </button>
                      <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">支持 ZIP, TAR, TAR.GZ 格式，最大10GB</p>
                      <p class="text-xs text-gray-400 dark:text-gray-500 mt-1">可以在服务创建后通过文件更新功能添加</p>
                    </div>
                  </div>
                {/if}
              </div>

            </div>

            <!-- Advanced Configuration Section -->
            <div class="bg-gray-50 dark:bg-gray-800/50 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
              <div class="flex items-center space-x-2 mb-4">
                <div class="flex items-center justify-center w-8 h-8 bg-purple-100 dark:bg-purple-900 rounded-lg">
                  <Settings class="w-4 h-4 text-purple-600 dark:text-purple-400" />
                </div>
                <h4 class="text-lg font-semibold text-gray-900 dark:text-white">资源选项</h4>
              </div>

              <div class="flex gap-6">
                <!-- Resource Configuration -->
                <div class="lg:col-span-2 space-y-2">
                  <label for="resource_config" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    资源配置 <span class="text-red-500">*</span>
                  </label>
                  <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
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
                        <div class="flex flex-col p-2 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:shadow-md {formData.resource_config === key ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'}">
                          <div class="flex items-center justify-between mb-2">
                            <span class="font-medium text-sm py-1 text-gray-900 dark:text-white">{config.label}</span>
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
                  {#if errors.resource_config}
                    <p class="text-sm text-red-600 dark:text-red-400 flex items-center space-x-1">
                      <AlertCircle class="w-4 h-4" />
                      <span>{errors.resource_config}</span>
                    </p>
                  {/if}
                  <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 mt-3">
                    <p class="text-sm text-blue-800 dark:text-blue-200 flex items-center space-x-2">
                      <Info class="w-4 h-4" />
                      <span>当前配置：CPU {formData.cpu_limit} cores，内存 {formData.memory_limit}</span>
                    </p>
                  </div>
                </div>

                <!-- Priority and Public Access -->
                <div>
                  <!-- Priority -->
                  <div class="space-y-2">
                    <label for="priority" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      启动优先级
                    </label>
                    <select
                      id="priority"
                      bind:value={formData.priority}
                      class="w-full px-4 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white transition-all duration-200 {errors.priority ? 'border-red-500 focus:ring-red-500' : ''}"
                      disabled={loading}
                    >
                      {#each priorityOptions as option}
                        <option value={option.value}>
                          {option.label}
                        </option>
                      {/each}
                    </select>
                    {#if errors.priority}
                      <p class="text-sm text-red-600 dark:text-red-400 flex items-center space-x-1">
                        <AlertCircle class="w-4 h-4" />
                        <span>{errors.priority}</span>
                      </p>
                    {/if}
                    <p class="text-xs text-gray-500 dark:text-gray-400">
                      数值越小优先级越高
                    </p>
                  </div>

                  <!-- Public Access -->
                  <div class="bg-gradient-to-r mt-2 from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg py-2 px-4 border border-green-200 dark:border-green-700">
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
            </div>
          </div>

          <!-- Progress Display -->
          {#if loading && progress > 0}
            <div class="px-4 pb-4">
              <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-xl p-4">
                <div class="flex items-center justify-between text-sm text-blue-800 dark:text-blue-200 mb-3">
                  <span class="font-medium">正在{creationMode === 'docker-upload' ? '上传镜像并' : ''}创建服务...</span>
                  <div class="flex items-center space-x-2">
                    <div class="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                    <span>{progress}%</span>
                  </div>
                </div>
                <div class="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2">
                  <div 
                    class="bg-blue-500 dark:bg-blue-400 h-2 rounded-full transition-all duration-300" 
                    style="width: {progress}%"
                  ></div>
                </div>
                <p class="text-xs text-blue-600 dark:text-blue-300 mt-2">
                  {creationMode === 'docker-upload' ? '镜像上传和' : ''}服务创建可能需要几分钟时间，请耐心等待
                </p>
              </div>
            </div>
          {/if}
        </div>

        <!-- Sticky Footer -->
        <div class="sticky bottom-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 px-6 py-4">
          <div class="flex items-center justify-between">
            <div class="text-sm text-gray-500 dark:text-gray-400">
              {#if loading}
                <div class="flex items-center space-x-2">
                  <div class="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                  <span>正在创建服务...</span>
                  {#if progress > 0}
                    <span class="text-blue-600 dark:text-blue-400 font-medium">{progress}%</span>
                  {/if}
                </div>
              {:else}
                确保所有配置正确后点击创建
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
                    <span>创建中...</span>
                  </div>
                {:else}
                  <div class="flex items-center space-x-2">
                    <Zap class="w-4 h-4" />
                    <span>
                      {creationMode === 'docker-upload' ? '上传并创建服务' : '基于镜像创建服务'}
                    </span>
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

  /* Line clamp utility for truncating text */
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>