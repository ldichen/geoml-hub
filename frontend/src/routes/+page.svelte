<script lang="ts">
  import { onMount } from 'svelte';
  import { Search, Plus, Star, Download, Eye, TrendingUp } from 'lucide-svelte';
  import { api } from '$lib/utils/api';
  import type { Repository, User, Classification } from '$lib/types';
  import RepositoryCard from '$lib/components/RepositoryCard.svelte';
  import SearchBar from '$lib/components/SearchBar.svelte';
  import Loading from '$lib/components/Loading.svelte';
  import ClassificationFilter from '$lib/components/ClassificationFilter.svelte';
  import { user, isAuthenticated } from '$lib/stores/auth';
  import { imagePreloader, extractAvatarUrls } from '$lib/utils/imagePreloader';

  let currentUser: User | null = null;
  let repositories: Repository[] = [];
  let featuredRepositories: Repository[] = [];
  let classifications: Classification[] = [];
  let loading = true;
  let error: string | null = null;

  let searchQuery = '';
  let selectedClassificationId: number | null = null;
  let selectedRepoType: string | null = null;
  let sortBy: string = 'updated_at';
  let sortOrder: string = 'desc';
  let activeTab: string = 'main';
  let selectedClassifications: Set<number> = new Set();
  let selectedTags: Set<string> = new Set();
  let selectedLicenses: Set<string> = new Set();
  let showAllLevel1 = false;
  let showAllLevel2 = false;
  let showAllLevel3 = false;
  let showAllTags = false;
  let showAllLicenses = false;
  
  // Pagination state
  let currentPage = 1;
  let perPage = 10;
  let totalPages = 1;
  let totalCount = 0;
  let gotoPageInput = '';
  let showGotoInput = false;
  
  // Trending sidebar state
  let trendingTab: string = 'featured';
  let trendingRepositories: Repository[] = [];
  let trendingLoading = false;

  // Define common tags and licenses
  const commonTags = [
    '深度学习', '计算机视觉', '自然语言处理', '遥感影像', '地理信息系统',
    '机器学习', '数据挖掘', '图像分割', '目标检测', '时间序列',
    '空间分析', '地图制图', '卫星数据', '地形分析', '气候建模'
  ];

  const commonLicenses = [
    'MIT', 'Apache-2.0', 'GPL-3.0', 'BSD-3-Clause', 'BSD-2-Clause',
    'LGPL-3.0', 'MPL-2.0', 'ISC', 'AGPL-3.0', 'Unlicense',
    'CC-BY-4.0', 'CC-BY-SA-4.0', 'CC0-1.0', 'WTFPL', 'Zlib'
  ];

  // Subscribe to user store
  $: currentUser = $user;

  onMount(async () => {
    await loadData();
    await loadTrendingData();
  });

  async function loadData() {
    try {
      loading = true;
      error = null;

      const [reposResponse, featuredResponse, classificationsResponse] = await Promise.all([
        api.listRepositories({
          page: currentPage,
          per_page: perPage,
          sort_by: sortBy,
          sort_order: sortOrder,
          ...(selectedClassifications.size > 0 && { classification_ids: Array.from(selectedClassifications) }),
          ...(selectedTags.size > 0 && { tags: Array.from(selectedTags).join(',') }),
          ...(selectedLicenses.size > 0 && { licenses: Array.from(selectedLicenses).join(',') }),
          ...(selectedRepoType && { repo_type: selectedRepoType }),
          ...(searchQuery && { q: searchQuery })
        }),
        api.listRepositories({
          per_page: 8,
          sort_by: 'stars_count',
          sort_order: 'desc',
          is_featured: true
        }),
        api.getClassificationTree()
      ]);

      repositories = reposResponse.items || reposResponse;
      featuredRepositories = featuredResponse.items || featuredResponse;
      classifications = classificationsResponse.classifications || classificationsResponse;
      
      // Update pagination info
      if (reposResponse.total !== undefined) {
        totalCount = reposResponse.total;
        totalPages = reposResponse.total_pages || Math.ceil(totalCount / perPage);
      } else {
        // 兼容旧API响应格式
        totalCount = repositories.length;
        totalPages = 1;
      }

      // 预加载头像图片
      const allRepos = [...repositories, ...featuredRepositories];
      const avatarUrls = extractAvatarUrls(allRepos);
      if (avatarUrls.length > 0) {
        imagePreloader.preloadBatch(avatarUrls);
      }

    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load data';
      console.error('Error loading data:', err);
    } finally {
      loading = false;
    }
  }

  async function handleSearch() {
    await loadData();
  }

  async function handleFilterChange() {
    currentPage = 1; // Reset to first page when filters change
    await loadData();
  }
  
  async function handlePageChange(page: number) {
    if (page >= 1 && page <= totalPages) {
      currentPage = page;
      await loadData();
      // Scroll to top of repository list
      document.querySelector('.repository-list')?.scrollIntoView({ behavior: 'smooth' });
    }
  }

  function handleGotoPage() {
    const page = parseInt(gotoPageInput);
    if (!isNaN(page) && page >= 1 && page <= totalPages) {
      handlePageChange(page);
      gotoPageInput = '';
      showGotoInput = false;
    }
  }

  function handleGotoKeydown(event) {
    if (event.key === 'Enter') {
      handleGotoPage();
    } else if (event.key === 'Escape') {
      gotoPageInput = '';
      showGotoInput = false;
    }
  }

  async function loadTrendingData() {
    try {
      trendingLoading = true;
      
      let sortBy = 'created_at';
      let sortOrder = 'desc';
      let isFeatures = false;
      
      // 根据选中的tab设置不同的排序方式
      switch (trendingTab) {
        case 'featured':
          sortBy = 'stars_count';
          sortOrder = 'desc';
          isFeatures = true;
          break;
        case 'trending':
          sortBy = 'views_count';
          sortOrder = 'desc';
          break;
        case 'latest':
          sortBy = 'created_at';
          sortOrder = 'desc';
          break;
        case 'recommended':
          sortBy = 'downloads_count';
          sortOrder = 'desc';
          break;
      }

      const response = await api.listRepositories({
        per_page: 10,
        sort_by: sortBy,
        sort_order: sortOrder,
        ...(isFeatures && { is_featured: true })
      });

      trendingRepositories = response.items || response;
      
      // 预加载trending部分的头像
      const trendingAvatarUrls = extractAvatarUrls(trendingRepositories);
      if (trendingAvatarUrls.length > 0) {
        imagePreloader.preloadBatch(trendingAvatarUrls);
      }
    } catch (err) {
      console.error('Error loading trending data:', err);
      trendingRepositories = [];
    } finally {
      trendingLoading = false;
    }
  }

  async function handleTrendingTabChange(newTab: string) {
    trendingTab = newTab;
    await loadTrendingData();
  }

  function handleCreateRepository() {
    if ($isAuthenticated) {
      // Redirect to create repository page
      window.location.href = '/new';
    } else {
      // Redirect to login
      window.location.href = '/login';
    }
  }

  function toggleClassification(classificationId: number) {
    if (selectedClassifications.has(classificationId)) {
      selectedClassifications.delete(classificationId);
    } else {
      selectedClassifications.add(classificationId);
    }
    selectedClassifications = selectedClassifications;
    handleFilterChange();
  }

  function resetClassifications() {
    selectedClassifications.clear();
    selectedClassifications = selectedClassifications;
    handleFilterChange();
  }

  function toggleTag(tag: string) {
    if (selectedTags.has(tag)) {
      selectedTags.delete(tag);
    } else {
      selectedTags.add(tag);
    }
    selectedTags = selectedTags;
    handleFilterChange();
  }

  function resetTags() {
    selectedTags.clear();
    selectedTags = selectedTags;
    handleFilterChange();
  }

  function toggleLicense(license: string) {
    if (selectedLicenses.has(license)) {
      selectedLicenses.delete(license);
    } else {
      selectedLicenses.add(license);
    }
    selectedLicenses = selectedLicenses;
    handleFilterChange();
  }

  function resetLicenses() {
    selectedLicenses.clear();
    selectedLicenses = selectedLicenses;
    handleFilterChange();
  }

  function getAllClassifications(classifications: Classification[], result: Classification[] = []): Classification[] {
    for (const classification of classifications) {
      result.push(classification);
      if (classification.children && classification.children.length > 0) {
        getAllClassifications(classification.children, result);
      }
    }
    return result;
  }

  $: allClassifications = getAllClassifications(classifications);
  $: level1Classifications = classifications.filter(c => c.level === 1);
  $: level2Classifications = allClassifications.filter(c => c.level === 2);
  $: level3Classifications = allClassifications.filter(c => c.level === 3);
