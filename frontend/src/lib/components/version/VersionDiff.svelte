<script>
	import { onMount } from 'svelte';
	import { api } from '$lib/utils/api.js';
	import Button from '../ui/Button.svelte';
	import Badge from '../ui/Badge.svelte';
	import Loading from '../Loading.svelte';
	
	export let fileId = null;
	export let fromVersion = null;
	export let toVersion = null;
	export let filePath = '';
	
	let diffData = null;
	let isLoading = true;
	let error = null;
	let viewMode = 'split'; // split, unified, side-by-side
	let showWhitespace = false;
	let showLineNumbers = true;
	
	onMount(async () => {
		await loadDiff();
	});
	
	async function loadDiff() {
		if (!fileId || !fromVersion || !toVersion) return;
		
		isLoading = true;
		error = null;
		
		try {
			const response = await api.get(
				`/api/file-editor/files/${fileId}/versions/${fromVersion.id}/diff/${toVersion.id}?include_content=true`
			);
			
			diffData = response.data;
			
		} catch (err) {
			console.error('加载版本差异失败:', err);
			error = err.response?.data?.detail || '加载版本差异失败';
		} finally {
			isLoading = false;
		}
	}
	
	// 解析差异内容
	function parseDiffContent(diffContent) {
		if (!diffContent) return [];
		
		const lines = diffContent.split('\n');
		const chunks = [];
		let currentChunk = null;
		
		for (let i = 0; i < lines.length; i++) {
			const line = lines[i];
			
			if (line.startsWith('@@')) {
				// 新的代码块
				if (currentChunk) {
					chunks.push(currentChunk);
				}
				
				currentChunk = {
					header: line,
					lines: []
				};
			} else if (currentChunk) {
				const type = line.startsWith('+') ? 'addition' : 
				             line.startsWith('-') ? 'deletion' : 'context';
				
				currentChunk.lines.push({
					type,
					content: line.substring(1),
					originalLine: line
				});
			}
		}
		
		if (currentChunk) {
			chunks.push(currentChunk);
		}
		
		return chunks;
	}
	
	// 获取行样式
	function getLineClass(lineType) {
		switch (lineType) {
			case 'addition':
				return 'diff-line-addition';
			case 'deletion':
				return 'diff-line-deletion';
			default:
				return 'diff-line-context';
		}
	}
	
	// 获取行前缀
	function getLinePrefix(lineType) {
		switch (lineType) {
			case 'addition':
				return '+';
			case 'deletion':
				return '-';
			default:
				return ' ';
		}
	}
	
	// 格式化日期
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
	
	$: diffChunks = diffData?.diff_content ? parseDiffContent(diffData.diff_content) : [];
	$: hasDifferences = diffChunks.length > 0;
</script>

