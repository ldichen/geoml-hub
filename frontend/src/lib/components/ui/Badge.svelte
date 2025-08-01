<script>
  export let variant = 'default'; // 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger'
  export let size = 'md'; // 'sm' | 'md' | 'lg'
  export let outline = false;
  export let removable = false;

  function getVariantClasses(variant, outline) {
    const baseClasses = 'inline-flex items-center font-medium rounded-full';
    
    if (outline) {
      switch (variant) {
        case 'primary':
          return `${baseClasses} border border-primary-200 text-primary-700 bg-primary-50 dark:border-primary-700 dark:text-primary-300 dark:bg-primary-900/20`;
        case 'secondary':
          return `${baseClasses} border border-gray-200 text-gray-700 bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:bg-gray-800`;
        case 'success':
          return `${baseClasses} border border-green-200 text-green-700 bg-green-50 dark:border-green-700 dark:text-green-300 dark:bg-green-900/20`;
        case 'warning':
          return `${baseClasses} border border-yellow-200 text-yellow-700 bg-yellow-50 dark:border-yellow-700 dark:text-yellow-300 dark:bg-yellow-900/20`;
        case 'danger':
          return `${baseClasses} border border-red-200 text-red-700 bg-red-50 dark:border-red-700 dark:text-red-300 dark:bg-red-900/20`;
        default:
          return `${baseClasses} border border-gray-200 text-gray-700 bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:bg-gray-800`;
      }
    } else {
      switch (variant) {
        case 'primary':
          return `${baseClasses} bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200`;
        case 'secondary':
          return `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200`;
        case 'success':
          return `${baseClasses} bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200`;
        case 'warning':
          return `${baseClasses} bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200`;
        case 'danger':
          return `${baseClasses} bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200`;
        default:
          return `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200`;
      }
    }
  }

  function getSizeClasses(size) {
    switch (size) {
      case 'sm':
        return 'px-2 py-0.5 text-xs';
      case 'md':
        return 'px-2.5 py-0.5 text-sm';
      case 'lg':
        return 'px-3 py-1 text-base';
      default:
        return 'px-2.5 py-0.5 text-sm';
    }
  }

  $: badgeClasses = `${getVariantClasses(variant, outline)} ${getSizeClasses(size)}`;
</script>

<span class={badgeClasses}>
  <slot />
  
  {#if removable}
    <button
      on:click
      class="ml-1 p-0.5 rounded-full hover:bg-black/10 dark:hover:bg-white/10 focus:outline-none focus:ring-2 focus:ring-current"
      aria-label="Remove badge"
    >
      <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
      </svg>
    </button>
  {/if}
</span>