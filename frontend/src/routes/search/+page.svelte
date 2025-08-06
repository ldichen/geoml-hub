<script>
    import { onMount } from 'svelte';
    import { page } from '$app/stores';
    import { goto } from '$app/navigation';
    import { _ } from 'svelte-i18n';
    import { Search, Filter, Grid, List, SortAsc, SortDesc } from 'lucide-svelte';
    import { api } from '$lib/utils/api.js';
    import { user as currentUser } from '$lib/stores/auth.js';
    import RepositoryCard from '$lib/components/RepositoryCard.svelte';
    import UserAvatar from '$lib/components/UserAvatar.svelte';
    import Loading from '$lib/components/Loading.svelte';
    import Pagination from '$lib/components/Pagination.svelte';
    
    let searchQuery = '';
    let searchType = 'repositories'; // repositories, users, all
    let repositories = [];
    let users = [];
    let loading = false;
    let error = '';
    let totalResults = 0;
    let currentPage = 1;
    let pageSize = 20;
    let viewMode = 'grid'; // grid, list
    
    // 筛选参数
    let filters = {
        repo_type: '', // model, dataset, space
        classification_id: null,
        tags: '',
        verified_only: false,
        sort_by: 'relevance',
        order: 'desc'
    };
    
    // 从URL参数初始化搜索
    $: if ($page.url.searchParams.get('q')) {
        searchQuery = $page.url.searchParams.get('q') || '';
        searchType = $page.url.searchParams.get('type') || 'repositories';
        filters.repo_type = $page.url.searchParams.get('repo_type') || '';
        filters.sort_by = $page.url.searchParams.get('sort') || 'relevance';
        filters.order = $page.url.searchParams.get('order') || 'desc';
        
        if (searchQuery) {
            performSearch();
        }
    }
    
    onMount(() => {
        if (searchQuery) {
            performSearch();
        }
    });
    
    async function performSearch() {
        if (!searchQuery.trim()) return;
        
        loading = true;
        error = '';
        
        try {
            if (searchType === 'repositories' || searchType === 'all') {
                const repoResponse = await api.listRepositories({
                    q: searchQuery,
                    repo_type: filters.repo_type || undefined,
                    classification_id: filters.classification_id || undefined,
                    tags: filters.tags || undefined,
                    sort_by: filters.sort_by,
                    sort_order: filters.order,
                    page: currentPage,
                    per_page: pageSize
                });
                repositories = repoResponse.items || repoResponse;
                totalResults = repoResponse.total || repositories.length;
            }
            
            if (searchType === 'users' || searchType === 'all') {
                const userResponse = await api.getUsers({
                    q: searchQuery,
                    verified_only: filters.verified_only,
                    sort_by: filters.sort_by === 'relevance' ? 'relevance' : 'created_at',
                    sort_order: filters.order,
                    page: currentPage,
                    per_page: pageSize
                });
                users = userResponse.items || userResponse;
            }
            
        } catch (err) {
            console.error('Search failed:', err);
            error = '网络错误，请稍后重试';
        } finally {
            loading = false;
        }
    }
    
    function handleSearch() {
        currentPage = 1;
        updateURL();
        performSearch();
    }
    
    function updateURL() {
        const params = new URLSearchParams();
        params.set('q', searchQuery);
        params.set('type', searchType);
        if (filters.repo_type) params.set('repo_type', filters.repo_type);
        if (filters.sort_by !== 'relevance') params.set('sort', filters.sort_by);
        if (filters.order !== 'desc') params.set('order', filters.order);
        
        goto(`/search?${params.toString()}`, { replaceState: true });
    }
    
    function handleFilterChange() {
        currentPage = 1;
        updateURL();
        performSearch();
    }
    
    function handlePageChange(event) {
        currentPage = event.detail;
        performSearch();
    }
    
    const repoTypes = [
        { value: '', label: '所有类型' },
        { value: 'model', label: '模型' },
        { value: 'dataset', label: '数据集' },
        { value: 'space', label: '空间' }
    ];
    
    const sortOptions = [
        { value: 'relevance', label: '相关度' },
        { value: 'updated_at', label: '更新时间' },
        { value: 'created_at', label: '创建时间' },
        { value: 'stars_count', label: '星标数' },
        { value: 'downloads_count', label: '下载数' }
    ];
