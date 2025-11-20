<script>
	import { page } from '$app/stores';
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/utils/api.js';
	
	import RepositoryHeader from '$lib/components/RepositoryHeader.svelte';
	import DraftManager from '$lib/components/draft/DraftManager.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Loading from '$lib/components/Loading.svelte';
	import Toast from '$lib/components/ui/Toast.svelte';

	// 路由参数
	$: username = $page.params.username;
	$: repositoryName = $page.params.repository;

	// 状态
	let repository = null;
	let userDrafts = [];
	let isLoading = true;
	let error = null;
	let toast = null;
	let currentUser = null;
	let filterType = 'all'; // all, auto, manual

	// 加载数据
	onMount(async () => {
		await Promise.all([
			loadRepository(),
			loadCurrentUser(),
			loadUserDrafts()
		]);
	});

	async function loadRepository() {
		try {
			const response = await api.getRepository(username, repositoryName);
			repository = response;
		} catch (err) {
			console.error('加载仓库信息失败:', err);
			error = err.response?.data?.detail || '加载仓库信息失败';
		}
	}

	async function loadCurrentUser() {
		// 临时简化：使用URL中的用户名作为当前用户
		currentUser = { username: username };
	}

	async function loadUserDrafts() {
		isLoading = true;
		error = null;

		try {
			// 临时简化：返回空的草稿列表
			userDrafts = [];
		} catch (err) {
			console.error('加载草稿失败:', err);
			error = err.response?.data?.detail || '加载草稿失败';
		} finally {
			isLoading = false;
		}
	}

	// 恢复草稿
	function handleRestoreDraft(event) {
		const { content, cursorPosition, filePath, draftId } = event.detail;
		
		// 跳转到编辑页面并传递草稿信息
		const editUrl = `/${username}/${repositoryName}/edit/${filePath}`;
		const params = new URLSearchParams({
			draft_id: draftId,
			restore: 'true'
		});
		
		goto(`${editUrl}?${params.toString()}`);
	}

	// 删除草稿
	function handleDraftDeleted(event) {
		toast = {
			type: 'success',
			message: '草稿已删除'
		};
		
		// 重新加载草稿列表
		loadUserDrafts();
	}

	// 处理错误
	function handleError(event) {
		toast = {
			type: 'error',
			message: event.detail.message
		};
	}

	// 批量删除草稿
	async function bulkDeleteDrafts() {
		if (!confirm('确定要删除所有自动保存的草稿吗？此操作无法撤销。')) {
			return;
		}

		try {
			await api.delete(`/api/repositories/${username}/${repositoryName}/drafts/cleanup`);
			toast = {
				type: 'success',
				message: '草稿清理完成'
			};
			await loadUserDrafts();
		} catch (err) {
			console.error('批量删除草稿失败:', err);
			toast = {
				type: 'error',
				message: '批量删除失败'
			};
		}
	}

	// 导出草稿
	async function exportDrafts() {
		try {
			const response = await api.get(`/api/repositories/${username}/${repositoryName}/drafts/export`, {
				responseType: 'blob'
			});

			// 创建下载链接
			const url = window.URL.createObjectURL(new Blob([response.data]));
			const link = document.createElement('a');
			link.href = url;
			link.setAttribute('download', `${repositoryName}_drafts_${new Date().toISOString().split('T')[0]}.zip`);
			document.body.appendChild(link);
			link.click();
			link.remove();
			window.URL.revokeObjectURL(url);

			toast = {
				type: 'success',
				message: '草稿导出完成'
			};
		} catch (err) {
			console.error('导出草稿失败:', err);
			toast = {
				type: 'error',
				message: '导出草稿失败'
			};
		}
	}

	// 格式化时间
	function formatDate(dateString) {
		const date = new Date(dateString);
		return new Intl.DateTimeFormat('zh-CN', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		}).format(date);
	}

	// 过滤草稿
	$: filteredDrafts = userDrafts.filter(draft => {
		if (filterType === 'auto') return draft.is_auto_save;
		if (filterType === 'manual') return !draft.is_auto_save;
		return true;
	});

	// 统计信息
	$: draftStats = {
		total: userDrafts.length,
		auto: userDrafts.filter(d => d.is_auto_save).length,
		manual: userDrafts.filter(d => !d.is_auto_save).length,
		totalSize: userDrafts.reduce((sum, d) => 
			sum + (new TextEncoder().encode(d.draft_content || '').length), 0
		)
	};
