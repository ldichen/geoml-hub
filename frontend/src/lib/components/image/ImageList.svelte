<script>
	import { onMount, createEventDispatcher } from 'svelte';
	import { api } from '$lib/utils/api.js';
	import ImageCard from './ImageCard.svelte';
	import ImageUploadModal from './ImageUploadModal.svelte';
	import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte';
	import Toast from '$lib/components/common/Toast.svelte';

	export let repositoryId;
	export let canManage = false; // 是否有管理权限

	const dispatch = createEventDispatcher();

	let images = [];
	let loading = true;
	let error = null;
	let showUploadModal = false;
	let toast = { show: false, message: '', type: 'info' };

	// 加载镜像列表
	async function loadImages() {
		try {
			loading = true;
			error = null;
			const response = await api.getRepositoryImages(repositoryId);
			if (response.success) {
				images = response.data || [];
			} else {
				throw new Error(response.error || '获取镜像列表失败');
			}
		} catch (err) {
			console.error('加载镜像列表失败:', err);
			error = err.message;
			showToast('加载镜像列表失败: ' + err.message, 'error');
		} finally {
			loading = false;
		}
	}

	// 显示提示信息
	function showToast(message, type = 'info') {
		toast = { show: true, message, type };
		setTimeout(() => {
			toast.show = false;
		}, 3000);
	}

	// 处理镜像上传成功
	function handleImageUploaded(event) {
		const { image } = event.detail;
		showToast(`镜像 ${image.name}:${image.tag} 上传已开始`, 'success');
		showUploadModal = false;
		// 重新加载镜像列表
		loadImages();
	}

	// 处理镜像删除
	async function handleImageDelete(event) {
		const { imageId } = event.detail;
		try {
			const response = await api.deleteImage(imageId);
			if (response.success) {
				showToast('镜像删除成功', 'success');
				// 重新加载镜像列表
				loadImages();
			} else {
				throw new Error(response.error || '删除失败');
			}
		} catch (err) {
			console.error('删除镜像失败:', err);
			showToast('删除镜像失败: ' + err.message, 'error');
		}
	}

	// 处理创建服务
	function handleCreateService(event) {
		dispatch('createService', event.detail);
	}

	// 处理查看详情
	function handleViewDetail(event) {
		dispatch('viewDetail', event.detail);
	}

	onMount(() => {
		loadImages();
	});
</script>

<div class="image-list">
	<!-- 头部操作栏 -->
	<div class="flex justify-between items-center mb-6">
		<div>
			<h3 class="text-lg font-semibold text-gray-900">Docker镜像</h3>
			<p class="text-sm text-gray-500 mt-1">
				管理仓库的Docker镜像，每个仓库最多3个镜像
			</p>
		</div>
		
		{#if canManage}
			<button
				class="btn btn-primary"
				on:click={() => showUploadModal = true}
				disabled={images.length >= 3}
			>
				<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
				</svg>
				上传镜像
			</button>
		{/if}
	</div>

	<!-- 镜像数量统计 -->
	{#if !loading}
		<div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
			<div class="flex items-center">
				<svg class="w-5 h-5 text-blue-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2h4a1 1 0 011 1v1a1 1 0 01-1 1v9a2 2 0 01-2 2H5a2 2 0 01-2-2V7a1 1 0 01-1-1V5a1 1 0 011-1h4z"></path>
				</svg>
				<div>
					<p class="text-sm font-medium text-blue-800">
						已使用 {images.length}/3 个镜像位
					</p>
					<p class="text-xs text-blue-600 mt-1">
						每个镜像最多可创建2个服务实例
					</p>
				</div>
			</div>
		</div>
	{/if}

	<!-- 加载状态 -->
	{#if loading}
		<div class="flex justify-center items-center py-12">
			<LoadingSpinner size="md" />
			<span class="ml-3 text-gray-600">加载镜像列表...</span>
		</div>
	{/if}

	<!-- 错误状态 -->
	{#if error}
		<div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
			<svg class="mx-auto h-12 w-12 text-red-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
			</svg>
			<h3 class="text-lg font-medium text-red-800 mb-2">加载失败</h3>
			<p class="text-red-600 mb-4">{error}</p>
			<button class="btn btn-outline" on:click={loadImages}>重试</button>
		</div>
	{/if}

	<!-- 空状态 -->
	{#if !loading && !error && images.length === 0}
		<div class="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
			<svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2h4a1 1 0 011 1v1a1 1 0 01-1-1V7a1 1 0 01-1-1v9a2 2 0 01-2 2H5a2 2 0 01-2-2V7a1 1 0 01-1-1V5a1 1 0 011-1h4z"></path>
			</svg>
			<h3 class="text-lg font-medium text-gray-900 mb-2">暂无镜像</h3>
			<p class="text-gray-500 mb-4">
				上传Docker镜像来部署模型服务
			</p>
			{#if canManage}
				<button
					class="btn btn-primary"
					on:click={() => showUploadModal = true}
				>
					上传第一个镜像
				</button>
			{/if}
		</div>
	{/if}

	<!-- 镜像列表 -->
	{#if !loading && !error && images.length > 0}
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
			{#each images as image (image.id)}
				<ImageCard 
					{image}
					{canManage}
					on:delete={handleImageDelete}
					on:createService={handleCreateService}
					on:viewDetail={handleViewDetail}
				/>
			{/each}
		</div>
	{/if}
</div>

<!-- 上传模态框 -->
{#if showUploadModal}
	<ImageUploadModal
		{repositoryId}
		on:uploaded={handleImageUploaded}
		on:close={() => showUploadModal = false}
	/>
{/if}

<!-- 提示消息 -->
{#if toast.show}
	<Toast message={toast.message} type={toast.type} />
{/if}

<style>
	.image-list {
		@apply w-full;
	}

	.btn {
		@apply px-4 py-2 rounded-lg font-medium transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed;
	}

	.btn-primary {
		@apply bg-blue-600 text-white hover:bg-blue-700;
	}

	.btn-outline {
		@apply border border-gray-300 text-gray-700 hover:bg-gray-50;
	}
</style>