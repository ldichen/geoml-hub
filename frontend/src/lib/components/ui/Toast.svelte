<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { CheckCircle, AlertCircle, XCircle, Info, X } from 'lucide-svelte';
  
  const dispatch = createEventDispatcher();

  export let variant = 'info'; // 'info' | 'success' | 'warning' | 'error'
  export let title = '';
  export let message = '';
  export let duration = 5000; // auto-dismiss after 5 seconds, set to 0 for no auto-dismiss
  export let dismissible = true;
  export let position = 'top-right'; // 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center'

  let visible = true;
  let timeoutId;

  function getVariantClasses(variant) {
    switch (variant) {
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-700 dark:text-green-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/20 dark:border-yellow-700 dark:text-yellow-200';
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-700 dark:text-red-200';
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/20 dark:border-blue-700 dark:text-blue-200';
    }
  }

  function getIcon(variant) {
    switch (variant) {
      case 'success':
        return CheckCircle;
      case 'warning':
        return AlertCircle;
      case 'error':
        return XCircle;
      default:
        return Info;
    }
  }

  function getIconColor(variant) {
    switch (variant) {
      case 'success':
        return 'text-green-600 dark:text-green-400';
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'error':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-blue-600 dark:text-blue-400';
    }
  }

  function getPositionClasses(position) {
    const baseClasses = 'fixed z-50';
    switch (position) {
      case 'top-left':
        return `${baseClasses} top-4 left-4`;
      case 'top-center':
        return `${baseClasses} top-4 left-1/2 transform -translate-x-1/2`;
      case 'top-right':
        return `${baseClasses} top-4 right-4`;
      case 'bottom-left':
        return `${baseClasses} bottom-4 left-4`;
      case 'bottom-center':
        return `${baseClasses} bottom-4 left-1/2 transform -translate-x-1/2`;
      case 'bottom-right':
        return `${baseClasses} bottom-4 right-4`;
      default:
        return `${baseClasses} top-4 right-4`;
    }
  }

  function dismiss() {
    visible = false;
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    dispatch('dismiss');
  }

  onMount(() => {
    if (duration > 0) {
      timeoutId = setTimeout(() => {
        dismiss();
      }, duration);
    }

    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  });

  $: Icon = getIcon(variant);
  $: iconColorClass = getIconColor(variant);
</script>

{#if visible}
  <div 
    class="{getPositionClasses(position)} max-w-md w-full"
    role="alert"
    aria-live="assertive"
  >
    <div class="rounded-lg border p-4 shadow-lg {getVariantClasses(variant)}">
      <div class="flex items-start">
        <div class="flex-shrink-0">
          <Icon class="h-5 w-5 {iconColorClass}" />
        </div>
        
        <div class="ml-3 flex-1">
          {#if title}
            <h3 class="text-sm font-medium mb-1">
              {title}
            </h3>
          {/if}
          
          <div class="text-sm">
            {#if message}
              <p>{message}</p>
            {:else}
              <slot />
            {/if}
          </div>
        </div>
        
        {#if dismissible}
          <div class="ml-4 flex-shrink-0">
            <button
              on:click={dismiss}
              class="inline-flex rounded-md p-1.5 hover:bg-black/5 dark:hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-current"
              aria-label="Dismiss notification"
            >
              <X class="h-4 w-4" />
            </button>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}