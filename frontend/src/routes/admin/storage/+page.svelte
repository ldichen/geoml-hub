<script>
    import { onMount } from 'svelte';
    import { api } from '$lib/utils/api.js';

    let storageStats = null;
    let loading = true;
    let error = null;
    let cleanupLoading = false;
    let cleanupResult = null;

    onMount(async () => {
        await loadStorageStats();
    });

    async function loadStorageStats() {
        try {
            loading = true;
            const response = await api.admin.getStorageStats();
            storageStats = response;
        } catch (err) {
            error = err.message;
        } finally {
            loading = false;
        }
    }

    async function performCleanup(options = {}) {
        try {
            cleanupLoading = true;
            const response = await api.admin.performStorageCleanup(options);
            cleanupResult = response;
            
            // 清理完成后重新加载统计数据
            await loadStorageStats();
        } catch (err) {
            error = err.message;
        } finally {
            cleanupLoading = false;
        }
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    function getStorageUsagePercentage(used, total) {
        if (!total || total === 0) return 0;
        return Math.round((used / total) * 100);
    }

    function getUsageColor(percentage) {
        if (percentage >= 90) return 'bg-red-500';
        if (percentage >= 70) return 'bg-yellow-500';
        if (percentage >= 50) return 'bg-blue-500';
        return 'bg-green-500';
    }

    function getFileTypeIcon(type) {
        switch (type) {
            case 'image': return '🖼️';
            case 'video': return '🎥';
            case 'audio': return '🎵';
            case 'document': return '📄';
            case 'archive': return '📦';
            case 'code': return '💻';
            case 'data': return '📊';
            case 'model': return '🤖';
            default: return '📁';
        }
    }
</script>

<div class="space-y-6">
    <div class="flex justify-between items-center">
        <h1 class="text-3xl font-bold text-gray-900">存储管理</h1>
        <button 
            on:click={loadStorageStats}
            class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
        >
            刷新数据
        </button>
    </div>

    {#if loading}
        <div class="flex justify-center items-center h-64">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
    {:else if error}
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            错误: {error}
        </div>
    {:else if storageStats}
        <!-- 存储概览 -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-blue-100 text-blue-600">
                        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">总存储使用</p>
                        <p class="text-2xl font-semibold text-gray-900">{formatBytes(storageStats.user_storage?.total_used || 0)}</p>
                    </div>
                </div>
                <div class="mt-4">
                    <div class="text-sm text-gray-600">
                        平均: {formatBytes(storageStats.user_storage?.average_used || 0)}
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-green-100 text-green-600">
                        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">总文件数</p>
                        <p class="text-2xl font-semibold text-gray-900">{formatNumber(storageStats.file_types?.total_files || 0)}</p>
                    </div>
                </div>
                <div class="mt-4">
                    <div class="text-sm text-gray-600">
                        类型: {Object.keys(storageStats.file_types?.by_type || {}).length} 种
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-purple-100 text-purple-600">
                        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">活跃用户</p>
                        <p class="text-2xl font-semibold text-gray-900">{formatNumber(storageStats.user_storage?.user_count || 0)}</p>
                    </div>
                </div>
                <div class="mt-4">
                    <div class="text-sm text-gray-600">
                        最大使用: {formatBytes(storageStats.user_storage?.max_used || 0)}
                    </div>
                </div>
            </div>

            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-yellow-100 text-yellow-600">
                        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">存储桶状态</p>
                        <p class="text-2xl font-semibold text-gray-900 capitalize">{storageStats.bucket?.status || 'unknown'}</p>
                    </div>
                </div>
                <div class="mt-4">
                    <div class="text-sm text-gray-600">
                        容量: {formatBytes(storageStats.bucket?.total_capacity || 0)}
                    </div>
                </div>
            </div>
        </div>

        <!-- 文件类型分析 -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold mb-4">文件类型分析</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {#each Object.entries(storageStats.file_types?.by_type || {}) as [type, data]}
                    <div class="border rounded-lg p-4">
                        <div class="flex items-center justify-between mb-2">
                            <div class="flex items-center">
                                <span class="text-2xl mr-2">{getFileTypeIcon(type)}</span>
                                <span class="font-medium capitalize">{type}</span>
                            </div>
                            <span class="text-sm text-gray-500">{data.count} 个文件</span>
                        </div>
                        <div class="text-sm text-gray-600 mb-2">
                            总大小: {formatBytes(data.total_size)}
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2">
                            <div 
                                class="bg-blue-500 h-2 rounded-full"
                                style="width: {Math.min((data.total_size / (storageStats.file_types?.total_size || 1)) * 100, 100)}%"
                            ></div>
                        </div>
                    </div>
                {/each}
            </div>
        </div>

        <!-- 存储配额管理 -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold mb-4">存储配额管理</h2>
            <div class="space-y-4">
                {#if storageStats.quota_info}
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div class="text-center">
                            <div class="text-2xl font-bold text-gray-900">{formatBytes(storageStats.quota_info.default_quota || 0)}</div>
                            <div class="text-sm text-gray-600">默认配额</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-gray-900">{formatBytes(storageStats.quota_info.total_allocated || 0)}</div>
                            <div class="text-sm text-gray-600">已分配配额</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-gray-900">{formatBytes(storageStats.quota_info.total_used || 0)}</div>
                            <div class="text-sm text-gray-600">实际使用</div>
                        </div>
                    </div>
                    
                    <div class="mt-4">
                        <div class="flex justify-between text-sm text-gray-600 mb-1">
                            <span>配额使用率</span>
                            <span>{getStorageUsagePercentage(storageStats.quota_info.total_used, storageStats.quota_info.total_allocated)}%</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-3">
                            <div 
                                class="h-3 rounded-full {getUsageColor(getStorageUsagePercentage(storageStats.quota_info.total_used, storageStats.quota_info.total_allocated))}"
                                style="width: {getStorageUsagePercentage(storageStats.quota_info.total_used, storageStats.quota_info.total_allocated)}%"
                            ></div>
                        </div>
                    </div>
                {/if}
            </div>
        </div>

        <!-- 存储清理工具 -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold mb-4">存储清理工具</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <h3 class="font-medium text-gray-900 mb-2">清理选项</h3>
                    <div class="space-y-3">
                        <button
                            on:click={() => performCleanup({ expired_sessions: true })}
                            disabled={cleanupLoading}
                            class="w-full bg-yellow-500 text-white px-4 py-2 rounded-lg hover:bg-yellow-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {cleanupLoading ? '清理中...' : '清理过期会话'}
                        </button>
                        <button
                            on:click={() => performCleanup({ orphaned_files: true })}
                            disabled={cleanupLoading}
                            class="w-full bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {cleanupLoading ? '清理中...' : '清理孤儿文件'}
                        </button>
                        <button
                            on:click={() => performCleanup({ expired_sessions: true, orphaned_files: true })}
                            disabled={cleanupLoading}
                            class="w-full bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {cleanupLoading ? '清理中...' : '执行完整清理'}
                        </button>
                    </div>
                </div>
                
                <div>
                    <h3 class="font-medium text-gray-900 mb-2">清理说明</h3>
                    <div class="text-sm text-gray-600 space-y-2">
                        <p><strong>过期会话清理:</strong> 删除超过24小时的未完成文件上传会话</p>
                        <p><strong>孤儿文件清理:</strong> 删除MinIO中没有数据库记录的文件</p>
                        <p><strong>完整清理:</strong> 执行所有清理操作，释放最大存储空间</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- 清理结果 -->
        {#if cleanupResult}
            <div class="bg-green-50 border border-green-200 rounded-lg p-6">
                <h3 class="text-lg font-medium text-green-900 mb-4">清理完成</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <h4 class="font-medium text-green-800 mb-2">清理统计</h4>
                        <div class="text-sm text-green-700 space-y-1">
                            <p>已清理会话: {cleanupResult.expired_sessions || 0} 个</p>
                            <p>已清理文件: {cleanupResult.orphaned_files || 0} 个</p>
                            <p>释放空间: {formatBytes(cleanupResult.freed_space || 0)}</p>
                        </div>
                    </div>
                    <div>
                        <h4 class="font-medium text-green-800 mb-2">执行时间</h4>
                        <div class="text-sm text-green-700">
                            <p>开始时间: {new Date(cleanupResult.start_time).toLocaleString()}</p>
                            <p>结束时间: {new Date(cleanupResult.end_time).toLocaleString()}</p>
                            <p>耗时: {((new Date(cleanupResult.end_time) - new Date(cleanupResult.start_time)) / 1000).toFixed(2)} 秒</p>
                        </div>
                    </div>
                </div>
            </div>
        {/if}

        <!-- MinIO 存储桶信息 -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold mb-4">MinIO 存储桶信息</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <h3 class="font-medium text-gray-900 mb-2">连接信息</h3>
                    <div class="text-sm text-gray-600 space-y-1">
                        <p><strong>端点:</strong> {storageStats.bucket?.endpoint || 'N/A'}</p>
                        <p><strong>存储桶:</strong> {storageStats.bucket?.bucket_name || 'N/A'}</p>
                        <p><strong>状态:</strong> <span class="capitalize">{storageStats.bucket?.status || 'unknown'}</span></p>
                    </div>
                </div>
                <div>
                    <h3 class="font-medium text-gray-900 mb-2">容量信息</h3>
                    <div class="text-sm text-gray-600 space-y-1">
                        <p><strong>总容量:</strong> {formatBytes(storageStats.bucket?.total_capacity || 0)}</p>
                        <p><strong>已使用:</strong> {formatBytes(storageStats.bucket?.used_space || 0)}</p>
                        <p><strong>可用空间:</strong> {formatBytes((storageStats.bucket?.total_capacity || 0) - (storageStats.bucket?.used_space || 0))}</p>
                    </div>
                </div>
            </div>
        </div>
    {/if}
</div>