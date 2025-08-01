<script>
    export let storageData = null;
    export let title = '存储监控';
    export let showDetails = true;

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

    $: usagePercentage = storageData && storageData.quota_info ? 
        getStorageUsagePercentage(storageData.quota_info.total_used, storageData.quota_info.total_allocated) : 0;
</script>

<div class="bg-white rounded-lg shadow p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
    
    {#if storageData}
        <!-- 存储概览 -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div class="text-center p-4 bg-blue-50 rounded-lg">
                <div class="text-2xl font-bold text-blue-600 mb-2">
                    {formatBytes(storageData.user_storage?.total_used || 0)}
                </div>
                <div class="text-sm text-gray-600">总使用量</div>
            </div>
            <div class="text-center p-4 bg-green-50 rounded-lg">
                <div class="text-2xl font-bold text-green-600 mb-2">
                    {formatNumber(storageData.file_types?.total_files || 0)}
                </div>
                <div class="text-sm text-gray-600">总文件数</div>
            </div>
            <div class="text-center p-4 bg-purple-50 rounded-lg">
                <div class="text-2xl font-bold text-purple-600 mb-2">
                    {formatNumber(storageData.user_storage?.user_count || 0)}
                </div>
                <div class="text-sm text-gray-600">活跃用户</div>
            </div>
        </div>

        {#if showDetails}
            <!-- 配额使用情况 -->
            {#if storageData.quota_info}
                <div class="mb-6">
                    <h4 class="font-medium text-gray-900 mb-3">存储配额使用情况</h4>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <div class="text-center">
                            <div class="text-lg font-semibold text-gray-900">
                                {formatBytes(storageData.quota_info.default_quota || 0)}
                            </div>
                            <div class="text-sm text-gray-600">默认配额</div>
                        </div>
                        <div class="text-center">
                            <div class="text-lg font-semibold text-gray-900">
                                {formatBytes(storageData.quota_info.total_allocated || 0)}
                            </div>
                            <div class="text-sm text-gray-600">已分配</div>
                        </div>
                        <div class="text-center">
                            <div class="text-lg font-semibold text-gray-900">
                                {formatBytes(storageData.quota_info.total_used || 0)}
                            </div>
                            <div class="text-sm text-gray-600">实际使用</div>
                        </div>
                    </div>
                    
                    <div class="mt-4">
                        <div class="flex justify-between text-sm text-gray-600 mb-1">
                            <span>配额使用率</span>
                            <span>{usagePercentage}%</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-3">
                            <div 
                                class="h-3 rounded-full transition-all duration-300 {getUsageColor(usagePercentage)}"
                                style="width: {usagePercentage}%"
                            ></div>
                        </div>
                    </div>
                </div>
            {/if}

            <!-- 文件类型分析 -->
            {#if storageData.file_types?.by_type}
                <div class="mb-6">
                    <h4 class="font-medium text-gray-900 mb-3">文件类型分析</h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {#each Object.entries(storageData.file_types.by_type) as [type, data]}
                            <div class="border rounded-lg p-3">
                                <div class="flex items-center justify-between mb-2">
                                    <div class="flex items-center">
                                        <span class="text-xl mr-2">{getFileTypeIcon(type)}</span>
                                        <span class="font-medium capitalize">{type}</span>
                                    </div>
                                    <span class="text-sm text-gray-500">{data.count}</span>
                                </div>
                                <div class="text-sm text-gray-600 mb-2">
                                    {formatBytes(data.total_size)}
                                </div>
                                <div class="w-full bg-gray-200 rounded-full h-2">
                                    <div 
                                        class="bg-blue-500 h-2 rounded-full transition-all duration-300"
                                        style="width: {Math.min((data.total_size / (storageData.file_types?.total_size || 1)) * 100, 100)}%"
                                    ></div>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}

            <!-- MinIO 存储桶信息 -->
            {#if storageData.bucket}
                <div class="border-t pt-4">
                    <h4 class="font-medium text-gray-900 mb-3">MinIO 存储桶</h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <div class="space-y-2 text-sm">
                                <div class="flex justify-between">
                                    <span class="text-gray-600">端点:</span>
                                    <span class="font-medium">{storageData.bucket.endpoint || 'N/A'}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-600">存储桶:</span>
                                    <span class="font-medium">{storageData.bucket.bucket_name || 'N/A'}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-600">状态:</span>
                                    <span class="font-medium capitalize {storageData.bucket.status === 'healthy' ? 'text-green-600' : 'text-red-600'}">
                                        {storageData.bucket.status || 'unknown'}
                                    </span>
                                </div>
                            </div>
                        </div>
                        <div>
                            <div class="space-y-2 text-sm">
                                <div class="flex justify-between">
                                    <span class="text-gray-600">总容量:</span>
                                    <span class="font-medium">{formatBytes(storageData.bucket.total_capacity || 0)}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-600">已使用:</span>
                                    <span class="font-medium">{formatBytes(storageData.bucket.used_space || 0)}</span>
                                </div>
                                <div class="flex justify-between">
                                    <span class="text-gray-600">可用空间:</span>
                                    <span class="font-medium">{formatBytes((storageData.bucket.total_capacity || 0) - (storageData.bucket.used_space || 0))}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            {/if}
        {/if}
    {:else}
        <div class="text-center py-8">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p class="text-gray-500">正在加载存储数据...</p>
        </div>
    {/if}
</div>