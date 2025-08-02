<script>
	import { onMount, createEventDispatcher } from 'svelte';
	import { api } from '$lib/utils/api.js';
	import { formatFileSize, formatDateTime, formatRelativeTime } from '$lib/utils/format.js';
	import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte';
	import ServiceFromImageModal from './ServiceFromImageModal.svelte';

	export let image;
	export let canManage = false;

	const dispatch = createEventDispatcher();

	let activeTab = 'overview';
	let services = [];
	let buildLogs = [];
	let loadingServices = false;
	let loadingLogs = false;
	let showCreateServiceModal = false;

	// 获取状态样式
	function getStatusStyle(status) {
		switch (status) {
			case 'ready':
				return 'bg-green-100 text-green-800';
			case 'uploading':
				return 'bg-blue-100 text-blue-800';
			case 'failed':
				return 'bg-red-100 text-red-800';
			default:
				return 'bg-gray-100 text-gray-800';
		}
	}

	// 获取状态文本
	function getStatusText(status) {
		switch (status) {
			case 'ready':
				return '就绪';
			case 'uploading':
				return '上传中';
			case 'failed':
				return '失败';
			default:
				return '未知';
		}
	}

	// 获取日志级别样式
	function getLogLevelStyle(level) {
		switch (level) {
			case 'error':
				return 'text-red-600';
			case 'warning':
				return 'text-amber-600';
			case 'info':
				return 'text-blue-600';
			case 'debug':
				return 'text-gray-600';
			default:
				return 'text-gray-600';
		}
	}

	// 加载服务列表
	async function loadServices() {
		try {
			loadingServices = true;
			const response = await api.getImageServices(image.id);
			if (response.success) {
				services = response.data || [];
			}
		} catch (err) {
			console.error('加载服务列表失败:', err);
		} finally {
			loadingServices = false;
		}
	}

	// 加载构建日志
	async function loadBuildLogs() {
		try {
			loadingLogs = true;
			const response = await api.getImageBuildLogs(image.id);
			if (response.success) {
				buildLogs = response.data || [];
			}
		} catch (err) {
			console.error('加载构建日志失败:', err);
		} finally {
			loadingLogs = false;
		}
	}

	// 切换标签页
	function switchTab(tab) {
		activeTab = tab;
		if (tab === 'services' && services.length === 0) {
			loadServices();
		} else if (tab === 'logs' && buildLogs.length === 0) {
			loadBuildLogs();
		}
	}

	// 关闭模态框
	function handleClose() {
		dispatch('close');
	}

	// 删除镜像
	function handleDelete() {
		if (confirm(`确定要删除镜像 ${image.name}:${image.tag} 吗？`)) {
			dispatch('delete', { imageId: image.id });
		}
	}

	// 创建服务
	function handleCreateService() {
		showCreateServiceModal = true;
	}

	// 处理服务创建成功
	function handleServiceCreated(event) {
		showCreateServiceModal = false;
		// 重新加载服务列表
		loadServices();
		// 更新镜像信息
		image.service_count = (image.service_count || 0) + 1;
		image.can_create_service = image.service_count < 2;
		dispatch('serviceCreated', event.detail);
	}

	onMount(() => {
		if (activeTab === 'services') {
			loadServices();
		}
	});
</script>

