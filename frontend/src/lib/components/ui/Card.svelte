<script>
  export let variant = 'default'; // 'default' | 'outline' | 'elevated'
  export let padding = 'md'; // 'none' | 'sm' | 'md' | 'lg'
  export let hover = false;
  export let clickable = false;

  function getVariantClasses(variant) {
    switch (variant) {
      case 'outline':
        return 'border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800';
      case 'elevated':
        return 'bg-white dark:bg-gray-800 shadow-lg border border-gray-100 dark:border-gray-700';
      default:
        return 'bg-white dark:bg-gray-800 shadow-sm border border-gray-200 dark:border-gray-700';
    }
  }

  function getPaddingClasses(padding) {
    switch (padding) {
      case 'none':
        return '';
      case 'sm':
        return 'p-4';
      case 'md':
        return 'p-6';
      case 'lg':
        return 'p-8';
      default:
        return 'p-6';
    }
  }

  $: cardClasses = `
    rounded-lg transition-all duration-200
    ${getVariantClasses(variant)}
    ${getPaddingClasses(padding)}
    ${hover ? 'hover:shadow-md hover:border-gray-300 dark:hover:border-gray-600' : ''}
    ${clickable ? 'cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700' : ''}
  `.trim().replace(/\s+/g, ' ');
</script>

{#if clickable}
<div 
  class={cardClasses}
  on:click
  on:keydown
  role="button"
  tabindex="0"
>
  {#if $$slots.header}
    <div class="mb-4">
      <slot name="header" />
    </div>
  {/if}

  <slot />

  {#if $$slots.footer}
    <div class="mt-4">
      <slot name="footer" />
    </div>
  {/if}
</div>
{:else}
<div 
  class={cardClasses}
>
  {#if $$slots.header}
    <div class="mb-4">
      <slot name="header" />
    </div>
  {/if}

  <slot />

  {#if $$slots.footer}
    <div class="mt-4">
      <slot name="footer" />
    </div>
  {/if}
</div>
{/if}