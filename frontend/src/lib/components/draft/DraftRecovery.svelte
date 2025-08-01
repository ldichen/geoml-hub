<script>
	import { createEventDispatcher } from 'svelte';
	import { onMount } from 'svelte';
	import { api } from '$lib/utils/api.js';
	import Button from '../ui/Button.svelte';
	import Badge from '../ui/Badge.svelte';
	import Modal from '../ui/Modal.svelte';

	export let fileId = null;
	export let showOnMount = false;

	const dispatch = createEventDispatcher();

	let availableDrafts = [];
	let isLoading = false;
	let error = null;
	let showRecoveryModal = false;
	let selectedDraft = null;

	onMount(async () => {
		if (showOnMount && fileId) {
			await checkForRecoverableDrafts();
		}
	});

	// 检查可恢复的草稿
	async function checkForRecoverableDrafts() {
		if (!fileId) return;

		isLoading = true;
		error = null;

		try {
			// 获取最近的草稿
			const response = await api.get(`/api/file-editor/files/${fileId}/drafts?limit=5&only_recent=true`);
			const recentDrafts = response.data.drafts || [];

			// 过滤出可能需要恢复的草稿（最近24小时内的）
			const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
			availableDrafts = recentDrafts.filter(draft => {
				const draftDate = new Date(draft.created_at);
				return draftDate > oneDayAgo;
			});

			// 如果有可恢复的草稿，显示恢复提示
			if (availableDrafts.length > 0) {
				showRecoveryModal = true;
			}

		} catch (err) {
			console.error('检查可恢复草稿失败:', err);
			error = err.response?.data?.detail || '检查草稿失败';
		} finally {
			isLoading = false;
		}
	}

	// 恢复选中的草稿
	function recoverDraft(draft) {
		dispatch('recoverDraft', {
			content: draft.draft_content,
			cursorPosition: draft.cursor_position,
			selectionRange: draft.selection_range,
			draftId: draft.id,
			draftTitle: draft.title
		});

		showRecoveryModal = false;
		selectedDraft = null;
	}

	// 忽略草稿恢复
	function ignoreDrafts() {
		showRecoveryModal = false;
		selectedDraft = null;
		
		dispatch('ignoreDrafts', {
			ignoredDrafts: availableDrafts.map(d => d.id)
		});
	}

	// 删除选中的草稿
	async function deleteDraft(draftId) {
		try {
			await api.delete(`/api/file-editor/drafts/${draftId}`);
			
			// 从列表中移除
			availableDrafts = availableDrafts.filter(d => d.id !== draftId);
			
			// 如果没有更多草稿，关闭模态框
			if (availableDrafts.length === 0) {
				showRecoveryModal = false;
			}

		} catch (err) {
			console.error('删除草稿失败:', err);
			error = '删除草稿失败';
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
			return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
		}
	}

	// 格式化内容预览
	function formatContentPreview(content) {
		if (!content) return '空内容';
		
		const lines = content.split('\n');
		const preview = lines.slice(0, 2).join('\n');
		
		if (lines.length > 2) {
			return preview + '...';
		}
		
		return preview;
	}

	// 获取草稿优先级（用于排序）
	function getDraftPriority(draft) {
		const isRecent = (new Date() - new Date(draft.created_at)) < (2 * 60 * 60 * 1000); // 2小时内
		const hasContent = draft.draft_content && draft.draft_content.trim().length > 50;
		const isAutoSave = draft.is_auto_save;

		let priority = 0;
		if (isRecent) priority += 3;
		if (hasContent) priority += 2;
		if (!isAutoSave) priority += 1; // 手动保存的优先级更高

		return priority;
	}

	// 手动触发检查
	export async function triggerCheck() {
		await checkForRecoverableDrafts();
	}

	// 排序草稿（按优先级和时间）
	$: sortedDrafts = availableDrafts
		.map(draft => ({
			...draft,
			priority: getDraftPriority(draft)
		}))
		.sort((a, b) => {
			if (a.priority !== b.priority) {
				return b.priority - a.priority;
			}
			return new Date(b.created_at) - new Date(a.created_at);
		});
</script>

