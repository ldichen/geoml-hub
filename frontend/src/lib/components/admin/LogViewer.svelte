<script>
    export let logs = [];
    export let loading = false;
    export let logLevel = 'INFO';
    export let logLimit = 100;
    export let onLevelChange = null;
    export let onLimitChange = null;
    export let onRefresh = null;

    function getLogLevelColor(level) {
        switch (level) {
            case 'DEBUG': return 'text-gray-600 bg-gray-100';
            case 'INFO': return 'text-blue-600 bg-blue-100';
            case 'WARNING': return 'text-yellow-600 bg-yellow-100';
            case 'ERROR': return 'text-red-600 bg-red-100';
            case 'CRITICAL': return 'text-red-700 bg-red-200';
            default: return 'text-gray-600 bg-gray-100';
        }
    }

    function formatLogTime(timestamp) {
        return new Date(timestamp).toLocaleString();
    }

    function handleLevelChange(event) {
        logLevel = event.target.value;
        if (onLevelChange) onLevelChange(logLevel);
    }

    function handleLimitChange(event) {
        logLimit = parseInt(event.target.value);
        if (onLimitChange) onLimitChange(logLimit);
    }

    function handleRefresh() {
        if (onRefresh) onRefresh();
    }
</script>

<div class="bg-white rounded-lg shadow p-6">
    <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold text-gray-900">系统日志</h3>
        <div class="flex items-center space-x-2">
            <select 
                value={logLevel}
                on:change={handleLevelChange}
                class="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
                <option value="DEBUG">调试</option>
                <option value="INFO">信息</option>
                <option value="WARNING">警告</option>
                <option value="ERROR">错误</option>
                <option value="CRITICAL">严重</option>
            </select>
            <select 
                value={logLimit}
                on:change={handleLimitChange}
                class="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
                <option value="50">50条</option>
                <option value="100">100条</option>
                <option value="200">200条</option>
                <option value="500">500条</option>
            </select>
            <button
                on:click={handleRefresh}
                class="bg-blue-500 text-white px-3 py-1 rounded-md hover:bg-blue-600 transition-colors text-sm"
            >
                刷新
            </button>
        </div>
    </div>
    
    {#if loading}
        <div class="flex justify-center items-center h-32">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
    {:else if logs.length > 0}
        <div class="max-h-96 overflow-y-auto">
            <div class="space-y-2">
                {#each logs as log}
                    <div class="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getLogLevelColor(log.level)}">
                            {log.level}
                        </span>
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center justify-between">
                                <p class="text-sm font-medium text-gray-900">{log.module || 'System'}</p>
                                <p class="text-xs text-gray-500">{formatLogTime(log.timestamp)}</p>
                            </div>
                            <p class="text-sm text-gray-700 mt-1 break-words">{log.message}</p>
                        </div>
                    </div>
                {/each}
            </div>
        </div>
    {:else}
        <div class="text-center py-8">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
            <p class="text-gray-500 mt-2">没有找到日志记录</p>
        </div>
    {/if}
</div>