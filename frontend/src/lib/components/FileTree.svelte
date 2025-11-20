<script>
	import { _ } from 'svelte-i18n';
	import { File, Folder, Download, Eye } from 'lucide-svelte';
	import { formatDistanceToNow } from 'date-fns';
	import zhCN from 'date-fns/locale/zh-CN/index.js';
	import { base } from '$app/paths';

	export let files = [];
	export let username;
	export let repositoryName;

	function formatFileSize(bytes) {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
	}

	function getFileIcon(filename) {
		const ext = filename.split('.').pop()?.toLowerCase();

		// 根据文件扩展名返回不同的图标或颜色
		const iconMap = {
			// 文档类
			md: 'text-blue-500',
			txt: 'text-gray-500',
			pdf: 'text-red-500',
			doc: 'text-blue-600',
			docx: 'text-blue-600',

			// 代码类
			py: 'text-yellow-500',
			js: 'text-yellow-400',
			ts: 'text-blue-400',
			html: 'text-orange-500',
			css: 'text-blue-500',
			json: 'text-green-500',
			xml: 'text-orange-400',
			yml: 'text-purple-500',
			yaml: 'text-purple-500',

			// 数据类
			csv: 'text-green-600',
			xlsx: 'text-green-600',
			xls: 'text-green-600',
			sql: 'text-orange-600',

			// 图片类
			jpg: 'text-purple-500',
			jpeg: 'text-purple-500',
			png: 'text-purple-500',
			gif: 'text-purple-500',
			svg: 'text-purple-400',

			// 模型类
			pkl: 'text-indigo-500',
			h5: 'text-indigo-500',
			pt: 'text-indigo-500',
			pth: 'text-indigo-500',
			onnx: 'text-indigo-500',
			pb: 'text-indigo-500'
		};

		return iconMap[ext] || 'text-gray-400';
	}

	function handleFileClick(file) {
		// 处理文件点击，可以导航到文件详情页面
		const filePath = file.file_path || file.path || file.filename;
		if (isDirectory(file)) {
			// 如果是目录，导航到目录页面
			window.location.href = `${base}/${username}/${repositoryName}/tree/main/${filePath}`;
		} else {
			// 如果是文件，导航到文件详情页面
			window.location.href = `${base}/${username}/${repositoryName}/blob/main/${filePath}`;
		}
	}

	function handleDownload(file, event) {
		event.stopPropagation();
		// 处理文件下载
		const downloadUrl = `/api/${username}/${repositoryName}/download/${
			file.file_path || file.path || file.filename
		}`;
		window.open(downloadUrl, '_blank');
	}

	// 判断是否为目录的函数
	function isDirectory(file) {
		// 检查多个可能的字段来判断是否为目录
		return (
			file.is_directory ||
			file.file_type === 'directory' ||
			file.type === 'directory' ||
			(!file.file_size && !file.mime_type && file.filename && !file.filename.includes('.'))
		);
	}

	// 按文件夹和文件分组并排序
	$: sortedFiles = files.sort((a, b) => {
		// 文件夹排在前面
		const aIsDir = isDirectory(a);
		const bIsDir = isDirectory(b);

		if (aIsDir && !bIsDir) return -1;
		if (!aIsDir && bIsDir) return 1;

		// 同类型按名称排序
		return a.filename.localeCompare(b.filename);
	});
</script>

<div class="space-y-1">
	{#if sortedFiles.length === 0}
		<div class="text-center py-8 text-gray-500 dark:text-gray-400">
			<Folder class="w-8 h-8 mx-auto mb-2 text-gray-300" />
			<p>{$_('file.no_files')}</p>
		</div>
	{:else}
		{#each sortedFiles as file}
			<div
				class="flex items-center justify-between p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded cursor-pointer group"
				on:click={() => handleFileClick(file)}
				role="button"
				tabindex="0"
				on:keydown={(e) => e.key === 'Enter' && handleFileClick(file)}
			>
				<div class="flex items-center space-x-3 flex-1 min-w-0">
					{#if isDirectory(file)}
						<Folder class="w-4 h-4 text-blue-500 flex-shrink-0" />
					{:else}
						<File class="w-4 h-4 {getFileIcon(file.filename)} flex-shrink-0" />
					{/if}

					<div class="flex-1 min-w-0">
						<div class="text-sm font-medium text-gray-900 dark:text-white truncate">
							{file.filename}
						</div>
						{#if !isDirectory(file)}
							<div class="text-xs text-gray-500 dark:text-gray-400 flex items-center space-x-2">
								<span>{formatFileSize(file.file_size || 0)}</span>
								<span>•</span>
								<span
									>{formatDistanceToNow(new Date(file.created_at || file.updated_at), {
										addSuffix: true,
										locale: zhCN
									})}</span
								>
							</div>
						{/if}
					</div>
				</div>

				{#if !isDirectory(file)}
					<div
						class="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity"
					>
						<button
							on:click={(e) => handleDownload(file, e)}
							class="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
							title={$_('common.download')}
						>
							<Download class="w-3 h-3 text-gray-500" />
						</button>
						<button
							class="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
							title={$_('common.view')}
						>
							<Eye class="w-3 h-3 text-gray-500" />
						</button>
					</div>
				{/if}
			</div>
		{/each}
	{/if}
</div>
