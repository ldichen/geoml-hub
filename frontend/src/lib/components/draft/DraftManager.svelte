<script>
	import { createEventDispatcher } from 'svelte';
	import { onMount } from 'svelte';
	import { api } from '$lib/utils/api.js';
	import Button from '../ui/Button.svelte';
	import Badge from '../ui/Badge.svelte';
	import Modal from '../ui/Modal.svelte';
	import Loading from '../Loading.svelte';

	export let fileId = null;
	export let currentUser = null;
	export let showInModal = false;

	const dispatch = createEventDispatcher();

	let drafts = [];
	let isLoading = true;
	let error = null;
	let selectedDraft = null;
	let showPreviewModal = false;
	let showDeleteConfirmModal = false;
	let draftToDelete = null;

	onMount(async () => {
		await loadDrafts();
	});

	async function loadDrafts() {
		if (!fileId) return;

		isLoading = true;
		error = null;

		try {
			const response = await api.get(`/api/file-editor/files/${fileId}/drafts?limit=20`);
			drafts = response.data.drafts || [];
		} catch (err) {
			console.error('加载草稿失败:', err);
			error = err.response?.data?.detail || '加载草稿失败';
		} finally {
			isLoading = false;
		}
	}

	// 预览草稿
	function previewDraft(draft) {
		selectedDraft = draft;
		showPreviewModal = true;
	}

	// 恢复草稿
	async function restoreDraft(draft) {
		try {
			dispatch('restoreDraft', {
				content: draft.draft_content,
				cursorPosition: draft.cursor_position,
				selectionRange: draft.selection_range,
				draftId: draft.id
			});

			// 删除已恢复的草稿
			await deleteDraft(draft.id);
			
		} catch (err) {
			console.error('恢复草稿失败:', err);
			dispatch('error', { message: '恢复草稿失败' });
		}
	}

	// 删除草稿
	async function deleteDraft(draftId) {
		try {
			await api.delete(`/api/file-editor/drafts/${draftId}`);
			await loadDrafts();
			
			dispatch('draftDeleted', { draftId });
		} catch (err) {
			console.error('删除草稿失败:', err);
			dispatch('error', { message: '删除草稿失败' });
		}
	}

	// 确认删除草稿
	function confirmDeleteDraft(draft) {
		draftToDelete = draft;
		showDeleteConfirmModal = true;
	}

	// 处理删除确认
	function handleDeleteConfirm() {
		if (draftToDelete) {
			deleteDraft(draftToDelete.id);
			draftToDelete = null;
		}
		showDeleteConfirmModal = false;
	}

	// 创建新草稿
	async function createDraft(content, title = null, description = null) {
		try {
			const response = await api.post(`/api/file-editor/files/${fileId}/drafts`, {
				base_version_id: null,
				draft_content: content,
				cursor_position: null,
				selection_range: null,
				title: title || `草稿 - ${new Date().toLocaleString()}`,
				description: description || '手动保存的草稿'
			});

			await loadDrafts();
			dispatch('draftCreated', { draft: response.data });
			
		} catch (err) {
			console.error('创建草稿失败:', err);
			throw err;
		}
	}

	// 格式化时间
	function formatDate(dateString) {
		const date = new Date(dateString);
		const now = new Date();
		const diffMs = now - date;
		const diffMins = Math.floor(diffMs / (1000 * 60));

		if (diffMins < 1) {
			return '刚刚';
		} else if (diffMins < 60) {
			return `${diffMins}分钟前`;
		} else if (diffMins < 1440) {
			const diffHours = Math.floor(diffMins / 60);
			return `${diffHours}小时前`;
		} else {
			const diffDays = Math.floor(diffMins / 1440);
			return `${diffDays}天前`;
		}
	}

	// 格式化内容预览
	function formatContentPreview(content) {
		if (!content) return '空内容';
		
		const lines = content.split('\n');
		const preview = lines.slice(0, 3).join('\n');
		
		if (lines.length > 3) {
			return preview + '\n...';
		}
		
		return preview;
	}

	// 获取草稿类型图标
	function getDraftTypeIcon(isAuto) {
		return isAuto ? '🔄' : '💾';
	}

	// 获取草稿类型文本
	function getDraftTypeText(isAuto) {
		return isAuto ? '自动保存' : '手动保存';
	}

	// 暴露方法给父组件
	export { createDraft };
