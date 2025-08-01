<script>
  import { createEventDispatcher } from 'svelte';
  import { Play, Square, RotateCcw, ExternalLink, Activity, Settings, Trash2, Eye, Clock, Cpu, HardDrive } from 'lucide-svelte';
  import { formatDistanceToNow } from 'date-fns';
  import { zhCN } from 'date-fns/locale';

  export let service;
  export let isOwner = false;
  export let loading = false;

  const dispatch = createEventDispatcher();

  // 获取服务状态颜色样式
  function getServiceStatusColor(status) {
    switch (status) {
      case 'running':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'starting':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'stopping':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      case 'stopped':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'idle':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'retry_pending':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      case 'permanently_failed':
        return 'bg-red-200 text-red-900 dark:bg-red-800 dark:text-red-100';
      case 'retry_exhausted':
        return 'bg-orange-200 text-orange-900 dark:bg-orange-800 dark:text-orange-100';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  }

  // 获取服务状态显示文本
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
        return '未知';
    }
  }

  function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  function handleStart() {
    dispatch('start', service);
  }

  function handleStop() {
    dispatch('stop', service);
  }

  function handleRestart() {
    dispatch('restart', service);
  }

  function handleDelete() {
    dispatch('delete', service);
  }

  function handleViewLogs() {
    dispatch('viewLogs', service);
  }

  function handleSettings() {
    dispatch('settings', service);
  }

  function handleDemo() {
    if (service.service_url) {
      window.open(service.service_url, '_blank');
    }
  }

  function handleMonitor() {
    dispatch('monitor', service);
  }

  $: canStart = service.status === 'stopped' || service.status === 'created' || service.status === 'error';
  $: canStop = service.status === 'running' || service.status === 'starting';
  $: canRestart = service.status === 'running';
  $: canAccessDemo = service.status === 'running' && service.service_url;
</script>

