<script>
  import { createEventDispatcher } from 'svelte';
  import { X, Save, Trash2, AlertCircle, Info, Eye, EyeOff, RefreshCw } from 'lucide-svelte';
  import { api } from '$lib/utils/api';

  export let service;
  export let isOpen = false;
  export let loading = false;

  const dispatch = createEventDispatcher();

  let formData = { ...service };
  let errors = {};
  let showAccessToken = false;
  let regeneratingToken = false;

  // Reset form data when service changes
  $: if (service) {
    formData = { ...service };
    errors = {};
  }

  function handleClose() {
    if (loading) return;
    dispatch('close');
    resetForm();
  }

  function resetForm() {
    formData = { ...service };
    errors = {};
    showAccessToken = false;
  }

  function validateForm() {
    errors = {};

    // Service name validation
    if (!formData.service_name?.trim()) {
      errors.service_name = '服务名称是必填项';
    } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.service_name)) {
      errors.service_name = '服务名称只能包含字母、数字、下划线和连字符';
    }

    // CPU limit validation
    if (!formData.cpu_limit?.trim()) {
      errors.cpu_limit = 'CPU限制是必填项';
    } else {
      const cpuValue = parseFloat(formData.cpu_limit);
      if (isNaN(cpuValue) || cpuValue <= 0 || cpuValue > 4) {
        errors.cpu_limit = 'CPU限制必须是0到4之间的数字';
      }
    }

    // Memory limit validation
    if (!formData.memory_limit?.trim()) {
      errors.memory_limit = '内存限制是必填项';
    } else if (!/^\d+(\.\d+)?(Mi|Gi|KB|MB|GB)$/i.test(formData.memory_limit)) {
      errors.memory_limit = '内存限制格式不正确，例如: 256Mi, 1Gi';
    }

    // Priority validation
    if (typeof formData.priority !== 'number' || formData.priority < 1 || formData.priority > 1000) {
      errors.priority = '优先级必须在1到1000之间';
    }

    return Object.keys(errors).length === 0;
  }

  async function handleSave() {
    if (!validateForm()) {
      return;
    }

    try {
      loading = true;

      // Prepare update data
      const updateData = {
        service_name: formData.service_name,
        description: formData.description,
        cpu_limit: formData.cpu_limit,
        memory_limit: formData.memory_limit,
        is_public: formData.is_public
      };

      await api.updateService(service.id, updateData);
      
      dispatch('updated', formData);
      handleClose();
    } catch (error) {
      console.error('Failed to update service:', error);
      // You might want to show a toast notification here
      alert(`更新服务失败: ${error.message}`);
    } finally {
      loading = false;
    }
  }

  async function handleRegenerateToken() {
    try {
      regeneratingToken = true;
      
      const response = await api.generateAccessToken(service.id, {
        regenerate_token: true
      });
      
      formData.access_token = response.access_token;
      
      dispatch('tokenRegenerated', response.access_token);
    } catch (error) {
      console.error('Failed to regenerate access token:', error);
      alert(`重新生成访问令牌失败: ${error.message}`);
    } finally {
      regeneratingToken = false;
    }
  }

  function copyAccessToken() {
    if (formData.access_token) {
      navigator.clipboard.writeText(formData.access_token).then(() => {
        // Show success feedback
        alert('访问令牌已复制到剪贴板');
      });
    }
  }

  function handleDelete() {
    dispatch('delete', service);
    handleClose();
  }

  function handleKeydown(event) {
    if (event.key === 'Escape' && !loading) {
      handleClose();
    }
  }

  // CPU and Memory presets
  const cpuPresets = [
    { value: '0.1', label: '0.1 cores' },
    { value: '0.2', label: '0.2 cores' },
    { value: '0.5', label: '0.5 cores' },
    { value: '1.0', label: '1.0 cores' }
  ];

  const memoryPresets = [
    { value: '128Mi', label: '128Mi' },
    { value: '256Mi', label: '256Mi' },
    { value: '512Mi', label: '512Mi' },
    { value: '1Gi', label: '1Gi' }
  ];
