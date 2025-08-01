<script>
	import { createEventDispatcher } from 'svelte';
	import { onMount } from 'svelte';
	import Button from '../ui/Button.svelte';
	import Badge from '../ui/Badge.svelte';
	
	export const repository = null; // External reference only
	export let filePath = '';
	export let activeView = 'files'; // files, history, collaborators
	
	const dispatch = createEventDispatcher();
	
	let fileTree = [];
	let recentFiles = [];
	let versionHistory = [];
	let activeCollaborators = [];
	let isLoading = false;
	
	// 侧边栏视图选项
	const views = [
		{ id: 'files', label: '文件', icon: '📁' },
		{ id: 'history', label: '历史', icon: '📜' },
		{ id: 'collaborators', label: '协作', icon: '👥' }
	];
	
	// 模拟数据加载
	onMount(async () => {
		await loadData();
	});
	
	async function loadData() {
		isLoading = true;
		try {
			// 模拟加载文件树
			fileTree = [
				{
					name: 'README.md',
					type: 'file',
					path: 'README.md',
					size: '2.1 KB',
					modified: '2024-01-15'
				},
				{
					name: 'model.py',
					type: 'file', 
					path: 'model.py',
					size: '15.3 KB',
					modified: '2024-01-14'
				},
				{
					name: 'config',
					type: 'directory',
					path: 'config',
					children: [
						{
							name: 'config.yaml',
							type: 'file',
							path: 'config/config.yaml',
							size: '1.2 KB',
							modified: '2024-01-13'
						}
					]
				},
				{
					name: 'data',
					type: 'directory',
					path: 'data',
					children: [
						{
							name: 'train.json',
							type: 'file',
							path: 'data/train.json',
							size: '125.4 KB',
							modified: '2024-01-12'
						}
					]
				}
			];
			
			// 模拟最近文件
			recentFiles = [
				{ name: 'model.py', path: 'model.py', modified: '刚刚' },
				{ name: 'README.md', path: 'README.md', modified: '1小时前' },
				{ name: 'config.yaml', path: 'config/config.yaml', modified: '昨天' }
			];
			
			// 模拟版本历史
			versionHistory = [
				{
					id: 'v1.2.0',
					message: '添加新的预处理功能',
					author: 'user1',
					date: '2024-01-15 14:30',
					filesChanged: 3
				},
				{
					id: 'v1.1.9',
					message: '修复数据加载bug',
					author: 'user2', 
					date: '2024-01-14 09:15',
					filesChanged: 1
				}
			];
			
			// 模拟协作者
			activeCollaborators = [
				{
					name: 'Alice Chen',
					avatar: '👩‍💻',
					status: 'editing',
					file: 'model.py',
					lastSeen: '现在'
				},
				{
					name: 'Bob Wang',
					avatar: '👨‍💻',
					status: 'viewing',
					file: 'README.md',
					lastSeen: '2分钟前'
				}
			];
		} catch (error) {
			console.error('加载侧边栏数据失败:', error);
		} finally {
			isLoading = false;
		}
	}
	
	function selectFile(file) {
		dispatch('fileSelect', {
			path: file.path,
			name: file.name,
			type: file.type
		});
	}
	
	function getFileIcon(fileName) {
		const ext = fileName.split('.').pop().toLowerCase();
		const iconMap = {
			md: '📝',
			py: '🐍',
			js: '📜',
			json: '🔧',
			yaml: '⚙️',
			yml: '⚙️',
			txt: '📄',
			csv: '📊',
			png: '🖼',
			jpg: '🖼',
			jpeg: '🖼'
		};
		return iconMap[ext] || '📄';
	}
	
	function formatFileSize(bytes) {
		if (!bytes) return '';
		const sizes = ['B', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(1024));
		return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
	}
</script>