<!-- 草稿恢复模态框 -->
{#if showRecoveryModal}
	<Modal
		title="发现未保存的草稿"
		size="large"
		on:close={() => showRecoveryModal = false}
	>
		<div class="space-y-4">
			<!-- 提示信息 -->
			<div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
				<div class="flex items-start space-x-3">
					<span class="text-blue-600 text-xl">💡</span>
					<div>
						<h4 class="text-sm font-medium text-blue-900 mb-1">
							检测到未保存的草稿
						</h4>
						<p class="text-sm text-blue-800">
							我们发现您之前编辑此文件时有未保存的草稿。您可以选择恢复其中一个草稿继续编辑，或者忽略它们开始新的编辑。
						</p>
					</div>
				</div>
			</div>

			<!-- 草稿列表 -->
			{#if isLoading}
				<div class="text-center py-4">
					<div class="inline-block w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
					<p class="text-sm text-gray-600 mt-2">检查草稿中...</p>
				</div>
			{:else if error}
				<div class="text-center py-4">
					<p class="text-red-600 text-sm">{error}</p>
				</div>
			{:else if sortedDrafts.length > 0}
				<div class="space-y-3 max-h-60 overflow-y-auto">
					{#each sortedDrafts as draft}
						<div 
							class="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors"
							class:ring-2={selectedDraft?.id === draft.id}
							class:ring-blue-500={selectedDraft?.id === draft.id}
							class:border-blue-300={selectedDraft?.id === draft.id}
						>
							<div class="flex items-start justify-between">
								<div class="flex-1 min-w-0">
									<!-- 草稿头部 -->
									<div class="flex items-center space-x-2 mb-2">
										<h4 class="text-sm font-medium text-gray-900 truncate">
											{draft.title || '未命名草稿'}
										</h4>
										<Badge 
											variant={draft.is_auto_save ? 'secondary' : 'primary'} 
											size="sm"
										>
											{draft.is_auto_save ? '自动保存' : '手动保存'}
										</Badge>
										{#if draft.priority >= 4}
											<Badge variant="warning" size="sm">
												推荐
											</Badge>
										{/if}
									</div>

									<!-- 时间和描述 -->
									<p class="text-xs text-gray-500 mb-2">
										{formatDate(draft.created_at)}
										{#if draft.description}
											• {draft.description}
										{/if}
									</p>

									<!-- 内容预览 -->
									<div class="bg-gray-50 rounded p-2 mb-2">
										<pre class="text-xs text-gray-700 font-mono whitespace-pre-wrap overflow-hidden max-h-12">
{formatContentPreview(draft.draft_content)}
										</pre>
									</div>

									<!-- 统计信息 -->
									<div class="flex items-center space-x-4 text-xs text-gray-500">
										<span>
											{draft.draft_content?.split('\n').length || 0} 行
										</span>
										<span>
											{Math.round((new TextEncoder().encode(draft.draft_content || '').length) / 1024 * 100) / 100} KB
										</span>
									</div>
								</div>

								<!-- 操作按钮 -->
								<div class="flex items-center space-x-2 ml-4">
									<Button
										variant="outline"
										size="sm"
										on:click={() => selectedDraft = selectedDraft?.id === draft.id ? null : draft}
									>
										{selectedDraft?.id === draft.id ? '取消选择' : '选择'}
									</Button>
									<Button
										variant="ghost"
										size="sm"
										on:click={() => deleteDraft(draft.id)}
									>
										🗑️
									</Button>
								</div>
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<div class="text-center py-4 text-gray-500">
					<p class="text-sm">没有找到可恢复的草稿</p>
				</div>
			{/if}
		</div>

		<div slot="footer" class="flex justify-between">
			<Button
				variant="outline"
				on:click={ignoreDrafts}
			>
				忽略草稿
			</Button>
			
			<div class="flex space-x-3">
				<Button
					variant="outline"
					on:click={() => showRecoveryModal = false}
				>
					稍后决定
				</Button>
				<Button
					variant="primary"
					disabled={!selectedDraft}
					on:click={() => recoverDraft(selectedDraft)}
				>
					恢复选中的草稿
				</Button>
			</div>
		</div>
	</Modal>
{/if}

<style>
	/* 自定义样式 */
</style>