<script>
    import { onMount, onDestroy } from 'svelte';
    import { api } from '$lib/utils/api.js';

    let healthData = null;
    let systemInfo = null;
    let logs = [];
    let loading = true;
    let error = null;
    let logsLoading = false;
    let logLevel = 'INFO';
    let logLimit = 100;
    let autoRefresh = false;
    let refreshInterval = null;

    onMount(async () => {
        await loadSystemData();
        await loadLogs();
    });

    async function loadSystemData() {
        try {
            loading = true;
            const [healthResponse, infoResponse] = await Promise.all([
                api.admin.getSystemHealth(),
                api.admin.getSystemInfo()
            ]);
            
            healthData = healthResponse;
            systemInfo = infoResponse;
        } catch (err) {
            error = err.message;
        } finally {
            loading = false;
        }
    }

    async function loadLogs() {
        try {
            logsLoading = true;
            const response = await api.admin.getSystemLogs({
                level: logLevel,
                limit: logLimit
            });
            logs = response.logs || [];
        } catch (err) {
            error = err.message;
        } finally {
            logsLoading = false;
        }
    }

    function toggleAutoRefresh() {
        autoRefresh = !autoRefresh;
        if (autoRefresh) {
            refreshInterval = setInterval(async () => {
                await loadSystemData();
                await loadLogs();
            }, 30000); // 30秒刷新
        } else {
            if (refreshInterval) {
                clearInterval(refreshInterval);
                refreshInterval = null;
            }
        }
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (days > 0) {
            return `${days}天 ${hours}小时 ${minutes}分钟`;
        } else if (hours > 0) {
            return `${hours}小时 ${minutes}分钟`;
        } else {
            return `${minutes}分钟`;
        }
    }

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

    // 清理定时器
    onDestroy(() => {
        if (refreshInterval) {
            clearInterval(refreshInterval);
        }
    });
</script>

