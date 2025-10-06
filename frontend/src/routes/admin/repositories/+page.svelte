<script>
    import { onMount } from 'svelte';
    import { api } from '$lib/utils/api.js';

    let repositories = [];
    let stats = null;
    let loading = true;
    let error = null;
    let searchTerm = '';
    let statusFilter = 'all';
    let typeFilter = 'all';
    let visibilityFilter = 'all';
    let sortBy = 'created';
    let sortOrder = 'desc';
    let currentPage = 1;
    let pageSize = 20;
    let totalRepositories = 0;
    let selectedRepo = null;
    let showRepoModal = false;
    let showDeleteModal = false;
    let modalLoading = false;
    let deleteConfirmText = '';

    onMount(async () => {
        await Promise.all([loadRepositories(), loadStats()]);
    });

    async function loadRepositories() {
        try {
            loading = true;
            const params = {
                skip: (currentPage - 1) * pageSize,
                limit: pageSize,
                search: searchTerm || undefined,
                is_active: statusFilter !== 'all' ? (statusFilter === 'active') : undefined,
                repo_type: typeFilter !== 'all' ? typeFilter : undefined,
                visibility: visibilityFilter !== 'all' ? visibilityFilter : undefined,
                sort_by: sortBy,
                order: sortOrder
            };

            const response = await api.getAdminRepositories(params);
            repositories = response.repositories || [];
            totalRepositories = response.total || 0;
        } catch (err) {
            error = err.message;
        } finally {
            loading = false;
        }
    }

    async function loadStats() {
        try {
            const response = await api.getAdminRepositoryStats();
            stats = response;
        } catch (err) {
            console.error('Failed to load stats:', err);
        }
    }

    async function handleSearch() {
        currentPage = 1;
        await loadRepositories();
    }

    async function handleSort(field) {
        if (sortBy === field) {
            sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            sortBy = field;
            sortOrder = 'desc';
        }
        currentPage = 1;
        await loadRepositories();
    }

    async function handleFilter() {
        currentPage = 1;
        await loadRepositories();
    }

    async function openRepoModal(repo) {
        selectedRepo = repo;
        showRepoModal = true;
    }

    async function updateRepositoryStatus(repoId, field, value) {
        try {
            modalLoading = true;
            await api.updateAdminRepositoryStatus(repoId, { [field]: value });
            
            // Update local data
            const repoIndex = repositories.findIndex(r => r.id === repoId);
            if (repoIndex !== -1) {
                repositories[repoIndex] = { ...repositories[repoIndex], [field]: value };
            }
            
            if (selectedRepo && selectedRepo.id === repoId) {
                selectedRepo = { ...selectedRepo, [field]: value };
            }
            
            showRepoModal = false;
            await loadStats(); // Refresh stats
        } catch (err) {
            error = err.message;
        } finally {
            modalLoading = false;
        }
    }

    async function restoreRepository(repoId) {
        try {
            modalLoading = true;
            await api.restoreAdminRepository(repoId);
            
            // Update local data
            const repoIndex = repositories.findIndex(r => r.id === repoId);
            if (repoIndex !== -1) {
                repositories[repoIndex] = { ...repositories[repoIndex], is_active: true };
            }
            
            showRepoModal = false;
            await loadStats(); // Refresh stats
        } catch (err) {
            error = err.message;
        } finally {
            modalLoading = false;
        }
    }

    async function openDeleteModal(repo) {
        selectedRepo = repo;
        deleteConfirmText = '';
        showDeleteModal = true;
    }

    async function hardDeleteRepository() {
        if (deleteConfirmText !== 'DELETE') {
            error = '请输入 DELETE 确认删除';
            return;
        }

        try {
            modalLoading = true;
            await api.hardDeleteAdminRepository(selectedRepo.id, true);
            
            // Remove from local data
            repositories = repositories.filter(r => r.id !== selectedRepo.id);
            totalRepositories--;
            
            showDeleteModal = false;
            selectedRepo = null;
            await loadStats(); // Refresh stats
        } catch (err) {
            error = err.message;
        } finally {
            modalLoading = false;
        }
    }

    function formatDate(dateString) {
        return new Date(dateString).toLocaleString();
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function getStatusBadge(repo) {
        if (!repo.is_active) return 'bg-red-100 text-red-800';
        if (repo.is_featured) return 'bg-purple-100 text-purple-800';
        if (repo.visibility === 'private') return 'bg-yellow-100 text-yellow-800';
        return 'bg-green-100 text-green-800';
    }

    function getStatusText(repo) {
        if (!repo.is_active) return '已删除';
        if (repo.is_featured) return '推荐';
        if (repo.visibility === 'private') return '私有';
        return '正常';
    }

    function getTypeIcon(type) {
        switch (type) {
            case 'model': return '🤖';
            case 'dataset': return '📊';
            case 'space': return '🚀';
            default: return '📁';
        }
    }

    $: totalPages = Math.ceil(totalRepositories / pageSize);
    $: canDelete = selectedRepo && deleteConfirmText === 'DELETE';
</script>

<div class="space-y-6">
    <div class="flex justify-between items-center">
        <h1 class="text-3xl font-bold text-gray-900">仓库管理</h1>
        <button 
            on:click={() => Promise.all([loadRepositories(), loadStats()])}
            class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
        >
            刷新
        </button>
    </div>

    <!-- 统计信息 -->
    {#if stats}
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="bg-white rounded-lg shadow p-4">
                <div class="flex items-center">
                    <div class="p-2 bg-blue-100 rounded-lg">
                        <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                        </svg>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm font-medium text-gray-500">总仓库数</p>
                        <p class="text-2xl font-semibold text-gray-900">{stats.overview?.total || 0}</p>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow p-4">
                <div class="flex items-center">
                    <div class="p-2 bg-green-100 rounded-lg">
                        <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm font-medium text-gray-500">活跃仓库</p>
                        <p class="text-2xl font-semibold text-gray-900">{stats.overview?.active || 0}</p>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow p-4">
                <div class="flex items-center">
                    <div class="p-2 bg-purple-100 rounded-lg">
                        <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"></path>
                        </svg>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm font-medium text-gray-500">推荐仓库</p>
                        <p class="text-2xl font-semibold text-gray-900">{stats.overview?.featured || 0}</p>
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow p-4">
                <div class="flex items-center">
                    <div class="p-2 bg-red-100 rounded-lg">
                        <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm font-medium text-gray-500">已删除</p>
                        <p class="text-2xl font-semibold text-gray-900">{stats.overview?.deleted || 0}</p>
                    </div>
                </div>
            </div>
        </div>
    {/if}

    <!-- 搜索和过滤 -->
    <div class="bg-white rounded-lg shadow p-6">
        <div class="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div class="md:col-span-2">
                <label for="search-input" class="block text-sm font-medium text-gray-700 mb-2">搜索仓库</label>
                <div class="flex">
                    <input
                        id="search-input"
                        type="text"
                        bind:value={searchTerm}
                        placeholder="搜索仓库名称、描述或完整名称..."
                        class="flex-1 border border-gray-300 rounded-l-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        on:keydown={(e) => e.key === 'Enter' && handleSearch()}
                    />
                    <button
                        on:click={handleSearch}
                        class="bg-blue-500 text-white px-4 py-2 rounded-r-md hover:bg-blue-600 transition-colors"
                    >
                        搜索
                    </button>
                </div>
            </div>
            
            <div>
                <label for="status-filter" class="block text-sm font-medium text-gray-700 mb-2">状态过滤</label>
                <select 
                    id="status-filter"
                    bind:value={statusFilter}
                    on:change={handleFilter}
                    class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="all">全部状态</option>
                    <option value="active">活跃仓库</option>
                    <option value="deleted">已删除</option>
                    <option value="recommended">推荐仓库</option>
                </select>
            </div>
            
            <div>
                <label for="type-filter" class="block text-sm font-medium text-gray-700 mb-2">类型过滤</label>
                <select 
                    id="type-filter"
                    bind:value={typeFilter}
                    on:change={handleFilter}
                    class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="all">全部类型</option>
                    <option value="model">模型</option>
                    <option value="dataset">数据集</option>
                    <option value="space">空间</option>
                </select>
            </div>
            
            <div>
                <label for="visibility-filter" class="block text-sm font-medium text-gray-700 mb-2">可见性</label>
                <select 
                    id="visibility-filter"
                    bind:value={visibilityFilter}
                    on:change={handleFilter}
                    class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="all">全部</option>
                    <option value="public">公开</option>
                    <option value="private">私有</option>
                </select>
            </div>
        </div>
    </div>

    {#if loading}
        <div class="flex justify-center items-center h-64">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
    {:else if error}
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            错误: {error}
        </div>
    {:else}
        <!-- 仓库列表 -->
        <div class="bg-white rounded-lg shadow overflow-hidden">
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                                on:click={() => handleSort('name')}>
                                仓库名称
                                {#if sortBy === 'name'}
                                    <span class="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                                {/if}
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                类型
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                状态
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                所有者
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                                on:click={() => handleSort('stars_count')}>
                                星标数
                                {#if sortBy === 'stars_count'}
                                    <span class="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                                {/if}
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                                on:click={() => handleSort('views_count')}>
                                浏览量
                                {#if sortBy === 'views_count'}
                                    <span class="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                                {/if}
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                                on:click={() => handleSort('downloads_count')}>
                                下载量
                                {#if sortBy === 'downloads_count'}
                                    <span class="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                                {/if}
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                                on:click={() => handleSort('total_size')}>
                                大小
                                {#if sortBy === 'total_size'}
                                    <span class="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                                {/if}
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                                on:click={() => handleSort('updated_at')}>
                                更新时间
                                {#if sortBy === 'updated_at'}
                                    <span class="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                                {/if}
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                操作
                            </th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        {#each repositories as repo}
                            <tr class="hover:bg-gray-50">
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <div class="flex items-center">
                                        <img
                                            src={repo.owner?.avatar_url || '/default-avatar.png'}
                                            alt={repo.owner?.username || 'User'}
                                            class="w-10 h-10 rounded-full mr-3"
                                        />
                                        <div>
                                            <a
                                                href="/{repo.owner?.username || 'unknown'}/{repo.name}"
                                                class="text-sm font-medium text-blue-600 hover:text-blue-800 hover:underline"
                                            >
                                                {repo.owner?.username || 'unknown'}/{repo.name}
                                            </a>
                                            <div class="text-sm text-gray-500">{repo.description || 'No description'}</div>
                                        </div>
                                    </div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    <span class="capitalize">{repo.repo_type}</span>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getStatusBadge(repo)}">
                                        {getStatusText(repo)}
                                    </span>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {repo.owner?.username || 'Unknown'}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {repo.stars_count || 0}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {repo.views_count || 0}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {repo.downloads_count || 0}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {formatBytes(repo.total_size || 0)}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {formatDate(repo.updated_at)}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                                    <button
                                        on:click={() => openRepoModal(repo)}
                                        class="text-blue-600 hover:text-blue-900"
                                    >
                                        管理
                                    </button>
                                    {#if !repo.is_active}
                                        <button
                                            on:click={() => restoreRepository(repo.id)}
                                            class="text-green-600 hover:text-green-900"
                                        >
                                            恢复
                                        </button>
                                        <button
                                            on:click={() => openDeleteModal(repo)}
                                            class="text-red-600 hover:text-red-900"
                                        >
                                            永久删除
                                        </button>
                                    {/if}
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>

            <!-- 分页 -->
            <div class="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200">
                <div class="flex-1 flex justify-between sm:hidden">
                    <button
                        on:click={() => { currentPage = Math.max(1, currentPage - 1); loadRepositories(); }}
                        disabled={currentPage === 1}
                        class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                    >
                        上一页
                    </button>
                    <button
                        on:click={() => { currentPage = Math.min(totalPages, currentPage + 1); loadRepositories(); }}
                        disabled={currentPage === totalPages}
                        class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                    >
                        下一页
                    </button>
                </div>
                <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                    <div>
                        <p class="text-sm text-gray-700">
                            显示 <span class="font-medium">{(currentPage - 1) * pageSize + 1}</span> 到 
                            <span class="font-medium">{Math.min(currentPage * pageSize, totalRepositories)}</span> 项，
                            共 <span class="font-medium">{totalRepositories}</span> 项
                        </p>
                    </div>
                    <div>
                        <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                            <button
                                on:click={() => { currentPage = Math.max(1, currentPage - 1); loadRepositories(); }}
                                disabled={currentPage === 1}
                                class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                            >
                                上一页
                            </button>
                            {#each Array.from({length: Math.min(10, totalPages)}, (_, i) => i + 1) as page}
                                <button
                                    on:click={() => { currentPage = page; loadRepositories(); }}
                                    class="relative inline-flex items-center px-4 py-2 border text-sm font-medium {currentPage === page ? 'z-10 bg-blue-50 border-blue-500 text-blue-600' : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'}"
                                >
                                    {page}
                                </button>
                            {/each}
                            <button
                                on:click={() => { currentPage = Math.min(totalPages, currentPage + 1); loadRepositories(); }}
                                disabled={currentPage === totalPages}
                                class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                            >
                                下一页
                            </button>
                        </nav>
                    </div>
                </div>
            </div>
        </div>
    {/if}
</div>

<!-- 仓库管理模态框 -->
{#if showRepoModal && selectedRepo}
    <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div class="mt-3 text-center">
                <h3 class="text-lg font-medium text-gray-900 mb-4">管理仓库: {selectedRepo.name}</h3>
                
                <div class="space-y-4">
                    <div class="flex items-center justify-between">
                        <span class="text-sm font-medium text-gray-700">仓库状态</span>
                        <button
                            on:click={() => updateRepositoryStatus(selectedRepo.id, 'is_active', !selectedRepo.is_active)}
                            disabled={modalLoading}
                            class="px-3 py-1 rounded text-sm font-medium {selectedRepo.is_active ? 'bg-red-100 text-red-700 hover:bg-red-200' : 'bg-green-100 text-green-700 hover:bg-green-200'} disabled:opacity-50"
                        >
                            {selectedRepo.is_active ? '软删除' : '恢复'}
                        </button>
                    </div>
                    
                    <div class="flex items-center justify-between">
                        <span class="text-sm font-medium text-gray-700">推荐状态</span>
                        <button
                            on:click={() => updateRepositoryStatus(selectedRepo.id, 'is_featured', !selectedRepo.is_featured)}
                            disabled={modalLoading}
                            class="px-3 py-1 rounded text-sm font-medium {selectedRepo.is_featured ? 'bg-purple-100 text-purple-700 hover:bg-purple-200' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'} disabled:opacity-50"
                        >
                            {selectedRepo.is_featured ? '取消推荐' : '设为推荐'}
                        </button>
                    </div>
                    
                    <div class="flex items-center justify-between">
                        <span class="text-sm font-medium text-gray-700">可见性</span>
                        <button
                            on:click={() => updateRepositoryStatus(selectedRepo.id, 'visibility', selectedRepo.visibility === 'public' ? 'private' : 'public')}
                            disabled={modalLoading}
                            class="px-3 py-1 rounded text-sm font-medium {selectedRepo.visibility === 'public' ? 'bg-blue-100 text-blue-700 hover:bg-blue-200' : 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'} disabled:opacity-50"
                        >
                            {selectedRepo.visibility === 'public' ? '设为私有' : '设为公开'}
                        </button>
                    </div>
                </div>
                
                <div class="mt-6 flex justify-center">
                    <button
                        on:click={() => { showRepoModal = false; selectedRepo = null; }}
                        class="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
                    >
                        关闭
                    </button>
                </div>
            </div>
        </div>
    </div>
{/if}

<!-- 永久删除确认模态框 -->
{#if showDeleteModal && selectedRepo}
    <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div class="mt-3 text-center">
                <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                    <svg class="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.728-.833-2.498 0L3.318 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                    </svg>
                </div>
                <h3 class="text-lg font-medium text-gray-900 mb-4">永久删除仓库</h3>
                <p class="text-sm text-gray-500 mb-4">
                    这将永久删除仓库 <strong>{selectedRepo.name}</strong> 及其所有文件。此操作不可恢复。
                </p>
                <p class="text-sm text-red-600 mb-4">
                    请输入 <strong>DELETE</strong> 确认删除：
                </p>
                <input
                    type="text"
                    bind:value={deleteConfirmText}
                    placeholder="输入 DELETE"
                    class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500 mb-4"
                />
                
                <div class="flex justify-center space-x-4">
                    <button
                        on:click={() => { showDeleteModal = false; selectedRepo = null; deleteConfirmText = ''; }}
                        class="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
                    >
                        取消
                    </button>
                    <button
                        on:click={hardDeleteRepository}
                        disabled={!canDelete || modalLoading}
                        class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:opacity-50"
                    >
                        {modalLoading ? '删除中...' : '永久删除'}
                    </button>
                </div>
            </div>
        </div>
    </div>
{/if}