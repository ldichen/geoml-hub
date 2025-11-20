<script>
  import { _ } from 'svelte-i18n';
  import { Eye, Download, Heart, Calendar, User, Building } from 'lucide-svelte';
  import { base } from '$app/paths';

  export let model;
  export let compact = false;
  export let hideThumb = false;
  export let trendingMode = false;

  function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  function handleCardClick() {
    // v2.0: Navigate to /{username}/{repository} pattern
    if (model.owner && model.name) {
      window.location.href = `${base}/${model.owner.username}/${model.name}`;
    } else if (model.full_name) {
      window.location.href = `${base}/${model.full_name}`;
    } else {
      console.warn('Model card: Invalid model data, missing owner/name information');
    }
  }
</script>

<div 
  class="{compact ? 'border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow' : 'card-hover p-6 animate-fade-in'}"
  role="button"
  tabindex="0"
  on:click={handleCardClick}
  on:keydown={(e) => e.key === 'Enter' && handleCardClick()}
>
  <!-- Thumbnail (hidden if hideThumb is true) -->
  {#if !hideThumb && !compact}
    <div class="aspect-w-16 aspect-h-9 mb-4">
      {#if model.thumbnail_url}
        <img 
          src={model.thumbnail_url} 
          alt={model.name}
          class="w-full h-40 object-cover rounded-lg bg-secondary-100 dark:bg-secondary-800"
        />
      {:else}
        <div class="w-full h-40 bg-gradient-to-br from-primary-100 to-primary-200 dark:from-primary-900/20 dark:to-primary-800/20 rounded-lg flex items-center justify-center">
          <span class="text-primary-600 dark:text-primary-400 font-medium text-lg">
            {model.name.charAt(0).toUpperCase()}
          </span>
        </div>
      {/if}
    </div>
  {/if}
  
  <!-- Header -->
  <div class="{compact ? 'mb-2' : 'mb-3'}">
    <h3 class="{compact ? 'text-base' : 'text-lg'} font-semibold text-secondary-900 dark:text-dark-700 mb-1 line-clamp-1">
      {model.name}
    </h3>
    {#if !trendingMode}
      <p class="text-sm text-secondary-600 dark:text-dark-500 {compact ? 'line-clamp-1' : 'line-clamp-2'}">
        {model.summary}
      </p>
    {/if}
  </div>
  
  <!-- Author & Organization -->
  {#if !compact && !trendingMode}
    <div class="flex items-center space-x-4 mb-3 text-sm text-secondary-600 dark:text-dark-500">
      {#if model.author}
        <div class="flex items-center space-x-1">
          <User class="w-4 h-4" />
          <span>{model.author}</span>
        </div>
      {/if}
      {#if model.organization}
        <div class="flex items-center space-x-1">
          <Building class="w-4 h-4" />
          <span class="truncate">{model.organization}</span>
        </div>
      {/if}
    </div>
  {/if}
  
  <!-- Classifications -->
  {#if model.classifications && model.classifications.length > 0 && !trendingMode}
    <div class="{compact ? 'mb-2' : 'mb-3'}">
      {#each model.classifications.slice(0, compact ? 1 : 2) as classification}
        <div class="mb-1">
          <span class="tag-primary text-xs">
            {classification.path.join(' → ')}
          </span>
        </div>
      {/each}
      {#if model.classifications.length > (compact ? 1 : 2)}
        <span class="text-xs text-secondary-500 dark:text-dark-400">
          +{model.classifications.length - (compact ? 1 : 2)} 更多分类
        </span>
      {/if}
    </div>
  {/if}
  
  <!-- Base Model -->
  {#if model.base_model && !compact && !trendingMode}
    <div class="mb-3">
      <span class="tag-secondary text-xs">
        基于: {model.base_model}
      </span>
    </div>
  {/if}
  
  <!-- Tags -->
  {#if model.tags && model.tags.length > 0 && !compact && !trendingMode}
    <div class="mb-4">
      <div class="flex flex-wrap gap-1">
        {#each model.tags.slice(0, 3) as tag}
          <span class="tag-secondary text-xs">
            {tag}
          </span>
        {/each}
        {#if model.tags.length > 3}
          <span class="text-xs text-secondary-500 dark:text-dark-400">
            +{model.tags.length - 3}
          </span>
        {/if}
      </div>
    </div>
  {/if}
  
  <!-- Stats -->
  <div class="flex items-center justify-between text-sm text-secondary-500 dark:text-dark-400">
    <div class="flex items-center {compact ? 'space-x-3' : 'space-x-4'}">
      <div class="flex items-center space-x-1">
        <Eye class="w-4 h-4" />
        <span>{model.view_count || 0}</span>
      </div>
      <div class="flex items-center space-x-1">
        <Download class="w-4 h-4" />
        <span>{model.download_count || 0}</span>
      </div>
      <div class="flex items-center space-x-1">
        <Heart class="w-4 h-4" />
        <span>{model.like_count || 0}</span>
      </div>
    </div>
    
    <div class="flex items-center space-x-1">
      <Calendar class="w-4 h-4" />
      <span>{formatDate(model.created_at)}</span>
    </div>
  </div>
  

</div>

<style>
  .line-clamp-1 {
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    line-clamp: 1;
    -webkit-box-orient: vertical;
  }
  
  .line-clamp-2 {
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
  }
</style>