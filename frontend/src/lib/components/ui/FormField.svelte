<script>
  import { generateId } from '$lib/utils/accessibility.js';
  import Input from './Input.svelte';
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();

  export let name = '';
  export let label = '';
  export let value = '';
  export let type = 'text';
  export let placeholder = '';
  export let error = '';
  export let hint = '';
  export let required = false;
  export let disabled = false;
  export let readonly = false;
  export let size = 'md';
  export let validators = [];

  // Generate unique IDs for accessibility
  const fieldId = generateId('field');
  const errorId = generateId('error');
  const hintId = generateId('hint');

  function handleInput(event) {
    value = event.detail;
    
    // Run validation if validators are provided
    if (validators.length > 0) {
      for (const validator of validators) {
        const result = validator(value);
        if (result !== true) {
          error = result;
          break;
        } else {
          error = '';
        }
      }
    }

    dispatch('input', { name, value, error });
  }

  function handleChange(event) {
    dispatch('change', { name, value: event.detail, error });
  }

  function handleBlur(event) {
    dispatch('blur', { name, value, error });
  }

  function handleFocus(event) {
    dispatch('focus', { name, value });
  }

  $: describedBy = [
    error ? errorId : null,
    hint ? hintId : null
  ].filter(Boolean).join(' ') || undefined;
</script>

<div class="space-y-1">
  {#if label}
    <label 
      for={fieldId}
      class="block text-sm font-medium text-gray-700 dark:text-gray-300"
    >
      {label}
      {#if required}
        <span class="text-red-500 ml-1" aria-label="required">*</span>
      {/if}
    </label>
  {/if}

  <Input
    id={fieldId}
    {name}
    {type}
    {placeholder}
    {disabled}
    {readonly}
    {required}
    {size}
    {value}
    error={error}
    hint=""
    aria-describedby={describedBy}
    aria-invalid={error ? 'true' : 'false'}
    on:input={handleInput}
    on:change={handleChange}
    on:focus={handleFocus}
    on:blur={handleBlur}
  />

  {#if error}
    <p 
      id={errorId}
      class="text-sm text-red-600 dark:text-red-400"
      role="alert"
      aria-live="polite"
    >
      {error}
    </p>
  {:else if hint}
    <p 
      id={hintId}
      class="text-sm text-gray-500 dark:text-gray-400"
    >
      {hint}
    </p>
  {/if}
</div>