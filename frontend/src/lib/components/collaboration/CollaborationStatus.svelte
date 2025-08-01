<script>
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { api } from '$lib/utils/api.js';
	import Button from '../ui/Button.svelte';
	import Badge from '../ui/Badge.svelte';
	
	export let fileId = null;
	export let currentUser = null;
	export let showInline = false; // 是否内联显示
	
	const dispatch = createEventDispatcher();
	
	let collaborators = [];
	let isLoading = false;
	let error = null;
	let pollInterval = null;
	let isLocked = false;
	let canEdit = true;
	
	onMount(() => {
		if (fileId) {
			loadCollaborationStatus();
			startPolling();
		}
	});
	
	onDestroy(() => {
		stopPolling();
	});
	
	async function loadCollaborationStatus() {
		if (!fileId) return;
		
		isLoading = true;
		error = null;
		
		try {
			const response = await api.get(`/api/file-editor/files/${fileId}/collaboration`);
			const data = response.data;
			
			collaborators = data.active_sessions || [];
			isLocked = data.is_locked || false;
			canEdit = data.can_edit || false;
			
			// 过滤掉当前用户
			if (currentUser) {
				collaborators = collaborators.filter(
					session => session.user_id !== currentUser.id
				);
			}
			
			// 通知父组件状态变化
			dispatch('statusChange', {
				collaborators,
				isLocked,
				canEdit,
				totalActiveUsers: data.total_active_users
			});
			
		} catch (err) {
			console.error('获取协作状态失败:', err);
			error = err.response?.data?.detail || '获取协作状态失败';
		} finally {
			isLoading = false;
		}
	}
	
	function startPolling() {
		// 每30秒轮询一次协作状态
		pollInterval = setInterval(() => {
			loadCollaborationStatus();
		}, 30000);
	}
	
	function stopPolling() {
		if (pollInterval) {
			clearInterval(pollInterval);
			pollInterval = null;
		}
	}
	
	// 获取用户状态颜色
	function getStatusColor(isReadonly) {
		return isReadonly ? 'bg-yellow-400' : 'bg-green-400';
	}
	
	// 获取用户状态文本
	function getStatusText(isReadonly) {
		return isReadonly ? '查看中' : '编辑中';
	}
	
	// 格式化最后活动时间
	function formatLastActivity(dateString) {
		const date = new Date(dateString);
		const now = new Date();
		const diffMs = now - date;
		const diffMins = Math.floor(diffMs / (1000 * 60));
		
		if (diffMins < 1) {
			return '刚刚';
		} else if (diffMins < 60) {
			return `${diffMins}分钟前`;
		} else {
			const diffHours = Math.floor(diffMins / 60);
			return `${diffHours}小时前`;
		}
	}
	
	// 获取用户头像
	function getUserAvatar(user) {
		// 简单的头像生成逻辑
		if (user?.avatar) {
			return user.avatar;
		}
		
		const colors = ['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-pink-500', 'bg-indigo-500'];
		const colorIndex = (user?.username?.charCodeAt(0) || 0) % colors.length;
		
		return {
			initials: user?.username?.substring(0, 2).toUpperCase() || '??',
			color: colors[colorIndex]
		};
	}
	
	// 响应式处理
	$: if (fileId) {
		loadCollaborationStatus();
	}
</script>