<div class="space-y-6">
    <div class="flex justify-between items-center">
        <h1 class="text-3xl font-bold text-gray-900">系统监控</h1>
        <div class="flex space-x-2">
            <button
                on:click={toggleAutoRefresh}
                class="px-4 py-2 rounded-lg transition-colors {autoRefresh ? 'bg-green-500 text-white hover:bg-green-600' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}"
            >
                {autoRefresh ? '停止自动刷新' : '开启自动刷新'}
            </button>
            <button 
                on:click={() => Promise.all([loadSystemData(), loadLogs()])}
                class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
            >
                立即刷新
            </button>
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
    {:else if healthData}
        <!-- 系统健康状态 -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold mb-4">系统健康状态</h2>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div class="text-center">
                    <div class="text-3xl font-bold {getHealthStatusColor(healthData.status)} rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-2">
                        {getHealthStatusIcon(healthData.status)}
                    </div>
                    <div class="text-sm text-gray-600">系统总体状态</div>
                    <div class="font-semibold capitalize">{healthData.status}</div>
                </div>
                <div class="text-center">
                    <div class="text-3xl font-bold {getHealthStatusColor(healthData.database?.status)} rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-2">
                        {getHealthStatusIcon(healthData.database?.status)}
                    </div>
                    <div class="text-sm text-gray-600">数据库</div>
                    <div class="font-semibold">
                        {healthData.database?.response_time ? `${healthData.database.response_time}ms` : 'N/A'}
                    </div>
                </div>
                <div class="text-center">
                    <div class="text-3xl font-bold {getHealthStatusColor(healthData.storage?.status)} rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-2">
                        {getHealthStatusIcon(healthData.storage?.status)}
                    </div>
                    <div class="text-sm text-gray-600">存储服务</div>
                    <div class="font-semibold">MinIO</div>
                </div>
                <div class="text-center">
                    <div class="text-3xl font-bold {getHealthStatusColor(healthData.filesystem?.status)} rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-2">
                        {getHealthStatusIcon(healthData.filesystem?.status)}
                    </div>
                    <div class="text-sm text-gray-600">文件系统</div>
                    <div class="font-semibold">
                        {healthData.filesystem?.disk_usage ? `${healthData.filesystem.disk_usage}%` : 'N/A'}
                    </div>
                </div>
            </div>
            
            <div class="text-sm text-gray-600 text-center">
                上次检查: {new Date(healthData.timestamp).toLocaleString()}
                {#if healthData.uptime}
                    | 运行时间: {formatUptime(healthData.uptime)}
                {/if}
            </div>
        </div>

        <!-- 系统信息 -->
        {#if systemInfo}
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-lg font-semibold mb-4">系统信息</h3>
                    <div class="space-y-3">
                        <div class="flex justify-between">
                            <span class="text-gray-600">操作系统</span>
                            <span class="font-medium">{systemInfo.system?.platform} {systemInfo.system?.platform_version}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">架构</span>
                            <span class="font-medium">{systemInfo.system?.architecture}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">主机名</span>
                            <span class="font-medium">{systemInfo.system?.hostname}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">CPU 核心</span>
                            <span class="font-medium">{systemInfo.system?.cpu_cores}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Python 版本</span>
                            <span class="font-medium">{systemInfo.system?.python_version?.split(' ')[0]}</span>
                        </div>
                    </div>
                </div>

                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-lg font-semibold mb-4">应用信息</h3>
                    <div class="space-y-3">
                        <div class="flex justify-between">
                            <span class="text-gray-600">应用名称</span>
                            <span class="font-medium">{systemInfo.application?.name}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">版本</span>
                            <span class="font-medium">{systemInfo.application?.version}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">环境</span>
                            <span class="font-medium">{systemInfo.application?.environment}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">调试模式</span>
                            <span class="font-medium">{systemInfo.application?.debug_mode ? '开启' : '关闭'}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">MinIO 端点</span>
                            <span class="font-medium">{systemInfo.application?.minio_endpoint}</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 资源使用情况 -->
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-lg font-semibold mb-4">资源使用情况</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <h4 class="font-medium text-gray-900 mb-3">内存使用</h4>
                        <div class="space-y-2">
                            <div class="flex justify-between text-sm">
                                <span>总内存</span>
                                <span>{formatBytes(systemInfo.system?.memory_total)}</span>
                            </div>
                            <div class="flex justify-between text-sm">
                                <span>可用内存</span>
                                <span>{formatBytes(systemInfo.system?.memory_available)}</span>
                            </div>
                            <div class="w-full bg-gray-200 rounded-full h-2">
                                <div 
                                    class="bg-blue-500 h-2 rounded-full"
                                    style="width: {((systemInfo.system?.memory_total - systemInfo.system?.memory_available) / systemInfo.system?.memory_total) * 100}%"
                                ></div>
                            </div>
                        </div>
                    </div>
                    <div>
                        <h4 class="font-medium text-gray-900 mb-3">磁盘使用</h4>
                        <div class="space-y-2">
                            <div class="flex justify-between text-sm">
                                <span>总空间</span>
                                <span>{formatBytes(systemInfo.system?.disk_usage?.total)}</span>
                            </div>
                            <div class="flex justify-between text-sm">
                                <span>可用空间</span>
                                <span>{formatBytes(systemInfo.system?.disk_usage?.free)}</span>
                            </div>
                            <div class="w-full bg-gray-200 rounded-full h-2">
                                <div 
                                    class="bg-green-500 h-2 rounded-full"
                                    style="width: {(systemInfo.system?.disk_usage?.used / systemInfo.system?.disk_usage?.total) * 100}%"
                                ></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        {/if}

        <!-- 系统日志 -->
        <div class="bg-white rounded-lg shadow p-6">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-semibold">系统日志</h3>
                <div class="flex space-x-2">
                    <select 
                        bind:value={logLevel}
                        on:change={loadLogs}
                        class="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="DEBUG">调试</option>
                        <option value="INFO">信息</option>
                        <option value="WARNING">警告</option>
                        <option value="ERROR">错误</option>
                        <option value="CRITICAL">严重</option>
                    </select>
                    <select 
                        bind:value={logLimit}
                        on:change={loadLogs}
                        class="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value="50">50条</option>
                        <option value="100">100条</option>
                        <option value="200">200条</option>
                        <option value="500">500条</option>
                    </select>
                </div>
            </div>
            
            {#if logsLoading}
                <div class="flex justify-center items-center h-32">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
            {:else if logs.length > 0}
                <div class="max-h-96 overflow-y-auto">
                    <div class="space-y-2">
                        {#each logs as log}
                            <div class="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getLogLevelColor(log.level)}">
                                    {log.level}
                                </span>
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center justify-between">
                                        <p class="text-sm font-medium text-gray-900">{log.module}</p>
                                        <p class="text-xs text-gray-500">{formatLogTime(log.timestamp)}</p>
                                    </div>
                                    <p class="text-sm text-gray-700 mt-1">{log.message}</p>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            {:else}
                <div class="text-center py-8 text-gray-500">
                    没有找到日志记录
                </div>
            {/if}
        </div>
    {/if}
</div>