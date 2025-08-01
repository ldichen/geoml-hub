<script>
  import { createEventDispatcher } from 'svelte';
  import { X, CheckCircle, AlertCircle, XCircle, Info } from 'lucide-svelte';
  
  const dispatch = createEventDispatcher();

  export let variant = 'info'; // 'info' | 'success' | 'warning' | 'danger'
  export let dismissible = false;
  export let title = '';
  export let icon = true;

  function getVariantClasses(variant) {
    switch (variant) {
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-700 dark:text-green-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/20 dark:border-yellow-700 dark:text-yellow-200';
      case 'danger':
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
      case 'danger':
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
      case 'danger':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-blue-600 dark:text-blue-400';
    }
  }

  function dismiss() {
    dispatch('dismiss');
  }

  $: Icon = getIcon(variant);
  $: iconColorClass = getIconColor(variant);
</script>

<div class="rounded-md border p-4 {getVariantClasses(variant)}">
  <div class="flex">
    {#if icon}
      <div class="flex-shrink-0">
        <Icon class="h-5 w-5 {iconColorClass}" />
      </div>
    {/if}
    
    <div class="flex-1 {icon ? 'ml-3' : ''}">
      {#if title}
        <h3 class="text-sm font-medium mb-1">
          {title}
        </h3>
      {/if}
      
      <div class="text-sm">
        <slot />
      </div>
    </div>
    
    {#if dismissible}
      <div class="ml-auto pl-3">
        <div class="-mx-1.5 -my-1.5">
          <button
            on:click={dismiss}
            class="inline-flex rounded-md p-1.5 hover:bg-black/5 dark:hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-current"
            aria-label="Dismiss"
          >
            <X class="h-5 w-5" />
          </button>
        </div>
      </div>
    {/if}
  </div>
</div>