{#if showInline}
	<!-- 内联显示模式 -->
	<div class="collaboration-inline flex items-center space-x-2">
		{#if isLoading}
			<div class="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
		{:else if error}
			<span class="text-red-500 text-sm">⚠️</span>
		{:else if collaborators.length > 0}
			<div class="flex items-center space-x-1">
				<span class="text-sm text-gray-600">协作中:</span>
				<div class="flex space-x-1">
					{#each collaborators.slice(0, 3) as session}
						{@const avatar = getUserAvatar(session.user)}
						<div class="relative">
							{#if typeof avatar === 'string'}
								<img
									src={avatar}
									alt={session.user?.username}
									class="w-6 h-6 rounded-full border-2 border-white"
								/>
							{:else}
								<div 
									class="w-6 h-6 rounded-full border-2 border-white flex items-center justify-center text-xs font-medium text-white {avatar.color}"
									title={session.user?.username}
								>
									{avatar.initials}
								</div>
							{/if}
							
							<!-- 状态指示器 -->
							<div 
								class="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white {getStatusColor(session.is_readonly)}"
								title={getStatusText(session.is_readonly)}
							></div>
						</div>
					{/each}
					
					{#if collaborators.length > 3}
						<div class="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-xs font-medium text-gray-600">
							+{collaborators.length - 3}
						</div>
					{/if}
				</div>
			</div>
		{:else if isLocked}
			<Badge variant="warning" size="sm">🔒 文件已锁定</Badge>
		{/if}
	</div>
{:else}
	<!-- 详细显示模式 -->
	<div class="collaboration-status bg-white rounded-lg border border-gray-200 p-4">
		<div class="flex items-center justify-between mb-4">
			<h3 class="text-lg font-medium text-gray-900">协作状态</h3>
			<Button
				variant="ghost"
				size="sm"
				on:click={loadCollaborationStatus}
				disabled={isLoading}
			>
				{#if isLoading}
					<div class="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
				{:else}
					🔄
				{/if}
			</Button>
		</div>
		
		{#if error}
			<div class="text-center py-6">
				<div class="text-red-500 mb-2">⚠️ {error}</div>
				<Button variant="outline" size="sm" on:click={loadCollaborationStatus}>
					重试
				</Button>
			</div>
		{:else if collaborators.length === 0}
			<div class="text-center py-6 text-gray-500">
				<div class="text-2xl mb-2">👤</div>
				<p class="text-sm">当前只有您在编辑此文件</p>
			</div>
		{:else}
			<!-- 协作者列表 -->
			<div class="space-y-3">
				<div class="text-sm text-gray-600 mb-3">
					共有 {collaborators.length + 1} 人正在处理此文件
				</div>
				
				{#each collaborators as session}
					{@const avatar = getUserAvatar(session.user)}
					<div class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
						<!-- 用户头像 -->
						<div class="relative flex-shrink-0">
							{#if typeof avatar === 'string'}
								<img
									src={avatar}
									alt={session.user?.username}
									class="w-10 h-10 rounded-full"
								/>
							{:else}
								<div 
									class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium text-white {avatar.color}"
								>
									{avatar.initials}
								</div>
							{/if}
							
							<!-- 状态指示器 -->
							<div 
								class="absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full border-2 border-white {getStatusColor(session.is_readonly)}"
							></div>
						</div>
						
						<!-- 用户信息 -->
						<div class="flex-1 min-w-0">
							<div class="flex items-center space-x-2">
								<h4 class="text-sm font-medium text-gray-900 truncate">
									{session.user?.username || 'Unknown User'}
								</h4>
								<Badge 
									variant={session.is_readonly ? 'secondary' : 'success'} 
									size="sm"
								>
									{getStatusText(session.is_readonly)}
								</Badge>
							</div>
							<p class="text-xs text-gray-500 mt-1">
								最后活动: {formatLastActivity(session.last_activity)}
							</p>
							{#if session.expires_at}
								<p class="text-xs text-gray-400">
									会话过期: {formatLastActivity(session.expires_at)}
								</p>
							{/if}
						</div>
						
						<!-- 操作按钮 -->
						<div class="flex-shrink-0">
							{#if session.user?.id !== currentUser?.id}
								<Button
									variant="outline"
									size="sm"
									on:click={() => dispatch('viewUser', { user: session.user })}
								>
									查看
								</Button>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		{/if}
		
		<!-- 状态信息 -->
		<div class="mt-4 pt-4 border-t border-gray-200">
			<div class="flex items-center justify-between text-sm">
				<div class="flex items-center space-x-4">
					<span class="text-gray-600">编辑权限:</span>
					<Badge variant={canEdit ? 'success' : 'warning'} size="sm">
						{canEdit ? '可编辑' : '只读'}
					</Badge>
				</div>
				
				{#if isLocked}
					<Badge variant="warning" size="sm">
						🔒 文件已锁定
					</Badge>
				{/if}
			</div>
			
			<div class="text-xs text-gray-500 mt-2">
				协作状态每30秒自动刷新
			</div>
		</div>
	</div>
{/if}

<style>
	.collaboration-inline {
		font-size: 0.875rem;
	}
	
	.collaboration-status {
		max-width: 400px;
	}
	
	@media (max-width: 640px) {
		.collaboration-status {
			max-width: none;
		}
	}
</style>