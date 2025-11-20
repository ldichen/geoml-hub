<script>
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import {
		Activity,
		Cpu,
		HardDrive,
		Wifi,
		Clock,
		RefreshCw,
		TrendingUp,
		AlertTriangle,
		CheckCircle,
		XCircle
	} from 'lucide-svelte';
	import { formatDistanceToNow } from 'date-fns';
	import zhCN from 'date-fns/locale/zh-CN/index.js';
	import { api } from '$lib/utils/api';
	import Loading from '../Loading.svelte';

	export let service;
	export let autoRefresh = true;
	export let refreshInterval = 30000; // 30 seconds

	const dispatch = createEventDispatcher();

	let metrics = null;
	let resourceUsage = null;
	let healthHistory = [];
	let loading = true;
	let error = null;
	let refreshTimer = null;
	let lastRefresh = null;

	onMount(() => {
		loadMonitoringData();
		if (autoRefresh) {
			startAutoRefresh();
		}
	});

	onDestroy(() => {
		if (refreshTimer) {
			clearInterval(refreshTimer);
		}
	});

	function startAutoRefresh() {
		if (refreshTimer) {
			clearInterval(refreshTimer);
		}
		refreshTimer = setInterval(() => {
			loadMonitoringData();
		}, refreshInterval);
	}

	function stopAutoRefresh() {
		if (refreshTimer) {
			clearInterval(refreshTimer);
			refreshTimer = null;
		}
	}

	async function loadMonitoringData() {
		try {
			loading = true;
			error = null;

			const [metricsData, resourceData, healthData] = await Promise.all([
				api.getServiceMetrics(service.id).catch(() => null),
				api.getServiceResourceUsage(service.id).catch(() => null),
				api.getServiceHealth(service.id).catch(() => ({ checks: [] }))
			]);

			metrics = metricsData;
			resourceUsage = resourceData;
			healthHistory = healthData.checks || [];
			lastRefresh = new Date();
		} catch (err) {
			error = err.message;
			console.error('Failed to load monitoring data:', err);
		} finally {
			loading = false;
		}
	}

	async function triggerHealthCheck() {
		try {
			await api.triggerHealthCheck(service.id);
			// Refresh data after health check
			setTimeout(() => loadMonitoringData(), 2000);
		} catch (err) {
			console.error('Failed to trigger health check:', err);
		}
	}

	function handleRefresh() {
		loadMonitoringData();
	}

	function toggleAutoRefresh() {
		autoRefresh = !autoRefresh;
		if (autoRefresh) {
			startAutoRefresh();
		} else {
			stopAutoRefresh();
		}
	}

	function formatBytes(bytes) {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
	}

	function getHealthStatusIcon(status) {
		switch (status) {
			case 'healthy':
				return CheckCircle;
			case 'unhealthy':
				return XCircle;
			case 'timeout':
				return Clock;
			default:
				return AlertTriangle;
		}
	}

	function getHealthStatusColor(status) {
		switch (status) {
			case 'healthy':
				return 'text-green-600 dark:text-green-400';
			case 'unhealthy':
				return 'text-red-600 dark:text-red-400';
			case 'timeout':
				return 'text-yellow-600 dark:text-yellow-400';
			default:
				return 'text-gray-600 dark:text-gray-400';
		}
	}

	function formatResponseTime(ms) {
		if (!ms) return '-';
		return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`;
	}

	$: healthStatus = healthHistory.length > 0 ? healthHistory[0].status : 'unknown';
	$: averageResponseTime =
		healthHistory.length > 0
			? Math.round(
					healthHistory.reduce((sum, check) => sum + (check.response_time_ms || 0), 0) /
						healthHistory.length
			  )
			: 0;
	$: successRate =
		healthHistory.length > 0
			? (
					(healthHistory.filter((check) => check.status === 'healthy').length /
						healthHistory.length) *
					100
			  ).toFixed(1)
			: 0;
</script>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
				服务监控 - {service.service_name}
			</h3>
			{#if lastRefresh}
				<p class="text-sm text-gray-500 dark:text-gray-400">
					最后更新: {formatDistanceToNow(lastRefresh, { addSuffix: true, locale: zhCN })}
				</p>
			{/if}
		</div>

		<div class="flex items-center space-x-3">
			<!-- Auto Refresh Toggle -->
			<label class="flex items-center space-x-2 cursor-pointer">
				<input
					type="checkbox"
					bind:checked={autoRefresh}
					on:change={toggleAutoRefresh}
					class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
				/>
				<span class="text-sm text-gray-700 dark:text-gray-300">自动刷新</span>
			</label>

			<!-- Manual Refresh -->
			<button
				class="px-3 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-lg transition-colors flex items-center space-x-1"
				on:click={handleRefresh}
				disabled={loading}
			>
				<RefreshCw class="w-4 h-4 {loading ? 'animate-spin' : ''}" />
				<span>刷新</span>
			</button>

			<!-- Health Check -->
			<button
				class="px-3 py-2 bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:hover:bg-blue-800 text-blue-700 dark:text-blue-300 text-sm font-medium rounded-lg transition-colors flex items-center space-x-1"
				on:click={triggerHealthCheck}
				disabled={loading}
			>
				<Activity class="w-4 h-4" />
				<span>健康检查</span>
			</button>
		</div>
	</div>

	{#if loading && !metrics}
		<div class="flex items-center justify-center py-12">
			<Loading size="lg" />
		</div>
	{:else if error}
		<div
			class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6"
		>
			<div class="flex items-center space-x-2">
				<AlertTriangle class="w-5 h-5 text-red-600 dark:text-red-400" />
				<h4 class="text-sm font-medium text-red-800 dark:text-red-200">加载监控数据失败</h4>
			</div>
			<p class="mt-2 text-sm text-red-700 dark:text-red-300">{error}</p>
			<button
				class="mt-3 px-3 py-1.5 bg-red-100 hover:bg-red-200 dark:bg-red-800 dark:hover:bg-red-700 text-red-700 dark:text-red-300 text-sm rounded transition-colors"
				on:click={handleRefresh}
			>
				重试
			</button>
		</div>
	{:else}
		<!-- Status Overview -->
		<div class="grid grid-cols-1 md:grid-cols-4 gap-6">
			<!-- Health Status -->
			<div
				class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6"
			>
				<div class="flex items-center space-x-3">
					<svelte:component
						this={getHealthStatusIcon(healthStatus)}
						class="w-8 h-8 {getHealthStatusColor(healthStatus)}"
					/>
					<div>
						<div class="text-sm text-gray-500 dark:text-gray-400">健康状态</div>
						<div class="text-lg font-semibold text-gray-900 dark:text-white">
							{healthStatus === 'healthy'
								? '健康'
								: healthStatus === 'unhealthy'
								? '不健康'
								: healthStatus === 'timeout'
								? '超时'
								: '未知'}
						</div>
					</div>
				</div>
			</div>

			<!-- Success Rate -->
			<div
				class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6"
			>
				<div class="flex items-center space-x-3">
					<TrendingUp class="w-8 h-8 text-green-600 dark:text-green-400" />
					<div>
						<div class="text-sm text-gray-500 dark:text-gray-400">成功率</div>
						<div class="text-lg font-semibold text-gray-900 dark:text-white">
							{successRate}%
						</div>
					</div>
				</div>
			</div>

			<!-- Response Time -->
			<div
				class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6"
			>
				<div class="flex items-center space-x-3">
					<Clock class="w-8 h-8 text-blue-600 dark:text-blue-400" />
					<div>
						<div class="text-sm text-gray-500 dark:text-gray-400">平均响应时间</div>
						<div class="text-lg font-semibold text-gray-900 dark:text-white">
							{formatResponseTime(averageResponseTime)}
						</div>
					</div>
				</div>
			</div>

			<!-- Access Count -->
			<div
				class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6"
			>
				<div class="flex items-center space-x-3">
					<Activity class="w-8 h-8 text-purple-600 dark:text-purple-400" />
					<div>
						<div class="text-sm text-gray-500 dark:text-gray-400">访问次数</div>
						<div class="text-lg font-semibold text-gray-900 dark:text-white">
							{metrics?.access_count || 0}
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Resource Usage -->
		{#if resourceUsage}
			<div
				class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6"
			>
				<h4 class="text-md font-semibold text-gray-900 dark:text-white mb-4">资源使用情况</h4>

				<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
					<!-- CPU Usage -->
					{#if resourceUsage.cpu_percent !== undefined}
						<div>
							<div class="flex items-center justify-between mb-2">
								<div class="flex items-center space-x-2">
									<Cpu class="w-4 h-4 text-gray-400" />
									<span class="text-sm font-medium text-gray-700 dark:text-gray-300">CPU使用率</span
									>
								</div>
								<span class="text-sm text-gray-600 dark:text-gray-400">
									{resourceUsage.cpu_percent.toFixed(1)}%
								</span>
							</div>
							<div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
								<div
									class="bg-blue-600 h-2 rounded-full transition-all duration-300"
									style="width: {Math.min(resourceUsage.cpu_percent, 100)}%"
								/>
							</div>
						</div>
					{/if}

					<!-- Memory Usage -->
					{#if resourceUsage.memory_mb !== undefined}
						<div>
							<div class="flex items-center justify-between mb-2">
								<div class="flex items-center space-x-2">
									<HardDrive class="w-4 h-4 text-gray-400" />
									<span class="text-sm font-medium text-gray-700 dark:text-gray-300">内存使用</span>
								</div>
								<span class="text-sm text-gray-600 dark:text-gray-400">
									{formatBytes(resourceUsage.memory_mb * 1024 * 1024)}
									{#if resourceUsage.memory_percent}
										({resourceUsage.memory_percent.toFixed(1)}%)
									{/if}
								</span>
							</div>
							{#if resourceUsage.memory_percent}
								<div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
									<div
										class="bg-green-600 h-2 rounded-full transition-all duration-300"
										style="width: {Math.min(resourceUsage.memory_percent, 100)}%"
									/>
								</div>
							{/if}
						</div>
					{/if}
				</div>
			</div>
		{/if}

		<!-- Service Metrics -->
		{#if metrics}
			<div
				class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6"
			>
				<h4 class="text-md font-semibold text-gray-900 dark:text-white mb-4">服务指标</h4>

				<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
					<div class="text-center">
						<div class="text-2xl font-bold text-gray-900 dark:text-white">
							{metrics.access_count}
						</div>
						<div class="text-sm text-gray-500 dark:text-gray-400">总访问次数</div>
					</div>

					<div class="text-center">
						<div class="text-2xl font-bold text-gray-900 dark:text-white">
							{metrics.start_count}
						</div>
						<div class="text-sm text-gray-500 dark:text-gray-400">启动次数</div>
					</div>

					<div class="text-center">
						<div class="text-2xl font-bold text-gray-900 dark:text-white">
							{Math.round(metrics.total_runtime_minutes / 60)}h
						</div>
						<div class="text-sm text-gray-500 dark:text-gray-400">总运行时长</div>
					</div>

					<div class="text-center">
						<div class="text-2xl font-bold text-gray-900 dark:text-white">
							{metrics.last_accessed_at
								? formatDistanceToNow(new Date(metrics.last_accessed_at), { locale: zhCN })
								: '-'}
						</div>
						<div class="text-sm text-gray-500 dark:text-gray-400">最后访问</div>
					</div>
				</div>
			</div>
		{/if}

		<!-- Health History -->
		{#if healthHistory.length > 0}
			<div
				class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6"
			>
				<h4 class="text-md font-semibold text-gray-900 dark:text-white mb-4">健康检查历史</h4>

				<div class="space-y-3">
					{#each healthHistory as check (check.id)}
						<div
							class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
						>
							<div class="flex items-center space-x-3">
								<svelte:component
									this={getHealthStatusIcon(check.status)}
									class="w-5 h-5 {getHealthStatusColor(check.status)}"
								/>
								<div>
									<div class="text-sm font-medium text-gray-900 dark:text-white">
										{check.status === 'healthy'
											? '健康'
											: check.status === 'unhealthy'
											? '不健康'
											: check.status === 'timeout'
											? '超时'
											: '未知'}
									</div>
									{#if check.error_message}
										<div class="text-xs text-red-600 dark:text-red-400">
											{check.error_message}
										</div>
									{/if}
								</div>
							</div>

							<div class="text-right">
								<div class="text-sm text-gray-600 dark:text-gray-300">
									{formatResponseTime(check.response_time_ms)}
								</div>
								<div class="text-xs text-gray-500 dark:text-gray-400">
									{formatDistanceToNow(new Date(check.checked_at), {
										addSuffix: true,
										locale: zhCN
									})}
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	{/if}
</div>
