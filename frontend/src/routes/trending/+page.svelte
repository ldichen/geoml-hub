<script>
    import { onMount } from 'svelte';
    import { page } from '$app/stores';
    import { _ } from 'svelte-i18n';
    import { TrendingUp, Calendar, Filter, Star, Download, Eye } from 'lucide-svelte';
    import { api } from '$lib/utils/api.js';
    import { PATHS } from '$lib/utils/paths.js';
    import RepositoryCard from '$lib/components/RepositoryCard.svelte';
    import Loading from '$lib/components/Loading.svelte';
    
    let repositories = [];
    let loading = true;
    let error = '';
    
    // 筛选参数
    let period = 'week'; // day, week, month, year
    let repoType = ''; // model, dataset, space, ''
    let classificationId = null;
    
    const periods = [
        { value: 'day', label: 'time.today' },
        { value: 'week', label: 'time.this_week' },
        { value: 'month', label: 'time.this_month' },
        { value: 'year', label: 'time.this_year' }
    ];
    
    const repoTypes = [
        { value: '', label: 'common.all' },
        { value: 'model', label: 'repository.model' },
        { value: 'dataset', label: 'repository.dataset' },
        { value: 'space', label: 'repository.space' }
    ];
    
    onMount(() => {
        loadTrendingRepositories();
    });
    
    async function loadTrendingRepositories() {
        loading = true;
        error = '';
        
        try {
            const response = await api.search.trending({
                period,
                repo_type: repoType || undefined,
                classification_id: classificationId || undefined,
                limit: 20
            });
            
            repositories = response.data || response;
        } catch (err) {
            console.error('Failed to load trending repositories:', err);
            error = $_('error.network_error');
        } finally {
            loading = false;
        }
    }
    
    function handleFilterChange() {
        loadTrendingRepositories();
    }
    
    function getPeriodDisplay(period) {
        switch (period) {
            case 'day':
                return $_('time.today');
            case 'week':
                return $_('time.this_week');
            case 'month':
                return $_('time.this_month');
            case 'year':
                return $_('time.this_year');
            default:
                return period;
        }
    }
</script>

