<script>
    import { onMount } from 'svelte';
    import { api } from '$lib/utils/api.js';

    let dashboardData = null;
    let healthData = null;
    let loading = true;
    let error = null;

    onMount(async () => {
        await loadDashboardData();
    });

    async function loadDashboardData() {
        try {
            loading = true;
            const [dashboardResponse, healthResponse] = await Promise.all([
                api.getAdminDashboard(),
                api.getAdminSystemHealth()
            ]);

            dashboardData = dashboardResponse;
            healthData = healthResponse;
        } catch (err) {
            error = err.message;
        } finally {
            loading = false;
        }
    }

    function formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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
</script>

<div class="space-y-6">
    <div class="flex justify-between items-center">
        <h1 class="text-3xl font-bold text-gray-900">管理员仪表板</h1>
        <button 
            on:click={loadDashboardData}
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
    {:else if dashboardData}
        <!-- 系统健康状态 -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold mb-4">系统健康状态</h2>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div class="text-center">
                    <div class="text-2xl font-bold {getHealthStatusColor(healthData?.overall)} rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-2">
                        {getHealthStatusIcon(healthData?.overall)}
                    </div>
                    <div class="text-sm text-gray-600">系统状态</div>
                    <div class="font-semibold capitalize">{healthData?.overall || 'unknown'}</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold {getHealthStatusColor(healthData?.services?.database?.status)} rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-2">
                        {getHealthStatusIcon(healthData?.services?.database?.status)}
                    </div>
                    <div class="text-sm text-gray-600">数据库</div>
                    <div class="font-semibold">
                        {healthData?.services?.database?.response_time_ms ? `${healthData.services.database.response_time_ms}ms` : 'N/A'}
                    </div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold {getHealthStatusColor(healthData?.services?.minio?.healthy ? 'healthy' : 'unhealthy')} rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-2">
                        {getHealthStatusIcon(healthData?.services?.minio?.healthy ? 'healthy' : 'unhealthy')}
                    </div>
                    <div class="text-sm text-gray-600">存储</div>
                    <div class="font-semibold">MinIO</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold {getHealthStatusColor(healthData?.services?.disk?.status)} rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-2">
                        {getHealthStatusIcon(healthData?.services?.disk?.status)}
                    </div>
                    <div class="text-sm text-gray-600">文件系统</div>
                    <div class="font-semibold">
                        {healthData?.services?.disk?.free_percentage ? `${healthData.services.disk.free_percentage}%` : 'N/A'}
                    </div>
                </div>
            </div>
        </div>

        <!-- 统计卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <!-- 用户统计 -->
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-blue-100 text-blue-600">
                        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">总用户数</p>
                        <p class="text-2xl font-semibold text-gray-900">{formatNumber(dashboardData.users?.total || 0)}</p>
                    </div>
                </div>
                <div class="mt-4">
                    <div class="flex justify-between text-sm text-gray-600">
                        <span>活跃用户</span>
                        <span>{formatNumber(dashboardData.users?.active || 0)}</span>
                    </div>
                    <div class="flex justify-between text-sm text-gray-600">
                        <span>验证用户</span>
                        <span>{formatNumber(dashboardData.users?.verified || 0)}</span>
                    </div>
                </div>
            </div>

            <!-- 仓库统计 -->
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-green-100 text-green-600">
                        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">总仓库数</p>
                        <p class="text-2xl font-semibold text-gray-900">{formatNumber(dashboardData.repositories?.total || 0)}</p>
                    </div>
                </div>
                <div class="mt-4">
                    <div class="flex justify-between text-sm text-gray-600">
                        <span>公开仓库</span>
                        <span>{formatNumber(dashboardData.repositories?.public || 0)}</span>
                    </div>
                    <div class="flex justify-between text-sm text-gray-600">
                        <span>私有仓库</span>
                        <span>{formatNumber(dashboardData.repositories?.private || 0)}</span>
                    </div>
                </div>
            </div>

            <!-- 存储统计 -->
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-yellow-100 text-yellow-600">
                        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">总存储量</p>
                        <p class="text-2xl font-semibold text-gray-900">{formatBytes(dashboardData.storage?.total_size_bytes || 0)}</p>
                    </div>
                </div>
                <div class="mt-4">
                    <div class="flex justify-between text-sm text-gray-600">
                        <span>总文件数</span>
                        <span>{formatNumber(dashboardData.storage?.active_files || 0)}</span>
                    </div>
                    <div class="flex justify-between text-sm text-gray-600">
                        <span>存储桶状态</span>
                        <span class="capitalize">{dashboardData.storage?.bucket_status || 'unknown'}</span>
                    </div>
                </div>
            </div>

            <!-- 活动统计 -->
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-full bg-purple-100 text-purple-600">
                        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                        </svg>
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">7天活动</p>
                        <p class="text-2xl font-semibold text-gray-900">{formatNumber((dashboardData.activity_7d?.uploads || 0) + (dashboardData.activity_7d?.downloads || 0) + (dashboardData.activity_7d?.views || 0))}</p>
                    </div>
                </div>
                <div class="mt-4">
                    <div class="flex justify-between text-sm text-gray-600">
                        <span>上传次数</span>
                        <span>{formatNumber(dashboardData.activity_7d?.uploads || 0)}</span>
                    </div>
                    <div class="flex justify-between text-sm text-gray-600">
                        <span>下载次数</span>
                        <span>{formatNumber(dashboardData.activity_7d?.downloads || 0)}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- 最近活动 -->
        {#if dashboardData.recent_activities}
            <div class="bg-white rounded-lg shadow p-6">
                <h2 class="text-xl font-semibold mb-4">最近活动</h2>
                <div class="space-y-4">
                    {#each dashboardData.recent_activities as activity}
                        <div class="flex items-center justify-between py-3 border-b border-gray-200 last:border-b-0">
                            <div class="flex items-center">
                                <div class="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                                <div>
                                    <p class="text-sm font-medium text-gray-900">{activity.action}</p>
                                    <p class="text-sm text-gray-500">{activity.user} • {activity.repository}</p>
                                </div>
                            </div>
                            <div class="text-sm text-gray-500">
                                {new Date(activity.timestamp).toLocaleString()}
                            </div>
                        </div>
                    {/each}
                </div>
            </div>
        {/if}

        <!-- 系统信息 -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold mb-4">系统信息</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <h3 class="font-medium text-gray-900 mb-2">运行时间</h3>
                    <p class="text-sm text-gray-600">{healthData?.uptime || 'N/A'}</p>
                </div>
                <div>
                    <h3 class="font-medium text-gray-900 mb-2">最后更新</h3>
                    <p class="text-sm text-gray-600">{new Date(healthData?.timestamp || Date.now()).toLocaleString()}</p>
                </div>
            </div>
        </div>
    {/if}
</div>