<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { ChevronDown } from 'lucide-svelte';
  
  const dispatch = createEventDispatcher();

  export let items = [];
  export let value = null;
  export let placeholder = 'Select an option';
  export let disabled = false;
  export let searchable = false;
  export let multiple = false;
  export let size = 'md'; // 'sm' | 'md' | 'lg'

  let isOpen = false;
  let searchTerm = '';
  let dropdownElement;
  let triggerElement;

  function getSizeClasses(size) {
    switch (size) {
      case 'sm':
        return 'px-3 py-1.5 text-sm';
      case 'md':
        return 'px-3 py-2 text-sm';
      case 'lg':
        return 'px-4 py-3 text-base';
      default:
        return 'px-3 py-2 text-sm';
    }
  }

  function toggleDropdown() {
    if (!disabled) {
      isOpen = !isOpen;
    }
  }

  function selectItem(item) {
    if (multiple) {
      if (Array.isArray(value)) {
        const index = value.findIndex(v => v.value === item.value);
        if (index > -1) {
          value = value.filter(v => v.value !== item.value);
        } else {
          value = [...value, item];
        }
      } else {
        value = [item];
      }
    } else {
      value = item;
      isOpen = false;
    }
    
    dispatch('select', { item, value });
  }

  function handleKeydown(event) {
    if (event.key === 'Escape') {
      isOpen = false;
    }
  }

  function handleClickOutside(event) {
    if (dropdownElement && !dropdownElement.contains(event.target)) {
      isOpen = false;
    }
  }

  onMount(() => {
    document.addEventListener('click', handleClickOutside);
    document.addEventListener('keydown', handleKeydown);
    
    return () => {
      document.removeEventListener('click', handleClickOutside);
      document.removeEventListener('keydown', handleKeydown);
    };
  });

  $: filteredItems = searchable && searchTerm
    ? items.filter(item => 
        item.label.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : items;

  $: selectedLabel = multiple
    ? (Array.isArray(value) && value.length > 0 
        ? `${value.length} selected`
        : placeholder)
    : (value ? value.label : placeholder);

  $: isSelected = (item) => {
    if (multiple && Array.isArray(value)) {
      return value.some(v => v.value === item.value);
    }
    return value && value.value === item.value;
  };
</script>

<div bind:this={dropdownElement} class="relative">
  <button
    bind:this={triggerElement}
    on:click={toggleDropdown}
    class="
      relative w-full cursor-default rounded-lg border border-gray-300 bg-white text-left 
      focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500
      dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100
      {getSizeClasses(size)}
      {disabled ? 'bg-gray-50 text-gray-500 cursor-not-allowed dark:bg-gray-700' : ''}
    "
    {disabled}
    aria-haspopup="listbox"
    aria-expanded={isOpen}
  >
    <span class="block truncate">
      {selectedLabel}
    </span>
    <span class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
      <ChevronDown 
        class="h-4 w-4 text-gray-400 transition-transform duration-200 {isOpen ? 'rotate-180' : ''}" 
      />
    </span>
  </button>

  {#if isOpen}
    <div class="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none dark:bg-gray-800 dark:ring-gray-700">
      {#if searchable}
        <div class="px-2 py-2">
          <input
            type="text"
            bind:value={searchTerm}
            placeholder="Search..."
            class="w-full rounded border border-gray-300 px-2 py-1 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
          />
        </div>
      {/if}

      {#each filteredItems as item}
        <button
          on:click={() => selectItem(item)}
          class="
            relative cursor-default select-none py-2 pl-3 pr-9 text-gray-900 hover:bg-primary-50 hover:text-primary-600
            dark:text-gray-100 dark:hover:bg-gray-700 dark:hover:text-primary-400
            {isSelected(item) ? 'bg-primary-100 text-primary-600 dark:bg-gray-700 dark:text-primary-400' : ''}
            w-full text-left
          "
          role="option"
          aria-selected={isSelected(item)}
        >
          <span class="block truncate">
            {item.label}
          </span>
          
          {#if isSelected(item)}
            <span class="absolute inset-y-0 right-0 flex items-center pr-4 text-primary-600 dark:text-primary-400">
              <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </span>
          {/if}
        </button>
      {/each}

      {#if filteredItems.length === 0}
        <div class="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">
          No options found
        </div>
      {/if}
    </div>
  {/if}
</div>