<div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-md transition-shadow">
  <!-- Header -->
  <div class="flex items-start justify-between mb-4">
    <div class="flex-1 min-w-0">
      <div class="flex items-center space-x-3 mb-2">
        <div class="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
          <Activity class="w-5 h-5 text-blue-600 dark:text-blue-400" />
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white truncate">
            {service.service_name}
          </h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 truncate">
            Model: {service.model_id}
          </p>
        </div>
      </div>
      
      {#if service.description}
        <p class="text-sm text-gray-600 dark:text-gray-300 mb-3">
          {service.description}
        </p>
      {/if}
    </div>
    
    <!-- Status Badge -->
    <div class="flex items-center space-x-2">
      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getServiceStatusColor(service.status)}">
        {getServiceStatusText(service.status)}
      </span>
      {#if service.is_public}
        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
          公开
        </span>
      {/if}
    </div>
  </div>

  <!-- Service Info -->
  <div class="grid grid-cols-2 gap-4 mb-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
    <div class="flex items-center space-x-2">
      <Cpu class="w-4 h-4 text-gray-400" />
      <span class="text-sm text-gray-600 dark:text-gray-300">
        CPU: {service.cpu_limit}
      </span>
    </div>
    
    <div class="flex items-center space-x-2">
      <HardDrive class="w-4 h-4 text-gray-400" />
      <span class="text-sm text-gray-600 dark:text-gray-300">
        内存: {service.memory_limit}
      </span>
    </div>
    
    {#if service.gradio_port}
      <div class="flex items-center space-x-2">
        <span class="text-sm text-gray-600 dark:text-gray-300">
          端口: {service.gradio_port}
        </span>
      </div>
    {/if}
    
    {#if service.model_ip}
      <div class="flex items-center space-x-2">
        <span class="text-sm text-gray-600 dark:text-gray-300">
          IP: {service.model_ip}
        </span>
      </div>
    {/if}
  </div>

  <!-- Statistics -->
  {#if service.access_count || service.start_count || service.total_runtime_minutes}
    <div class="grid grid-cols-3 gap-4 mb-4 text-center">
      {#if service.access_count}
        <div>
          <div class="text-lg font-semibold text-gray-900 dark:text-white">
            {service.access_count}
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">访问次数</div>
        </div>
      {/if}
      
      {#if service.start_count}
        <div>
          <div class="text-lg font-semibold text-gray-900 dark:text-white">
            {service.start_count}
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">启动次数</div>
        </div>
      {/if}
      
      {#if service.total_runtime_minutes}
        <div>
          <div class="text-lg font-semibold text-gray-900 dark:text-white">
            {Math.round(service.total_runtime_minutes / 60)}h
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">运行时长</div>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Retry Information -->
  {#if service.auto_start_retry_count > 0 || service.last_failure_reason}
    <div class="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
      {#if service.auto_start_retry_count > 0}
        <div class="text-sm text-yellow-800 dark:text-yellow-200 mb-1">
          重试次数: {service.auto_start_retry_count}
        </div>
      {/if}
      {#if service.last_failure_reason}
        <div class="text-xs text-yellow-700 dark:text-yellow-300">
          最后失败原因: {service.last_failure_reason}
        </div>
      {/if}
    </div>
  {/if}

  <!-- Timestamps -->
  <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-4">
    <div class="flex items-center space-x-1">
      <Clock class="w-3 h-3" />
      <span>
        创建于 {formatDistanceToNow(new Date(service.created_at), { addSuffix: true, locale: zhCN })}
      </span>
    </div>
    
    {#if service.last_accessed_at}
      <div class="flex items-center space-x-1">
        <Eye class="w-3 h-3" />
        <span>
          最后访问 {formatDistanceToNow(new Date(service.last_accessed_at), { addSuffix: true, locale: zhCN })}
        </span>
      </div>
    {/if}
  </div>

  <!-- Actions -->
  <div class="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-600">
    <div class="flex items-center space-x-2">
      <!-- Demo Button -->
      {#if canAccessDemo}
        <button
          class="px-3 py-1.5 bg-green-100 hover:bg-green-200 dark:bg-green-900 dark:hover:bg-green-800 text-green-700 dark:text-green-300 text-sm font-medium rounded transition-colors flex items-center space-x-1"
          on:click={handleDemo}
          disabled={loading}
        >
          <ExternalLink class="w-4 h-4" />
          <span>试用</span>
        </button>
      {/if}

      <!-- Monitor Button -->
      <button
        class="px-3 py-1.5 bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:hover:bg-blue-800 text-blue-700 dark:text-blue-300 text-sm font-medium rounded transition-colors flex items-center space-x-1"
        on:click={handleMonitor}
        disabled={loading}
      >
        <Activity class="w-4 h-4" />
        <span>监控</span>
      </button>

      <!-- View Logs Button -->
      <button
        class="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium rounded transition-colors"
        on:click={handleViewLogs}
        disabled={loading}
      >
        日志
      </button>
    </div>

    {#if isOwner}
      <div class="flex items-center space-x-2">
        <!-- Control Buttons -->
        {#if canStart}
          <button
            class="px-3 py-1.5 bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:hover:bg-blue-800 text-blue-700 dark:text-blue-300 text-sm font-medium rounded transition-colors flex items-center space-x-1"
            on:click={handleStart}
            disabled={loading}
          >
            <Play class="w-4 h-4" />
            <span>启动</span>
          </button>
        {/if}

        {#if canStop}
          <button
            class="px-3 py-1.5 bg-orange-100 hover:bg-orange-200 dark:bg-orange-900 dark:hover:bg-orange-800 text-orange-700 dark:text-orange-300 text-sm font-medium rounded transition-colors flex items-center space-x-1"
            on:click={handleStop}
            disabled={loading}
          >
            <Square class="w-4 h-4" />
            <span>停止</span>
          </button>
        {/if}

        {#if canRestart}
          <button
            class="px-3 py-1.5 bg-yellow-100 hover:bg-yellow-200 dark:bg-yellow-900 dark:hover:bg-yellow-800 text-yellow-700 dark:text-yellow-300 text-sm font-medium rounded transition-colors flex items-center space-x-1"
            on:click={handleRestart}
            disabled={loading}
          >
            <RotateCcw class="w-4 h-4" />
            <span>重启</span>
          </button>
        {/if}

        <!-- Settings and Delete -->
        <button
          class="px-2 py-1.5 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium rounded transition-colors"
          on:click={handleSettings}
          disabled={loading}
        >
          <Settings class="w-4 h-4" />
        </button>

        <button
          class="px-2 py-1.5 bg-red-100 hover:bg-red-200 dark:bg-red-900 dark:hover:bg-red-800 text-red-700 dark:text-red-300 text-sm font-medium rounded transition-colors"
          on:click={handleDelete}
          disabled={loading}
        >
          <Trash2 class="w-4 h-4" />
        </button>
      </div>
    {/if}
  </div>
</div>