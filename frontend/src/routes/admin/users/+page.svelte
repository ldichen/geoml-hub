<script>
    import { onMount } from 'svelte';
    import { api } from '$lib/utils/api.js';

    let users = [];
    let loading = true;
    let error = null;
    let searchTerm = '';
    let statusFilter = 'all';
    let sortBy = 'created';
    let sortOrder = 'desc';
    let currentPage = 1;
    let pageSize = 20;
    let totalUsers = 0;
    let selectedUser = null;
    let showUserModal = false;
    let modalLoading = false;

    onMount(async () => {
        await loadUsers();
    });

    async function loadUsers() {
        try {
            loading = true;
            const params = {
                skip: (currentPage - 1) * pageSize,
                limit: pageSize,
                search: searchTerm || undefined,
                sort_by: sortBy,
                order: sortOrder
            };

            // Add status filters based on statusFilter value
            if (statusFilter === 'active') {
                params.is_active = true;
            } else if (statusFilter === 'inactive') {
                params.is_active = false;
            } else if (statusFilter === 'verified') {
                params.is_verified = true;
            } else if (statusFilter === 'unverified') {
                params.is_verified = false;
            }

            const response = await api.getAdminUsers(params);
            users = response.users || [];
            totalUsers = response.total || 0;
        } catch (err) {
            error = err.message;
        } finally {
            loading = false;
        }
    }

    async function handleSearch() {
        currentPage = 1;
        await loadUsers();
    }

    async function handleSort(field) {
        if (sortBy === field) {
            sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            sortBy = field;
            sortOrder = 'desc';
        }
        currentPage = 1;
        await loadUsers();
    }

    async function handleStatusFilter(status) {
        statusFilter = status;
        currentPage = 1;
        await loadUsers();
    }

    async function openUserModal(user) {
        selectedUser = user;
        showUserModal = true;
    }

    async function updateUserStatus(userId, field, value) {
        try {
            modalLoading = true;
            await api.updateAdminUserStatus(userId, { [field]: value });
            
            // 更新本地数据
            const userIndex = users.findIndex(u => u.id === userId);
            if (userIndex !== -1) {
                users[userIndex] = { ...users[userIndex], [field]: value };
            }
            
            if (selectedUser && selectedUser.id === userId) {
                selectedUser = { ...selectedUser, [field]: value };
            }
            
            showUserModal = false;
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

    function getStatusBadge(user) {
        if (!user.is_active) return 'bg-red-100 text-red-800';
        if (!user.is_verified) return 'bg-yellow-100 text-yellow-800';
        if (user.is_admin) return 'bg-purple-100 text-purple-800';
        return 'bg-green-100 text-green-800';
    }

    function getStatusText(user) {
        if (!user.is_active) return '已禁用';
        if (!user.is_verified) return '未验证';
        if (user.is_admin) return '管理员';
        return '正常';
    }

    $: totalPages = Math.ceil(totalUsers / pageSize);
</script>

<div class="space-y-6">
    <div class="flex justify-between items-center">
        <h1 class="text-3xl font-bold text-gray-900">用户管理</h1>
        <button 
            on:click={loadUsers}
            class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
        >
            刷新
        </button>
    </div>

    <!-- 搜索和过滤 -->
    <div class="bg-white rounded-lg shadow p-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="md:col-span-2">
                <label for="user-search" class="block text-sm font-medium text-gray-700 mb-2">搜索用户</label>
                <div class="flex">
                    <input
                        id="user-search"
                        type="text"
                        bind:value={searchTerm}
                        placeholder="搜索用户名、邮箱或姓名..."
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
                    on:change={() => handleStatusFilter(statusFilter)}
                    class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="all">全部状态</option>
                    <option value="active">活跃用户</option>
                    <option value="inactive">禁用用户</option>
                    <option value="verified">已验证</option>
                    <option value="unverified">未验证</option>
                    <option value="admin">管理员</option>
                </select>
            </div>
            
            <div>
                <label for="sort-by" class="block text-sm font-medium text-gray-700 mb-2">排序方式</label>
                <select 
                    id="sort-by"
                    bind:value={sortBy}
                    on:change={loadUsers}
                    class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    <option value="created">创建时间</option>
                    <option value="updated">更新时间</option>
                    <option value="username">用户名</option>
                    <option value="repositories">仓库数量</option>
                    <option value="storage">存储使用</option>
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
        <!-- 用户列表 -->
        <div class="bg-white rounded-lg shadow overflow-hidden">
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                                on:click={() => handleSort('username')}>
                                用户名
                                {#if sortBy === 'username'}
                                    <span class="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                                {/if}
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                邮箱
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                状态
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                                on:click={() => handleSort('repositories')}>
                                仓库数
                                {#if sortBy === 'repositories'}
                                    <span class="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                                {/if}
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                                on:click={() => handleSort('storage')}>
                                存储使用
                                {#if sortBy === 'storage'}
                                    <span class="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                                {/if}
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                                on:click={() => handleSort('created')}>
                                创建时间
                                {#if sortBy === 'created'}
                                    <span class="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                                {/if}
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                操作
                            </th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        {#each users as user}
                            <tr class="hover:bg-gray-50">
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <div class="flex items-center">
                                        <div class="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                                            <span class="text-sm font-medium text-gray-700">
                                                {user.username?.charAt(0)?.toUpperCase() || 'U'}
                                            </span>
                                        </div>
                                        <div class="ml-4">
                                            <div class="text-sm font-medium text-gray-900">{user.username}</div>
                                            <div class="text-sm text-gray-500">{user.full_name || ''}</div>
                                        </div>
                                    </div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {user.email}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getStatusBadge(user)}">
                                        {getStatusText(user)}
                                    </span>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {user.public_repos_count || 0}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {formatBytes(user.storage_used || 0)}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {formatDate(user.created_at)}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                    <button
                                        on:click={() => openUserModal(user)}
                                        class="text-blue-600 hover:text-blue-900 mr-3"
                                    >
                                        管理
                                    </button>
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
                        on:click={() => { currentPage = Math.max(1, currentPage - 1); loadUsers(); }}
                        disabled={currentPage === 1}
                        class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                    >
                        上一页
                    </button>
                    <button
                        on:click={() => { currentPage = Math.min(totalPages, currentPage + 1); loadUsers(); }}
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
                            <span class="font-medium">{Math.min(currentPage * pageSize, totalUsers)}</span> 项，
                            共 <span class="font-medium">{totalUsers}</span> 项
                        </p>
                    </div>
                    <div>
                        <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                            <button
                                on:click={() => { currentPage = Math.max(1, currentPage - 1); loadUsers(); }}
                                disabled={currentPage === 1}
                                class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                            >
                                上一页
                            </button>
                            {#each Array.from({length: Math.min(10, totalPages)}, (_, i) => i + 1) as page}
                                <button
                                    on:click={() => { currentPage = page; loadUsers(); }}
                                    class="relative inline-flex items-center px-4 py-2 border text-sm font-medium {currentPage === page ? 'z-10 bg-blue-50 border-blue-500 text-blue-600' : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'}"
                                >
                                    {page}
                                </button>
                            {/each}
                            <button
                                on:click={() => { currentPage = Math.min(totalPages, currentPage + 1); loadUsers(); }}
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

<!-- 用户管理模态框 -->
{#if showUserModal && selectedUser}
    <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div class="mt-3 text-center">
                <h3 class="text-lg font-medium text-gray-900 mb-4">管理用户: {selectedUser.username}</h3>
                
                <div class="space-y-4">
                    <div class="flex items-center justify-between">
                        <span class="text-sm font-medium text-gray-700">账户状态</span>
                        <button
                            on:click={() => updateUserStatus(selectedUser.id, 'is_active', !selectedUser.is_active)}
                            disabled={modalLoading}
                            class="px-3 py-1 rounded text-sm font-medium {selectedUser.is_active ? 'bg-red-100 text-red-700 hover:bg-red-200' : 'bg-green-100 text-green-700 hover:bg-green-200'} disabled:opacity-50"
                        >
                            {selectedUser.is_active ? '禁用' : '启用'}
                        </button>
                    </div>
                    
                    <div class="flex items-center justify-between">
                        <span class="text-sm font-medium text-gray-700">邮箱验证</span>
                        <button
                            on:click={() => updateUserStatus(selectedUser.id, 'is_verified', !selectedUser.is_verified)}
                            disabled={modalLoading}
                            class="px-3 py-1 rounded text-sm font-medium {selectedUser.is_verified ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200' : 'bg-green-100 text-green-700 hover:bg-green-200'} disabled:opacity-50"
                        >
                            {selectedUser.is_verified ? '取消验证' : '验证'}
                        </button>
                    </div>
                    
                    <div class="flex items-center justify-between">
                        <span class="text-sm font-medium text-gray-700">管理员权限</span>
                        <button
                            on:click={() => updateUserStatus(selectedUser.id, 'is_admin', !selectedUser.is_admin)}
                            disabled={modalLoading}
                            class="px-3 py-1 rounded text-sm font-medium {selectedUser.is_admin ? 'bg-purple-100 text-purple-700 hover:bg-purple-200' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'} disabled:opacity-50"
                        >
                            {selectedUser.is_admin ? '撤销管理员' : '授予管理员'}
                        </button>
                    </div>
                </div>
                
                <div class="mt-6 flex justify-center">
                    <button
                        on:click={() => { showUserModal = false; selectedUser = null; }}
                        class="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
                    >
                        关闭
                    </button>
                </div>
            </div>
        </div>
    </div>
{/if}