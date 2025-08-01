<script>
  import { _ } from 'svelte-i18n';
  import { ChevronDown, ChevronRight } from 'lucide-svelte';
  import { createEventDispatcher } from 'svelte';
  
  export let categories = [];
  export let selectedCategoryId = null;
  export let selectedSubcategoryId = null;
  
  const dispatch = createEventDispatcher();
  
  let expandedCategories = new Set();
  
  function toggleCategory(categoryId) {
    if (expandedCategories.has(categoryId)) {
      expandedCategories.delete(categoryId);
    } else {
      expandedCategories.add(categoryId);
    }
    expandedCategories = new Set(expandedCategories);
  }
  
  function selectCategory(categoryId) {
    dispatch('categoryChange', { categoryId, subcategoryId: null });
  }
  
  function selectSubcategory(categoryId, subcategoryId) {
    dispatch('categoryChange', { categoryId, subcategoryId });
  }
  
  function clearFilters() {
    dispatch('categoryChange', { categoryId: null, subcategoryId: null });
  }
</script>

<div class="bg-white dark:bg-dark-50 rounded-lg shadow-sm border border-secondary-200 dark:border-secondary-700 p-4">
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold text-secondary-900 dark:text-dark-700">
      {$_('category.title')}
    </h3>
    {#if selectedCategoryId || selectedSubcategoryId}
      <button
        class="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
        on:click={clearFilters}
      >
        {$_('search.clearFilters')}
      </button>
    {/if}
  </div>
  
  <div class="space-y-2">
    <!-- All Categories Option -->
    <button
      class="w-full text-left px-3 py-2 rounded-md transition-colors {!selectedCategoryId ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400' : 'hover:bg-secondary-50 dark:hover:bg-secondary-800'}"
      on:click={() => selectCategory(null)}
    >
      <span class="font-medium">{$_('category.all')}</span>
    </button>
    
    {#each categories as category}
      <div class="space-y-1">
        <!-- Main Category -->
        <div class="flex items-center">
          <button
            class="flex-1 flex items-center space-x-2 px-3 py-2 rounded-md transition-colors {selectedCategoryId === category.id && !selectedSubcategoryId ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400' : 'hover:bg-secondary-50 dark:hover:bg-secondary-800'}"
            on:click={() => selectCategory(category.id)}
          >
            <span class="font-medium">{category.display_name}</span>
            {#if category.model_count !== undefined}
              <span class="text-xs text-secondary-500 dark:text-dark-400">
                ({category.model_count})
              </span>
            {/if}
          </button>
          
          {#if category.subcategories && category.subcategories.length > 0}
            <button
              class="p-1 rounded-md hover:bg-secondary-100 dark:hover:bg-secondary-800 transition-colors"
              on:click={() => toggleCategory(category.id)}
            >
              {#if expandedCategories.has(category.id)}
                <ChevronDown class="w-4 h-4 text-secondary-500 dark:text-dark-400" />
              {:else}
                <ChevronRight class="w-4 h-4 text-secondary-500 dark:text-dark-400" />
              {/if}
            </button>
          {/if}
        </div>
        
        <!-- Subcategories -->
        {#if expandedCategories.has(category.id) && category.subcategories}
          <div class="ml-4 space-y-1">
            {#each category.subcategories as subcategory}
              <button
                class="w-full text-left px-3 py-2 rounded-md transition-colors {selectedSubcategoryId === subcategory.id ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400' : 'hover:bg-secondary-50 dark:hover:bg-secondary-800'}"
                on:click={() => selectSubcategory(category.id, subcategory.id)}
              >
                <span class="text-sm">{subcategory.display_name}</span>
                {#if subcategory.model_count !== undefined}
                  <span class="text-xs text-secondary-500 dark:text-dark-400 ml-2">
                    ({subcategory.model_count})
                  </span>
                {/if}
              </button>
            {/each}
          </div>
        {/if}
      </div>
    {/each}
  </div>
</div>