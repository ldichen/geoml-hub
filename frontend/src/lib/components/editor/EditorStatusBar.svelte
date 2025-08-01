<script>
	export let cursorPosition = { line: 1, column: 1 };
	export let selectedText = '';
	export let wordCount = 0;
	export let lineCount = 1;
	export let language = '';
	export let isModified = false;
	export let lastSavedAt = null;
	export let isSaving = false;
	
	// 格式化时间
	function formatTime(date) {
		if (!date) return '';
		return new Intl.DateTimeFormat('zh-CN', {
			hour: '2-digit',
			minute: '2-digit',
			second: '2-digit'
		}).format(date);
	}
	
	// 获取语言显示名
	function getLanguageDisplay(lang) {
		const languageNames = {
			javascript: 'JavaScript',
			typescript: 'TypeScript',
			python: 'Python',
			json: 'JSON',
			markdown: 'Markdown',
			yaml: 'YAML',
			yml: 'YAML',
			html: 'HTML',
			css: 'CSS',
			sql: 'SQL'
		};
		return languageNames[lang] || lang.toUpperCase();
	}
	
	// 计算选中文本统计
	$: selectedStats = selectedText ? {
		length: selectedText.length,
		lines: selectedText.split('\n').length,
		words: selectedText.split(/\s+/).filter(w => w.length > 0).length
	} : null;
</script>

<div class="editor-status-bar flex items-center justify-between px-4 py-1 text-xs bg-gray-50 border-t border-gray-200">
	<!-- 左侧：位置和选择信息 -->
	<div class="flex items-center space-x-4 text-gray-600">
		<!-- 光标位置 -->
		<span class="flex items-center space-x-1">
			<span class="font-medium">行 {cursorPosition.line}</span>
			<span>列 {cursorPosition.column}</span>
		</span>
		
		<!-- 选中文本信息 -->
		{#if selectedStats}
			<span class="text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
				已选择 {selectedStats.length} 个字符
				{#if selectedStats.lines > 1}
					， {selectedStats.lines} 行
				{/if}
				{#if selectedStats.words > 0}
					， {selectedStats.words} 个词
				{/if}
			</span>
		{/if}
		
		<!-- 文档统计 -->
		<span class="flex items-center space-x-3">
			<span>{lineCount} 行</span>
			<span>{wordCount} 词</span>
		</span>
	</div>
	
	<!-- 右侧：语言、保存状态等 -->
	<div class="flex items-center space-x-4 text-gray-600">
		<!-- 语言标识 -->
		{#if language}
			<span class="px-2 py-0.5 bg-gray-200 text-gray-700 rounded text-xs">
				{getLanguageDisplay(language)}
			</span>
		{/if}
		
		<!-- 保存状态 -->
		<div class="flex items-center space-x-2">
			{#if isSaving}
				<div class="flex items-center space-x-1 text-blue-600">
					<div class="animate-spin rounded-full h-2 w-2 border border-blue-600 border-t-transparent"></div>
					<span>保存中</span>
				</div>
			{:else if isModified}
				<span class="text-orange-600 flex items-center space-x-1">
					<span class="w-1.5 h-1.5 bg-orange-400 rounded-full"></span>
					<span>未保存</span>
				</span>
			{:else if lastSavedAt}
				<span class="text-green-600 flex items-center space-x-1">
					<span class="w-1.5 h-1.5 bg-green-400 rounded-full"></span>
					<span>已保存于 {formatTime(lastSavedAt)}</span>
				</span>
			{/if}
		</div>
		
		<!-- 编码信息 -->
		<span class="text-gray-500">UTF-8</span>
		
		<!-- 行尾格式 -->
		<span class="text-gray-500">LF</span>
	</div>
</div>

<style>
	.editor-status-bar {
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
		min-height: 24px;
		background: linear-gradient(to bottom, #f8f9fa, #f1f3f4);
		border-top: 1px solid #dee2e6;
	}
	
	@media (max-width: 768px) {
		.editor-status-bar {
			padding: 4px 12px;
		}
		
		.editor-status-bar :global(.space-x-4) {
			gap: 8px;
		}
		
		.editor-status-bar :global(.space-x-3) {
			gap: 12px;
		}
	}
	
	@media (max-width: 640px) {
		.editor-status-bar {
			flex-direction: column;
			align-items: flex-start;
			gap: 2px;
			padding: 6px 12px;
		}
	}
</style>