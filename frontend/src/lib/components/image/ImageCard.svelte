<script>
	import { createEventDispatcher } from 'svelte';
	import { formatFileSize, formatDateTime, formatRelativeTime } from '$lib/utils/format.js';

	export let image;
	export let canManage = false;

	const dispatch = createEventDispatcher();

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

	// 删除镜像
	function handleDelete() {
		if (confirm(`确定要删除镜像 ${image.name}:${image.tag} 吗？`)) {
			dispatch('delete', { imageId: image.id });
		}
	}

	// 创建服务
	function handleCreateService() {
		dispatch('createService', { image });
	}

	// 查看详情
	function handleViewDetail() {
		dispatch('viewDetail', { image });
	}
</script>

<div class="image-card bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200">
	<!-- 头部信息 -->
	<div class="flex items-start justify-between mb-4">
		<div class="flex-1">
			<div class="flex items-center mb-2">
				<h4 class="text-lg font-semibold text-gray-900 mr-3">
					{image.name}:{image.tag}
				</h4>
				<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getStatusStyle(image.status)}">
					{getStatusText(image.status)}
				</span>
			</div>
			
			{#if image.description}
				<p class="text-sm text-gray-600 mb-3">{image.description}</p>
			{/if}
			
			<div class="flex items-center text-xs text-gray-500 space-x-4">
				<span>镜像ID: {image.id}</span>
				{#if image.harbor_size}
					<span>大小: {formatFileSize(image.harbor_size)}</span>
				{/if}
				<span>创建于: {formatRelativeTime(image.created_at)}</span>
			</div>
		</div>

		<!-- 操作菜单 -->
		{#if canManage}
			<div class="relative group">
				<button class="p-2 hover:bg-gray-100 rounded-lg transition-colors">
					<svg class="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
						<path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path>
					</svg>
				</button>
				
				<!-- 下拉菜单 -->
				<div class="absolute right-0 top-full mt-1 w-48 bg-white rounded-lg border border-gray-200 shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
					<div class="py-1">
						<button
							class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
							on:click={handleViewDetail}
						>
							<svg class="w-4 h-4 mr-3 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
							</svg>
							查看详情
						</button>
						
						{#if image.status === 'ready' && image.can_create_service}
							<button
								class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
								on:click={handleCreateService}
							>
								<svg class="w-4 h-4 mr-3 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
								</svg>
								创建服务
							</button>
						{/if}
						
						<hr class="my-1 border-gray-100">
						
						<button
							class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
							on:click={handleDelete}
						>
							<svg class="w-4 h-4 mr-3 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
							</svg>
							删除镜像
						</button>
					</div>
				</div>
			</div>
		{/if}
	</div>

	<!-- 上传进度 -->
	{#if image.status === 'uploading'}
		<div class="mb-4">
			<div class="flex justify-between text-sm text-gray-600 mb-1">
				<span>上传进度</span>
				<span>{image.upload_progress}%</span>
			</div>
			<div class="w-full bg-gray-200 rounded-full h-2">
				<div 
					class="bg-blue-500 h-2 rounded-full transition-all duration-300"
					style="width: {image.upload_progress}%"
				></div>
			</div>
		</div>
	{/if}

	<!-- 错误信息 -->
	{#if image.status === 'failed' && image.error_message}
		<div class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
			<p class="text-sm text-red-600">{image.error_message}</p>
		</div>
	{/if}

	<!-- 服务统计 -->
	<div class="border-t border-gray-100 pt-4">
		<div class="flex items-center justify-between">
			<div class="flex items-center text-sm text-gray-600">
				<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"></path>
				</svg>
				<span>已创建 {image.service_count || 0}/2 个服务</span>
			</div>

			{#if image.status === 'ready'}
				<div class="flex items-center space-x-2">
					{#if image.can_create_service && canManage}
						<button
							class="btn btn-sm btn-primary"
							on:click={handleCreateService}
						>
							创建服务
						</button>
					{/if}
					
					<button
						class="btn btn-sm btn-outline"
						on:click={handleViewDetail}
					>
						查看详情
					</button>
				</div>
			{/if}
		</div>
	</div>

	<!-- Harbor镜像名称 -->
	{#if image.full_name}
		<div class="mt-3 p-2 bg-gray-50 rounded border">
			<p class="text-xs text-gray-500 mb-1">Harbor镜像路径:</p>
			<code class="text-xs text-gray-700 font-mono">{image.full_name}</code>
		</div>
	{/if}
</div>

<style>
	.image-card {
		@apply relative;
	}

	.btn {
		@apply px-3 py-1.5 rounded-lg font-medium transition-colors duration-200;
	}
	
	.btn:disabled {
		@apply opacity-50 cursor-not-allowed;
	}

	.btn-sm {
		@apply px-2 py-1 text-sm;
	}

	.btn-primary {
		@apply bg-blue-600 text-white;
	}
	
	.btn-primary:hover {
		@apply bg-blue-700;
	}

	.btn-outline {
		@apply border border-gray-300 text-gray-700;
	}
	
	.btn-outline:hover {
		@apply bg-gray-50;
	}
</style>