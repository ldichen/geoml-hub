<script lang="ts">
  import { onMount } from 'svelte';
  import { Star, Users, GitFork, Download, Calendar, MapPin, Globe, Mail, HardDrive, Folder, File, Upload, Search } from 'lucide-svelte';
  import { api } from '$lib/utils/api';
  import type { User, UserStats, Repository } from '$lib/types';
  import RepositoryCard from './RepositoryCard.svelte';
  import SocialButton from './SocialButton.svelte';
  import UserAvatar from './UserAvatar.svelte';
  import Loading from './Loading.svelte';
  import PersonalFileManager from './PersonalFileManager.svelte';

  export let username: string;
  export let currentUser: User | null = null;

  let user: User | null = null;
  let userStats: UserStats | null = null;
  let repositories: Repository[] = [];
  let starredRepositories: Repository[] = [];
  let userStorage: any = null;
  let personalFiles: any = null;
  let personalSpaceStats: any = null;
  let loading = true;
  let error: string | null = null;
  let activeTab = 'repositories';
  let isFollowing = false;
  let starredLoading = false;

  onMount(async () => {
    await loadUserData();
  });

  async function loadUserData() {
    try {
      loading = true;
      error = null;

      const requests = [
        api.getUserByUsername(username),
        api.getUserStatsByUsername(username),
        api.getUserRepositoriesByUsername(username, { per_page: 20 })
      ];

      // Only fetch storage info if viewing own profile or user has permissions
      if (currentUser && (currentUser.username === username || currentUser.is_admin)) {
        requests.push(api.getUserStorage(username));
        requests.push(loadPersonalSpaceStats(username));
      }

      const responses = await Promise.all(requests);
      
      let userResponse, statsResponse, reposResponse, storageResponse, personalStatsResponse;
      
      if (currentUser && (currentUser.username === username || currentUser.is_admin)) {
        [userResponse, statsResponse, reposResponse, storageResponse, personalStatsResponse] = responses;
        userStorage = storageResponse || null;
        personalSpaceStats = personalStatsResponse || null;
      } else {
        [userResponse, statsResponse, reposResponse] = responses;
      }

      user = userResponse;
      userStats = statsResponse;
      repositories = reposResponse.items || reposResponse;
      
      // Check if current user is following this user
      if (currentUser && currentUser.username !== username) {
        await checkFollowStatus();
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load user data';
      console.error('Error loading user data:', err);
    } finally {
      loading = false;
    }
  }

  async function checkFollowStatus() {
    if (!currentUser) return;
    
    try {
      // 检查当前用户是否关注目标用户
      const followingResponse = await api.getUserFollowing(currentUser.username, { per_page: 1000 });
      const followingList = followingResponse.items || followingResponse;
      isFollowing = followingList.some(follow => follow.following?.username === username || follow.username === username);
    } catch (err) {
      console.error('Error checking follow status:', err);
      isFollowing = false;
    }
  }

  async function loadStarredRepositories() {
    if (starredRepositories.length > 0) return; // Already loaded
    
    try {
      starredLoading = true;
      const response = await api.getUserStarredRepositories(username, { per_page: 20 });
      starredRepositories = response.items || response;
    } catch (err) {
      console.error('Error loading starred repositories:', err);
      starredRepositories = [];
    } finally {
      starredLoading = false;
    }
  }

  async function handleFollow() {
    if (!user || !currentUser) return;

    try {
      if (isFollowing) {
        await api.unfollowUserByUsername(username);
        isFollowing = false;
        user.followers_count -= 1;
      } else {
        await api.followUserByUsername(username);
        isFollowing = true;
        user.followers_count += 1;
      }
    } catch (err) {
      console.error('Error following/unfollowing user:', err);
    }
  }

  async function loadPersonalSpaceStats(username: string) {
    try {
      const response = await fetch(`/api/personal-files/${username}/stats`, {
        credentials: 'include'
      });
      if (response.ok) {
        return await response.json();
      }
    } catch (err) {
      console.error('Error loading personal space stats:', err);
    }
    return null;
  }

  async function loadPersonalFiles(username: string, path: string = '/') {
    try {
      const response = await fetch(`/api/personal-files/${username}/browse?path=${encodeURIComponent(path)}`, {
        credentials: 'include'
      });
      if (response.ok) {
        return await response.json();
      }
    } catch (err) {
      console.error('Error loading personal files:', err);
    }
    return null;
  }

  function formatDate(dateString: string) {
    return new Date(dateString).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  function formatFileSize(bytes: number) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  {#if loading}
    <div class="flex items-center justify-center py-12">
      <Loading size="lg" />
    </div>
  {:else if error}
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800 dark:text-red-200">
              加载失败
            </h3>
            <p class="mt-1 text-sm text-red-700 dark:text-red-300">
              {error}
            </p>
          </div>
        </div>
      </div>
    </div>
  {:else if user}
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- User Header -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 mb-6">
        <div class="p-6">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div class="flex items-center space-x-4">
              <UserAvatar {user} size="xl" />
              <div>
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
                  {user.full_name || user.username}
                </h1>
                <p class="text-gray-600 dark:text-gray-300">@{user.username}</p>
                {#if user.bio}
                  <p class="mt-2 text-gray-700 dark:text-gray-300">{user.bio}</p>
                {/if}
              </div>
            </div>
            
            <div class="mt-4 sm:mt-0 flex items-center space-x-3">
              {#if currentUser && currentUser.username !== user.username}
                <SocialButton
                  type="follow"
                  active={isFollowing}
                  on:click={handleFollow}
                />
              {/if}
            </div>
          </div>

          <!-- User Meta -->
          <div class="mt-4 flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
            {#if user.location}
              <div class="flex items-center space-x-1">
                <MapPin class="h-4 w-4" />
                <span>{user.location}</span>
              </div>
            {/if}
            {#if user.website}
              <div class="flex items-center space-x-1">
                <Globe class="h-4 w-4" />
                <a href={user.website} target="_blank" rel="noopener noreferrer" 
                   class="text-blue-600 dark:text-blue-400 hover:underline">
                  {user.website}
                </a>
              </div>
            {/if}
            <div class="flex items-center space-x-1">
              <Calendar class="h-4 w-4" />
              <span>加入于 {formatDate(user.created_at)}</span>
            </div>
          </div>

          <!-- Stats -->
          <div class="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="text-center">
              <div class="text-2xl font-bold text-gray-900 dark:text-white">
                {user.public_repos_count}
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400">仓库</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-gray-900 dark:text-white">
                {user.followers_count}
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400">关注者</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-gray-900 dark:text-white">
                {user.following_count}
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400">关注中</div>
            </div>
            {#if userStats && userStats.repositories}
              <div class="text-center">
                <div class="text-2xl font-bold text-gray-900 dark:text-white">
                  {userStats.repositories.total_stars || 0}
                </div>
                <div class="text-sm text-gray-600 dark:text-gray-400">获得星标</div>
              </div>
            {/if}
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div class="border-b border-gray-200 dark:border-gray-700">
          <nav class="flex space-x-8 px-6" aria-label="Tabs">
            <button
              class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'repositories' 
                ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
              on:click={() => activeTab = 'repositories'}
            >
              仓库 ({user.public_repos_count})
            </button>
            <button
              class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'stars' 
                ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
              on:click={() => {
                activeTab = 'stars';
                loadStarredRepositories();
              }}
            >
              星标仓库
            </button>
            <button
              class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'following' 
                ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
              on:click={() => activeTab = 'following'}
            >
              关注中 ({user.following_count})
            </button>
            {#if currentUser?.username === username || currentUser?.is_admin}
              <button
                class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'personal-files' 
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
                on:click={() => activeTab = 'personal-files'}
              >
                <HardDrive class="h-4 w-4 inline mr-1" />
                个人文件
              </button>
              {#if userStorage}
                <button
                  class="py-4 px-1 border-b-2 font-medium text-sm {activeTab === 'storage' 
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
                  on:click={() => activeTab = 'storage'}
                >
                  <HardDrive class="h-4 w-4 inline mr-1" />
                  存储空间
                </button>
              {/if}
            {/if}
          </nav>
        </div>

        <div class="p-6">
          {#if activeTab === 'repositories'}
            {#if repositories.length > 0}
              <div class="grid gap-4">
                {#each repositories as repo}
                  <RepositoryCard {repo} {currentUser} />
                {/each}
              </div>
            {:else}
              <div class="text-center py-12">
                <div class="text-gray-500 dark:text-gray-400">
                  <GitFork class="h-12 w-12 mx-auto mb-4" />
                  <p>该用户还没有公开仓库</p>
                </div>
              </div>
            {/if}
          {:else if activeTab === 'stars'}
            {#if starredLoading}
              <div class="flex items-center justify-center py-12">
                <Loading size="lg" />
              </div>
            {:else if starredRepositories.length > 0}
              <div class="grid gap-4">
                {#each starredRepositories as repo}
                  <RepositoryCard {repo} {currentUser} />
                {/each}
              </div>
            {:else}
              <div class="text-center py-12">
                <div class="text-gray-500 dark:text-gray-400">
                  <Star class="h-12 w-12 mx-auto mb-4" />
                  <p>
                    {currentUser && currentUser.username === username 
                      ? '你还没有星标任何仓库' 
                      : '该用户还没有星标任何仓库'}
                  </p>
                </div>
              </div>
            {/if}
          {:else if activeTab === 'following'}
            <div class="text-center py-12">
              <div class="text-gray-500 dark:text-gray-400">
                <Users class="h-12 w-12 mx-auto mb-4" />
                <p>关注列表功能开发中...</p>
              </div>
            </div>
          {:else if activeTab === 'personal-files'}
            <!-- Personal Files Space -->
            <PersonalFileManager {username} {currentUser} />
          {:else if activeTab === 'storage' && userStorage}
            <!-- Storage Management -->
            <div class="space-y-6">
              <!-- Storage Overview -->
              <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
                <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">存储概览</h3>
                
                <!-- Storage Usage Bar -->
                <div class="mb-4">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                      已使用: {formatFileSize(userStorage.storage_used)} / {formatFileSize(userStorage.storage_quota)}
                    </span>
                    <span class="text-sm text-gray-500 dark:text-gray-400">
                      {userStorage.storage_usage_percentage.toFixed(1)}%
                    </span>
                  </div>
                  <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div 
                      class="h-2 rounded-full {userStorage.storage_usage_percentage > 90 ? 'bg-red-600' : userStorage.storage_usage_percentage > 70 ? 'bg-yellow-500' : 'bg-blue-600'}"
                      style="width: {Math.min(userStorage.storage_usage_percentage, 100)}%"
                    ></div>
                  </div>
                </div>

                <!-- Storage Stats -->
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div class="text-center">
                    <div class="text-xl font-bold text-gray-900 dark:text-white">
                      {userStorage.total_repositories || 0}
                    </div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">仓库数量</div>
                  </div>
                  <div class="text-center">
                    <div class="text-xl font-bold text-gray-900 dark:text-white">
                      {userStorage.total_files || 0}
                    </div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">文件数量</div>
                  </div>
                  <div class="text-center">
                    <div class="text-xl font-bold text-gray-900 dark:text-white">
                      {formatFileSize(userStorage.storage_quota - userStorage.storage_used)}
                    </div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">剩余空间</div>
                  </div>
                </div>
              </div>

              <!-- Storage Breakdown -->
              {#if userStorage.storage_breakdown}
                <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                  <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">按文件类型统计</h3>
                  <div class="space-y-3">
                    {#each Object.entries(userStorage.storage_breakdown) as [fileType, data]}
                      <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                          <div class="w-3 h-3 bg-blue-500 rounded-full"></div>
                          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                            {fileType === 'other' ? '其他' : fileType.toUpperCase()}
                          </span>
                        </div>
                        <div class="text-right">
                          <div class="text-sm font-medium text-gray-900 dark:text-white">
                            {formatFileSize(data?.total_size || 0)}
                          </div>
                          <div class="text-xs text-gray-500 dark:text-gray-400">
                            {data?.count || 0} 个文件
                          </div>
                        </div>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}

              <!-- Largest Repositories -->
              {#if userStorage.largest_repositories && userStorage.largest_repositories.length > 0}
                <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                  <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">占用空间最大的仓库</h3>
                  <div class="space-y-3">
                    {#each userStorage.largest_repositories as repo}
                      <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                        <div>
                          <div class="font-medium text-gray-900 dark:text-white">
                            {repo.name}
                          </div>
                          <div class="text-sm text-gray-600 dark:text-gray-400">
                            {repo.type} • {repo.files} 个文件
                          </div>
                        </div>
                        <div class="text-sm font-medium text-gray-900 dark:text-white">
                          {formatFileSize(repo.size)}
                        </div>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .bg-gray-50 {
    background-color: #f9fafb;
  }
</style>