<div class="version-diff">
	<!-- 头部信息 -->
	<div class="diff-header bg-white border-b border-gray-200 p-6">
		<div class="flex items-center justify-between mb-4">
			<div>
				<h2 class="text-xl font-semibold text-gray-900">版本对比</h2>
				<p class="text-sm text-gray-600 mt-1">{filePath}</p>
			</div>
			
			<!-- 视图选项 -->
			<div class="flex items-center space-x-2">
				<div class="flex rounded-lg border border-gray-300 overflow-hidden">
					<button
						class="px-3 py-1.5 text-sm transition-colors"
						class:bg-blue-100={viewMode === 'split'}
						class:text-blue-700={viewMode === 'split'}
						class:bg-white={viewMode !== 'split'}
						class:text-gray-600={viewMode !== 'split'}
						on:click={() => viewMode = 'split'}
					>
						分屏
					</button>
					<button
						class="px-3 py-1.5 text-sm border-l border-gray-300 transition-colors"
						class:bg-blue-100={viewMode === 'unified'}
						class:text-blue-700={viewMode === 'unified'}
						class:bg-white={viewMode !== 'unified'}
						class:text-gray-600={viewMode !== 'unified'}
						on:click={() => viewMode = 'unified'}
					>
						统一
					</button>
				</div>
				
				<Button
					variant="outline"
					size="sm"
					on:click={() => showLineNumbers = !showLineNumbers}
				>
					{showLineNumbers ? '隐藏' : '显示'}行号
				</Button>
				
				<Button
					variant="outline"
					size="sm"
					on:click={() => showWhitespace = !showWhitespace}
				>
					{showWhitespace ? '隐藏' : '显示'}空白字符
				</Button>
			</div>
		</div>
		
		<!-- 版本信息 -->
		<div class="grid grid-cols-2 gap-6">
			<div class="bg-red-50 border border-red-200 rounded-lg p-4">
				<div class="flex items-center space-x-2 mb-2">
					<span class="w-4 h-4 bg-red-500 rounded"></span>
					<h3 class="font-medium text-red-900">版本 {fromVersion?.version_number}</h3>
					<Badge variant="secondary" size="sm">{fromVersion?.version_hash}</Badge>
				</div>
				<p class="text-sm text-red-800 mb-2">
					{fromVersion?.commit_message || '无提交信息'}
				</p>
				<div class="text-xs text-red-700">
					{fromVersion?.author?.username} • {formatDate(fromVersion?.created_at)}
				</div>
			</div>
			
			<div class="bg-green-50 border border-green-200 rounded-lg p-4">
				<div class="flex items-center space-x-2 mb-2">
					<span class="w-4 h-4 bg-green-500 rounded"></span>
					<h3 class="font-medium text-green-900">版本 {toVersion?.version_number}</h3>
					<Badge variant="secondary" size="sm">{toVersion?.version_hash}</Badge>
				</div>
				<p class="text-sm text-green-800 mb-2">
					{toVersion?.commit_message || '无提交信息'}
				</p>
				<div class="text-xs text-green-700">
					{toVersion?.author?.username} • {formatDate(toVersion?.created_at)}
				</div>
			</div>
		</div>
		
		<!-- 差异统计 -->
		{#if diffData?.diff_summary}
			<div class="mt-4 flex items-center space-x-6 text-sm">
				{#if diffData.diff_summary.lines_added > 0}
					<span class="text-green-600">
						<span class="font-medium">+{diffData.diff_summary.lines_added}</span> 添加
					</span>
				{/if}
				{#if diffData.diff_summary.lines_removed > 0}
					<span class="text-red-600">
						<span class="font-medium">-{diffData.diff_summary.lines_removed}</span> 删除
					</span>
				{/if}
				{#if diffData.diff_summary.lines_changed > 0}
					<span class="text-blue-600">
						<span class="font-medium">~{diffData.diff_summary.lines_changed}</span> 修改
					</span>
				{/if}
			</div>
		{/if}
	</div>
	
	<!-- 差异内容 -->
	<div class="diff-content">
		{#if isLoading}
			<Loading message="加载版本差异中..." />
		{:else if error}
			<div class="text-center py-12">
				<div class="text-red-500 text-lg mb-4">❌ {error}</div>
				<Button on:click={loadDiff}>重试</Button>
			</div>
		{:else if !hasDifferences}
			<div class="text-center py-12 bg-gray-50">
				<div class="text-gray-400 text-4xl mb-4">🔍</div>
				<p class="text-gray-600">两个版本之间没有差异</p>
			</div>
		{:else}
			{#if viewMode === 'unified'}
				<!-- 统一视图 -->
				<div class="diff-unified">
					{#each diffChunks as chunk}
						<div class="diff-chunk mb-6">
							<!-- 块头部 -->
							<div class="diff-chunk-header bg-gray-100 px-4 py-2 border-l-4 border-gray-400">
								<code class="text-sm text-gray-700">{chunk.header}</code>
							</div>
							
							<!-- 块内容 -->
							<div class="diff-chunk-content border-l-4 border-gray-200">
								{#each chunk.lines as line, lineIndex}
									<div class="diff-line flex {getLineClass(line.type)}" class:show-whitespace={showWhitespace}>
										{#if showLineNumbers}
											<div class="diff-line-number bg-gray-50 px-3 py-1 text-xs text-gray-500 font-mono border-r border-gray-200 select-none">
												{lineIndex + 1}
											</div>
										{/if}
										<div class="diff-line-prefix px-2 py-1 text-sm font-mono select-none">
											{getLinePrefix(line.type)}
										</div>
										<div class="diff-line-content flex-1 px-3 py-1 text-sm font-mono whitespace-pre overflow-x-auto">
											{line.content}
										</div>
									</div>
								{/each}
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<!-- 分屏视图 -->
				<div class="diff-split grid grid-cols-2 gap-px bg-gray-200">
					<!-- 左侧：旧版本 -->
					<div class="diff-side bg-white">
						<div class="diff-side-header bg-red-50 px-4 py-2 border-b border-red-200">
							<h4 class="text-sm font-medium text-red-900">
								版本 {fromVersion?.version_number}
							</h4>
						</div>
						<div class="diff-side-content">
							{#each diffChunks as chunk}
								<div class="diff-chunk">
									{#each chunk.lines as line, lineIndex}
										{#if line.type !== 'addition'}
											<div class="diff-line flex {getLineClass(line.type)}">
												{#if showLineNumbers}
													<div class="diff-line-number bg-gray-50 px-3 py-1 text-xs text-gray-500 font-mono border-r border-gray-200 select-none">
														{lineIndex + 1}
													</div>
												{/if}
												<div class="diff-line-content flex-1 px-3 py-1 text-sm font-mono whitespace-pre overflow-x-auto">
													{line.content}
												</div>
											</div>
										{/if}
									{/each}
								</div>
							{/each}
						</div>
					</div>
					
					<!-- 右侧：新版本 -->
					<div class="diff-side bg-white">
						<div class="diff-side-header bg-green-50 px-4 py-2 border-b border-green-200">
							<h4 class="text-sm font-medium text-green-900">
								版本 {toVersion?.version_number}
							</h4>
						</div>
						<div class="diff-side-content">
							{#each diffChunks as chunk}
								<div class="diff-chunk">
									{#each chunk.lines as line, lineIndex}
										{#if line.type !== 'deletion'}
											<div class="diff-line flex {getLineClass(line.type)}">
												{#if showLineNumbers}
													<div class="diff-line-number bg-gray-50 px-3 py-1 text-xs text-gray-500 font-mono border-r border-gray-200 select-none">
														{lineIndex + 1}
													</div>
												{/if}
												<div class="diff-line-content flex-1 px-3 py-1 text-sm font-mono whitespace-pre overflow-x-auto">
													{line.content}
												</div>
											</div>
										{/if}
									{/each}
								</div>
							{/each}
						</div>
					</div>
				</div>
			{/if}
		{/if}
	</div>
</div>

<style>
	.version-diff {
		background: #f8f9fa;
		min-height: 100vh;
	}
	
	.diff-line-addition {
		background-color: #d4edda;
		border-left: 3px solid #28a745;
	}
	
	.diff-line-deletion {
		background-color: #f8d7da;
		border-left: 3px solid #dc3545;
	}
	
	.diff-line-context {
		background-color: #ffffff;
		border-left: 3px solid transparent;
	}
	
	.diff-line:hover {
		background-color: rgba(0, 0, 0, 0.05);
	}
	
	.show-whitespace .diff-line-content {
		white-space: pre;
	}
	
	.show-whitespace .diff-line-content::before {
		content: '';
		background-image: 
			radial-gradient(circle, #ccc 1px, transparent 1px),
			radial-gradient(circle, #ccc 1px, transparent 1px);
		background-size: 1ch 1em;
		background-position: 0 0, 0.5ch 0;
		opacity: 0.3;
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		pointer-events: none;
	}
	
	.diff-chunk-header {
		font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
	}
	
	.diff-line-number {
		min-width: 50px;
		text-align: right;
		user-select: none;
	}
	
	.diff-line-prefix {
		width: 24px;
		text-align: center;
		font-weight: bold;
	}
	
	.diff-line-addition .diff-line-prefix {
		color: #28a745;
		background-color: #d4edda;
	}
	
	.diff-line-deletion .diff-line-prefix {
		color: #dc3545;
		background-color: #f8d7da;
	}
	
	@media (max-width: 768px) {
		.diff-split {
			grid-template-columns: 1fr;
		}
		
		.diff-side-header {
			display: block;
		}
	}
</style>