</script>

<svelte:window on:keydown={handleKeydown} />

{#if isOpen}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
          服务设置 - {service.service_name}
        </h3>
        <button
          class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          on:click={handleClose}
          disabled={loading}
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Form -->
      <form on:submit|preventDefault={handleSave}>
        <div class="p-6 space-y-6">
          <!-- Basic Settings -->
          <div>
            <h4 class="text-md font-medium text-gray-900 dark:text-white mb-4">基本设置</h4>
            
            <div class="space-y-4">
              <!-- Service Name -->
              <div>
                <label for="service_name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  服务名称 *
                </label>
                <input
                  type="text"
                  id="service_name"
                  bind:value={formData.service_name}
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white {errors.service_name ? 'border-red-500' : ''}"
                  disabled={loading}
                  required
                />
                {#if errors.service_name}
                  <p class="mt-1 text-sm text-red-600 dark:text-red-400 flex items-center space-x-1">
                    <AlertCircle class="w-4 h-4" />
                    <span>{errors.service_name}</span>
                  </p>
                {/if}
              </div>

              <!-- Description -->
              <div>
                <label for="description" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  服务描述
                </label>
                <textarea
                  id="description"
                  bind:value={formData.description}
                  rows="3"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  disabled={loading}
                ></textarea>
              </div>

              <!-- Public Access -->
              <div class="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="is_public"
                  bind:checked={formData.is_public}
                  class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  disabled={loading}
                />
                <label for="is_public" class="text-sm text-gray-700 dark:text-gray-300">
                  公开访问（允许任何人使用此服务）
                </label>
              </div>
            </div>
          </div>

          <!-- Resource Configuration -->
          <div>
            <h4 class="text-md font-medium text-gray-900 dark:text-white mb-4">资源配置</h4>
            
            <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4">
              <div class="flex items-start space-x-2">
                <Info class="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
                <div class="text-sm text-blue-800 dark:text-blue-200">
                  <p class="font-medium mb-1">注意</p>
                  <p>修改资源配置需要重启服务才能生效。建议在服务停止时进行修改。</p>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <!-- CPU Limit -->
              <div>
                <label for="cpu_limit" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  CPU限制 *
                </label>
                <div class="space-y-2">
                  <input
                    type="text"
                    id="cpu_limit"
                    bind:value={formData.cpu_limit}
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white {errors.cpu_limit ? 'border-red-500' : ''}"
                    disabled={loading}
                    required
                  />
                  <div class="flex flex-wrap gap-1">
                    {#each cpuPresets as preset}
                      <button
                        type="button"
                        class="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded transition-colors"
                        on:click={() => formData.cpu_limit = preset.value}
                        disabled={loading}
                      >
                        {preset.label}
                      </button>
                    {/each}
                  </div>
                </div>
                {#if errors.cpu_limit}
                  <p class="mt-1 text-sm text-red-600 dark:text-red-400 flex items-center space-x-1">
                    <AlertCircle class="w-4 h-4" />
                    <span>{errors.cpu_limit}</span>
                  </p>
                {/if}
              </div>

              <!-- Memory Limit -->
              <div>
                <label for="memory_limit" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  内存限制 *
                </label>
                <div class="space-y-2">
                  <input
                    type="text"
                    id="memory_limit"
                    bind:value={formData.memory_limit}
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white {errors.memory_limit ? 'border-red-500' : ''}"
                    disabled={loading}
                    required
                  />
                  <div class="flex flex-wrap gap-1">
                    {#each memoryPresets as preset}
                      <button
                        type="button"
                        class="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded transition-colors"
                        on:click={() => formData.memory_limit = preset.value}
                        disabled={loading}
                      >
                        {preset.label}
                      </button>
                    {/each}
                  </div>
                </div>
                {#if errors.memory_limit}
                  <p class="mt-1 text-sm text-red-600 dark:text-red-400 flex items-center space-x-1">
                    <AlertCircle class="w-4 h-4" />
                    <span>{errors.memory_limit}</span>
                  </p>
                {/if}
              </div>
            </div>
          </div>

          <!-- Access Token -->
          <div>
            <h4 class="text-md font-medium text-gray-900 dark:text-white mb-4">访问令牌</h4>
            
            <div class="space-y-4">
              <div>
                <label for="access_token" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  当前访问令牌
                </label>
                <div class="flex space-x-2">
                  <div class="flex-1 relative">
                    <input
                      type={showAccessToken ? 'text' : 'password'}
                      id="access_token"
                      value={formData.access_token || ''}
                      class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                      readonly
                    />
                    <button
                      type="button"
                      class="absolute inset-y-0 right-0 pr-3 flex items-center"
                      on:click={() => showAccessToken = !showAccessToken}
                    >
                      <svelte:component 
                        this={showAccessToken ? EyeOff : Eye} 
                        class="w-4 h-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                      />
                    </button>
                  </div>
                  
                  <button
                    type="button"
                    class="px-3 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-md transition-colors"
                    on:click={copyAccessToken}
                    disabled={!formData.access_token}
                  >
                    复制
                  </button>
                  
                  <button
                    type="button"
                    class="px-3 py-2 bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:hover:bg-blue-800 text-blue-700 dark:text-blue-300 text-sm font-medium rounded-md transition-colors flex items-center space-x-1"
                    on:click={handleRegenerateToken}
                    disabled={regeneratingToken}
                  >
                    <RefreshCw class="w-4 h-4 {regeneratingToken ? 'animate-spin' : ''}" />
                    <span>{regeneratingToken ? '生成中...' : '重新生成'}</span>
                  </button>
                </div>
                <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  访问令牌用于API调用和服务访问认证
                </p>
              </div>
            </div>
          </div>

          <!-- Service Information (Read-only) -->
          <div>
            <h4 class="text-md font-medium text-gray-900 dark:text-white mb-4">服务信息</h4>
            
            <div class="grid grid-cols-2 gap-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div>
                <label class="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  模型ID
                </label>
                <p class="text-sm text-gray-900 dark:text-white">{service.model_id}</p>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  模型服务器IP
                </label>
                <p class="text-sm text-gray-900 dark:text-white">{service.model_ip}</p>
              </div>
              
              {#if service.gradio_port}
                <div>
                  <label class="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                    分配端口
                  </label>
                  <p class="text-sm text-gray-900 dark:text-white">{service.gradio_port}</p>
                </div>
              {/if}
              
              <div>
                <label class="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                  启动优先级
                </label>
                <p class="text-sm text-gray-900 dark:text-white">{service.priority}</p>
              </div>
            </div>
          </div>

          <!-- Danger Zone -->
          <div class="border-t border-gray-200 dark:border-gray-700 pt-6">
            <h4 class="text-md font-medium text-red-600 dark:text-red-400 mb-4">危险操作</h4>
            
            <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div class="flex justify-between items-center">
                <div>
                  <h5 class="text-sm font-medium text-red-800 dark:text-red-200">删除服务</h5>
                  <p class="mt-1 text-sm text-red-700 dark:text-red-300">
                    一旦删除，服务的所有数据和配置将永久丢失，无法恢复
                  </p>
                </div>
                <button
                  type="button"
                  class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-md transition-colors flex items-center space-x-1"
                  on:click={handleDelete}
                  disabled={loading}
                >
                  <Trash2 class="w-4 h-4" />
                  <span>删除服务</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex justify-end space-x-3 p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-600 hover:bg-gray-200 dark:hover:bg-gray-500 rounded-md transition-colors"
            on:click={handleClose}
            disabled={loading}
          >
            取消
          </button>
          <button
            type="submit"
            class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-md transition-colors flex items-center space-x-1"
            disabled={loading}
          >
            <Save class="w-4 h-4" />
            <span>{loading ? '保存中...' : '保存更改'}</span>
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}