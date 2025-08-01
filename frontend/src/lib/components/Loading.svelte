<script>
  import { _ } from 'svelte-i18n';
  
  export let text = '';
  export let message = '';
  export let size = 'md';
  export let center = false;
  
  $: sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  };
  
  $: textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg'
  };
</script>

<div class="flex items-center space-x-3 {center ? 'justify-center' : ''}">
  <div class="animate-spin rounded-full border-2 border-secondary-200 dark:border-secondary-700 border-t-primary-600 dark:border-t-primary-400 {sizeClasses[size]}"></div>
  
  {#if message || text}
    <span class="text-secondary-600 dark:text-dark-500 {textSizeClasses[size]}">
      {message || text}
    </span>
  {:else}
    <span class="text-secondary-600 dark:text-dark-500 {textSizeClasses[size]}">
      {$_('common.loading')}
    </span>
  {/if}
</div>