</script>

<div class="draft-manager">
	{#if showInModal}
		<!-- 模态框头部 -->
		<div class="flex items-center justify-between mb-4">
			<h2 class="text-lg font-medium text-gray-900">草稿管理</h2>
			<Button
				variant="outline"
				size="sm"
				on:click={loadDrafts}
				disabled={isLoading}
			>
				{#if isLoading}
					<div class="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
				{:else}
					🔄
				{/if}
			</Button>
		</div>
	{:else}
		<!-- 侧边栏头部 -->
		<div class="flex items-center justify-between mb-3">
			<h3 class="text-sm font-medium text-gray-900">草稿</h3>
			<Button
				variant="ghost"
				size="sm"
				on:click={loadDrafts}
				disabled={isLoading}
			>
				🔄
			</Button>
		</div>
	{/if}

	<!-- 内容区域 -->
	{#if isLoading}
		<Loading message="加载草稿中..." />
	{:else if error}
		<div class="text-center py-6">
			<div class="text-red-500 mb-2">⚠️ {error}</div>
			<Button variant="outline" size="sm" on:click={loadDrafts}>
				重试
			</Button>
		</div>
	{:else if drafts.length === 0}
		<div class="text-center py-6 text-gray-500">
			<div class="text-2xl mb-2">📝</div>
			<p class="text-sm">暂无草稿</p>
		</div>
	{:else}
		<!-- 草稿列表 -->
		<div class="space-y-3">
			{#each drafts as draft}
				<div class="bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors">
					<div class="p-4">
						<!-- 草稿头部 -->
						<div class="flex items-start justify-between mb-2">
							<div class="flex-1 min-w-0">
								<div class="flex items-center space-x-2 mb-1">
									<span class="text-lg">{getDraftTypeIcon(draft.is_auto_save)}</span>
									<h4 class="text-sm font-medium text-gray-900 truncate">
										{draft.title || '未命名草稿'}
									</h4>
									<Badge variant="secondary" size="sm">
										{getDraftTypeText(draft.is_auto_save)}
									</Badge>
								</div>
								
								<p class="text-xs text-gray-500 mb-2">
									{formatDate(draft.created_at)}
									{#if draft.description}
										• {draft.description}
									{/if}
								</p>
							</div>
						</div>

						<!-- 内容预览 -->
						<div class="bg-gray-50 rounded p-2 mb-3">
							<pre class="text-xs text-gray-700 font-mono whitespace-pre-wrap overflow-hidden max-h-16">
{formatContentPreview(draft.draft_content)}
							</pre>
						</div>

						<!-- 草稿统计 -->
						<div class="flex items-center space-x-4 text-xs text-gray-500 mb-3">
							<span>
								{draft.draft_content?.split('\n').length || 0} 行
							</span>
							<span>
								{Math.round((new TextEncoder().encode(draft.draft_content || '').length) / 1024 * 100) / 100} KB
							</span>
							{#if draft.cursor_position}
								<span>
									位置: 行{draft.cursor_position.line}列{draft.cursor_position.column}
								</span>
							{/if}
						</div>

						<!-- 操作按钮 -->
						<div class="flex items-center space-x-2">
							<Button
								variant="outline"
								size="sm"
								on:click={() => previewDraft(draft)}
							>
								👁 预览
							</Button>
							
							<Button
								variant="primary"
								size="sm"
								on:click={() => restoreDraft(draft)}
							>
								📤 恢复
							</Button>
							
							<Button
								variant="ghost"
								size="sm"
								on:click={() => confirmDeleteDraft(draft)}
							>
								🗑️
							</Button>
						</div>
					</div>
				</div>
			{/each}
		</div>

		<!-- 加载更多 -->
		{#if drafts.length >= 20}
			<div class="text-center mt-4">
				<Button
					variant="outline"
					size="sm"
					on:click={() => dispatch('loadMore')}
				>
					加载更多草稿
				</Button>
			</div>
		{/if}
	{/if}
</div>

<!-- 草稿预览模态框 -->
{#if showPreviewModal && selectedDraft}
	<Modal
		title="草稿预览"
		size="large"
		on:close={() => {
			showPreviewModal = false;
			selectedDraft = null;
		}}
	>
		<div class="space-y-4">
			<!-- 草稿信息 -->
			<div class="bg-gray-50 rounded-lg p-4">
				<div class="grid grid-cols-2 gap-4 text-sm">
					<div>
						<span class="font-medium text-gray-700">标题:</span>
						<span class="text-gray-900">{selectedDraft.title || '未命名草稿'}</span>
					</div>
					<div>
						<span class="font-medium text-gray-700">创建时间:</span>
						<span class="text-gray-900">{formatDate(selectedDraft.created_at)}</span>
					</div>
					<div>
						<span class="font-medium text-gray-700">类型:</span>
						<Badge variant="secondary" size="sm">
							{getDraftTypeText(selectedDraft.is_auto_save)}
						</Badge>
					</div>
					<div>
						<span class="font-medium text-gray-700">大小:</span>
						<span class="text-gray-900">
							{Math.round((new TextEncoder().encode(selectedDraft.draft_content || '').length) / 1024 * 100) / 100} KB
						</span>
					</div>
				</div>
				
				{#if selectedDraft.description}
					<div class="mt-2">
						<span class="font-medium text-gray-700">描述:</span>
						<span class="text-gray-900">{selectedDraft.description}</span>
					</div>
				{/if}
			</div>

			<!-- 内容预览 -->
			<div>
				<h4 class="text-sm font-medium text-gray-900 mb-2">内容预览</h4>
				<div class="bg-gray-900 rounded-lg p-4 max-h-96 overflow-y-auto">
					<pre class="text-sm text-gray-100 font-mono whitespace-pre-wrap">
{selectedDraft.draft_content || ''}
					</pre>
				</div>
			</div>
		</div>

		<div slot="footer" class="flex justify-end space-x-3">
			<Button
				variant="outline"
				on:click={() => {
					showPreviewModal = false;
					selectedDraft = null;
				}}
			>
				关闭
			</Button>
			<Button
				variant="primary"
				on:click={() => {
					restoreDraft(selectedDraft);
					showPreviewModal = false;
					selectedDraft = null;
				}}
			>
				恢复此草稿
			</Button>
		</div>
	</Modal>
{/if}

<!-- 删除确认模态框 -->
{#if showDeleteConfirmModal && draftToDelete}
	<Modal
		title="删除草稿"
		on:close={() => {
			showDeleteConfirmModal = false;
			draftToDelete = null;
		}}
	>
		<div class="space-y-4">
			<p class="text-gray-700">
				确定要删除草稿 "<strong>{draftToDelete.title || '未命名草稿'}</strong>" 吗？
			</p>
			<p class="text-sm text-gray-500">
				此操作无法撤销。
			</p>
		</div>

		<div slot="footer" class="flex justify-end space-x-3">
			<Button
				variant="outline"
				on:click={() => {
					showDeleteConfirmModal = false;
					draftToDelete = null;
				}}
			>
				取消
			</Button>
			<Button
				variant="danger"
				on:click={handleDeleteConfirm}
			>
				删除草稿
			</Button>
		</div>
	</Modal>
{/if}

<style>
	.draft-manager {
		max-height: 500px;
		overflow-y: auto;
	}
</style>