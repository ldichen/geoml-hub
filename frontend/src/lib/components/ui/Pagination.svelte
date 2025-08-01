<script>
  import { createEventDispatcher } from 'svelte';
  import { ChevronLeft, ChevronRight } from 'lucide-svelte';

  const dispatch = createEventDispatcher();

  export let currentPage = 1;
  export let totalPages = 1;
  export let showFirstLast = true;
  export let showPrevNext = true;
  export let maxVisiblePages = 5;
  export let size = 'md'; // 'sm' | 'md' | 'lg'

  function changePage(page) {
    if (page >= 1 && page <= totalPages && page !== currentPage) {
      dispatch('change', { page });
    }
  }

  function getSizeClasses(size) {
    switch (size) {
      case 'sm':
        return 'px-2 py-1 text-xs';
      case 'lg':
        return 'px-4 py-3 text-base';
      default:
        return 'px-3 py-2 text-sm';
    }
  }

  function getIconSize(size) {
    switch (size) {
      case 'sm':
        return 'h-3 w-3';
      case 'lg':
        return 'h-5 w-5';
      default:
        return 'h-4 w-4';
    }
  }

  // Calculate visible page numbers
  $: visiblePages = (() => {
    const half = Math.floor(maxVisiblePages / 2);
    let start = Math.max(1, currentPage - half);
    let end = Math.min(totalPages, start + maxVisiblePages - 1);
    
    // Adjust start if we're near the end
    if (end - start + 1 < maxVisiblePages) {
      start = Math.max(1, end - maxVisiblePages + 1);
    }
    
    const pages = [];
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    
    return pages;
  })();

  $: sizeClasses = getSizeClasses(size);
  $: iconClasses = getIconSize(size);
</script>

{#if totalPages > 1}
  <nav class="flex items-center justify-center space-x-1" aria-label="Pagination">
    <!-- First page -->
    {#if showFirstLast && currentPage > 1}
      <button
        on:click={() => changePage(1)}
        class="
          inline-flex items-center justify-center border border-gray-300 bg-white text-gray-500
          hover:bg-gray-50 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 
          focus:ring-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-400 
          dark:hover:bg-gray-700 dark:hover:text-gray-300 rounded-md transition-colors
          {sizeClasses}
        "
        aria-label="Go to first page"
      >
        1
      </button>
      
      {#if visiblePages[0] > 2}
        <span class="px-1 text-gray-500 dark:text-gray-400">...</span>
      {/if}
    {/if}

    <!-- Previous page -->
    {#if showPrevNext}
      <button
        on:click={() => changePage(currentPage - 1)}
        disabled={currentPage <= 1}
        class="
          inline-flex items-center justify-center border border-gray-300 bg-white text-gray-500
          hover:bg-gray-50 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 
          focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed
          dark:bg-gray-800 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700 
          dark:hover:text-gray-300 rounded-md transition-colors
          {sizeClasses}
        "
        aria-label="Go to previous page"
      >
        <ChevronLeft class={iconClasses} />
      </button>
    {/if}

    <!-- Page numbers -->
    {#each visiblePages as page}
      <button
        on:click={() => changePage(page)}
        class="
          inline-flex items-center justify-center border rounded-md transition-colors
          focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500
          {page === currentPage 
            ? 'border-primary-500 bg-primary-600 text-white' 
            : 'border-gray-300 bg-white text-gray-500 hover:bg-gray-50 hover:text-gray-700 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-300'
          }
          {sizeClasses}
        "
        aria-label={page === currentPage ? `Current page, page ${page}` : `Go to page ${page}`}
        aria-current={page === currentPage ? 'page' : undefined}
      >
        {page}
      </button>
    {/each}

    <!-- Next page -->
    {#if showPrevNext}
      <button
        on:click={() => changePage(currentPage + 1)}
        disabled={currentPage >= totalPages}
        class="
          inline-flex items-center justify-center border border-gray-300 bg-white text-gray-500
          hover:bg-gray-50 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 
          focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed
          dark:bg-gray-800 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700 
          dark:hover:text-gray-300 rounded-md transition-colors
          {sizeClasses}
        "
        aria-label="Go to next page"
      >
        <ChevronRight class={iconClasses} />
      </button>
    {/if}

    <!-- Last page -->
    {#if showFirstLast && currentPage < totalPages}
      {#if visiblePages[visiblePages.length - 1] < totalPages - 1}
        <span class="px-1 text-gray-500 dark:text-gray-400">...</span>
      {/if}
      
      <button
        on:click={() => changePage(totalPages)}
        class="
          inline-flex items-center justify-center border border-gray-300 bg-white text-gray-500
          hover:bg-gray-50 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 
          focus:ring-primary-500 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-400 
          dark:hover:bg-gray-700 dark:hover:text-gray-300 rounded-md transition-colors
          {sizeClasses}
        "
        aria-label="Go to last page"
      >
        {totalPages}
      </button>
    {/if}
  </nav>
{/if}