<script>
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { EditorView, basicSetup } from 'codemirror';
	import { EditorState } from '@codemirror/state';
	import { javascript } from '@codemirror/lang-javascript';
	import { python } from '@codemirror/lang-python';
	import { json } from '@codemirror/lang-json';
	import { markdown } from '@codemirror/lang-markdown';
	import { yaml } from '@codemirror/lang-yaml';
	import { oneDark } from '@codemirror/theme-one-dark';
	import { indentWithTab } from '@codemirror/commands';
	import { keymap } from '@codemirror/view';
	import { linter, lintGutter } from '@codemirror/lint';
	
	import EditorToolbar from './EditorToolbar.svelte';
	import EditorStatusBar from './EditorStatusBar.svelte';
	import EditorSidebar from './EditorSidebar.svelte';

	export let fileContent = '';
	export let fileName = '';
	export let filePath = '';
	export let language = '';
	export let readonly = false;
	export let theme = 'light';
	export let showToolbar = true;
	export let showStatusBar = true;
	export let showSidebar = true;
	export let autoSave = true;
	export let autoSaveInterval = 30000; // 30秒
	export let repository = null;
	
	const dispatch = createEventDispatcher();
	
	let editorElement;
	let editor;
	let currentContent = fileContent;
	let isModified = false;
	let isSaving = false;
	let lastSavedAt = null;
	let autoSaveTimer;
	let cursorPosition = { line: 1, column: 1 };
	let selectedText = '';
	let wordCount = 0;
	let lineCount = 1;
	
	// 语言配置映射
	const languageMap = {
		javascript: javascript(),
		typescript: javascript({ typescript: true }),
		python: python(),
		json: json(),
		markdown: markdown(),
		yaml: yaml(),
		yml: yaml()
	};
	
	// 根据文件扩展名检测语言
	function detectLanguage(fileName) {
		const ext = fileName.split('.').pop().toLowerCase();
		return languageMap[ext] || null;
	}
	
	// 创建编辑器
	function createEditor() {
		if (!editorElement) return;
		
		console.log('📝 FileEditor 创建编辑器 - 内容长度:', currentContent.length);
		
		const langSupport = language ? languageMap[language] : detectLanguage(fileName);
		const extensions = [
			basicSetup,
			keymap.of([indentWithTab]),
			EditorView.updateListener.of(handleEditorUpdate),
			EditorView.lineWrapping,
			...(langSupport ? [langSupport] : []),
			...(theme === 'dark' ? [oneDark] : []),
			...(readonly ? [EditorState.readOnly.of(true)] : []),
			lintGutter(),
		];
		
		const state = EditorState.create({
			doc: currentContent,
			extensions
		});
		
		editor = new EditorView({
			state,
			parent: editorElement
		});
		
		console.log('📝 编辑器创建完成，文档内容长度:', editor.state.doc.length);
	}
	
	// 编辑器更新处理
	function handleEditorUpdate(update) {
		if (update.docChanged) {
			const newContent = update.state.doc.toString();
			currentContent = newContent;
			isModified = newContent !== fileContent;
			
			// 更新统计信息
			updateStats();
			
			// 触发内容变更事件
			dispatch('contentChange', {
				content: newContent,
				isModified: isModified
			});
			
			// 自动保存
			if (autoSave && isModified && !readonly) {
				scheduleAutoSave();
			}
		}
		
		// 更新光标位置
		const selection = update.state.selection.main;
		const pos = update.state.doc.lineAt(selection.head);
		cursorPosition = {
			line: pos.number,
			column: selection.head - pos.from + 1
		};
		
		// 更新选中文本
		selectedText = update.state.sliceDoc(selection.from, selection.to);
	}
	
	// 更新统计信息
	function updateStats() {
		wordCount = currentContent.split(/\s+/).filter(word => word.length > 0).length;
		lineCount = currentContent.split('\n').length;
	}
	
	// 计划自动保存
	function scheduleAutoSave() {
		if (autoSaveTimer) {
			clearTimeout(autoSaveTimer);
		}
		
		autoSaveTimer = setTimeout(() => {
			saveDraft();
		}, autoSaveInterval);
	}
	
	// 保存草稿
	async function saveDraft() {
		if (!isModified || readonly) return;
		
		isSaving = true;
		try {
			await dispatch('saveDraft', {
				content: currentContent,
				cursorPosition,
				filePath
			});
			lastSavedAt = new Date();
		} catch (error) {
			dispatch('error', { message: '草稿保存失败', error });
		} finally {
			isSaving = false;
		}
	}
	
	// 手动保存
	async function saveFile() {
		if (!isModified || readonly) return;
		
		isSaving = true;
		try {
			await dispatch('saveFile', {
				content: currentContent,
				message: '更新文件内容'
			});
			fileContent = currentContent;
			isModified = false;
			lastSavedAt = new Date();
		} catch (error) {
			dispatch('error', { message: '文件保存失败', error });
		} finally {
			isSaving = false;
		}
	}
	
	// 撤销
	function undo() {
		if (editor) {
			editor.dispatch({ effects: [] });
		}
	}
	
	// 重做
	function redo() {
		if (editor) {
			editor.dispatch({ effects: [] });
		}
	}
	
	// 查找替换
	function openFindReplace() {
		dispatch('openFindReplace');
	}
	
	// 格式化代码
	function formatCode() {
		dispatch('formatCode', { content: currentContent, language });
	}
	
	// 键盘快捷键
	function handleKeydown(event) {
		if (event.ctrlKey || event.metaKey) {
			switch (event.key) {
				case 's':
					event.preventDefault();
					saveFile();
					break;
				case 'z':
					if (event.shiftKey) {
						event.preventDefault();
						redo();
					} else {
						event.preventDefault();
						undo();
					}
					break;
				case 'f':
					event.preventDefault();
					openFindReplace();
					break;
			}
		}
	}
	
	onMount(() => {
		console.log('📝 FileEditor onMount - fileContent长度:', fileContent.length);
		
		// 确保使用最新的 fileContent 设置 currentContent
		if (fileContent && fileContent.length > 0) {
			currentContent = fileContent;
			console.log('📝 设置 currentContent 长度:', currentContent.length);
		}
		
		createEditor();
		updateStats();
	});
	
	onDestroy(() => {
		if (autoSaveTimer) {
			clearTimeout(autoSaveTimer);
		}
		if (editor) {
			editor.destroy();
		}
	});
	
	// 响应式更新 - 当fileContent prop改变时
	$: if (fileContent !== currentContent) {
		console.log('📝 FileEditor fileContent prop 改变:');
		console.log('新的 fileContent:', fileContent);
		console.log('新的 fileContent 长度:', fileContent.length);
		console.log('当前 currentContent:', currentContent);
		console.log('当前 currentContent 长度:', currentContent.length);
		
		currentContent = fileContent;
		
		if (editor && !isModified) {
			console.log('📝 更新编辑器内容...');
			editor.dispatch({
				changes: {
					from: 0,
					to: editor.state.doc.length,
					insert: fileContent
				}
			});
			updateStats();
			console.log('📝 编辑器内容更新完成');
		}
	}
	
	$: if (editor && theme) {
		// 主题切换逻辑
		createEditor();
	}
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="file-editor flex flex-col h-full">
	<!-- 编辑器工具栏 -->
	{#if showToolbar}
		<EditorToolbar 
			{fileName}
			{isModified}
			{isSaving}
			{readonly}
			canUndo={false}
			canRedo={false}
			on:save={saveFile}
			on:undo={undo}
			on:redo={redo}
			on:format={formatCode}
			on:find={openFindReplace}
			on:preview={() => dispatch('preview')}
		/>
	{/if}
	
	<div class="editor-main flex flex-1 overflow-hidden">
		<!-- 侧边栏 -->
		{#if showSidebar}
			<EditorSidebar 
				{repository}
				{filePath}
				on:fileSelect={event => dispatch('fileSelect', event.detail)}
				on:newFile={() => dispatch('newFile')}
				on:uploadFile={() => dispatch('uploadFile')}
			/>
		{/if}
		
		<!-- 编辑器主体 -->
		<div class="editor-content flex-1 relative">
			<div 
				bind:this={editorElement}
				class="editor-wrapper h-full"
				class:readonly
			></div>
			
			<!-- 加载覆盖层 -->
			{#if isSaving}
				<div class="absolute inset-0 bg-black bg-opacity-10 flex items-center justify-center">
					<div class="bg-white rounded-lg p-4 shadow-lg">
						<div class="flex items-center space-x-2">
							<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
							<span class="text-sm text-gray-600">保存中...</span>
						</div>
					</div>
				</div>
			{/if}
		</div>
	</div>
	
	<!-- 状态栏 -->
	{#if showStatusBar}
		<EditorStatusBar 
			{cursorPosition}
			{selectedText}
			{wordCount}
			{lineCount}
			{language}
			{isModified}
			{lastSavedAt}
			{isSaving}
		/>
	{/if}
</div>

<style>
	.file-editor {
		background: var(--bg-primary);
		border: 1px solid var(--border-color);
		border-radius: 8px;
		overflow: hidden;
	}
	
	.editor-wrapper {
		font-family: 'JetBrains Mono', 'Consolas', monospace;
		font-size: 14px;
		line-height: 1.5;
	}
	
	.editor-wrapper.readonly {
		background-color: var(--bg-secondary);
	}
	
	:global(.cm-editor) {
		height: 100%;
		background-color: #f8f9fa;
	}
	
	:global(.cm-focused) {
		outline: none;
	}
	
	:global(.cm-content) {
		padding: 16px;
		min-height: 100%;
		color: #1f2937 !important;
		font-size: 14px;
		line-height: 1.6;
	}
	
	:global(.cm-line) {
		padding: 0 4px;
		color: #1f2937 !important;
	}
	
	:global(.cm-gutters) {
		background-color: #f9fafb;
		border-right: 1px solid #e5e7eb;
	}
	
	:global(.cm-lineNumbers .cm-gutterElement) {
		padding: 0 8px;
		min-width: 40px;
		text-align: right;
		color: #6b7280;
		font-size: 12px;
	}
	
	/* 确保编辑器文本颜色正确 */
	:global(.cm-editor .cm-content) {
		color: #111827 !important;
	}
	
	:global(.cm-editor .cm-line) {
		color: #111827 !important;
	}
</style>