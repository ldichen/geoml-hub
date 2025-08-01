<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { Download, Filter, RefreshCw, Search, Calendar, AlertTriangle, Info, CheckCircle, XCircle } from 'lucide-svelte';
  import { formatDistanceToNow } from 'date-fns';
  import { zhCN } from 'date-fns/locale';
  import { api } from '$lib/utils/api';
  import Loading from '../Loading.svelte';

  export let service;
  export let autoRefresh = false;
  export let maxHeight = '500px';

  const dispatch = createEventDispatcher();

  let logs = [];
  let loading = true;
  let error = null;
  let currentPage = 1;
  let pageSize = 50;
  let totalLogs = 0;
  let hasMore = false;

  // Filters
  let levelFilter = '';
  let eventTypeFilter = '';
  let searchQuery = '';
  let showFilterMenu = false;

  // Auto refresh
  let refreshTimer = null;
  let refreshInterval = 10000; // 10 seconds

  onMount(() => {
    loadLogs();
    if (autoRefresh) {
      startAutoRefresh();
    }
  });

  function startAutoRefresh() {
    if (refreshTimer) {
      clearInterval(refreshTimer);
    }
    refreshTimer = setInterval(() => {
      loadLogs(1, true);
    }, refreshInterval);
  }

  function stopAutoRefresh() {
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
  }

  async function loadLogs(page = 1, append = false) {
    try {
      loading = true;
      error = null;

      const params = {
        page,
        size: pageSize
      };

      if (levelFilter) params.level = levelFilter;
      if (eventTypeFilter) params.event_type = eventTypeFilter;
      if (searchQuery) params.search = searchQuery;

      const response = await api.repositories.getServiceLogs(service.id, params);
      
      if (append && page > 1) {
        logs = [...logs, ...response.logs];
      } else {
        logs = response.logs;
      }
      
      totalLogs = response.total;
      currentPage = page;
      hasMore = logs.length < totalLogs;

    } catch (err) {
      error = err.message;
      console.error('Failed to load service logs:', err);
    } finally {
      loading = false;
    }
  }

  function handleRefresh() {
    loadLogs(1);
  }

  function handleLoadMore() {
    if (!loading && hasMore) {
      loadLogs(currentPage + 1, true);
    }
  }

  function handleSearch() {
    currentPage = 1;
    loadLogs(1);
  }

  function handleFilterChange() {
    currentPage = 1;
    loadLogs(1);
    showFilterMenu = false;
  }

  function clearFilters() {
    levelFilter = '';
    eventTypeFilter = '';
    searchQuery = '';
    showFilterMenu = false;
    handleFilterChange();
  }

  function toggleAutoRefresh() {
    autoRefresh = !autoRefresh;
    if (autoRefresh) {
      startAutoRefresh();
    } else {
      stopAutoRefresh();
    }
  }

  function exportLogs() {
    // Create CSV content
    const headers = ['时间', '级别', '事件类型', '消息', '用户', 'IP地址'];
    const csvContent = [
      headers.join(','),
      ...logs.map(log => [
        new Date(log.created_at).toLocaleString(),
        log.log_level,
        log.event_type || '',
        `"${log.message.replace(/"/g, '""')}"`,
        log.user_id || '',
        log.ip_address || ''
      ].join(','))
    ].join('\n');

    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `service-${service.service_name}-logs.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function getLogLevelIcon(level) {
    switch (level) {
      case 'info':
        return Info;
      case 'warning':
        return AlertTriangle;
      case 'error':
        return XCircle;
      case 'debug':
        return CheckCircle;
      default:
        return Info;
    }
  }

  function getLogLevelColor(level) {
    switch (level) {
      case 'info':
        return 'text-blue-600 dark:text-blue-400';
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'error':
        return 'text-red-600 dark:text-red-400';
      case 'debug':
        return 'text-gray-600 dark:text-gray-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  }

  function getLogLevelBg(level) {
    switch (level) {
      case 'info':
        return 'bg-blue-50 dark:bg-blue-900/20';
      case 'warning':
        return 'bg-yellow-50 dark:bg-yellow-900/20';
      case 'error':
        return 'bg-red-50 dark:bg-red-900/20';
      case 'debug':
        return 'bg-gray-50 dark:bg-gray-800';
      default:
        return 'bg-gray-50 dark:bg-gray-800';
    }
  }

  function formatLogLevel(level) {
    switch (level) {
      case 'info':
        return '信息';
      case 'warning':
        return '警告';
      case 'error':
        return '错误';
      case 'debug':
        return '调试';
      default:
        return level;
    }
  }

  function formatEventType(eventType) {
    switch (eventType) {
      case 'create':
        return '创建';
      case 'start':
        return '启动';
      case 'stop':
        return '停止';
      case 'access':
        return '访问';
      case 'error':
        return '错误';
      case 'health_check':
        return '健康检查';
      default:
        return eventType || '-';
    }
  }

  // Get unique values for filters
  $: uniqueLevels = [...new Set(logs.map(log => log.log_level))];
  $: uniqueEventTypes = [...new Set(logs.map(log => log.event_type).filter(Boolean))];
</script>

<div class="space-y-4">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
        服务日志 - {service.service_name}
      </h3>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        共 {totalLogs} 条日志记录
      </p>
    </div>
    
    <div class="flex items-center space-x-3">
      <!-- Auto Refresh Toggle -->
      <label class="flex items-center space-x-2 cursor-pointer">
        <input
          type="checkbox"
          bind:checked={autoRefresh}
          on:change={toggleAutoRefresh}
          class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <span class="text-sm text-gray-700 dark:text-gray-300">自动刷新</span>
      </label>

      <!-- Export Logs -->
      <button
        class="px-3 py-2 bg-green-100 hover:bg-green-200 dark:bg-green-900 dark:hover:bg-green-800 text-green-700 dark:text-green-300 text-sm font-medium rounded-lg transition-colors flex items-center space-x-1"
        on:click={exportLogs}
        disabled={loading || logs.length === 0}
      >
        <Download class="w-4 h-4" />
        <span>导出</span>
      </button>

      <!-- Refresh -->
      <button
        class="px-3 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-lg transition-colors flex items-center space-x-1"
        on:click={handleRefresh}
        disabled={loading}
      >
        <RefreshCw class="w-4 h-4 {loading ? 'animate-spin' : ''}" />
        <span>刷新</span>
      </button>
    </div>
  </div>

  <!-- Filters -->
  <div class="flex items-center space-x-4">
    <!-- Search -->
    <div class="flex-1 relative">
      <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <Search class="h-4 w-4 text-gray-400" />
      </div>
      <input
        type="text"
        bind:value={searchQuery}
        on:keydown={(e) => e.key === 'Enter' && handleSearch()}
        placeholder="搜索日志消息..."
        class="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg leading-5 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      />
    </div>

    <!-- Filters Dropdown -->
    <div class="relative">
      <button
        class="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        on:click={() => showFilterMenu = !showFilterMenu}
      >
        <Filter class="w-4 h-4" />
        <span>筛选</span>
        {#if levelFilter || eventTypeFilter}
          <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
            {(levelFilter ? 1 : 0) + (eventTypeFilter ? 1 : 0)}
          </span>
        {/if}
      </button>
      
      {#if showFilterMenu}
        <div class="absolute right-0 top-full mt-1 w-64 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg z-10">
          <div class="p-4 space-y-4">
            <!-- Log Level Filter -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                日志级别
              </label>
              <select
                bind:value={levelFilter}
                on:change={handleFilterChange}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="">全部</option>
                {#each uniqueLevels as level}
                  <option value={level}>{formatLogLevel(level)}</option>
                {/each}
              </select>
            </div>

            <!-- Event Type Filter -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                事件类型
              </label>
              <select
                bind:value={eventTypeFilter}
                on:change={handleFilterChange}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="">全部</option>
                {#each uniqueEventTypes as eventType}
                  <option value={eventType}>{formatEventType(eventType)}</option>
                {/each}
              </select>
            </div>

            <!-- Clear Filters -->
            <button
              class="w-full px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              on:click={clearFilters}
            >
              清除筛选
            </button>
          </div>
        </div>
      {/if}
    </div>
  </div>

  <!-- Logs Container -->
  <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
    {#if loading && logs.length === 0}
      <div class="flex items-center justify-center py-12">
        <Loading size="lg" />
      </div>
    {:else if error}
      <div class="p-6">
        <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div class="flex items-center space-x-2">
            <AlertTriangle class="w-5 h-5 text-red-600 dark:text-red-400" />
            <h4 class="text-sm font-medium text-red-800 dark:text-red-200">加载日志失败</h4>
          </div>
          <p class="mt-2 text-sm text-red-700 dark:text-red-300">{error}</p>
          <button
            class="mt-3 px-3 py-1.5 bg-red-100 hover:bg-red-200 dark:bg-red-800 dark:hover:bg-red-700 text-red-700 dark:text-red-300 text-sm rounded transition-colors"
            on:click={handleRefresh}
          >
            重试
          </button>
        </div>
      </div>
    {:else if logs.length === 0}
      <div class="text-center py-12">
        <div class="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center mx-auto mb-4">
          <Calendar class="w-8 h-8 text-gray-400" />
        </div>
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
          没有找到日志记录
        </h3>
        <p class="text-gray-500 dark:text-gray-400">
          {levelFilter || eventTypeFilter || searchQuery ? '尝试调整筛选条件' : '此服务还没有生成任何日志'}
        </p>
      </div>
    {:else}
      <!-- Logs List -->
      <div class="divide-y divide-gray-200 dark:divide-gray-700" style="max-height: {maxHeight}; overflow-y: auto;">
        {#each logs as log (log.id)}
          <div class="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            <div class="flex items-start space-x-3">
              <!-- Log Level Icon -->
              <div class="flex-shrink-0 mt-0.5">
                <svelte:component 
                  this={getLogLevelIcon(log.log_level)} 
                  class="w-5 h-5 {getLogLevelColor(log.log_level)}"
                />
              </div>
              
              <!-- Log Content -->
              <div class="flex-1 min-w-0">
                <!-- Header -->
                <div class="flex items-center space-x-3 mb-1">
                  <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium {getLogLevelBg(log.log_level)} {getLogLevelColor(log.log_level)}">
                    {formatLogLevel(log.log_level)}
                  </span>
                  
                  {#if log.event_type}
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                      {formatEventType(log.event_type)}
                    </span>
                  {/if}
                  
                  <span class="text-xs text-gray-500 dark:text-gray-400">
                    {formatDistanceToNow(new Date(log.created_at), { addSuffix: true, locale: zhCN })}
                  </span>
                </div>
                
                <!-- Message -->
                <p class="text-sm text-gray-900 dark:text-white break-words">
                  {log.message}
                </p>
                
                <!-- Metadata -->
                {#if log.user_id || log.ip_address}
                  <div class="flex items-center space-x-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                    {#if log.user_id}
                      <span>用户: {log.user_id}</span>
                    {/if}
                    {#if log.ip_address}
                      <span>IP: {log.ip_address}</span>
                    {/if}
                  </div>
                {/if}
              </div>
              
              <!-- Timestamp -->
              <div class="flex-shrink-0 text-xs text-gray-500 dark:text-gray-400">
                {new Date(log.created_at).toLocaleString()}
              </div>
            </div>
          </div>
        {/each}
      </div>

      <!-- Load More -->
      {#if hasMore}
        <div class="p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            class="w-full px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
            on:click={handleLoadMore}
            disabled={loading}
          >
            {loading ? '加载中...' : '加载更多'}
          </button>
        </div>
      {/if}
    {/if}
  </div>
</div>

<!-- Click outside to close filter menu -->
{#if showFilterMenu}
  <div
    class="fixed inset-0 z-0"
    on:click={() => showFilterMenu = false}
  ></div>
{/if}