<script>
	import { createEventDispatcher } from 'svelte';
	import { onMount, onDestroy } from 'svelte';
	import { api } from '$lib/utils/api.js';

	export let fileId = null;
	export let content = '';
	export let cursorPosition = null;
	export let selectionRange = null;
	export let autoSaveInterval = 30000; // 30秒
	export let enabled = true;
	export let baseVersionId = null;

	const dispatch = createEventDispatcher();

	let autoSaveTimer = null;
	let lastSavedContent = '';
	let isSaving = false;
	let lastSaveTime = null;
	let saveStatus = 'idle'; // idle, saving, saved, error

	onMount(() => {
		if (enabled) {
			startAutoSave();
		}
	});

	onDestroy(() => {
		stopAutoSave();
	});

	// 开始自动保存
	function startAutoSave() {
		if (autoSaveTimer) return;

		autoSaveTimer = setInterval(() => {
			if (shouldSave()) {
				saveDraft();
			}
		}, autoSaveInterval);
	}

	// 停止自动保存
	function stopAutoSave() {
		if (autoSaveTimer) {
			clearInterval(autoSaveTimer);
			autoSaveTimer = null;
		}
	}

	// 检查是否需要保存
	function shouldSave() {
		if (!enabled || !fileId || isSaving) return false;
		if (!content || content.trim() === '') return false;
		if (content === lastSavedContent) return false;
		
		return true;
	}

	// 保存草稿
	async function saveDraft() {
		if (!shouldSave()) return;

		isSaving = true;
		saveStatus = 'saving';

		try {
			const response = await api.post(`/api/file-editor/files/${fileId}/drafts`, {
				base_version_id: baseVersionId,
				draft_content: content,
				cursor_position: cursorPosition,
				selection_range: selectionRange,
				title: `自动保存 - ${new Date().toLocaleString()}`,
				description: '自动保存的草稿',
				is_auto_save: true
			});

			lastSavedContent = content;
			lastSaveTime = new Date();
			saveStatus = 'saved';

			dispatch('draftSaved', {
				draft: response.data,
				timestamp: lastSaveTime
			});

			// 3秒后重置状态
			setTimeout(() => {
				if (saveStatus === 'saved') {
					saveStatus = 'idle';
				}
			}, 3000);

		} catch (err) {
			console.error('自动保存草稿失败:', err);
			saveStatus = 'error';
			
			dispatch('saveError', {
				error: err.response?.data?.detail || '自动保存失败',
				timestamp: new Date()
			});

			// 5秒后重置错误状态
			setTimeout(() => {
				if (saveStatus === 'error') {
					saveStatus = 'idle';
				}
			}, 5000);
		} finally {
			isSaving = false;
		}
	}

	// 手动保存
	export async function forceSave() {
		if (!fileId || !content) return;

		await saveDraft();
	}

	// 清理旧草稿
	async function cleanupOldDrafts() {
		try {
			await api.delete(`/api/file-editor/files/${fileId}/drafts/cleanup`);
		} catch (err) {
			console.error('清理旧草稿失败:', err);
		}
	}

	// 格式化最后保存时间
	function formatLastSaveTime() {
		if (!lastSaveTime) return '';

		const now = new Date();
		const diffMs = now - lastSaveTime;
		const diffSecs = Math.floor(diffMs / 1000);

		if (diffSecs < 60) {
			return `${diffSecs}秒前`;
		} else if (diffSecs < 3600) {
			const diffMins = Math.floor(diffSecs / 60);
			return `${diffMins}分钟前`;
		} else {
			return lastSaveTime.toLocaleTimeString();
		}
	}

	// 响应式更新
	$: if (enabled && fileId) {
		startAutoSave();
	} else {
		stopAutoSave();
	}

	// 导出状态和方法
	export { saveStatus, lastSaveTime, formatLastSaveTime, cleanupOldDrafts };
</script>

<!-- 自动保存状态指示器 -->
<div class="auto-saver-status">
	{#if saveStatus === 'saving'}
		<div class="flex items-center space-x-2 text-blue-600">
			<div class="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
			<span class="text-xs">保存中...</span>
		</div>
	{:else if saveStatus === 'saved'}
		<div class="flex items-center space-x-2 text-green-600">
			<span class="text-xs">✓</span>
			<span class="text-xs">已保存 {formatLastSaveTime()}</span>
		</div>
	{:else if saveStatus === 'error'}
		<div class="flex items-center space-x-2 text-red-600">
			<span class="text-xs">⚠️</span>
			<span class="text-xs">保存失败</span>
		</div>
	{:else if enabled && lastSaveTime}
		<div class="flex items-center space-x-2 text-gray-500">
			<span class="text-xs">💾</span>
			<span class="text-xs">上次保存: {formatLastSaveTime()}</span>
		</div>
	{/if}
</div>

<style>
	.auto-saver-status {
		display: inline-flex;
		align-items: center;
		font-size: 0.75rem;
		line-height: 1rem;
	}
</style>