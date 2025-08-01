<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { Keys, handleArrowNavigation } from '$lib/utils/accessibility.js';

  const dispatch = createEventDispatcher();

  export let tabs = []; // Array of { id, label, disabled?, badge? }
  export let activeTab = null;
  export let variant = 'default'; // 'default' | 'pills' | 'underline'
  export let size = 'md'; // 'sm' | 'md' | 'lg'

  let tabListElement;
  let tabElements = [];

  onMount(() => {
    // Set initial active tab if not provided
    if (!activeTab && tabs.length > 0) {
      activeTab = tabs[0].id;
    }
  });

  function selectTab(tabId) {
    if (tabs.find(tab => tab.id === tabId && !tab.disabled)) {
      activeTab = tabId;
      dispatch('change', { activeTab });
    }
  }

  function handleKeydown(event, tabId) {
    const currentIndex = tabs.findIndex(tab => tab.id === tabId);
    const enabledTabs = tabElements.filter(el => !el.disabled);
    const currentEnabledIndex = enabledTabs.findIndex(el => el === event.target);

    switch (event.key) {
      case Keys.ARROW_LEFT:
      case Keys.ARROW_RIGHT:
      case Keys.HOME:
      case Keys.END:
        handleArrowNavigation(event, enabledTabs, currentEnabledIndex, true);
        break;
      
      case Keys.ENTER:
      case Keys.SPACE:
        event.preventDefault();
        selectTab(tabId);
        break;
    }
  }

  function getVariantClasses(variant, isActive, disabled) {
    const baseClasses = 'relative inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500';

    if (disabled) {
      return `${baseClasses} cursor-not-allowed opacity-50`;
    }

    switch (variant) {
      case 'pills':
        return isActive
          ? `${baseClasses} bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300 rounded-md`
          : `${baseClasses} text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-300 dark:hover:bg-gray-800 rounded-md`;
      
      case 'underline':
        return isActive
          ? `${baseClasses} text-primary-600 dark:text-primary-400 border-b-2 border-primary-600 dark:border-primary-400`
          : `${baseClasses} text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 border-b-2 border-transparent hover:border-gray-300 dark:hover:border-gray-600`;
      
      default:
        return isActive
          ? `${baseClasses} bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-300 dark:border-gray-600 rounded-t-md -mb-px z-10`
          : `${baseClasses} text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 border border-transparent hover:border-gray-300 dark:hover:border-gray-600 rounded-t-md`;
    }
  }

  function getSizeClasses(size) {
    switch (size) {
      case 'sm':
        return 'px-3 py-1.5 text-sm';
      case 'lg':
        return 'px-6 py-3 text-base';
      default:
        return 'px-4 py-2 text-sm';
    }
  }

  $: containerClasses = variant === 'underline' 
    ? 'border-b border-gray-200 dark:border-gray-700'
    : variant === 'default'
    ? 'border-b border-gray-200 dark:border-gray-700'
    : '';
</script>

<div class="w-full">
  <!-- Tab List -->
  <div 
    bind:this={tabListElement}
    class="flex space-x-1 {containerClasses}"
    role="tablist"
    aria-label="Tabs"
  >
    {#each tabs as tab, index}
      <button
        bind:this={tabElements[index]}
        class="{getVariantClasses(variant, activeTab === tab.id, tab.disabled)} {getSizeClasses(size)}"
        role="tab"
        tabindex={activeTab === tab.id ? 0 : -1}
        aria-selected={activeTab === tab.id}
        aria-controls="tabpanel-{tab.id}"
        disabled={tab.disabled}
        on:click={() => selectTab(tab.id)}
        on:keydown={(e) => handleKeydown(e, tab.id)}
      >
        <span>{tab.label}</span>
        
        {#if tab.badge}
          <span class="ml-2 inline-flex items-center justify-center px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-800 rounded-full dark:bg-gray-700 dark:text-gray-200">
            {tab.badge}
          </span>
        {/if}
      </button>
    {/each}
  </div>

  <!-- Tab Panels -->
  <div class="mt-4">
    {#each tabs as tab}
      <div
        id="tabpanel-{tab.id}"
        class={activeTab === tab.id ? 'block' : 'hidden'}
        role="tabpanel"
        tabindex="0"
        aria-labelledby="tab-{tab.id}"
      >
        <slot name="panel" {tab} active={activeTab === tab.id} />
      </div>
    {/each}
  </div>
</div>

<style>
  /* Hide default focus outline since we're using focus:ring */
  button:focus {
    outline: none;
  }
</style>