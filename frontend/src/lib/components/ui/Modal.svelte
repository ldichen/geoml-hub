<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { X } from 'lucide-svelte';
  
  const dispatch = createEventDispatcher();

  export let show = false;
  export let title = '';
  export let size = 'md'; // 'sm' | 'md' | 'lg' | 'xl' | 'full'
  export let closable = true;
  export let closeOnBackdrop = true;
  export let center = true;

  let modalElement;
  let previousFocus;

  function getSizeClasses(size) {
    switch (size) {
      case 'sm':
        return 'max-w-md';
      case 'md':
        return 'max-w-lg';
      case 'lg':
        return 'max-w-2xl';
      case 'xl':
        return 'max-w-4xl';
      case 'full':
        return 'max-w-screen-xl mx-4';
      default:
        return 'max-w-lg';
    }
  }

  function close() {
    if (closable) {
      show = false;
      dispatch('close');
    }
  }

  function handleBackdropClick(event) {
    if (closeOnBackdrop && event.target === event.currentTarget) {
      close();
    }
  }

  function handleKeydown(event) {
    if (event.key === 'Escape' && closable) {
      close();
    }
  }

  onMount(() => {
    function handleFocus() {
      if (show && modalElement) {
        previousFocus = document.activeElement;
        const focusableElements = modalElement.querySelectorAll(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusableElements.length > 0) {
          focusableElements[0].focus();
        }
      } else if (previousFocus) {
        previousFocus.focus();
        previousFocus = null;
      }
    }

    function handleDocumentKeydown(event) {
      if (show && event.key === 'Escape' && closable) {
        close();
      }
    }

    if (show) {
      document.body.style.overflow = 'hidden';
      document.addEventListener('keydown', handleDocumentKeydown);
      handleFocus();
    } else {
      document.body.style.overflow = '';
      document.removeEventListener('keydown', handleDocumentKeydown);
    }

    return () => {
      document.body.style.overflow = '';
      document.removeEventListener('keydown', handleDocumentKeydown);
      if (previousFocus) {
        previousFocus.focus();
      }
    };
  });

  $: {
    if (show) {
      document.body.style.overflow = 'hidden';
      document.addEventListener('keydown', handleKeydown);
    } else {
      document.body.style.overflow = '';
      document.removeEventListener('keydown', handleKeydown);
    }
  }

  $: modalClasses = `
    relative w-full mx-auto bg-white dark:bg-gray-800 rounded-lg shadow-xl transform transition-all
    ${getSizeClasses(size)}
  `.trim().replace(/\s+/g, ' ');
</script>

{#if show}
  <!-- Modal Container -->
  <div class="fixed inset-0 z-50 overflow-y-auto">
    <!-- Backdrop -->
    <button 
      class="fixed inset-0 bg-black bg-opacity-50 transition-opacity w-full h-full border-0 p-0 cursor-default"
      on:click={handleBackdropClick}
      aria-label="Close modal"
      tabindex="-1"
    ></button>

    <!-- Modal -->
    <div class={`flex min-h-full items-center justify-center p-4 ${center ? 'items-center' : 'items-start pt-16'}`}>
      <div 
        bind:this={modalElement}
        class={modalClasses}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'modal-title' : undefined}
        tabindex="-1"
      >
        <!-- Header -->
        {#if title || closable || $$slots.header}
          <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <div class="flex-1">
              {#if $$slots.header}
                <slot name="header" />
              {:else if title}
                <h3 id="modal-title" class="text-lg font-semibold text-gray-900 dark:text-white">
                  {title}
                </h3>
              {/if}
            </div>
            
            {#if closable}
              <button
                on:click={close}
                class="ml-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded-md p-1"
                aria-label="Close modal"
              >
                <X class="h-5 w-5" />
              </button>
            {/if}
          </div>
        {/if}

        <!-- Body -->
        <div class="p-6">
          <slot />
        </div>

        <!-- Footer -->
        {#if $$slots.footer}
          <div class="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 dark:border-gray-700">
            <slot name="footer" />
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}