<!-- 模态框背景 -->
<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" on:click={handleClose}>
	<!-- 模态框内容 -->
	<div class="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-screen overflow-hidden" on:click|stopPropagation>
		<!-- 头部 -->
		<div class="flex items-center justify-between p-6 border-b border-gray-200">
			<div class="flex-1">
				<div class="flex items-center mb-2">
					<h2 class="text-xl font-semibold text-gray-900 mr-3">
						{image.name}:{image.tag}
					</h2>
					<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getStatusStyle(image.status)}">
						{getStatusText(image.status)}
					</span>
				</div>
				{#if image.description}
					<p class="text-sm text-gray-600">{image.description}</p>
				{/if}
			</div>
			<button
				class="text-gray-400 hover:text-gray-600 transition-colors"
				on:click={handleClose}
			>
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
				</svg>
			</button>
		</div>

		<!-- 标签页导航 -->
		<div class="border-b border-gray-200">
			<nav class="flex px-6">
				<button
					class="py-3 px-4 text-sm font-medium border-b-2 transition-colors {activeTab === 'overview' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
					on:click={() => switchTab('overview')}
				>
					概览
				</button>
				<button
					class="py-3 px-4 text-sm font-medium border-b-2 transition-colors {activeTab === 'services' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
					on:click={() => switchTab('services')}
				>
					服务 ({image.service_count || 0})
				</button>
				<button
					class="py-3 px-4 text-sm font-medium border-b-2 transition-colors {activeTab === 'logs' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
					on:click={() => switchTab('logs')}
				>
					构建日志
				</button>
			</nav>
		</div>

		<!-- 内容区域 -->
		<div class="p-6 max-h-96 overflow-y-auto">
			<!-- 概览标签页 -->
			{#if activeTab === 'overview'}
				<div class="space-y-6">
					<!-- 基本信息 -->
					<div>
						<h3 class="text-lg font-medium text-gray-900 mb-4">基本信息</h3>
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
							<div class="bg-gray-50 p-4 rounded-lg">
								<dt class="text-sm font-medium text-gray-500">镜像ID</dt>
								<dd class="mt-1 text-sm text-gray-900">{image.id}</dd>
							</div>
							<div class="bg-gray-50 p-4 rounded-lg">
								<dt class="text-sm font-medium text-gray-500">镜像名称</dt>
								<dd class="mt-1 text-sm text-gray-900">{image.name}:{image.tag}</dd>
							</div>
							<div class="bg-gray-50 p-4 rounded-lg">
								<dt class="text-sm font-medium text-gray-500">状态</dt>
								<dd class="mt-1">
									<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getStatusStyle(image.status)}">
										{getStatusText(image.status)}
									</span>
								</dd>
							</div>
							<div class="bg-gray-50 p-4 rounded-lg">
								<dt class="text-sm font-medium text-gray-500">创建时间</dt>
								<dd class="mt-1 text-sm text-gray-900">
									{formatDateTime(image.created_at)}
								</dd>
							</div>
							{#if image.harbor_size}
								<div class="bg-gray-50 p-4 rounded-lg">
									<dt class="text-sm font-medium text-gray-500">镜像大小</dt>
									<dd class="mt-1 text-sm text-gray-900">{formatFileSize(image.harbor_size)}</dd>
								</div>
							{/if}
							<div class="bg-gray-50 p-4 rounded-lg">
								<dt class="text-sm font-medium text-gray-500">服务数量</dt>
								<dd class="mt-1 text-sm text-gray-900">{image.service_count || 0}/2</dd>
							</div>
						</div>
					</div>

					<!-- Harbor信息 -->
					{#if image.full_name}
						<div>
							<h3 class="text-lg font-medium text-gray-900 mb-4">Harbor信息</h3>
							<div class="bg-gray-50 p-4 rounded-lg">
								<dt class="text-sm font-medium text-gray-500 mb-2">镜像路径</dt>
								<dd class="bg-white p-3 rounded border font-mono text-sm">{image.full_name}</dd>
								{#if image.harbor_digest}
									<dt class="text-sm font-medium text-gray-500 mt-3 mb-2">镜像摘要</dt>
									<dd class="bg-white p-3 rounded border font-mono text-xs text-gray-600">
										{image.harbor_digest}
									</dd>
								{/if}
							</div>
						</div>
					{/if}

					<!-- 上传进度 -->
					{#if image.status === 'uploading'}
						<div>
							<h3 class="text-lg font-medium text-gray-900 mb-4">上传进度</h3>
							<div class="bg-gray-50 p-4 rounded-lg">
								<div class="flex justify-between text-sm text-gray-600 mb-2">
									<span>上传进度</span>
									<span>{image.upload_progress}%</span>
								</div>
								<div class="w-full bg-gray-200 rounded-full h-3">
									<div 
										class="bg-blue-500 h-3 rounded-full transition-all duration-300"
										style="width: {image.upload_progress}%"
									></div>
								</div>
							</div>
						</div>
					{/if}

					<!-- 错误信息 -->
					{#if image.status === 'failed' && image.error_message}
						<div>
							<h3 class="text-lg font-medium text-gray-900 mb-4">错误信息</h3>
							<div class="bg-red-50 border border-red-200 p-4 rounded-lg">
								<p class="text-sm text-red-600">{image.error_message}</p>
							</div>
						</div>
					{/if}
				</div>
			{/if}

			<!-- 服务标签页 -->
			{#if activeTab === 'services'}
				<div>
					<div class="flex items-center justify-between mb-4">
						<h3 class="text-lg font-medium text-gray-900">关联服务</h3>
						{#if canManage && image.status === 'ready' && image.can_create_service}
							<button
								class="btn btn-primary btn-sm"
								on:click={handleCreateService}
							>
								创建服务
							</button>
						{/if}
					</div>

					{#if loadingServices}
						<div class="flex justify-center items-center py-8">
							<LoadingSpinner size="md" />
							<span class="ml-3 text-gray-600">加载服务列表...</span>
						</div>
					{:else if services.length === 0}
						<div class="text-center py-8">
							<svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"></path>
							</svg>
							<h4 class="text-lg font-medium text-gray-900 mb-2">暂无服务</h4>
							<p class="text-gray-500 mb-4">
								基于此镜像还未创建任何服务
							</p>
							{#if canManage && image.status === 'ready' && image.can_create_service}
								<button
									class="btn btn-primary"
									on:click={handleCreateService}
								>
									创建第一个服务
								</button>
							{/if}
						</div>
					{:else}
						<div class="space-y-4">
							{#each services as service}
								<div class="border border-gray-200 rounded-lg p-4">
									<div class="flex items-center justify-between">
										<div>
											<h4 class="text-sm font-medium text-gray-900">{service.service_name}</h4>
											<p class="text-xs text-gray-500 mt-1">
												创建于 {formatRelativeTime(service.created_at)}
											</p>
										</div>
										<div class="flex items-center space-x-2">
											<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
												{service.status === 'running' ? 'bg-green-100 text-green-800' :
												service.status === 'stopped' ? 'bg-gray-100 text-gray-800' :
												service.status === 'error' ? 'bg-red-100 text-red-800' :
												'bg-yellow-100 text-yellow-800'}">
												{service.status}
											</span>
											{#if service.service_url}
												<a
													href={service.service_url}
													target="_blank"
													class="text-blue-600 hover:text-blue-800 text-xs"
												>
													访问服务
												</a>
											{/if}
										</div>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			{/if}

			<!-- 构建日志标签页 -->
			{#if activeTab === 'logs'}
				<div>
					<h3 class="text-lg font-medium text-gray-900 mb-4">构建日志</h3>

					{#if loadingLogs}
						<div class="flex justify-center items-center py-8">
							<LoadingSpinner size="md" />
							<span class="ml-3 text-gray-600">加载构建日志...</span>
						</div>
					{:else if buildLogs.length === 0}
						<div class="text-center py-8">
							<svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
							</svg>
							<h4 class="text-lg font-medium text-gray-900 mb-2">暂无日志</h4>
							<p class="text-gray-500">还没有构建日志记录</p>
						</div>
					{:else}
						<div class="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm max-h-64 overflow-y-auto">
							{#each buildLogs as log}
								<div class="flex items-start space-x-2 py-1">
									<span class="text-gray-500 text-xs whitespace-nowrap">
										{formatDateTime(log.created_at, 'HH:mm:ss')}
									</span>
									<span class="text-xs {getLogLevelStyle(log.level)} uppercase font-medium">
										{log.level}
									</span>
									{#if log.stage}
										<span class="text-blue-400 text-xs">[{log.stage}]</span>
									{/if}
									<span class="flex-1 text-xs">{log.message}</span>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			{/if}
		</div>

		<!-- 底部操作栏 -->
		{#if canManage}
			<div class="flex justify-between items-center p-6 border-t border-gray-200">
				<div class="flex space-x-3">
					{#if image.status === 'ready' && image.can_create_service}
						<button
							class="btn btn-primary"
							on:click={handleCreateService}
						>
							创建服务
						</button>
					{/if}
				</div>
				
				<button
					class="btn btn-danger"
					on:click={handleDelete}
				>
					删除镜像
				</button>
			</div>
		{/if}
	</div>
</div>

<!-- 创建服务模态框 -->
{#if showCreateServiceModal}
	<ServiceFromImageModal
		{image}
		on:created={handleServiceCreated}
		on:close={() => showCreateServiceModal = false}
	/>
{/if}

<style>
	.btn {
		@apply px-4 py-2 rounded-lg font-medium transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed;
	}

	.btn-sm {
		@apply px-3 py-1.5 text-sm;
	}

	.btn-primary {
		@apply bg-blue-600 text-white hover:bg-blue-700;
	}

	.btn-danger {
		@apply bg-red-600 text-white hover:bg-red-700;
	}
</style>