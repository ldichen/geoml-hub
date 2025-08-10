<script>
  import { createEventDispatcher } from 'svelte';
  import { Plus, MoreHorizontal, Play, Square, Trash2 } from 'lucide-svelte';
  import ServiceCard from './ServiceCard.svelte';
  import Loading from '../Loading.svelte';

  export let services = [];
  export let loading = false;
  export let isOwner = false;
  export let showCreateButton = true;
  export let showBatchActions = true;

  const dispatch = createEventDispatcher();

  let selectedServices = new Set();

  // Use all services since we removed filtering
  $: filteredServices = services;

  // Check if all services are selected
  $: allSelected = filteredServices.length > 0 && selectedServices.size === filteredServices.length;
  
  // Check if some services are selected
  $: someSelected = selectedServices.size > 0 && selectedServices.size < filteredServices.length;

  function handleCreateService() {
    dispatch('createService');
  }

  function handleServiceAction(event, action) {
    dispatch(action, event.detail);
  }

  function toggleServiceSelection(serviceId) {
    if (selectedServices.has(serviceId)) {
      selectedServices.delete(serviceId);
    } else {
      selectedServices.add(serviceId);
    }
    selectedServices = selectedServices;
  }

  function toggleAllSelection() {
    if (allSelected) {
      selectedServices.clear();
    } else {
      selectedServices = new Set(filteredServices.map(s => s.id));
    }
    selectedServices = selectedServices;
  }

  function handleBatchStart() {
    const serviceIds = Array.from(selectedServices);
    dispatch('batchStart', serviceIds);
    selectedServices.clear();
    selectedServices = selectedServices;
  }

  function handleBatchStop() {
    const serviceIds = Array.from(selectedServices);
    dispatch('batchStop', serviceIds);
    selectedServices.clear();
    selectedServices = selectedServices;
  }

  function handleBatchDelete() {
    const serviceIds = Array.from(selectedServices);
    dispatch('batchDelete', serviceIds);
    selectedServices.clear();
    selectedServices = selectedServices;
  }

  // Get service status display text
  function getServiceStatusText(status) {
    switch (status) {
      case 'running':
        return '运行中';
      case 'starting':
        return '启动中';
      case 'stopping':
        return '停止中';
      case 'stopped':
        return '已停止';
      case 'error':
        return '错误';
      case 'idle':
        return '空闲';
      case 'created':
        return '已创建';
      case 'retry_pending':
        return '等待重试';
      case 'permanently_failed':
        return '永久失败';
      case 'retry_exhausted':
        return '重试次数耗尽';
      default:
        return status;
    }
  }
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div class="flex items-center space-x-4">
      <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
        Model Services ({services.length})
      </h2>
      
    </div>

    <div class="flex items-center space-x-3">
      <!-- Batch Actions -->
      {#if showBatchActions && isOwner && selectedServices.size > 0}
        <div class="flex items-center space-x-2">
          <button
            class="px-3 py-2 bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:hover:bg-blue-800 text-blue-700 dark:text-blue-300 text-sm font-medium rounded-lg transition-colors flex items-center space-x-1"
            on:click={handleBatchStart}
            disabled={loading}
          >
            <Play class="w-4 h-4" />
            <span>批量启动 ({selectedServices.size})</span>
          </button>
          
          <button
            class="px-3 py-2 bg-orange-100 hover:bg-orange-200 dark:bg-orange-900 dark:hover:bg-orange-800 text-orange-700 dark:text-orange-300 text-sm font-medium rounded-lg transition-colors flex items-center space-x-1"
            on:click={handleBatchStop}
            disabled={loading}
          >
            <Square class="w-4 h-4" />
            <span>批量停止</span>
          </button>
          
          <button
            class="px-3 py-2 bg-red-100 hover:bg-red-200 dark:bg-red-900 dark:hover:bg-red-800 text-red-700 dark:text-red-300 text-sm font-medium rounded-lg transition-colors flex items-center space-x-1"
            on:click={handleBatchDelete}
            disabled={loading}
          >
            <Trash2 class="w-4 h-4" />
            <span>批量删除</span>
          </button>
        </div>
      {/if}

      <!-- Create Service Button -->
      {#if showCreateButton && isOwner}
        <button
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center space-x-2"
          on:click={handleCreateService}
          disabled={loading}
        >
          <Plus class="w-4 h-4" />
          <span>创建服务</span>
        </button>
      {/if}
    </div>
  </div>

  <!-- Bulk Selection -->
  {#if showBatchActions && isOwner && filteredServices.length > 0}
    <div class="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
      <label class="flex items-center space-x-2 cursor-pointer">
        <input
          type="checkbox"
          checked={allSelected}
          indeterminate={someSelected}
          on:change={toggleAllSelection}
          class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <span class="text-sm text-gray-700 dark:text-gray-300">
          {#if allSelected}
            已选择全部 {filteredServices.length} 个服务
          {:else if someSelected}
            已选择 {selectedServices.size} 个服务
          {:else}
            选择全部
          {/if}
        </span>
      </label>
    </div>
  {/if}

  <!-- Loading State -->
  {#if loading}
    <div class="flex items-center justify-center py-12">
      <Loading size="lg" />
    </div>
  {:else if filteredServices.length === 0}
    <!-- Empty State -->
    <div class="text-center py-12">
      <div class="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center mx-auto mb-4">
        <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path>
        </svg>
      </div>
      
      {#if services.length === 0}
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
          还没有模型服务
        </h3>
        <p class="text-gray-500 dark:text-gray-400 mb-4">
          创建您的第一个模型服务来部署和分享您的模型
        </p>
      {/if}
    </div>
  {:else}
    <!-- Services Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
      {#each filteredServices as service (service.id)}
        <div class="relative">
          {#if showBatchActions && isOwner}
            <div class="absolute top-4 left-4 z-10">
              <input
                type="checkbox"
                checked={selectedServices.has(service.id)}
                on:change={() => toggleServiceSelection(service.id)}
                class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
            </div>
          {/if}
          
          <ServiceCard
            {service}
            {isOwner}
            {loading}
            on:start={(e) => handleServiceAction(e, 'start')}
            on:stop={(e) => handleServiceAction(e, 'stop')}
            on:restart={(e) => handleServiceAction(e, 'restart')}
            on:delete={(e) => handleServiceAction(e, 'delete')}
            on:viewLogs={(e) => handleServiceAction(e, 'viewLogs')}
            on:settings={(e) => handleServiceAction(e, 'settings')}
            on:monitor={(e) => handleServiceAction(e, 'monitor')}
          />
        </div>
      {/each}
    </div>
  {/if}
</div>

