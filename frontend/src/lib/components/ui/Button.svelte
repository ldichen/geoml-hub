<script>
  export let variant = 'primary'; // 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline'
  export let size = 'md'; // 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  export let disabled = false;
  export let loading = false;
  export let href = null;
  export let type = 'button';
  export let fullWidth = false;

  function getVariantClasses(variant) {
    const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
    
    switch (variant) {
      case 'primary':
        return `${baseClasses} bg-primary-600 hover:bg-primary-700 text-white shadow-sm focus:ring-primary-500`;
      case 'secondary':
        return `${baseClasses} bg-gray-100 hover:bg-gray-200 text-gray-900 focus:ring-gray-500 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-100`;
      case 'danger':
        return `${baseClasses} bg-red-600 hover:bg-red-700 text-white shadow-sm focus:ring-red-500`;
      case 'ghost':
        return `${baseClasses} text-gray-600 hover:bg-gray-100 focus:ring-gray-500 dark:text-gray-400 dark:hover:bg-gray-800`;
      case 'outline':
        return `${baseClasses} border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-gray-300`;
      default:
        return `${baseClasses} bg-primary-600 hover:bg-primary-700 text-white shadow-sm focus:ring-primary-500`;
    }
  }

  function getSizeClasses(size) {
    switch (size) {
      case 'xs':
        return 'px-2 py-1 text-xs';
      case 'sm':
        return 'px-3 py-1.5 text-sm';
      case 'md':
        return 'px-4 py-2 text-sm';
      case 'lg':
        return 'px-6 py-3 text-base';
      case 'xl':
        return 'px-8 py-4 text-lg';
      default:
        return 'px-4 py-2 text-sm';
    }
  }

  function getIconSize(size) {
    switch (size) {
      case 'xs':
        return 'h-3 w-3';
      case 'sm':
        return 'h-4 w-4';
      case 'md':
        return 'h-4 w-4';
      case 'lg':
        return 'h-5 w-5';
      case 'xl':
        return 'h-6 w-6';
      default:
        return 'h-4 w-4';
    }
  }

  $: buttonClasses = `${getVariantClasses(variant)} ${getSizeClasses(size)} ${fullWidth ? 'w-full' : ''}`;
  $: iconClasses = getIconSize(size);
</script>

{#if href}
  <a 
    {href}
    class={buttonClasses}
    class:opacity-50={disabled}
    class:pointer-events-none={disabled}
    on:click
  >
    {#if loading}
      <div class="animate-spin rounded-full border-2 border-current border-t-transparent {iconClasses} mr-2"></div>
    {/if}
    <slot />
  </a>
{:else}
  <button
    {type}
    class={buttonClasses}
    {disabled}
    on:click
  >
    {#if loading}
      <div class="animate-spin rounded-full border-2 border-current border-t-transparent {iconClasses} mr-2"></div>
    {/if}
    <slot />
  </button>
{/if}