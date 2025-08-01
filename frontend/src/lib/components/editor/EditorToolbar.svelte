<script>
	import { createEventDispatcher } from 'svelte';
	import Button from '../ui/Button.svelte';
	import Dropdown from '../ui/Dropdown.svelte';
	
	export let fileName = '';
	export let isModified = false;
	export let isSaving = false;
	export let readonly = false;
	export let canUndo = false;
	export let canRedo = false;
	
	const dispatch = createEventDispatcher();
	
	// 工具栏操作
	const actions = [
		{
			id: 'save',
			label: '保存',
			icon: 'save',
			shortcut: 'Ctrl+S',
			disabled: !isModified || readonly || isSaving,
			handler: () => dispatch('save')
		},
		{
			id: 'undo',
			label: '撤销',
			icon: 'undo',
			shortcut: 'Ctrl+Z',
			disabled: !canUndo || readonly,
			handler: () => dispatch('undo')
		},
		{
			id: 'redo',
			label: '重做',
			icon: 'redo',
			shortcut: 'Ctrl+Shift+Z',
			disabled: !canRedo || readonly,
			handler: () => dispatch('redo')
		},
		{
			id: 'find',
			label: '查找',
			icon: 'search',
			shortcut: 'Ctrl+F',
			disabled: false,
			handler: () => dispatch('find')
		},
		{
			id: 'format',
			label: '格式化',
			icon: 'format',
			shortcut: 'Shift+Alt+F',
			disabled: readonly,
			handler: () => dispatch('format')
		}
	];
	
	// 视图选项
	const viewOptions = [
		{
			id: 'preview',
			label: '预览',
			icon: 'eye',
			handler: () => dispatch('preview')
		},
		{
			id: 'split',
			label: '分屏',
			icon: 'split',
			handler: () => dispatch('split')
		},
		{
			id: 'fullscreen',
			label: '全屏',
			icon: 'fullscreen',
			handler: () => dispatch('fullscreen')
		}
	];
	
	// 更多选项
	const moreOptions = [
		{
			id: 'history',
			label: '版本历史',
			icon: 'history',
			handler: () => dispatch('history')
		},
		{
			id: 'settings',
			label: '编辑器设置',
			icon: 'settings',
			handler: () => dispatch('settings')
		},
		{
			id: 'download',
			label: '下载文件',
			icon: 'download',
			handler: () => dispatch('download')
		}
	];
	
	function getIcon(iconName) {
		const icons = {
			save: '💾',
			undo: '↶',
			redo: '↷',
			search: '🔍',
			format: '🎨',
			eye: '👁',
			split: '⬜',
			fullscreen: '⛶',
			history: '📜',
			settings: '⚙️',
			download: '📥',
			more: '⋯'
		};
		return icons[iconName] || iconName;
	}
</script>

<div class="editor-toolbar flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-white">
	<!-- 左侧：文件信息和主要操作 -->
	<div class="flex items-center space-x-4">
		<!-- 文件名和状态 -->
		<div class="flex items-center space-x-2">
			<h3 class="text-sm font-medium text-gray-900 truncate max-w-48">
				{fileName}
			</h3>
			{#if isModified}
				<span class="w-2 h-2 bg-orange-400 rounded-full" title="文件已修改"></span>
			{/if}
			{#if readonly}
				<span class="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">只读</span>
			{/if}
		</div>
		
		<!-- 主要操作按钮 -->
		<div class="flex items-center space-x-1">
			{#each actions as action}
				<Button
					variant="ghost"
					size="sm"
					disabled={action.disabled}
					title="{action.label} ({action.shortcut})"
					on:click={action.handler}
				>
					<span class="text-base">{getIcon(action.icon)}</span>
				</Button>
			{/each}
		</div>
	</div>
	
	<!-- 中间：保存状态 -->
	<div class="flex items-center space-x-2">
		{#if isSaving}
			<div class="flex items-center space-x-2 text-sm text-blue-600">
				<div class="animate-spin rounded-full h-3 w-3 border border-blue-600 border-t-transparent"></div>
				<span>保存中...</span>
			</div>
		{:else if isModified}
			<span class="text-sm text-orange-600">未保存的更改</span>
		{:else}
			<span class="text-sm text-green-600">已保存</span>
		{/if}
	</div>
	
	<!-- 右侧：视图和更多选项 -->
	<div class="flex items-center space-x-2">
		<!-- 视图选项 -->
		<div class="flex items-center space-x-1">
			{#each viewOptions as option}
				<Button
					variant="ghost"
					size="sm"
					title={option.label}
					on:click={option.handler}
				>
					<span class="text-base">{getIcon(option.icon)}</span>
				</Button>
			{/each}
		</div>
		
		<!-- 更多选项下拉菜单 -->
		<Dropdown>
			<Button
				slot="trigger"
				variant="ghost"
				size="sm"
				title="更多选项"
			>
				<span class="text-base">{getIcon('more')}</span>
			</Button>
			
			<div slot="content" class="py-1">
				{#each moreOptions as option}
					<button
						class="flex items-center space-x-2 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
						on:click={option.handler}
					>
						<span>{getIcon(option.icon)}</span>
						<span>{option.label}</span>
					</button>
				{/each}
			</div>
		</Dropdown>
	</div>
</div>

<style>
	.editor-toolbar {
		background: linear-gradient(to bottom, #fafafa, #f5f5f5);
		border-bottom: 1px solid #e5e5e5;
		backdrop-filter: blur(8px);
	}
	
	@media (max-width: 768px) {
		.editor-toolbar {
			padding: 8px 12px;
		}
		
		.editor-toolbar :global(.space-x-4) {
			gap: 8px;
		}
		
		.max-w-48 {
			max-width: 120px;
		}
	}
</style>