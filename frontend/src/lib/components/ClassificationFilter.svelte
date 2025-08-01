<script>
  import { createEventDispatcher } from 'svelte';
  import { ChevronRight, ChevronDown } from 'lucide-svelte';
  
  export let classificationTree = [];
  export let selectedClassificationId = null;
  
  const dispatch = createEventDispatcher();
  
  let expandedNodes = new Set();
  
  function toggleNode(nodeId) {
    if (expandedNodes.has(nodeId)) {
      expandedNodes.delete(nodeId);
    } else {
      expandedNodes.add(nodeId);
    }
    expandedNodes = expandedNodes;
  }
  
  function selectClassification(classificationId) {
    selectedClassificationId = classificationId;
    dispatch('select', classificationId);
  }
  
  function clearSelection() {
    selectedClassificationId = null;
    dispatch('select', null);
  }
  
  function hasChildren(node) {
    return node.children && node.children.length > 0;
  }
  
  function isExpanded(nodeId) {
    return expandedNodes.has(nodeId);
  }
  
  function isSelected(nodeId) {
    return selectedClassificationId === nodeId;
  }
</script>

<div class="classification-filter">
  <div class="flex items-center justify-between mb-4">
    <h3 class="text-lg font-semibold text-secondary-900 dark:text-dark-700">
      分类筛选
    </h3>
    {#if selectedClassificationId}
      <button 
        class="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
        on:click={clearSelection}
      >
        清除筛选
      </button>
    {/if}
  </div>
  
  <div class="space-y-1">
    {#each classificationTree as level1}
      <div class="classification-node border-l border-secondary-200 dark:border-secondary-700 pl-2">
        <!-- Level 1 Node -->
        <div class="flex items-center">
          {#if hasChildren(level1)}
            <button 
              class="flex items-center justify-center w-6 h-6 rounded hover:bg-secondary-100 dark:hover:bg-secondary-700"
              on:click={() => toggleNode(level1.id)}
            >
              {#if isExpanded(level1.id)}
                <ChevronDown class="w-4 h-4 text-secondary-600 dark:text-dark-500" />
              {:else}
                <ChevronRight class="w-4 h-4 text-secondary-600 dark:text-dark-500" />
              {/if}
            </button>
          {:else}
            <div class="w-6 h-6"></div>
          {/if}
          
          <button 
            class="flex-1 text-left px-2 py-1 rounded text-sm font-medium transition-colors
                   {isSelected(level1.id) 
                     ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300' 
                     : 'text-secondary-700 dark:text-dark-600 hover:bg-secondary-50 dark:hover:bg-secondary-800'}"
            on:click={() => selectClassification(level1.id)}
          >
            {level1.name}
          </button>
        </div>
        
        <!-- Level 2 Children -->
        {#if hasChildren(level1) && isExpanded(level1.id)}
          <div class="ml-6 mt-1 space-y-1">
            {#each level1.children as level2}
              <div class="classification-node border-l border-secondary-200 dark:border-secondary-700 pl-2">
                <!-- Level 2 Node -->
                <div class="flex items-center">
                  {#if hasChildren(level2)}
                    <button 
                      class="flex items-center justify-center w-5 h-5 rounded hover:bg-secondary-100 dark:hover:bg-secondary-700"
                      on:click={() => toggleNode(level2.id)}
                    >
                      {#if isExpanded(level2.id)}
                        <ChevronDown class="w-3 h-3 text-secondary-600 dark:text-dark-500" />
                      {:else}
                        <ChevronRight class="w-3 h-3 text-secondary-600 dark:text-dark-500" />
                      {/if}
                    </button>
                  {:else}
                    <div class="w-5 h-5"></div>
                  {/if}
                  
                  <button 
                    class="flex-1 text-left px-2 py-1 rounded text-sm transition-colors
                           {isSelected(level2.id) 
                             ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300' 
                             : 'text-secondary-600 dark:text-dark-500 hover:bg-secondary-50 dark:hover:bg-secondary-800'}"
                    on:click={() => selectClassification(level2.id)}
                  >
                    {level2.name}
                  </button>
                </div>
                
                <!-- Level 3 Children -->
                {#if hasChildren(level2) && isExpanded(level2.id)}
                  <div class="ml-5 mt-1 space-y-1">
                    {#each level2.children as level3}
                      <button 
                        class="w-full text-left px-2 py-1 rounded text-xs transition-colors
                               {isSelected(level3.id) 
                                 ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300' 
                                 : 'text-secondary-500 dark:text-dark-400 hover:bg-secondary-50 dark:hover:bg-secondary-800'}"
                        on:click={() => selectClassification(level3.id)}
                      >
                        {level3.name}
                      </button>
                    {/each}
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/each}
  </div>
</div>