</script>

<svelte:head>
	<title>草稿管理 - {repositoryName} - GeoML-Hub</title>
</svelte:head>

{#if toast}
	<Toast type={toast.type} message={toast.message} on:close={() => toast = null} />
{/if}

<div class="drafts-page">
	<!-- 仓库头部 -->
	{#if repository}
		<RepositoryHeader {repository} activeTab="files" />
	{/if}

	<!-- 页面头部 -->
	<div class="bg-white border-b border-gray-200">
		<div class="container mx-auto px-4 py-6">
			<div class="flex items-center justify-between">
				<div>
					<nav class="flex items-center space-x-2 text-sm text-gray-600 mb-2">
						<a href="{base}/{username}/{repositoryName}" class="hover:text-blue-600">
							{repositoryName}
						</a>
						<span>/</span>
						<span class="text-blue-600 font-medium">草稿管理</span>
					</nav>
					
					<h1 class="text-2xl font-bold text-gray-900">草稿管理</h1>
					<p class="text-gray-600 mt-1">
						管理您在此仓库中的所有草稿文件
					</p>
				</div>

				<div class="flex items-center space-x-2">
					<Button
						variant="outline"
						size="sm"
						on:click={loadUserDrafts}
						disabled={isLoading}
					>
						🔄 刷新
					</Button>
					<Button
						variant="outline"
						size="sm"
						on:click={exportDrafts}
						disabled={userDrafts.length === 0}
					>
						📤 导出
					</Button>
					<Button
						variant="outline"
						size="sm"
						on:click={bulkDeleteDrafts}
						disabled={draftStats.auto === 0}
					>
						🗑️ 清理自动草稿
					</Button>
				</div>
			</div>
		</div>
	</div>

	<!-- 统计信息 -->
	<div class="bg-gray-50 border-b border-gray-200">
		<div class="container mx-auto px-4 py-4">
			<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
				<div class="bg-white rounded-lg p-4 border border-gray-200">
					<div class="text-2xl font-bold text-gray-900">{draftStats.total}</div>
					<div class="text-sm text-gray-600">总草稿数</div>
				</div>
				<div class="bg-white rounded-lg p-4 border border-gray-200">
					<div class="text-2xl font-bold text-blue-600">{draftStats.auto}</div>
					<div class="text-sm text-gray-600">自动保存</div>
				</div>
				<div class="bg-white rounded-lg p-4 border border-gray-200">
					<div class="text-2xl font-bold text-green-600">{draftStats.manual}</div>
					<div class="text-sm text-gray-600">手动保存</div>
				</div>
				<div class="bg-white rounded-lg p-4 border border-gray-200">
					<div class="text-2xl font-bold text-purple-600">
						{Math.round(draftStats.totalSize / 1024 * 100) / 100}
					</div>
					<div class="text-sm text-gray-600">总大小 (KB)</div>
				</div>
			</div>
		</div>
	</div>

	<!-- 过滤器 -->
	<div class="bg-white border-b border-gray-200">
		<div class="container mx-auto px-4 py-3">
			<div class="flex items-center space-x-4">
				<span class="text-sm font-medium text-gray-700">筛选:</span>
				<div class="flex space-x-1">
					<Button
						variant={filterType === 'all' ? 'primary' : 'ghost'}
						size="sm"
						on:click={() => filterType = 'all'}
					>
						全部 ({draftStats.total})
					</Button>
					<Button
						variant={filterType === 'auto' ? 'primary' : 'ghost'}
						size="sm"
						on:click={() => filterType = 'auto'}
					>
						自动保存 ({draftStats.auto})
					</Button>
					<Button
						variant={filterType === 'manual' ? 'primary' : 'ghost'}
						size="sm"
						on:click={() => filterType = 'manual'}
					>
						手动保存 ({draftStats.manual})
					</Button>
				</div>
			</div>
		</div>
	</div>

	<!-- 主要内容 -->
	<div class="container mx-auto px-4 py-6">
		{#if isLoading}
			<Loading message="加载草稿中..." />
		{:else if error}
			<div class="text-center py-12">
				<div class="text-red-500 text-lg mb-4">❌ {error}</div>
				<Button on:click={loadUserDrafts}>重试</Button>
			</div>
		{:else if filteredDrafts.length === 0}
			<div class="text-center py-12">
				<div class="text-gray-400 text-4xl mb-4">📝</div>
				<h3 class="text-lg font-medium text-gray-900 mb-2">
					{filterType === 'all' ? '暂无草稿' : `暂无${filterType === 'auto' ? '自动保存的' : '手动保存的'}草稿`}
				</h3>
				<p class="text-gray-600 mb-4">
					开始编辑文件时会自动创建草稿，您也可以手动保存草稿。
				</p>
				<Button
					variant="primary"
					on:click={() => goto(`${base}/${username}/${repositoryName}`)}
				>
					浏览文件
				</Button>
			</div>
		{:else}
			<!-- 草稿列表 -->
			<div class="space-y-4">
				{#each filteredDrafts as draft}
					<div class="bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors">
						<div class="p-6">
							<div class="flex items-start justify-between">
								<div class="flex-1 min-w-0">
									<!-- 草稿头部 -->
									<div class="flex items-center space-x-3 mb-3">
										<div class="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
											<span class="text-lg">
												{draft.is_auto_save ? '🔄' : '💾'}
											</span>
										</div>
										
										<div class="flex-1 min-w-0">
											<h3 class="text-lg font-medium text-gray-900 truncate">
												{draft.title || '未命名草稿'}
											</h3>
											<p class="text-sm text-gray-600">
												{draft.file?.filename || '未知文件'} • {formatDate(draft.created_at)}
											</p>
										</div>

										<div class="flex items-center space-x-2">
											<Badge 
												variant={draft.is_auto_save ? 'secondary' : 'primary'} 
												size="sm"
											>
												{draft.is_auto_save ? '自动保存' : '手动保存'}
											</Badge>
										</div>
									</div>

									<!-- 草稿信息 -->
									<div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600 mb-4">
										<div>
											<span class="font-medium">文件路径:</span>
											<span class="block truncate">{draft.file?.file_path || 'N/A'}</span>
										</div>
										<div>
											<span class="font-medium">大小:</span>
											<span class="block">
												{Math.round((new TextEncoder().encode(draft.draft_content || '').length) / 1024 * 100) / 100} KB
											</span>
										</div>
										<div>
											<span class="font-medium">行数:</span>
											<span class="block">
												{draft.draft_content?.split('\n').length || 0} 行
											</span>
										</div>
										<div>
											<span class="font-medium">描述:</span>
											<span class="block truncate">
												{draft.description || '无描述'}
											</span>
										</div>
									</div>

									<!-- 内容预览 -->
									{#if draft.draft_content}
										<div class="bg-gray-50 rounded-lg p-3 mb-4">
											<pre class="text-sm text-gray-700 font-mono whitespace-pre-wrap overflow-hidden max-h-20">
{draft.draft_content.split('\n').slice(0, 3).join('\n')}{draft.draft_content.split('\n').length > 3 ? '\n...' : ''}
											</pre>
										</div>
									{/if}

									<!-- 操作按钮 -->
									<div class="flex items-center space-x-2">
										<Button
											variant="primary"
											size="sm"
											on:click={() => handleRestoreDraft({ 
												detail: {
													content: draft.draft_content,
													cursorPosition: draft.cursor_position,
													filePath: draft.file?.file_path,
													draftId: draft.id
												}
											})}
										>
											📤 恢复编辑
										</Button>
										
										<Button
											variant="outline"
											size="sm"
											on:click={() => goto(`${base}/${username}/${repositoryName}/blob/${draft.file?.file_path}`)}
										>
											👁 查看原文件
										</Button>
									</div>
								</div>
							</div>
						</div>
					</div>
				{/each}
			</div>

			<!-- 加载更多 -->
			{#if filteredDrafts.length >= 50}
				<div class="text-center mt-6">
					<Button
						variant="outline"
						on:click={loadUserDrafts}
					>
						加载更多草稿
					</Button>
				</div>
			{/if}
		{/if}
	</div>
</div>

<style>
	.drafts-page {
		min-height: 100vh;
		background: #f8f9fa;
	}
</style>