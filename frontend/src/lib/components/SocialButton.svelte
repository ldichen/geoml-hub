<script>
  import { Star, UserPlus, UserMinus, Heart, Share2, GitFork } from 'lucide-svelte';
  import { createEventDispatcher } from 'svelte';
  import { _ } from 'svelte-i18n';

  const dispatch = createEventDispatcher();

  export let type = 'star'; // 'star' | 'follow' | 'like' | 'share' | 'fork'
  export let active = false;
  export let count = null;
  export let disabled = false;
  export let size = 'md'; // 'sm' | 'md' | 'lg'
  export let variant = 'default'; // 'default' | 'outline' | 'ghost'
  export let loading = false;

  function handleClick() {
    if (disabled || loading) return;
    dispatch('click');
  }

  function getIcon(type) {
    switch (type) {
      case 'star':
        return Star;
      case 'follow':
        return active ? UserMinus : UserPlus;
      case 'like':
        return Heart;
      case 'share':
        return Share2;
      case 'fork':
        return GitFork;
      default:
        return Star;
    }
  }

  function getLabel(type, active) {
    switch (type) {
      case 'star':
        return active ? $_('repository.unstar') : $_('repository.star');
      case 'follow':
        return active ? $_('user.unfollow') : $_('user.follow');
      case 'like':
        return active ? $_('social.unlike') : $_('social.like');
      case 'share':
        return $_('social.share');
      case 'fork':
        return $_('repository.fork');
      default:
        return '';
    }
  }

  function getSizeClasses(size) {
    switch (size) {
      case 'sm':
        return 'px-2 py-1 text-xs';
      case 'md':
        return 'px-3 py-1.5 text-sm';
      case 'lg':
        return 'px-4 py-2 text-base';
      default:
        return 'px-3 py-1.5 text-sm';
    }
  }

  function getIconSizeClasses(size) {
    switch (size) {
      case 'sm':
        return 'h-3 w-3';
      case 'md':
        return 'h-4 w-4';
      case 'lg':
        return 'h-5 w-5';
      default:
        return 'h-4 w-4';
    }
  }

  function getVariantClasses(variant, type, active) {
    const baseClasses = 'inline-flex items-center justify-center space-x-1 rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
    
    if (variant === 'ghost') {
      if (active) {
        switch (type) {
          case 'star':
            return `${baseClasses} text-yellow-600 dark:text-yellow-400 hover:bg-yellow-50 dark:hover:bg-yellow-900/20`;
          case 'follow':
            return `${baseClasses} text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20`;
          case 'like':
            return `${baseClasses} text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20`;
          default:
            return `${baseClasses} text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20`;
        }
      } else {
        return `${baseClasses} text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800`;
      }
    }
    
    if (variant === 'outline') {
      if (active) {
        switch (type) {
          case 'star':
            return `${baseClasses} border border-yellow-300 dark:border-yellow-600 text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 hover:bg-yellow-100 dark:hover:bg-yellow-900/30`;
          case 'follow':
            return `${baseClasses} border border-red-300 dark:border-red-600 text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30`;
          case 'like':
            return `${baseClasses} border border-red-300 dark:border-red-600 text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30`;
          default:
            return `${baseClasses} border border-blue-300 dark:border-blue-600 text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30`;
        }
      } else {
        return `${baseClasses} border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700`;
      }
    }
    
    // Default variant
    if (active) {
      switch (type) {
        case 'star':
          return `${baseClasses} bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 hover:bg-yellow-200 dark:hover:bg-yellow-900/40`;
        case 'follow':
          return `${baseClasses} bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-900/40`;
        case 'like':
          return `${baseClasses} bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-900/40`;
        default:
          return `${baseClasses} bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/40`;
      }
    } else {
      switch (type) {
        case 'follow':
          return `${baseClasses} bg-blue-600 dark:bg-blue-500 text-white hover:bg-blue-700 dark:hover:bg-blue-600`;
        default:
          return `${baseClasses} bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600`;
      }
    }
  }

  $: Icon = getIcon(type);
  $: label = getLabel(type, active);
  $: buttonClasses = `${getVariantClasses(variant, type, active)} ${getSizeClasses(size)}`;
  $: iconClasses = getIconSizeClasses(size);
</script>

<button
  class={buttonClasses}
  class:opacity-50={disabled || loading}
  class:cursor-not-allowed={disabled || loading}
  {disabled}
  on:click={handleClick}
  aria-label={label}
>
  {#if loading}
    <div class="animate-spin rounded-full border-2 border-current border-t-transparent {iconClasses}"></div>
  {:else}
    <Icon class={iconClasses} fill={active && (type === 'star' || type === 'like') ? 'currentColor' : 'none'} />
  {/if}
  
  <span>{label}</span>
  
  {#if count !== null && count > 0}
    <span class="ml-1 px-1.5 py-0.5 text-xs bg-black/10 dark:bg-white/10 rounded-full">
      {count}
    </span>
  {/if}
</button>