<svelte:head>
    <title>{$_('search.trending')} - GeoML-Hub</title>
    <meta name="description" content={$_('search.trending_description')} />
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <!-- 页面头部 -->
    <div class="mb-8">
        <div class="flex items-center space-x-2 mb-4">
            <TrendingUp class="w-8 h-8 text-primary-600" />
            <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
                {$_('search.trending')}
            </h1>
        </div>
        <p class="text-lg text-gray-600 dark:text-gray-400">
            {$_('search.trending_subtitle')} {getPeriodDisplay(period)}
        </p>
    </div>
    
    <!-- 筛选器 -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6 mb-6">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            <div class="flex items-center space-x-2">
                <Filter class="w-5 h-5 text-gray-400" />
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {$_('search.filters')}:
                </span>
            </div>
            
            <div class="flex flex-wrap items-center gap-4">
                <!-- 时间周期 -->
                <div class="flex items-center space-x-2">
                    <Calendar class="w-4 h-4 text-gray-400" />
                    <select
                        bind:value={period}
                        on:change={handleFilterChange}
                        class="input-sm"
                    >
                        {#each periods as periodOption}
                            <option value={periodOption.value}>
                                {$_(periodOption.label)}
                            </option>
                        {/each}
                    </select>
                </div>
                
                <!-- 仓库类型 -->
                <div class="flex items-center space-x-2">
                    <span class="text-sm text-gray-600 dark:text-gray-400">
                        {$_('repository.type')}:
                    </span>
                    <select
                        bind:value={repoType}
                        on:change={handleFilterChange}
                        class="input-sm"
                    >
                        {#each repoTypes as type}
                            <option value={type.value}>
                                {$_(type.label)}
                            </option>
                        {/each}
                    </select>
                </div>
            </div>
        </div>
    </div>
    
    <!-- 趋势仓库列表 -->
    {#if loading}
        <div class="flex justify-center py-12">
            <Loading />
        </div>
    {:else if error}
        <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <div class="flex items-center">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                    </svg>
                </div>
                <div class="ml-3">
                    <p class="text-red-800 dark:text-red-200">{error}</p>
                </div>
            </div>
        </div>
    {:else if repositories.length > 0}
        <!-- 趋势指标说明 -->
        <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
            <div class="flex items-start space-x-2">
                <TrendingUp class="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
                <div class="text-sm text-blue-700 dark:text-blue-300">
                    <p class="font-medium mb-1">{$_('search.trending_explanation')}</p>
                    <p>{$_('search.trending_metrics_hint')}</p>
                </div>
            </div>
        </div>
        
        <!-- 仓库网格 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#each repositories as repository, index}
                <div class="relative">
                    <!-- 排名标识 -->
                    <div class="absolute top-4 left-4 z-10 bg-primary-600 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
                        {index + 1}
                    </div>
                    
                    <RepositoryCard {repository} showTrendingBadge={true} />
                </div>
            {/each}
        </div>
        
        <!-- 加载更多 -->
        <div class="text-center mt-8">
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
                {$_('search.showing_top_trending')} {getPeriodDisplay(period)}
            </p>
            <a href="{PATHS.SEARCH}?sort=stars&order=desc" class="btn btn-secondary">
                {$_('search.view_all_repositories')}
            </a>
        </div>
    {:else}
        <!-- 无数据状态 -->
        <div class="text-center py-12">
            <TrendingUp class="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {$_('search.no_trending_found')}
            </h3>
            <p class="text-gray-500 dark:text-gray-400 mb-6">
                {$_('search.no_trending_hint')}
            </p>
            <div class="flex justify-center space-x-4">
                <a href={PATHS.SEARCH} class="btn btn-primary">
                    {$_('search.explore_repositories')}
                </a>
                <a href={PATHS.HOME} class="btn btn-secondary">
                    {$_('navigation.home')}
                </a>
            </div>
        </div>
    {/if}
</div>

<!-- 趋势统计面板 -->
{#if repositories.length > 0}
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                {$_('search.trending_stats')}
            </h2>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <!-- 平均星标数 -->
                <div class="text-center">
                    <div class="flex items-center justify-center w-12 h-12 bg-yellow-100 dark:bg-yellow-900/20 rounded-full mx-auto mb-2">
                        <Star class="w-6 h-6 text-yellow-600" />
                    </div>
                    <p class="text-2xl font-bold text-gray-900 dark:text-white">
                        {Math.round(repositories.reduce((sum, r) => sum + (r.stars_count || 0), 0) / repositories.length)}
                    </p>
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                        {$_('search.avg_stars')}
                    </p>
                </div>
                
                <!-- 平均下载数 -->
                <div class="text-center">
                    <div class="flex items-center justify-center w-12 h-12 bg-green-100 dark:bg-green-900/20 rounded-full mx-auto mb-2">
                        <Download class="w-6 h-6 text-green-600" />
                    </div>
                    <p class="text-2xl font-bold text-gray-900 dark:text-white">
                        {Math.round(repositories.reduce((sum, r) => sum + (r.downloads_count || 0), 0) / repositories.length)}
                    </p>
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                        {$_('search.avg_downloads')}
                    </p>
                </div>
                
                <!-- 平均浏览数 -->
                <div class="text-center">
                    <div class="flex items-center justify-center w-12 h-12 bg-blue-100 dark:bg-blue-900/20 rounded-full mx-auto mb-2">
                        <Eye class="w-6 h-6 text-blue-600" />
                    </div>
                    <p class="text-2xl font-bold text-gray-900 dark:text-white">
                        {Math.round(repositories.reduce((sum, r) => sum + (r.views_count || 0), 0) / repositories.length)}
                    </p>
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                        {$_('search.avg_views')}
                    </p>
                </div>
            </div>
        </div>
    </div>
{/if}