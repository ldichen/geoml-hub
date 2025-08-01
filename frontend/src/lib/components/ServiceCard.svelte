<script>
  import { _ } from 'svelte-i18n';
  import { ExternalLink, Activity, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-svelte';
  
  export let service;
  
  function getHealthStatusIcon(status) {
    switch (status) {
      case 'healthy':
        return CheckCircle;
      case 'unhealthy':
        return XCircle;
      default:
        return AlertCircle;
    }
  }
  
  function getHealthStatusColor(status) {
    switch (status) {
      case 'healthy':
        return 'text-success-600 dark:text-success-400';
      case 'unhealthy':
        return 'text-error-600 dark:text-error-400';
      default:
        return 'text-warning-600 dark:text-warning-400';
    }
  }
  
  function getHealthStatusText(status) {
    switch (status) {
      case 'healthy':
        return $_('service.healthy');
      case 'unhealthy':
        return $_('service.unhealthy');
      default:
        return $_('service.unknown');
    }
  }
  
  function formatResponseTime(ms) {
    if (!ms) return '-';
    return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`;
  }
  
  function formatSuccessRate(rate) {
    if (!rate) return '-';
    return `${rate.toFixed(1)}%`;
  }
  
  function visitService() {
    if (service.service_page_url) {
      window.open(service.service_page_url, '_blank');
    }
  }
</script>

<div class="card p-6">
  <!-- Header -->
  <div class="flex items-start justify-between mb-4">
    <div class="flex-1">
      <h3 class="text-lg font-semibold text-secondary-900 dark:text-dark-700 mb-1">
        {service.service_name}
      </h3>
      {#if service.service_description}
        <p class="text-sm text-secondary-600 dark:text-dark-500">
          {service.service_description}
        </p>
      {/if}
    </div>
    
    <!-- Health Status -->
    <div class="flex items-center space-x-2">
      <svelte:component 
        this={getHealthStatusIcon(service.health_status)} 
        class="w-4 h-4 {getHealthStatusColor(service.health_status)}"
      />
      <span class="text-sm {getHealthStatusColor(service.health_status)}">
        {getHealthStatusText(service.health_status)}
      </span>
    </div>
  </div>
  
  <!-- Service URL -->
  <div class="mb-4">
    <div class="flex items-center space-x-2 text-sm text-secondary-600 dark:text-dark-500">
      <Activity class="w-4 h-4" />
      <span class="font-mono text-xs bg-secondary-100 dark:bg-secondary-800 px-2 py-1 rounded">
        {service.service_url}
      </span>
    </div>
  </div>
  
  <!-- Performance Metrics -->
  <div class="grid grid-cols-2 gap-4 mb-6">
    <div class="text-center">
      <div class="text-sm text-secondary-500 dark:text-dark-400 mb-1">
        {$_('service.responseTime')}
      </div>
      <div class="text-lg font-semibold text-secondary-900 dark:text-dark-700">
        {formatResponseTime(service.avg_response_time_ms)}
      </div>
    </div>
    
    <div class="text-center">
      <div class="text-sm text-secondary-500 dark:text-dark-400 mb-1">
        {$_('service.successRate')}
      </div>
      <div class="text-lg font-semibold text-secondary-900 dark:text-dark-700">
        {formatSuccessRate(service.success_rate)}
      </div>
    </div>
  </div>
  
  <!-- Last Check -->
  {#if service.last_health_check}
    <div class="flex items-center space-x-2 text-xs text-secondary-500 dark:text-dark-400 mb-4">
      <Clock class="w-3 h-3" />
      <span>
        {$_('service.lastCheck')}: {new Date(service.last_health_check).toLocaleString()}
      </span>
    </div>
  {/if}
  
  <!-- Actions -->
  <div class="flex space-x-3">
    <button
      class="btn-primary flex-1 flex items-center justify-center space-x-2"
      on:click={visitService}
      disabled={!service.service_page_url || !service.is_active}
    >
      <ExternalLink class="w-4 h-4" />
      <span>{$_('service.visitService')}</span>
    </button>
    
    <button
      class="btn-secondary flex items-center space-x-2"
      disabled={!service.is_active}
    >
      <Activity class="w-4 h-4" />
      <span>{$_('service.testService')}</span>
    </button>
  </div>
  
  <!-- Inactive Badge -->
  {#if !service.is_active}
    <div class="mt-4 text-center">
      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-secondary-100 dark:bg-secondary-800 text-secondary-700 dark:text-secondary-300">
        服务已停用
      </span>
    </div>
  {/if}
</div>