</script>

<svelte:head>
    <title>{$_('search.search')} - GeoML-Hub</title>
    <meta name="description" content={$_('search.search_description')} />
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <!-- 搜索栏 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <form on:submit|preventDefault={handleSearch} class="space-y-4">
            <!-- 主搜索输入 -->
            <div class="flex space-x-4">
                <div class="flex-1">
                    <label for="search" class="sr-only">{$_('search.search')}</label>
                    <div class="relative">
                        <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Search class="h-5 w-5 text-gray-400" />
                        </div>
                        <input
                            id="search"
                            type="text"
                            bind:value={searchQuery}
                            placeholder={$_('search.search_placeholder')}
                            class="input pl-10 w-full"
                        />
                    </div>
                </div>
                <button type="submit" class="btn btn-primary">
                    {$_('search.search')}
                </button>
            </div>
            
            <!-- 搜索类型选择 -->
            <div class="flex space-x-4">
                <div class="flex space-x-2">
                    {#each ['repositories', 'users', 'all'] as type}
                        <label class="flex items-center">
                            <input
                                type="radio"
                                bind:group={searchType}
                                value={type}
                                on:change={handleFilterChange}
                                class="form-radio h-4 w-4 text-primary-600"
                            />
                            <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">
                                {$_(`search.${type}`)}
                            </span>
                        </label>
                    {/each}
                </div>
            </div>
        </form>
    </div>
    
    <!-- 筛选器和视图控制 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4 mb-6">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            <!-- 筛选器 -->
            <div class="flex flex-wrap items-center space-x-4">
                {#if searchType === 'repositories' || searchType === 'all'}
                    <!-- 仓库类型筛选 -->
                    <div class="flex items-center space-x-2">
                        <Filter class="h-4 w-4 text-gray-400" />
                        <select
                            bind:value={filters.repo_type}
                            on:change={handleFilterChange}
                            class="input-sm"
                        >
                            {#each repoTypes as type}
                                <option value={type.value}>{type.label}</option>
                            {/each}
                        </select>
                    </div>
                {/if}
                
                {#if searchType === 'users' || searchType === 'all'}
                    <!-- 已验证用户筛选 -->
                    <label class="flex items-center">
                        <input
                            type="checkbox"
                            bind:checked={filters.verified_only}
                            on:change={handleFilterChange}
                            class="form-checkbox h-4 w-4 text-primary-600"
                        />
                        <span class="ml-2 text-sm text-gray-700 dark:text-gray-300">
                            {$_('user.verified_only')}
                        </span>
                    </label>
                {/if}
                
                <!-- 排序 -->
                <div class="flex items-center space-x-2">
                    <select
                        bind:value={filters.sort_by}
                        on:change={handleFilterChange}
                        class="input-sm"
                    >
                        {#each sortOptions as option}
                            <option value={option.value}>{option.label}</option>
                        {/each}
                    </select>
                    
                    <button
                        on:click={() => {
                            filters.order = filters.order === 'desc' ? 'asc' : 'desc';
                            handleFilterChange();
                        }}
                        class="btn btn-sm btn-secondary"
                    >
                        {#if filters.order === 'desc'}
                            <SortDesc class="h-4 w-4" />
                        {:else}
                            <SortAsc class="h-4 w-4" />
                        {/if}
                    </button>
                </div>
            </div>
            
            <!-- 视图模式 -->
            <div class="flex items-center space-x-2">
                <button
                    on:click={() => viewMode = 'grid'}
                    class="p-2 rounded {viewMode === 'grid' ? 'bg-primary-100 text-primary-600' : 'text-gray-400 hover:text-gray-600'}"
                >
                    <Grid class="h-4 w-4" />
                </button>
                <button
                    on:click={() => viewMode = 'list'}
                    class="p-2 rounded {viewMode === 'list' ? 'bg-primary-100 text-primary-600' : 'text-gray-400 hover:text-gray-600'}"
                >
                    <List class="h-4 w-4" />
                </button>
            </div>
        </div>
    </div>
    
    <!-- 搜索结果 -->
    {#if loading}
        <div class="flex justify-center py-12">
            <Loading />
        </div>
    {:else if error}
        <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <p class="text-red-800 dark:text-red-200">{error}</p>
        </div>
    {:else if searchQuery}
        <!-- 结果统计 -->
        <div class="mb-6">
            <p class="text-sm text-gray-600 dark:text-gray-400">
                {#if searchType === 'repositories' || searchType === 'all'}
                    {$_('search.found')} {totalResults} {$_('search.repositories')}
                {/if}
                {#if searchType === 'users' || searchType === 'all'}
                    {users.length} {$_('search.users')}
                {/if}
                {#if searchQuery}
                    {$_('search.for')} "{searchQuery}"
                {/if}
            </p>
        </div>
        
        <!-- 仓库结果 -->
        {#if (searchType === 'repositories' || searchType === 'all') && repositories.length > 0}
            <div class="mb-8">
                <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    {$_('search.repositories')}
                </h2>
                
                {#if viewMode === 'grid'}
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {#each repositories as repository}
                            <RepositoryCard repo={repository} currentUser={$currentUser} compact={true} />
                        {/each}
                    </div>
                {:else}
                    <div class="space-y-4">
                        {#each repositories as repository}
                            <RepositoryCard repo={repository} currentUser={$currentUser} />
                        {/each}
                    </div>
                {/if}
            </div>
        {/if}
        
        <!-- 用户结果 -->
        {#if (searchType === 'users' || searchType === 'all') && users.length > 0}
            <div class="mb-8">
                <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    {$_('search.users')}
                </h2>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {#each users as user}
                        <a href="/{user.username}" class="block">
                            <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow">
                                <div class="flex items-center space-x-4">
                                    <UserAvatar {user} size="lg" />
                                    <div class="flex-1 min-w-0">
                                        <h3 class="text-lg font-semibold text-gray-900 dark:text-white truncate">
                                            {user.username}
                                        </h3>
                                        {#if user.full_name}
                                            <p class="text-sm text-gray-600 dark:text-gray-400 truncate">
                                                {user.full_name}
                                            </p>
                                        {/if}
                                        {#if user.bio}
                                            <p class="text-sm text-gray-500 dark:text-gray-400 mt-2 line-clamp-2">
                                                {user.bio}
                                            </p>
                                        {/if}
                                        <div class="flex items-center space-x-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                                            <span>{user.repositories_count || 0} {$_('user.repositories')}</span>
                                            <span>{user.followers_count || 0} {$_('user.followers')}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </a>
                    {/each}
                </div>
            </div>
        {/if}
        
        <!-- 无结果 -->
        {#if repositories.length === 0 && users.length === 0}
            <div class="text-center py-12">
                <Search class="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    {$_('search.no_results')}
                </h3>
                <p class="text-gray-500 dark:text-gray-400">
                    {$_('search.try_different_keywords')}
                </p>
            </div>
        {/if}
        
        <!-- 分页 -->
        {#if totalResults > pageSize}
            <div class="mt-8">
                <Pagination
                    current={currentPage}
                    total={Math.ceil(totalResults / pageSize)}
                    on:change={handlePageChange}
                />
            </div>
        {/if}
    {:else}
        <!-- 默认状态 -->
        <div class="text-center py-12">
            <Search class="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                {$_('search.search_models_datasets')}
            </h2>
            <p class="text-gray-500 dark:text-gray-400">
                {$_('search.search_hint')}
            </p>
        </div>
    {/if}
</div>