<script>
  import { createEventDispatcher } from 'svelte';
  import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-svelte';
  
  export let type = 'info'; // 'success', 'error', 'warning', 'info'
  export let message = '';
  export let duration = 5000; // 自动消失时间(毫秒)，0表示不自动消失
  export let closable = true; // 是否可手动关闭
  export let id = Math.random().toString(36).substr(2, 9); // 唯一ID
  
  const dispatch = createEventDispatcher();
  
  // 图标映射
  const icons = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertTriangle,
    info: Info
  };
  
  // 样式映射
  const styles = {
    success: 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900 dark:border-green-700 dark:text-green-200',
    error: 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900 dark:border-red-700 dark:text-red-200',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900 dark:border-yellow-700 dark:text-yellow-200',
    info: 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900 dark:border-blue-700 dark:text-blue-200'
  };
  
  // 图标颜色映射
  const iconColors = {
    success: 'text-green-500',
    error: 'text-red-500',
    warning: 'text-yellow-500',
    info: 'text-blue-500'
  };
  
  let visible = true;
  let timeoutId;
  
  // 自动消失定时器
  if (duration > 0) {
    timeoutId = setTimeout(() => {
      close();
    }, duration);
  }
  
  function close() {
    visible = false;
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    dispatch('close', { id });
  }
  
  // 清理定时器
  function onDestroy() {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  }
</script>

{#if visible}
  <div 
    class="toast flex items-start p-4 border rounded-lg shadow-lg max-w-md animate-slide-in {styles[type]}"
    role="alert"
    aria-live="polite"
  >
    <!-- 图标 -->
    <div class="flex-shrink-0 mr-3">
      <svelte:component this={icons[type]} class="w-5 h-5 {iconColors[type]}" />
    </div>
    
    <!-- 消息内容 -->
    <div class="flex-1 min-w-0">
      <p class="text-sm font-medium leading-5">{message}</p>
    </div>
    
    <!-- 关闭按钮 -->
    {#if closable}
      <button
        on:click={close}
        class="flex-shrink-0 ml-4 p-1 rounded-md hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
        aria-label="关闭通知"
      >
        <X class="w-4 h-4" />
      </button>
    {/if}
  </div>
{/if}

<style>
  .toast {
    animation: slide-in 0.3s ease-out;
  }
  
  @keyframes slide-in {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  .animate-slide-in {
    animation: slide-in 0.3s ease-out;
  }
</style>