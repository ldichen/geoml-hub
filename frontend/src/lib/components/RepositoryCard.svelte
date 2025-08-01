<script lang="ts">
  import { Star, Download, Eye, GitFork, Calendar, Lock, ChevronRight } from 'lucide-svelte';
  import { formatDistanceToNow } from 'date-fns';
  import { zhCN } from 'date-fns/locale';
  import type { Repository, User } from '$lib/types';
  import UserAvatar from './UserAvatar.svelte';
  import SocialButton from './SocialButton.svelte';
  import { api } from '$lib/utils/api';

  export let repo: Repository;
  export let currentUser: User | null = null;
  export let showOwner: boolean = true;
  export let compact: boolean = false;

  async function handleStar() {
    if (!currentUser) return;

    try {
      if (repo.is_starred) {
        await api.unstarRepository(repo.owner?.username || '', repo.name);
        repo.is_starred = false;
        repo.stars_count -= 1;
      } else {
        await api.starRepository(repo.owner?.username || '', repo.name);
        repo.is_starred = true;
        repo.stars_count += 1;
      }
    } catch (err) {
      console.error('Error starring/unstarring repository:', err);
    }
  }

  function formatFileSize(bytes: number) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

</script>

<div class="repository-card rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 transition-all duration-200">
  <div class="flex items-start justify-between">
    <div class="flex-1 min-w-0">
      <!-- Repository Header -->
      <div class="flex items-center space-x-3 mb-2">
        {#if showOwner && repo.owner}
          <UserAvatar user={repo.owner} size="sm" />
          <span class="text-sm text-gray-600 dark:text-gray-400">
            {repo.owner.username}
          </span>
          <span class="text-gray-400 dark:text-gray-600">/</span>
        {/if}
        
        <a 
          href="/{repo.owner?.username || 'unknown'}/{repo.name}"
          class="text-lg font-semibold text-blue-600 dark:text-blue-400 hover:underline truncate"
        >
          {repo.name}
        </a>
        
        {#if repo.visibility === 'private'}
          <Lock class="h-4 w-4 text-gray-400" />
        {/if}
      </div>

      <!-- Classifications -->
      {#if repo.classification_path && repo.classification_path.length > 0}
        <div class="flex items-center space-x-1 mb-2">
          {#each repo.classification_path as classification, index}
            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200">
              {classification}
            </span>
            {#if index < repo.classification_path.length - 1}
              <ChevronRight class="h-3 w-3 text-gray-400" />
            {/if}
          {/each}
        </div>
      {/if}

      <!-- Description -->
      {#if repo.description}
        <p class="text-gray-700 dark:text-gray-300 text-sm mb-3 {compact ? 'line-clamp-2' : 'line-clamp-3'}">
          {repo.description}
        </p>
      {/if}


      <!-- Stats -->
      <div class="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
        <div class="flex items-center space-x-1">
          <Star class="h-4 w-4" />
          <span>{repo.stars_count}</span>
        </div>
        <div class="flex items-center space-x-1">
          <Download class="h-4 w-4" />
          <span>{repo.downloads_count}</span>
        </div>
        <div class="flex items-center space-x-1">
          <Eye class="h-4 w-4" />
          <span>{repo.views_count}</span>
        </div>
        {#if repo.total_size > 0}
          <div class="flex items-center space-x-1">
            <span>{formatFileSize(repo.total_size)}</span>
          </div>
        {/if}
      </div>

    </div>

    <!-- Actions and Updated Time -->
    <div class="flex flex-col items-end space-y-2 ml-4">
      {#if currentUser && repo.owner?.username !== currentUser.username}
        <SocialButton
          type="star"
          active={repo.is_starred}
          count={repo.stars_count}
          on:click={handleStar}
        />
      {/if}
      
      <!-- Updated Time -->
      <div class="flex items-center space-x-1 text-xs text-gray-500 dark:text-gray-400">
        <Calendar class="h-3 w-3" />
        <span>
          更新于 {formatDistanceToNow(new Date(repo.updated_at), { addSuffix: true, locale: zhCN })}
        </span>
      </div>
    </div>
  </div>
</div>

<style>
  .repository-card {
    background: linear-gradient(to right, var(--color-gray-50), var(--color-white));
  }

  .repository-card:hover {
    background: linear-gradient(to right, var(--color-gray-100), var(--color-gray-50));
    box-shadow: var(--tw-shadow-hover);
    cursor: pointer;
  }

  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  .line-clamp-3 {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>