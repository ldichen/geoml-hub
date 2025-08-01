<script>
    export let healthData = null;
    export let title = '系统健康状态';
    export let showDetails = true;

    function getHealthStatusColor(status) {
        switch (status) {
            case 'healthy': return 'text-green-600 bg-green-100';
            case 'warning': return 'text-yellow-600 bg-yellow-100';
            case 'critical': return 'text-red-600 bg-red-100';
            case 'degraded': return 'text-orange-600 bg-orange-100';
            default: return 'text-gray-600 bg-gray-100';
        }
    }

    function getHealthStatusIcon(status) {
        switch (status) {
            case 'healthy': return '✓';
            case 'warning': return '⚠';
            case 'critical': return '✗';
            case 'degraded': return '⚠';
            default: return '?';
        }
    }

    function getHealthStatusText(status) {
        switch (status) {
            case 'healthy': return '正常';
            case 'warning': return '警告';
            case 'critical': return '严重';
            case 'degraded': return '降级';
            default: return '未知';
        }
    }

    function formatUptime(seconds) {
        if (!seconds) return 'N/A';
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (days > 0) {
            return `${days}天 ${hours}小时`;
        } else if (hours > 0) {
            return `${hours}小时 ${minutes}分钟`;
        } else {
            return `${minutes}分钟`;
        }
    }
</script>

<div class="bg-white rounded-lg shadow p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
    
    {#if healthData}
        <!-- 总体状态 -->
        <div class="flex items-center justify-center mb-6">
            <div class="text-center">
                <div class="text-4xl font-bold {getHealthStatusColor(healthData.status)} rounded-full w-24 h-24 flex items-center justify-center mx-auto mb-2">
                    {getHealthStatusIcon(healthData.status)}
                </div>
                <div class="text-lg font-semibold text-gray-900">
                    {getHealthStatusText(healthData.status)}
                </div>
                <div class="text-sm text-gray-500">
                    {new Date(healthData.timestamp).toLocaleString()}
                </div>
            </div>
        </div>

        {#if showDetails}
            <!-- 详细状态 -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div class="text-center p-4 bg-gray-50 rounded-lg">
                    <div class="text-2xl font-bold {getHealthStatusColor(healthData.database?.status)} rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-2">
                        {getHealthStatusIcon(healthData.database?.status)}
                    </div>
                    <div class="text-sm font-medium text-gray-900">数据库</div>
                    <div class="text-sm text-gray-500">
                        {healthData.database?.response_time ? `${healthData.database.response_time}ms` : 'N/A'}
                    </div>
                </div>

                <div class="text-center p-4 bg-gray-50 rounded-lg">
                    <div class="text-2xl font-bold {getHealthStatusColor(healthData.storage?.status)} rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-2">
                        {getHealthStatusIcon(healthData.storage?.status)}
                    </div>
                    <div class="text-sm font-medium text-gray-900">存储</div>
                    <div class="text-sm text-gray-500">MinIO</div>
                </div>

                <div class="text-center p-4 bg-gray-50 rounded-lg">
                    <div class="text-2xl font-bold {getHealthStatusColor(healthData.filesystem?.status)} rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-2">
                        {getHealthStatusIcon(healthData.filesystem?.status)}
                    </div>
                    <div class="text-sm font-medium text-gray-900">文件系统</div>
                    <div class="text-sm text-gray-500">
                        {healthData.filesystem?.disk_usage ? `${healthData.filesystem.disk_usage}%` : 'N/A'}
                    </div>
                </div>
            </div>

            <!-- 系统信息 -->
            <div class="border-t pt-4">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                        <span class="font-medium text-gray-700">运行时间:</span>
                        <span class="text-gray-600 ml-2">{formatUptime(healthData.uptime)}</span>
                    </div>
                    <div>
                        <span class="font-medium text-gray-700">最后检查:</span>
                        <span class="text-gray-600 ml-2">{new Date(healthData.timestamp).toLocaleString()}</span>
                    </div>
                </div>
            </div>
        {/if}
    {:else}
        <div class="text-center py-8">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p class="text-gray-500">正在检查系统健康状态...</p>
        </div>
    {/if}
</div>