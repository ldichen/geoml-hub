<script>
  import { createEventDispatcher } from 'svelte';
  
  const dispatch = createEventDispatcher();

  export let value = '';
  export let type = 'text';
  export let placeholder = '';
  export let disabled = false;
  export let readonly = false;
  export let required = false;
  export let label = '';
  export let error = '';
  export let hint = '';
  export let size = 'md'; // 'sm' | 'md' | 'lg'
  export let fullWidth = true;
  export let id = '';

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

  function handleInput(event) {
    value = event.target.value;
    dispatch('input', value);
  }

  function handleChange(event) {
    dispatch('change', event.target.value);
  }

  function handleFocus(event) {
    dispatch('focus', event);
  }

  function handleBlur(event) {
    dispatch('blur', event);
  }

  $: inputClasses = `
    block rounded-lg border transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2
    ${error 
      ? 'border-red-300 focus:border-red-500 focus:ring-red-500' 
      : 'border-gray-300 focus:border-primary-500 focus:ring-primary-500 dark:border-gray-600 dark:focus:border-primary-400'
    }
    ${disabled 
      ? 'bg-gray-50 text-gray-500 cursor-not-allowed dark:bg-gray-800' 
      : 'bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100'
    }
    ${fullWidth ? 'w-full' : ''}
    ${getSizeClasses(size)}
  `.trim().replace(/\s+/g, ' ');
</script>

<div class="space-y-1">
  {#if label}
    <label 
      for={id} 
      class="block text-sm font-medium text-gray-700 dark:text-gray-300"
    >
      {label}
      {#if required}
        <span class="text-red-500 ml-1">*</span>
      {/if}
    </label>
  {/if}
  
  <input
    {id}
    {type}
    {placeholder}
    {disabled}
    {readonly}
    {required}
    {value}
    class={inputClasses}
    on:input={handleInput}
    on:change={handleChange}
    on:focus={handleFocus}
    on:blur={handleBlur}
    on:keydown
    on:keyup
    on:keypress
  />
  
  {#if error}
    <p class="text-sm text-red-600 dark:text-red-400">
      {error}
    </p>
  {:else if hint}
    <p class="text-sm text-gray-500 dark:text-gray-400">
      {hint}
    </p>
  {/if}
</div>