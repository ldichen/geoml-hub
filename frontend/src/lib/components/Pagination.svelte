<script>
  import { _ } from 'svelte-i18n';
  import { ChevronLeft, ChevronRight } from 'lucide-svelte';
  import { createEventDispatcher } from 'svelte';
  
  export let currentPage = 1;
  export let totalPages = 1;
  export let total = 0;
  export let pageSize = 20;
  export let showSummary = true;
  
  const dispatch = createEventDispatcher();
  
  $: startItem = (currentPage - 1) * pageSize + 1;
  $: endItem = Math.min(currentPage * pageSize, total);
  $: hasNext = currentPage < totalPages;
  $: hasPrev = currentPage > 1;
  
  function goToPage(page) {
    if (page >= 1 && page <= totalPages && page !== currentPage) {
      dispatch('pageChange', { page });
    }
  }
  
  function getVisiblePages() {
    const delta = 2;
    const range = [];
    const rangeWithDots = [];
    
    for (let i = Math.max(2, currentPage - delta); 
         i <= Math.min(totalPages - 1, currentPage + delta); 
         i++) {
      range.push(i);
    }
    
    if (currentPage - delta > 2) {
      rangeWithDots.push(1, '...');
    } else {
      rangeWithDots.push(1);
    }
    
    rangeWithDots.push(...range);
    
    if (currentPage + delta < totalPages - 1) {
      rangeWithDots.push('...', totalPages);
    } else {
      rangeWithDots.push(totalPages);
    }
    
    return rangeWithDots;
  }
  
  $: visiblePages = getVisiblePages();
</script>

{#if totalPages > 1}
  <div class="flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0">
    <!-- Summary -->
    {#if showSummary}
      <div class="text-sm text-secondary-600 dark:text-dark-500">
        {$_('pagination.showing', { 
          values: { 
            from: startItem, 
            to: endItem, 
            total: total 
          } 
        })}
      </div>
    {/if}
    
    <!-- Pagination Controls -->
    <div class="flex items-center space-x-1">
      <!-- Previous Button -->
      <button
        class="flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-md border border-secondary-300 dark:border-secondary-600 bg-white dark:bg-dark-50 text-secondary-700 dark:text-dark-600 hover:bg-secondary-50 dark:hover:bg-secondary-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        disabled={!hasPrev}
        on:click={() => goToPage(currentPage - 1)}
      >
        <ChevronLeft class="w-4 h-4" />
        <span class="hidden sm:inline">{$_('pagination.previous')}</span>
      </button>
      
      <!-- Page Numbers -->
      <div class="flex items-center space-x-1">
        {#each visiblePages as page}
          {#if page === '...'}
            <span class="px-3 py-2 text-sm text-secondary-500 dark:text-dark-400">
              ...
            </span>
          {:else}
            <button
              class="px-3 py-2 text-sm font-medium rounded-md transition-colors {page === currentPage ? 'bg-primary-600 text-white' : 'bg-white dark:bg-dark-50 text-secondary-700 dark:text-dark-600 hover:bg-secondary-50 dark:hover:bg-secondary-800 border border-secondary-300 dark:border-secondary-600'}"
              on:click={() => goToPage(page)}
            >
              {page}
            </button>
          {/if}
        {/each}
      </div>
      
      <!-- Next Button -->
      <button
        class="flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-md border border-secondary-300 dark:border-secondary-600 bg-white dark:bg-dark-50 text-secondary-700 dark:text-dark-600 hover:bg-secondary-50 dark:hover:bg-secondary-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        disabled={!hasNext}
        on:click={() => goToPage(currentPage + 1)}
      >
        <span class="hidden sm:inline">{$_('pagination.next')}</span>
        <ChevronRight class="w-4 h-4" />
      </button>
    </div>
  </div>
{/if}