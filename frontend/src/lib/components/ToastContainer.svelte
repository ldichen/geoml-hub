<script>
  import { toasts, removeToast } from '$lib/utils/toast.js';
  import Toast from './ui/Toast.svelte';
  
  function handleDismiss(event) {
    removeToast(event.detail);
  }

  // Group toasts by position
  $: toastsByPosition = $toasts.reduce((acc, toast) => {
    const position = toast.position || 'top-right';
    if (!acc[position]) {
      acc[position] = [];
    }
    acc[position].push(toast);
    return acc;
  }, {});

  function getContainerClasses(position) {
    const baseClasses = 'fixed z-50 max-w-md w-full space-y-2';
    
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
</script>

<!-- Render toast containers for each position -->
{#each Object.entries(toastsByPosition) as [position, positionToasts]}
  <div class={getContainerClasses(position)}>
    {#each positionToasts as toast (toast.id)}
      <div class="animate-fade-in">
        <Toast
          variant={toast.variant}
          title={toast.title}
          message={toast.message}
          duration={0}
          dismissible={toast.dismissible}
          position="static"
          on:dismiss={() => removeToast(toast.id)}
        />
      </div>
    {/each}
  </div>
{/each}

<style>
  .animate-fade-in {
    animation: fadeIn 0.3s ease-out;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
</style>