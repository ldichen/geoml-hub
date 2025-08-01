<script>
	import { createEventDispatcher } from 'svelte';
	import { onMount } from 'svelte';
	import Button from '../ui/Button.svelte';
	import Badge from '../ui/Badge.svelte';
	import Loading from '../Loading.svelte';
	import { api } from '$lib/utils/api.js';
	
	export let fileId = null;
	export let filePath = '';
	export let repository = null;
	export let currentVersionId = null;
	
	const dispatch = createEventDispatcher();
	
	let versions = [];
	let isLoading = true;
	let error = null;
	let selectedVersions = { from: null, to: null };
	let showDiff = false;
	
	onMount(async () => {
		await loadVersionHistory();
	});
	
	async function loadVersionHistory() {
		if (!fileId) return;
		
		isLoading = true;
		error = null;
		
		try {
			const response = await api.get(`/api/file-editor/files/${fileId}/versions?limit=50`);
			versions = response.data.versions || [];
		} catch (err) {
			console.error('加载版本历史失败:', err);
			error = err.response?.data?.detail || '加载版本历史失败';
		} finally {
			isLoading = false;
		}
	}
	
	// 查看版本内容
	function viewVersion(version) {
		dispatch('viewVersion', {
			versionId: version.id,
			versionNumber: version.version_number,
			versionHash: version.version_hash
		});
	}
	
	// 恢复到指定版本
	async function restoreVersion(version) {
		if (!confirm(`确定要恢复到版本 ${version.version_number} 吗？`)) {
			return;
		}
		
		try {
			const response = await api.post(`/api/file-editor/files/${fileId}/restore/${version.id}`, {
				message: `恢复到版本 ${version.version_number}: ${version.commit_message}`
			});
			
			dispatch('versionRestored', {
				newVersionId: response.data.id,
				restoredFromVersion: version.version_number
			});
			
			// 重新加载版本历史
			await loadVersionHistory();
			
		} catch (err) {
			console.error('恢复版本失败:', err);
			dispatch('error', {
				message: err.response?.data?.detail || '恢复版本失败'
			});
		}
	}
	
	// 选择版本进行对比
	function selectVersionForDiff(version, type) {
		selectedVersions[type] = version;
		
		if (selectedVersions.from && selectedVersions.to) {
			showVersionDiff();
		}
	}
	
	// 显示版本差异
	function showVersionDiff() {
		if (!selectedVersions.from || !selectedVersions.to) return;
		
		dispatch('showDiff', {
			fromVersion: selectedVersions.from,
			toVersion: selectedVersions.to
		});
		
		// 重置选择
		selectedVersions = { from: null, to: null };
	}
	
	// 下载版本文件
	async function downloadVersion(version) {
		try {
			const response = await api.get(`/api/file-editor/files/${fileId}/versions/${version.id}/content`, {
				responseType: 'blob'
			});
			
			// 创建下载链接
			const url = window.URL.createObjectURL(new Blob([response.data]));
			const link = document.createElement('a');
			link.href = url;
			link.setAttribute('download', `${filePath.split('/').pop()}_v${version.version_number}`);
			document.body.appendChild(link);
			link.click();
			link.remove();
			window.URL.revokeObjectURL(url);
			
		} catch (err) {
			console.error('下载版本失败:', err);
			dispatch('error', {
				message: '下载版本失败'
			});
		}
	}
	
	// 格式化时间
	function formatDate(dateString) {
		const date = new Date(dateString);
		const now = new Date();
		const diffMs = now - date;
		const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
		
		if (diffDays === 0) {
			return new Intl.DateTimeFormat('zh-CN', {
				hour: '2-digit',
				minute: '2-digit'
			}).format(date) + ' (今天)';
		} else if (diffDays === 1) {
			return '昨天 ' + new Intl.DateTimeFormat('zh-CN', {
				hour: '2-digit',
				minute: '2-digit'
			}).format(date);
		} else if (diffDays < 7) {
			return `${diffDays}天前`;
		} else {
			return new Intl.DateTimeFormat('zh-CN', {
				year: 'numeric',
				month: 'short',
				day: 'numeric',
				hour: '2-digit',
				minute: '2-digit'
			}).format(date);
		}
	}
	
	// 格式化文件大小
	function formatFileSize(bytes) {
		if (!bytes) return '0 B';
		const sizes = ['B', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(1024));
		return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
	}
	
	// 获取版本类型图标
	function getVersionTypeIcon(versionType) {
		const icons = {
			INITIAL: '🎉',
			EDIT: '✏️',
			MERGE: '🔀',
			RESTORE: '⮌'
		};
		return icons[versionType] || '📄';
	}
	
	// 获取版本类型描述
	function getVersionTypeText(versionType) {
		const texts = {
			INITIAL: '初始版本',
			EDIT: '编辑',
			MERGE: '合并',
			RESTORE: '恢复'
		};
		return texts[versionType] || '未知';
	}
</script>