<div class="editor-sidebar w-64 bg-gray-50 border-r border-gray-200 flex flex-col">
	<!-- 侧边栏头部 -->
	<div class="sidebar-header px-4 py-3 border-b border-gray-200">
		<div class="flex space-x-1">
			{#each views as view}
				<button
					class="px-3 py-1.5 text-xs rounded transition-colors"
					class:bg-blue-100={activeView === view.id}
					class:text-blue-700={activeView === view.id}
					class:text-gray-600={activeView !== view.id}
					class:hover:bg-gray-100={activeView !== view.id}
					on:click={() => activeView = view.id}
				>
					<span class="mr-1">{view.icon}</span>
					{view.label}
				</button>
			{/each}
		</div>
	</div>
	
	<!-- 侧边栏内容 -->
	<div class="sidebar-content flex-1 overflow-y-auto">
		{#if isLoading}
			<div class="p-4 text-center">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
				<p class="text-sm text-gray-600 mt-2">加载中...</p>
			</div>
		{:else}
			<!-- 文件浏览视图 -->
			{#if activeView === 'files'}
				<div class="p-3">
					<!-- 操作按钮 -->
					<div class="mb-4 space-y-2">
						<Button
							variant="outline"
							size="sm"
							class="w-full justify-start"
							on:click={() => dispatch('newFile')}
						>
							<span class="mr-2">📄</span>
							新建文件
						</Button>
						<Button
							variant="outline"
							size="sm"
							class="w-full justify-start"
							on:click={() => dispatch('uploadFile')}
						>
							<span class="mr-2">📤</span>
							上传文件
						</Button>
					</div>
					
					<!-- 最近文件 -->
					{#if recentFiles.length > 0}
						<div class="mb-4">
							<h4 class="text-xs font-medium text-gray-700 mb-2">最近文件</h4>
							<div class="space-y-1">
								{#each recentFiles as file}
									<button
										class="w-full text-left p-2 rounded hover:bg-gray-100 transition-colors"
										class:bg-blue-50={filePath === file.path}
										on:click={() => selectFile(file)}
									>
										<div class="flex items-center space-x-2">
											<span class="text-sm">{getFileIcon(file.name)}</span>
											<div class="flex-1 min-w-0">
												<p class="text-sm font-medium text-gray-900 truncate">
													{file.name}
												</p>
												<p class="text-xs text-gray-500">
													{file.modified}
												</p>
											</div>
										</div>
									</button>
								{/each}
							</div>
						</div>
					{/if}
					
					<!-- 文件树 -->
					<div>
						<h4 class="text-xs font-medium text-gray-700 mb-2">所有文件</h4>
						<div class="space-y-1">
							{#each fileTree as item}
								<div class="file-tree-item">
									{#if item.type === 'directory'}
										<details class="group">
											<summary class="flex items-center space-x-2 p-2 rounded hover:bg-gray-100 cursor-pointer">
												<span class="text-sm">📁</span>
												<span class="text-sm font-medium text-gray-900">{item.name}</span>
											</summary>
											<div class="ml-4 mt-1 space-y-1">
												{#each item.children as child}
													<button
														class="w-full text-left p-2 rounded hover:bg-gray-100 transition-colors"
														class:bg-blue-50={filePath === child.path}
														on:click={() => selectFile(child)}
													>
														<div class="flex items-center space-x-2">
															<span class="text-sm">{getFileIcon(child.name)}</span>
															<div class="flex-1 min-w-0">
																<p class="text-sm text-gray-900 truncate">{child.name}</p>
																<p class="text-xs text-gray-500">{child.size}</p>
															</div>
														</div>
													</button>
												{/each}
											</div>
										</details>
									{:else}
										<button
											class="w-full text-left p-2 rounded hover:bg-gray-100 transition-colors"
											class:bg-blue-50={filePath === item.path}
											on:click={() => selectFile(item)}
										>
											<div class="flex items-center space-x-2">
												<span class="text-sm">{getFileIcon(item.name)}</span>
												<div class="flex-1 min-w-0">
													<p class="text-sm text-gray-900 truncate">{item.name}</p>
													<p class="text-xs text-gray-500">{item.size}</p>
												</div>
											</div>
										</button>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				</div>
			{/if}
			
			<!-- 版本历史视图 -->
			{#if activeView === 'history'}
				<div class="p-3">
					<h4 class="text-xs font-medium text-gray-700 mb-3">版本历史</h4>
					<div class="space-y-3">
						{#each versionHistory as version}
							<div class="p-3 bg-white rounded border border-gray-200 hover:border-gray-300 transition-colors">
								<div class="flex items-start justify-between">
									<div class="flex-1 min-w-0">
										<p class="text-sm font-medium text-gray-900">{version.id}</p>
										<p class="text-sm text-gray-600 mt-1">{version.message}</p>
										<div class="flex items-center space-x-2 mt-2 text-xs text-gray-500">
											<span>{version.author}</span>
											<span>•</span>
											<span>{version.date}</span>
										</div>
									</div>
									<Badge variant="secondary" size="sm">
										{version.filesChanged} 文件
									</Badge>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}
			
			<!-- 协作者视图 -->
			{#if activeView === 'collaborators'}
				<div class="p-3">
					<h4 class="text-xs font-medium text-gray-700 mb-3">当前协作者</h4>
					<div class="space-y-3">
						{#each activeCollaborators as collaborator}
							<div class="flex items-center space-x-3 p-2 rounded hover:bg-gray-100">
								<div class="relative">
									<span class="text-2xl">{collaborator.avatar}</span>
									<div 
										class="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white"
										class:bg-green-400={collaborator.status === 'editing'}
										class:bg-yellow-400={collaborator.status === 'viewing'}
									></div>
								</div>
								<div class="flex-1 min-w-0">
									<p class="text-sm font-medium text-gray-900">{collaborator.name}</p>
									<p class="text-xs text-gray-500">
										{collaborator.status === 'editing' ? '正在编辑' : '正在查看'} {collaborator.file}
									</p>
									<p class="text-xs text-gray-400">{collaborator.lastSeen}</p>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		{/if}
	</div>
</div>

<style>
	.editor-sidebar {
		background: linear-gradient(to bottom, #fafafa, #f8f9fa);
		border-right: 1px solid #e9ecef;
	}
	
	.sidebar-header {
		background: rgba(255, 255, 255, 0.7);
		backdrop-filter: blur(8px);
	}
	
	.file-tree-item :global(details[open] > summary) {
		margin-bottom: 4px;
	}
	
	.file-tree-item :global(summary::marker) {
		display: none;
	}
	
	.file-tree-item :global(summary::before) {
		content: '▶';
		display: inline-block;
		margin-right: 4px;
		transition: transform 0.2s;
		font-size: 10px;
	}
	
	.file-tree-item :global(details[open] summary::before) {
		transform: rotate(90deg);
	}
	
	@media (max-width: 768px) {
		.editor-sidebar {
			width: 240px;
		}
	}
</style>