</script>

<svelte:head>
  <title>GeoML Hub - 地理科学机器学习模型库</title>
  <meta name="description" content="为地理科学设计的机器学习模型库，发现、分享和部署地理空间AI模型" />
</svelte:head>

<div class="min-h-screen dark:bg-gray-900">
  <!-- Hero Section -->
  <div class="bg-gradient-to-r from-blue-600 to-indigo-700 dark:from-blue-800 dark:to-indigo-900">
    <div class="container py-10">
      <div class="text-center">
        <h1 class="text-4xl sm:text-5xl font-bold text-white mb-4">
          🌍 GeoML Hub
        </h1>
        <p class="text-xl text-blue-100 mb-8 max-w-3xl mx-auto">
          地理科学设计的机器学习模型库 - 发现、分享和部署地理空间AI模型
        </p>
        
        <!-- Search Bar -->
        <div class="max-w-2xl mx-auto mb-4">
          <SearchBar
            bind:value={searchQuery}
            placeholder="搜索模型、数据集、用户..."
            on:search={handleSearch}
          />
        </div>
        
      </div>
    </div>
  </div>

  <div class="container bg-white">
    <!-- Featured Repositories -->
    {#if featuredRepositories.length > 0}
      <div class="mb-12 pt-8">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
            <TrendingUp class="h-6 w-6 mr-2" />
            精选仓库
          </h2>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {#each featuredRepositories as repo (repo.id)}
            <RepositoryCard {repo} {currentUser} compact={true} />
          {/each}
        </div>
      </div>
    {/if}

    <!-- Main Content -->
    <div class="flex flex-col lg:flex-row gap-6">
      <!-- Sidebar Filters (3/10) -->
      <div class="lg:w-[25%] border-gray-100 lg:border-r pt-8 flex-shrink-0 min-h-screen sidebar-gradient-left">
        <div class="p-2">
          <!-- Tabs Navigation -->
          <div class="border-b border-gray-200 dark:border-gray-700 mb-6">
            <nav class="flex space-x-6" aria-label="Tabs">
              <button
                class="py-2 px-1 border-b-2 font-medium text-sm {activeTab === 'main' 
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
                on:click={() => activeTab = 'main'}
              >
                Main
              </button>
              <button
                class="py-2 px-1 border-b-2 font-medium text-sm {activeTab === 'class' 
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
                on:click={() => activeTab = 'class'}
              >
                Class
              </button>
              <button
                class="py-2 px-1 border-b-2 font-medium text-sm {activeTab === 'tags' 
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
                on:click={() => activeTab = 'tags'}
              >
                Tags
              </button>
              <button
                class="py-2 px-1 border-b-2 font-medium text-sm {activeTab === 'licenses' 
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
                on:click={() => activeTab = 'licenses'}
              >
                Licenses
              </button>
            </nav>
          </div>

          <!-- Tab Content -->
          {#if activeTab === 'main'}
            <!-- Classification Tags (copied from class tab) -->
            <div class="space-y-6">
              <!-- Level 1 Classifications -->
              {#if level1Classifications.length > 0}
                <div>
                  <div class="flex items-center justify-between mb-3">
                    <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">一级分类</h4>
                    {#if level1Classifications.some(c => selectedClassifications.has(c.id))}
                      <button
                        class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
                        on:click={() => {
                          level1Classifications.forEach(c => selectedClassifications.delete(c.id));
                          selectedClassifications = selectedClassifications;
                          handleFilterChange();
                        }}
                      >
                        <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                        Reset
                      </button>
                    {/if}
                  </div>
                  <div class="flex flex-wrap gap-2">
                    {#each (showAllLevel1 ? level1Classifications : level1Classifications.slice(0, 10)) as classification}
                      <button
                        class="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors border {selectedClassifications.has(classification.id) 
                          ? 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700' 
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700'}"
                        on:click={() => toggleClassification(classification.id)}
                      >
                        {classification.name}
                      </button>
                    {/each}
                    {#if level1Classifications.length > 10}
                      <button
                        class="inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                        on:click={() => showAllLevel1 = !showAllLevel1}
                      >
                        {showAllLevel1 ? '收起' : `+ ${level1Classifications.length - 10}`}
                      </button>
                    {/if}
                  </div>
                </div>
              {/if}

              <!-- Level 2 Classifications -->
              {#if level2Classifications.length > 0}
                <div>
                  <div class="flex items-center justify-between mb-3">
                    <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">二级分类</h4>
                    {#if level2Classifications.some(c => selectedClassifications.has(c.id))}
                      <button
                        class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
                        on:click={() => {
                          level2Classifications.forEach(c => selectedClassifications.delete(c.id));
                          selectedClassifications = selectedClassifications;
                          handleFilterChange();
                        }}
                      >
                        <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                        Reset
                      </button>
                    {/if}
                  </div>
                  <div class="flex flex-wrap gap-2">
                    {#each (showAllLevel2 ? level2Classifications : level2Classifications.slice(0, 10)) as classification}
                      <button
                        class="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors border {selectedClassifications.has(classification.id) 
                          ? 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700' 
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700'}"
                        on:click={() => toggleClassification(classification.id)}
                      >
                        {classification.name}
                      </button>
                    {/each}
                    {#if level2Classifications.length > 10}
                      <button
                        class="inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                        on:click={() => showAllLevel2 = !showAllLevel2}
                      >
                        {showAllLevel2 ? '收起' : `+ ${level2Classifications.length - 10}`}
                      </button>
                    {/if}
                  </div>
                </div>
              {/if}

              <!-- Level 3 Classifications -->
              {#if level3Classifications.length > 0}
                <div>
                  <div class="flex items-center justify-between mb-3">
                    <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">三级分类</h4>
                    {#if level3Classifications.some(c => selectedClassifications.has(c.id))}
                      <button
                        class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
                        on:click={() => {
                          level3Classifications.forEach(c => selectedClassifications.delete(c.id));
                          selectedClassifications = selectedClassifications;
                          handleFilterChange();
                        }}
                      >
                        <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                        Reset
                      </button>
                    {/if}
                  </div>
                  <div class="flex flex-wrap gap-2">
                    {#each (showAllLevel3 ? level3Classifications : level3Classifications.slice(0, 10)) as classification}
                      <button
                        class="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors border {selectedClassifications.has(classification.id) 
                          ? 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700' 
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700'}"
                        on:click={() => toggleClassification(classification.id)}
                      >
                        {classification.name}
                      </button>
                    {/each}
                    {#if level3Classifications.length > 10}
                      <button
                        class="inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                        on:click={() => showAllLevel3 = !showAllLevel3}
                      >
                        {showAllLevel3 ? '收起' : `+ ${level3Classifications.length - 10}`}
                      </button>
                    {/if}
                  </div>
                </div>
              {/if}
            </div>
          {:else if activeTab === 'class'}
            <!-- Classification Tags -->
            <div class="space-y-6">
              <!-- Level 1 Classifications -->
              {#if level1Classifications.length > 0}
                <div>
                  <div class="flex items-center justify-between mb-3">
                    <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">一级分类</h4>
                    {#if level1Classifications.some(c => selectedClassifications.has(c.id))}
                      <button
                        class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
                        on:click={() => {
                          level1Classifications.forEach(c => selectedClassifications.delete(c.id));
                          selectedClassifications = selectedClassifications;
                          handleFilterChange();
                        }}
                      >
                        <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                        Reset
                      </button>
                    {/if}
                  </div>
                  <div class="flex flex-wrap gap-2">
                    {#each (showAllLevel1 ? level1Classifications : level1Classifications.slice(0, 10)) as classification}
                      <button
                        class="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors border {selectedClassifications.has(classification.id) 
                          ? 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700' 
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700'}"
                        on:click={() => toggleClassification(classification.id)}
                      >
                        {classification.name}
                      </button>
                    {/each}
                    {#if level1Classifications.length > 10}
                      <button
                        class="inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                        on:click={() => showAllLevel1 = !showAllLevel1}
                      >
                        {showAllLevel1 ? '收起' : `+ ${level1Classifications.length - 10}`}
                      </button>
                    {/if}
                  </div>
                </div>
              {/if}

              <!-- Level 2 Classifications -->
              {#if level2Classifications.length > 0}
                <div>
                  <div class="flex items-center justify-between mb-3">
                    <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">二级分类</h4>
                    {#if level2Classifications.some(c => selectedClassifications.has(c.id))}
                      <button
                        class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
                        on:click={() => {
                          level2Classifications.forEach(c => selectedClassifications.delete(c.id));
                          selectedClassifications = selectedClassifications;
                          handleFilterChange();
                        }}
                      >
                        <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                        Reset
                      </button>
                    {/if}
                  </div>
                  <div class="flex flex-wrap gap-2">
                    {#each (showAllLevel2 ? level2Classifications : level2Classifications.slice(0, 10)) as classification}
                      <button
                        class="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors border {selectedClassifications.has(classification.id) 
                          ? 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700' 
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700'}"
                        on:click={() => toggleClassification(classification.id)}
                      >
                        {classification.name}
                      </button>
                    {/each}
                    {#if level2Classifications.length > 10}
                      <button
                        class="inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                        on:click={() => showAllLevel2 = !showAllLevel2}
                      >
                        {showAllLevel2 ? '收起' : `+ ${level2Classifications.length - 10}`}
                      </button>
                    {/if}
                  </div>
                </div>
              {/if}

              <!-- Level 3 Classifications -->
              {#if level3Classifications.length > 0}
                <div>
                  <div class="flex items-center justify-between mb-3">
                    <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">三级分类</h4>
                    {#if level3Classifications.some(c => selectedClassifications.has(c.id))}
                      <button
                        class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
                        on:click={() => {
                          level3Classifications.forEach(c => selectedClassifications.delete(c.id));
                          selectedClassifications = selectedClassifications;
                          handleFilterChange();
                        }}
                      >
                        <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                        Reset
                      </button>
                    {/if}
                  </div>
                  <div class="flex flex-wrap gap-2">
                    {#each (showAllLevel3 ? level3Classifications : level3Classifications.slice(0, 10)) as classification}
                      <button
                        class="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors border {selectedClassifications.has(classification.id) 
                          ? 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700' 
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700'}"
                        on:click={() => toggleClassification(classification.id)}
                      >
                        {classification.name}
                      </button>
                    {/each}
                    {#if level3Classifications.length > 10}
                      <button
                        class="inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                        on:click={() => showAllLevel3 = !showAllLevel3}
                      >
                        {showAllLevel3 ? '收起' : `+ ${level3Classifications.length - 10}`}
                      </button>
                    {/if}
                  </div>
                </div>
              {/if}
            </div>
          {:else if activeTab === 'tags'}
            <!-- Tags -->
            <div>
              <div class="flex items-center justify-between mb-3">
                <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">常见标签</h4>
                {#if selectedTags.size > 0}
                  <button
                    class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
                    on:click={resetTags}
                  >
                    <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                    </svg>
                    Reset
                  </button>
                {/if}
              </div>
              <div class="flex flex-wrap gap-2">
                {#each (showAllTags ? commonTags : commonTags.slice(0, 10)) as tag}
                  <button
                    class="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors border {selectedTags.has(tag) 
                      ? 'bg-green-100 text-green-800 border-green-300 dark:bg-green-900 dark:text-green-200 dark:border-green-700' 
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700'}"
                    on:click={() => toggleTag(tag)}
                  >
                    {tag}
                  </button>
                {/each}
                {#if commonTags.length > 10}
                  <button
                    class="inline-flex items-center px-3 py-1 text-sm font-medium text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 transition-colors"
                    on:click={() => showAllTags = !showAllTags}
                  >
                    {showAllTags ? '收起' : `+ ${commonTags.length - 10}`}
                  </button>
                {/if}
              </div>
            </div>
          {:else if activeTab === 'licenses'}
            <!-- Licenses -->
            <div>
              <div class="flex items-center justify-between mb-3">
                <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">常见许可证</h4>
                {#if selectedLicenses.size > 0}
                  <button
                    class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
                    on:click={resetLicenses}
                  >
                    <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                    </svg>
                    Reset
                  </button>
                {/if}
              </div>
              <div class="flex flex-wrap gap-2">
                {#each (showAllLicenses ? commonLicenses : commonLicenses.slice(0, 10)) as license}
                  <button
                    class="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium transition-colors border {selectedLicenses.has(license) 
                      ? 'bg-purple-100 text-purple-800 border-purple-300 dark:bg-purple-900 dark:text-purple-200 dark:border-purple-700' 
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700'}"
                    on:click={() => toggleLicense(license)}
                  >
                    {license}
                  </button>
                {/each}
                {#if commonLicenses.length > 10}
                  <button
                    class="inline-flex items-center px-3 py-1 text-sm font-medium text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 transition-colors"
                    on:click={() => showAllLicenses = !showAllLicenses}
                  >
                    {showAllLicenses ? '收起' : `+ ${commonLicenses.length - 10}`}
                  </button>
                {/if}
              </div>
            </div>
          {/if}
        </div>
      </div>

      <!-- Repository List (7/10) -->
      <div class="lg:w-[50%] pt-8 flex-1 repository-list">
        {#if loading}
          <div class="flex items-center justify-center py-12">
            <Loading size="lg" />
          </div>
        {:else if error}
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
        {:else if repositories.length > 0}
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
                仓库列表
              </h2>
              <div class="flex items-center space-x-4">
                <span class="text-sm text-gray-500 dark:text-gray-400">
                  {totalCount > 0 ? `共 ${totalCount} 个仓库` : `${repositories.length} 个仓库`}
                  {#if totalPages > 1}
                    <span class="ml-2">第 {currentPage} / {totalPages} 页</span>
                  {/if}
                </span>
                <!-- Sort Options -->
                <select
                  bind:value={sortBy}
                  on:change={handleFilterChange}
                  class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white text-sm bg-white appearance-none cursor-pointer min-w-[120px]"
                >
                  <option value="updated_at">最近更新</option>
                  <option value="created_at">最新创建</option>
                  <option value="stars_count">最多星标</option>
                  <option value="downloads_count">最多下载</option>
                  <option value="views_count">最多查看</option>
                </select>
              </div>
            </div>
            
            <div class="space-y-4">
              {#each repositories as repo (repo.id)}
                <RepositoryCard {repo} {currentUser} />
              {/each}
            </div>
            
            <!-- Enhanced Pagination -->
            {#if totalPages > 1}
              <div class="mt-8 flex flex-col items-center space-y-4">
                <!-- Main Pagination Navigation -->
                <div class="flex items-center justify-center space-x-2">
                  <!-- First Page Button -->
                  <button
                    on:click={() => handlePageChange(1)}
                    disabled={currentPage <= 1}
                    class="inline-flex items-center px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 bg-white text-gray-500 hover:bg-gray-50 hover:text-gray-700 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                    title="第一页"
                  >
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"/>
                    </svg>
                    首页
                  </button>

                  <!-- Previous Button -->
                  <button
                    on:click={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage <= 1}
                    class="inline-flex items-center px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 bg-white text-gray-500 hover:bg-gray-50 hover:text-gray-700 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                    title="上一页"
                  >
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
                    </svg>
                    上一页
                  </button>
                  
                  <!-- Page Numbers with better spacing and styling -->
                  <div class="flex items-center space-x-1">
                    {#each Array.from({length: Math.min(totalPages, 7)}, (_, i) => {
                      const startPage = Math.max(1, Math.min(currentPage - 3, totalPages - 6));
                      return startPage + i;
                    }) as pageNum}
                      {#if pageNum <= totalPages}
                        <!-- Show ellipsis before if needed -->
                        {#if pageNum === Math.max(1, Math.min(currentPage - 3, totalPages - 6)) && pageNum > 1}
                          {#if pageNum > 2}
                            <span class="px-2 py-2 text-gray-500 dark:text-gray-400">...</span>
                          {/if}
                        {/if}
                        
                        <button
                          on:click={() => handlePageChange(pageNum)}
                          class="inline-flex items-center justify-center w-10 h-10 text-sm font-semibold rounded-lg transition-all duration-200 {pageNum === currentPage 
                            ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg transform scale-110' 
                            : 'bg-white text-gray-700 border border-gray-300 hover:bg-blue-50 hover:text-blue-600 hover:border-blue-300 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700 dark:hover:text-blue-400 dark:hover:border-blue-500'}"
                        >
                          {pageNum}
                        </button>
                        
                        <!-- Show ellipsis after if needed -->
                        {#if pageNum === Math.min(totalPages, Math.max(1, Math.min(currentPage - 3, totalPages - 6)) + 6) && pageNum < totalPages}
                          {#if pageNum < totalPages - 1}
                            <span class="px-2 py-2 text-gray-500 dark:text-gray-400">...</span>
                          {/if}
                        {/if}
                      {/if}
                    {/each}
                  </div>
                  
                  <!-- Next Button -->
                  <button
                    on:click={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage >= totalPages}
                    class="inline-flex items-center px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 bg-white text-gray-500 hover:bg-gray-50 hover:text-gray-700 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                    title="下一页"
                  >
                    下一页
                    <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                    </svg>
                  </button>

                  <!-- Last Page Button -->
                  <button
                    on:click={() => handlePageChange(totalPages)}
                    disabled={currentPage >= totalPages}
                    class="inline-flex items-center px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 bg-white text-gray-500 hover:bg-gray-50 hover:text-gray-700 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                    title="最后一页"
                  >
                    末页
                    <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7"/>
                    </svg>
                  </button>
                </div>

                <!-- Page Info and Quick Jump -->
                <div class="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                  <span class="bg-gray-100 dark:bg-gray-800 px-3 py-1 rounded-full">
                    第 <span class="font-semibold text-blue-600 dark:text-blue-400">{currentPage}</span> 页 / 
                    共 <span class="font-semibold">{totalPages}</span> 页
                  </span>
                  
                  <!-- Quick Jump -->
                  <div class="flex items-center space-x-2">
                    {#if !showGotoInput}
                      <button
                        on:click={() => showGotoInput = true}
                        class="inline-flex items-center px-3 py-1 text-xs font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-md transition-colors"
                      >
                        <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 9l3 3-3 3m-6 0l3-3-3-3"/>
                        </svg>
                        跳转
                      </button>
                    {:else}
                      <div class="flex items-center space-x-2">
                        <span class="text-xs">跳转到</span>
                        <input
                          bind:value={gotoPageInput}
                          on:keydown={handleGotoKeydown}
                          placeholder="页码"
                          class="w-16 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          type="number"
                          min="1"
                          max={totalPages}
                          autofocus
                        />
                        <span class="text-xs">页</span>
                        <button
                          on:click={handleGotoPage}
                          class="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                        >
                          确定
                        </button>
                        <button
                          on:click={() => {showGotoInput = false; gotoPageInput = '';}}
                          class="px-2 py-1 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                        >
                          取消
                        </button>
                      </div>
                    {/if}
                  </div>
                </div>
              </div>
            {/if}
          </div>
        {:else}
          <div class="text-center py-12">
            <div class="text-gray-500 dark:text-gray-400">
              <Search class="h-12 w-12 mx-auto mb-4" />
              <p class="text-lg font-medium mb-2">未找到仓库</p>
              <p>尝试调整搜索条件或筛选选项</p>
            </div>
          </div>
        {/if}
      </div>
      <!-- Trending Sidebar (3/10) -->
      <div class="lg:w-[25%] border-gray-100 lg:border-l pt-8 flex-shrink-0 min-h-screen sidebar-gradient-right">
        <div class="p-2">
          <!-- Trending Title Section -->
          <div class="mb-6">
            <div class="flex items-center">
              <div class="flex items-center space-x-2">
                <TrendingUp class="h-5 w-5 text-gray-500 dark:text-gray-400" />
                <h3 class="text-xl font-semibold text-gray-900 dark:text-white">Trending</h3>
              </div>
              <span class="text-xs font-semibold text-gray-600 dark:text-gray-400 dark:bg-gray-700 px-2 py-1 ml-4">
                last 7 days
              </span>
            </div>
          </div>

          <!-- Trending Tabs Navigation -->
          <div class="border-b border-gray-200 dark:border-gray-700 mb-6">
            <nav class="flex space-x-6" aria-label="Trending Tabs">
              <button
                class="py-2 px-1 border-b-2 font-medium text-sm {trendingTab === 'featured' 
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
                on:click={() => handleTrendingTabChange('featured')}
              >
                精选
              </button>
              <button
                class="py-2 px-1 border-b-2 font-medium text-sm {trendingTab === 'trending' 
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
                on:click={() => handleTrendingTabChange('trending')}
              >
                热门
              </button>
              <button
                class="py-2 px-1 border-b-2 font-medium text-sm {trendingTab === 'latest' 
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
                on:click={() => handleTrendingTabChange('latest')}
              >
                最新
              </button>
              <button
                class="py-2 px-1 border-b-2 font-medium text-sm {trendingTab === 'recommended' 
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
                on:click={() => handleTrendingTabChange('recommended')}
              >
                推荐
              </button>
            </nav>
          </div>

          <!-- Trending Tab Content -->
          <div class="space-y-3">
            {#if trendingLoading}
              <div class="flex items-center justify-center py-8">
                <Loading size="sm" />
              </div>
            {:else if trendingRepositories.length > 0}
              {#each trendingRepositories as repo, index (repo.id)}
                <div class="group">
                  <a 
                    href="/{repo.owner?.username}/{repo.name}" 
                    class="block p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  >
                    <div class="flex items-start space-x-3">
                      <!-- Repository Icon -->
                      <div class="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                        <span class="text-xs font-medium text-blue-600 dark:text-blue-300">
                          {repo.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      
                      <!-- Repository Info -->
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center space-x-1 mb-1">
                          <span class="text-xs font-medium text-gray-500 dark:text-gray-400">
                            #{index + 1}
                          </span>
                          <span class="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {repo.owner?.username}/{repo.name}
                          </span>
                        </div>
                        
                        {#if repo.description}
                          <p class="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 mb-2">
                            {repo.description}
                          </p>
                        {/if}
                        
                        <!-- Stats -->
                        <div class="flex items-center space-x-3 text-xs text-gray-500 dark:text-gray-400">
                          {#if trendingTab === 'featured' || trendingTab === 'recommended'}
                            <div class="flex items-center space-x-1">
                              <Star class="h-3 w-3" />
                              <span>{repo.stars_count || 0}</span>
                            </div>
                          {/if}
                          {#if trendingTab === 'trending'}
                            <div class="flex items-center space-x-1">
                              <Eye class="h-3 w-3" />
                              <span>{repo.views_count || 0}</span>
                            </div>
                          {/if}
                          {#if trendingTab === 'recommended'}
                            <div class="flex items-center space-x-1">
                              <Download class="h-3 w-3" />
                              <span>{repo.downloads_count || 0}</span>
                            </div>
                          {/if}
                          <span>•</span>
                          <span>about 16 hours ago</span>
                        </div>
                      </div>
                    </div>
                  </a>
                </div>
              {/each}
            {:else}
              <div class="text-center py-8">
                <div class="text-gray-400 mb-2">
                  {#if trendingTab === 'featured'}
                    <TrendingUp class="h-8 w-8 mx-auto" />
                  {:else if trendingTab === 'trending'}
                    <Eye class="h-8 w-8 mx-auto" />
                  {:else if trendingTab === 'latest'}
                    <Plus class="h-8 w-8 mx-auto" />
                  {:else if trendingTab === 'recommended'}
                    <Star class="h-8 w-8 mx-auto" />
                  {/if}
                </div>
                <p class="text-sm text-gray-500 dark:text-gray-400">暂无数据</p>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .bg-gradient-to-r {
    background: linear-gradient(to right, var(--tw-gradient-stops));
  }
  
  .line-clamp-2 {
    overflow: hidden;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
  }
</style>