<div class="version-history">
	<!-- 头部 -->
	<div class="flex items-center justify-between mb-6">
		<div>
			<h2 class="text-xl font-semibold text-gray-900">版本历史</h2>
			<p class="text-sm text-gray-600 mt-1">
				{filePath} 的所有版本记录
			</p>
		</div>
		
		<div class="flex items-center space-x-2">
			<Button
				variant="outline"
				size="sm"
				on:click={loadVersionHistory}
				disabled={isLoading}
			>
				🔄 刷新
			</Button>
			
			{#if selectedVersions.from && selectedVersions.to}
				<Button
					variant="primary"
					size="sm"
					on:click={showVersionDiff}
				>
					📊 对比版本
				</Button>
			{/if}
		</div>
	</div>
	
	<!-- 内容区域 -->
	{#if isLoading}
		<Loading message="加载版本历史中..." />
	{:else if error}
		<div class="text-center py-12">
			<div class="text-red-500 text-lg mb-4">❌ {error}</div>
			<Button on:click={loadVersionHistory}>重试</Button>
		</div>
	{:else if versions.length === 0}
		<div class="text-center py-12">
			<div class="text-gray-400 text-4xl mb-4">📜</div>
			<p class="text-gray-600">暂无版本历史</p>
		</div>
	{:else}
		<!-- 版本对比提示 -->
		{#if selectedVersions.from || selectedVersions.to}
			<div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
				<div class="flex items-center justify-between">
					<div class="flex items-center space-x-2">
						<span class="text-blue-600">📊</span>
						<span class="text-sm text-blue-800">
							选择版本进行对比
							{#if selectedVersions.from}
								- 已选择起始版本: v{selectedVersions.from.version_number}
							{/if}
							{#if selectedVersions.to}
								- 已选择结束版本: v{selectedVersions.to.version_number}
							{/if}
						</span>
					</div>
					<Button
						variant="ghost"
						size="sm"
						on:click={() => selectedVersions = { from: null, to: null }}
					>
						取消
					</Button>
				</div>
			</div>
		{/if}
		
		<!-- 版本列表 -->
		<div class="space-y-4">
			{#each versions as version, index}
				<div 
					class="bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
					class:border-blue-300={version.id === currentVersionId}
					class:bg-blue-50={version.id === currentVersionId}
				>
					<div class="p-6">
						<div class="flex items-start space-x-4">
							<!-- 版本图标和编号 -->
							<div class="flex-shrink-0">
								<div class="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center">
									<span class="text-lg">{getVersionTypeIcon(version.version_type)}</span>
								</div>
							</div>
							
							<!-- 版本信息 -->
							<div class="flex-1 min-w-0">
								<div class="flex items-center space-x-2 mb-2">
									<h3 class="text-lg font-medium text-gray-900">
										版本 {version.version_number}
									</h3>
									<Badge variant="secondary" size="sm">
										{version.version_hash}
									</Badge>
									{#if version.id === currentVersionId}
										<Badge variant="success" size="sm">
											当前版本
										</Badge>
									{/if}
									<Badge variant="outline" size="sm">
										{getVersionTypeText(version.version_type)}
									</Badge>
								</div>
								
								<p class="text-gray-700 mb-3">
									{version.commit_message || '无提交信息'}
								</p>
								
								<div class="flex items-center space-x-4 text-sm text-gray-600 mb-3">
									<span class="flex items-center space-x-1">
										<span>👤</span>
										<span>{version.author?.username || 'Unknown'}</span>
									</span>
									<span class="flex items-center space-x-1">
										<span>🕒</span>
										<span>{formatDate(version.created_at)}</span>
									</span>
									<span class="flex items-center space-x-1">
										<span>📦</span>
										<span>{formatFileSize(version.file_size)}</span>
									</span>
								</div>
								
								<!-- 差异摘要 -->
								{#if version.diff_summary}
									<div class="flex items-center space-x-4 text-sm mb-3">
										{#if version.diff_summary.lines_added > 0}
											<span class="text-green-600">
												+{version.diff_summary.lines_added} 行添加
											</span>
										{/if}
										{#if version.diff_summary.lines_removed > 0}
											<span class="text-red-600">
												-{version.diff_summary.lines_removed} 行删除
											</span>
										{/if}
										{#if version.diff_summary.lines_changed > 0}
											<span class="text-blue-600">
												~{version.diff_summary.lines_changed} 行修改
											</span>
										{/if}
									</div>
								{/if}
								
								<!-- 操作按钮 -->
								<div class="flex items-center space-x-2">
									<Button
										variant="outline"
										size="sm"
										on:click={() => viewVersion(version)}
									>
										👁 查看
									</Button>
									
									{#if version.id !== currentVersionId}
										<Button
											variant="outline"
											size="sm"
											on:click={() => restoreVersion(version)}
										>
											⮌ 恢复
										</Button>
									{/if}
									
									<Button
										variant="outline"
										size="sm"
										on:click={() => downloadVersion(version)}
									>
										📥 下载
									</Button>
									
									<!-- 版本对比选择 -->
									<div class="flex items-center space-x-1">
										<Button
											variant={selectedVersions.from?.id === version.id ? 'primary' : 'ghost'}
											size="sm"
											on:click={() => selectVersionForDiff(version, 'from')}
										>
											A
										</Button>
										<Button
											variant={selectedVersions.to?.id === version.id ? 'primary' : 'ghost'}
											size="sm"
											on:click={() => selectVersionForDiff(version, 'to')}
										>
											B
										</Button>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			{/each}
		</div>
		
		<!-- 加载更多 -->
		{#if versions.length >= 50}
			<div class="text-center mt-6">
				<Button
					variant="outline"
					on:click={() => dispatch('loadMore')}
				>
					加载更多版本
				</Button>
			</div>
		{/if}
	{/if}
</div>

<style>
	.version-history {
		max-width: 800px;
		margin: 0 auto;
		padding: 24px;
	}
</style>