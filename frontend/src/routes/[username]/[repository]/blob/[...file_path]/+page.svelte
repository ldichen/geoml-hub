<script>
	import { page } from '$app/stores';
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/utils/api.js';
	import { marked } from 'marked';

	import { Star, Download, Eye, Calendar, FileText, ChevronRight } from 'lucide-svelte';
	import { formatDistanceToNow } from 'date-fns';
	import zhCN from 'date-fns/locale/zh-CN/index.js';
	import { user as currentUser } from '$lib/stores/auth.js';
	import UserAvatar from '$lib/components/UserAvatar.svelte';
	import SocialButton from '$lib/components/SocialButton.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import Loading from '$lib/components/Loading.svelte';
	import Toast from '$lib/components/ui/Toast.svelte';

	// 路由参数
	$: username = $page.params.username;
	$: repositoryName = $page.params.repository;
	$: filePath = $page.params.file_path;

	// 状态
	let repository = null;
	let fileContent = '';
	let fileInfo = null;
	let versionHistory = [];
	let isLoading = true;
	let error = null;
	let currentView = 'content'; // content, history, raw
	let currentMarkdownView = 'preview'; // preview, code (for markdown files)
	let canEdit = false;
	let toast = null;

	// 加载数据
	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		isLoading = true;
		error = null;

		try {
			// 并行加载仓库信息和文件内容
			const [repoResponse, fileResponse] = await Promise.all([
				api.getRepository(username, repositoryName),
				api.getRepositoryFileContent(username, repositoryName, filePath)
			]);

			repository = repoResponse;
			fileInfo = fileResponse;
			fileContent = fileInfo.content || '';

			// 检查编辑权限
			await checkEditPermission();

			// 加载版本历史
			if (currentView === 'history') {
				await loadVersionHistory();
			}
		} catch (err) {
			error = err.response?.data?.detail || '加载文件失败';
		} finally {
			isLoading = false;
		}
	}

	async function checkEditPermission() {
		// 只有仓库拥有者可以编辑文件
		canEdit = $currentUser && repository && $currentUser.username === repository.owner?.username;
	}

	async function loadVersionHistory() {
		// 临时简化：返回空的版本历史（实际应用中需要实现版本控制API）
		versionHistory = [];
	}

	// 导航到编辑页面
	function editFile() {
		goto(`${base}/${username}/${repositoryName}/edit/${filePath}`);
	}

	// 下载文件
	async function downloadFile() {
		try {
			// 使用仓库API的下载端点
			const response = await api.getDownloadUrl(username, repositoryName, filePath);

			// 直接跳转到下载URL
			const link = document.createElement('a');
			link.href = response.download_url;
			link.setAttribute('download', fileInfo.filename);
			document.body.appendChild(link);
			link.click();
			link.remove();

			toast = { type: 'success', message: '文件下载成功' };
		} catch (err) {
			toast = { type: 'error', message: '文件下载失败' };
		}
	}

	// 复制文件内容
	async function copyContent() {
		try {
			await navigator.clipboard.writeText(fileContent);
			toast = { type: 'success', message: '内容已复制到剪贴板' };
		} catch (err) {
			toast = { type: 'error', message: '复制失败' };
		}
	}

	// 删除文件
	async function deleteFile() {
		if (!confirm(`确定要删除文件 "${fileInfo.filename}" 吗？此操作无法撤销。`)) {
			return;
		}

		try {
			await api.deleteFile(fileInfo.id);
			toast = { type: 'success', message: '文件删除成功' };

			// 删除成功后跳转回仓库主页的Files标签
			setTimeout(() => {
				goto(`${base}/${username}/${repositoryName}?tab=files`);
			}, 1500);
		} catch (err) {
			console.error('Delete file failed:', err);
			toast = { type: 'error', message: `删除文件失败：${err.message}` };
		}
	}

	// 获取文件类型图标
	function getFileIcon(filename) {
		const ext = filename.split('.').pop().toLowerCase();
		const iconMap = {
			md: '📝',
			py: '🐍',
			js: '📜',
			ts: '📘',
			json: '🔧',
			yaml: '⚙️',
			yml: '⚙️',
			txt: '📄',
			csv: '📊',
			png: '🖼',
			jpg: '🖼',
			jpeg: '🖼',
			gif: '🖼',
			pdf: '📕'
		};
		return iconMap[ext] || '📄';
	}

	// 格式化文件大小
	function formatFileSize(bytes) {
		if (!bytes) return '0 B';
		const sizes = ['B', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(1024));
		return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
	}

	// 处理 Star 操作
	async function handleStar() {
		if (!repository || !$currentUser) return;

		try {
			if (repository.is_starred) {
				await api.unstarRepository(username, repositoryName);
				repository.is_starred = false;
				repository.stars_count -= 1;
			} else {
				await api.starRepository(username, repositoryName);
				repository.is_starred = true;
				repository.stars_count += 1;
			}
		} catch (err) {
			console.error('Error starring repository:', err);
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

	// 检测文件是否为文本文件
	function isTextFile(filename) {
		const textExtensions = [
			'md',
			'txt',
			'py',
			'js',
			'ts',
			'json',
			'yaml',
			'yml',
			'csv',
			'html',
			'css',
			'sql'
		];
		const ext = filename.split('.').pop().toLowerCase();
		return textExtensions.includes(ext);
	}

	// 检测文件语言
	function detectLanguage(filename) {
		const ext = filename.split('.').pop().toLowerCase();
		const languageMap = {
			md: 'markdown',
			markdown: 'markdown',
			py: 'python',
			js: 'javascript',
			ts: 'typescript',
			json: 'json',
			yaml: 'yaml',
			yml: 'yaml'
		};
		return languageMap[ext] || 'text';
	}

	// 检测文件是否为图片
	function isImageFile(filename) {
		const imageExtensions = ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'];
		const ext = filename.split('.').pop().toLowerCase();
		return imageExtensions.includes(ext);
	}

	// 检测文件是否为视频
	function isVideoFile(filename) {
		const videoExtensions = ['mp4', 'avi', 'mov', 'webm', 'mkv', 'flv', 'wmv', 'm4v'];
		const ext = filename.split('.').pop().toLowerCase();
		return videoExtensions.includes(ext);
	}

	// 检测文件是否为模型文件
	function isModelFile(filename) {
		const modelExtensions = [
			'pt',
			'pth',
			'bin',
			'pb',
			'h5',
			'onnx',
			'pkl',
			'joblib',
			'safetensors'
		];
		const ext = filename.split('.').pop().toLowerCase();
		return modelExtensions.includes(ext);
	}

	// 检测文件是否为数据文件
	function isDataFile(filename) {
		const dataExtensions = ['csv', 'json', 'xml', 'parquet', 'h5', 'hdf5', 'npz', 'npy', 'tsv'];
		const ext = filename.split('.').pop().toLowerCase();
		return dataExtensions.includes(ext);
	}

	// 检测文件是否为PDF
	function isPdfFile(filename) {
		const ext = filename.split('.').pop().toLowerCase();
		return ext === 'pdf';
	}

	// 检测文件是否为Markdown文件
	function isMarkdownFile(filename) {
		const markdownExtensions = ['md', 'markdown'];
		const ext = filename.split('.').pop().toLowerCase();
		return markdownExtensions.includes(ext);
	}

	// 检测文件是否过大 (300MB)
	function isLargeFile(fileSize) {
		return fileSize > 300 * 1024 * 1024; // 300MB
	}

	// 获取模型文件类型
	function getModelType(filename) {
		const ext = filename.split('.').pop().toLowerCase();
		const modelTypes = {
			pt: 'PyTorch',
			pth: 'PyTorch',
			bin: 'Transformers',
			pb: 'TensorFlow',
			h5: 'Keras/HDF5',
			onnx: 'ONNX',
			pkl: 'Scikit-learn/Pickle',
			joblib: 'Joblib',
			safetensors: 'SafeTensors'
		};
		return modelTypes[ext] || 'Unknown';
	}

	// 统一的Markdown渲染函数（与仓库主页保持一致）
	function renderMarkdown(content) {
		if (!content) return '';

		// 处理YAML front matter
		const metadataMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);

		if (metadataMatch) {
			const metadata = metadataMatch[1];
			const bodyContent = metadataMatch[2];

			// 渲染metadata块（保留特殊样式）
			const metadataHtml = `<div class="metadata-block bg-gray-800 text-gray-100 p-4 rounded-lg mb-6 font-mono text-sm border border-gray-600">
				<div class="inline-block bg-gray-700 text-gray-200 px-2 py-1 rounded text-xs mb-3 font-semibold">metadata</div>
				<pre class="whitespace-pre-wrap text-gray-100">${highlightYaml(metadata.trim())}</pre>
			</div>`;

			// 使用marked.js渲染markdown内容
			let html = marked(bodyContent);

			// 应用与仓库主页相同的后处理
			html = processMarkdownHtml(html);

			return metadataHtml + html;
		} else {
			// 没有YAML front matter，直接使用marked.js
			let html = marked(content);
			return processMarkdownHtml(html);
		}
	}

	// 后处理HTML（与仓库主页processMarkdown保持一致）
	function processMarkdownHtml(html) {
		// 为表格添加滚动容器
		html = html.replace(/<table>/g, '<div class="table-container"><table>');
		html = html.replace(/<\/table>/g, '</table></div>');

		// 处理相对路径的图片引用，转换为正确的API端点
		html = html.replace(
			/<img([^>]*?)src=["']((?!https?:\/\/)(?!\/)\.?\/?[^"']+)["']/gi,
			(match, attributes, imagePath) => {
				// 移除开头的 ./ 如果存在
				const cleanPath = imagePath.replace(/^\.\//, '');
				const newSrc = `/api/repositories/${username}/${repositoryName}/raw/${cleanPath}`;
				return `<img${attributes}src="${newSrc}"`;
			}
		);

		return html;
	}

	// 语法高亮功能
	function applyBasicSyntaxHighlight(content, language) {
		if (!content) return content;

		// 基本的语法高亮规则
		let highlighted = content;

		if (language === 'markdown' || language === 'md') {
			highlighted = content
				// YAML front matter
				.replace(/^---\n([\s\S]*?)\n---/gm, (match, yaml) => {
					return `<span class="yaml-frontmatter">---\n${highlightYaml(yaml)}\n---</span>`;
				})
				// Headers
				.replace(/^(#{1,6})\s+(.*)$/gm, '<span class="md-header">$1 $2</span>')
				// Bold
				.replace(/\*\*(.*?)\*\*/g, '<span class="md-bold">**$1**</span>')
				// Italic
				.replace(/\*(.*?)\*/g, '<span class="md-italic">*$1*</span>')
				// Links
				.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<span class="md-link">[$1]($2)</span>')
				// Code blocks
				.replace(/```([\s\S]*?)```/g, '<span class="md-code-block">```$1```</span>')
				// Inline code
				.replace(/`([^`]+)`/g, '<span class="md-inline-code">`$1`</span>')
				// Lists
				.replace(/^(\s*[-*+])\s+(.*)$/gm, '<span class="md-list">$1 $2</span>')
				// Numbers list
				.replace(/^(\s*\d+\.)\s+(.*)$/gm, '<span class="md-list">$1 $2</span>');
		}

		return highlighted;
	}

	function highlightYaml(yaml) {
		return (
			yaml
				// Keys
				.replace(/^(\s*)([^:\s]+)(\s*:)/gm, '$1<span class="yaml-key">$2</span>$3')
				// String values
				.replace(/:\s*([^\s].*)/g, ': <span class="yaml-value">$1</span>')
				// Comments
				.replace(/(#.*)/g, '<span class="yaml-comment">$1</span>')
		);
	}

	// 响应式处理
	$: if (currentView === 'history' && versionHistory.length === 0) {
		loadVersionHistory();
	}
</script>

<svelte:head>
	<title>{fileInfo?.filename || '文件查看'} - {repositoryName} - GeoML-Hub</title>
</svelte:head>

{#if toast}
	<Toast type={toast.type} message={toast.message} on:close={() => (toast = null)} />
{/if}

<div class="file-viewer">
	<!-- 仓库头部 -->
	{#if repository}
		<div
			class="bg-linear-to-t from-blue-500/8 dark:from-blue-500/20 to-white to-70% dark:to-gray-950 border-b border-gray-100 dark:border-gray-800 pt-6 sm:pt-9"
		>
			<div class="container">
				<!-- Repository Info -->
				<div>
					<div class="flex items-start justify-between">
						<div class="flex-1 min-w-0">
							<!-- Repository title with stats -->
							<div class="flex items-center justify-between mb-2">
								<div class="flex items-center">
									<div class="flex items-center space-x-2">
										<UserAvatar user={repository.owner} size="sm" />
										<a
											href="{base}/{repository.owner?.username}"
											class="text-blue-600 dark:text-blue-300 hover:text-blue-700 dark:hover:text-blue-200 hover:underline"
										>
											{repository.owner?.username}
										</a>
										<span class="text-gray-500 dark:text-gray-400">/</span>
										<h1 class="text-xl font-bold text-gray-900 dark:text-white">
											{repository.name}
										</h1>
										{#if repository.visibility === 'private'}
											<span
												class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
											>
												私有
											</span>
										{/if}
									</div>

									<!-- Stats next to repository name with proper spacing -->
									<div
										class="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400 ml-6"
									>
										<div class="flex items-center space-x-1">
											<Star class="h-4 w-4" />
											<span>{repository.stars_count}</span>
										</div>
										<div class="flex items-center space-x-1">
											<Download class="h-4 w-4" />
											<span>{repository.downloads_count}</span>
										</div>
										<div class="flex items-center space-x-1">
											<Eye class="h-4 w-4" />
											<span>{repository.views_count}</span>
										</div>
										{#if repository.total_size > 0}
											<div class="flex items-center space-x-1">
												<span>{formatFileSize(repository.total_size)}</span>
											</div>
										{/if}
									</div>
								</div>

								<!-- Created time on the right -->
								<div class="flex items-center space-x-1 text-xs text-gray-500 dark:text-gray-400">
									<Calendar class="h-3 w-3" />
									<span>
										创建于 {formatDistanceToNow(new Date(repository.created_at), {
											addSuffix: true,
											locale: zhCN
										})}
									</span>
								</div>
							</div>

							<!-- Description -->
							{#if repository.description}
								<p class="text-gray-700 dark:text-gray-300 mb-4">
									{repository.description}
								</p>
							{/if}

							<!-- Tags Row (Orange) -->
							{#if repository.tags && repository.tags.length > 0}
								<div class="flex flex-wrap gap-1 mb-2">
									{#each repository.tags as tag}
										<span
											class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200"
										>
											{tag}
										</span>
									{/each}
								</div>
							{/if}

							<!-- Classification Row (Blue) -->
							{#if repository.classification_path && repository.classification_path.length > 0}
								<div class="flex items-center space-x-1 mb-2">
									{#each repository.classification_path as classification, index}
										<span
											class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200"
										>
											{classification}
										</span>
										{#if index < repository.classification_path.length - 1}
											<ChevronRight class="h-3 w-3 text-gray-400" />
										{/if}
									{/each}
								</div>
							{/if}
						</div>

						<!-- Actions -->
						<div class="flex items-center space-x-2 ml-6">
							{#if $currentUser && repository.owner?.username !== $currentUser.username}
								<SocialButton
									type="star"
									active={repository.is_starred}
									count={repository.stars_count}
									on:click={handleStar}
								/>
							{/if}
						</div>
					</div>
				</div>

				<!-- Navigation Tabs -->
				<div class="border-b border-gray-200 dark:border-gray-700">
					<nav class="flex space-x-8" aria-label="Tabs">
						<a
							href="{base}/{repository.owner?.username}/{repository.name}"
							class="py-2 px-1 border-b-2 font-medium text-sm border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
						>
							<FileText class="h-4 w-4 inline mr-1" />
							Model Card
						</a>
						<span
							class="py-2 px-1 border-b-2 font-medium text-sm border-blue-500 text-blue-600 dark:text-blue-400"
						>
							<FileText class="h-4 w-4 inline mr-1" />
							Files
						</span>
					</nav>
				</div>
			</div>
		</div>
	{/if}

	<div class="bg-white">
		<div class="container mx-auto px-4 py-6">
			{#if isLoading}
				<Loading message="加载文件中..." />
			{:else if error}
				<div class="text-center py-12">
					<div class="text-red-500 text-lg mb-4">❌ 加载失败</div>
					<p class="text-gray-600 mb-4">{error}</p>
					<Button on:click={loadData}>重试</Button>
				</div>
			{:else if fileInfo}
				<!-- 文件路径面包屑 -->
				<nav class="flex items-center space-x-2 text-sm text-gray-600 mb-4">
					<a href="{base}/{username}/{repositoryName}" class="hover:text-blue-600">
						{repositoryName}
					</a>
					{#each filePath.split('/') as segment, i}
						<span>/</span>
						{#if i === filePath.split('/').length - 1}
							<span class="text-gray-900 font-medium">{segment}</span>
						{:else}
							<a
								href="{base}/{username}/{repositoryName}/tree/{filePath
									.split('/')
									.slice(0, i + 1)
									.join('/')}"
								class="hover:text-blue-600"
							>
								{segment}
							</a>
						{/if}
					{/each}
				</nav>

				<!-- 文件内容区域 -->
				<div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
					<!-- 视图切换 -->
					<div class="px-6 py-3 bg-white border-b border-gray-200">
						<div class="flex space-x-1">
							{#if currentView === 'content' && isMarkdownFile(fileInfo.filename)}
								<!-- Markdown文件的Preview/Code切换 -->
								<button
									class="px-3 py-1.5 text-sm rounded transition-colors"
									class:bg-blue-100={currentMarkdownView === 'preview'}
									class:text-blue-700={currentMarkdownView === 'preview'}
									class:text-gray-600={currentMarkdownView !== 'preview'}
									class:hover:bg-gray-100={currentMarkdownView !== 'preview'}
									on:click={() => (currentMarkdownView = 'preview')}
								>
									👁️ Preview
								</button>
								<button
									class="px-3 py-1.5 text-sm rounded transition-colors"
									class:bg-blue-100={currentMarkdownView === 'code'}
									class:text-blue-700={currentMarkdownView === 'code'}
									class:text-gray-600={currentMarkdownView !== 'code'}
									class:hover:bg-gray-100={currentMarkdownView !== 'code'}
									on:click={() => (currentMarkdownView = 'code')}
								>
									📄 Code
								</button>
							{:else}
								<!-- 非Markdown文件的常规切换 -->
								<button
									class="px-3 py-1.5 text-sm rounded transition-colors"
									class:bg-blue-100={currentView === 'content'}
									class:text-blue-700={currentView === 'content'}
									class:text-gray-600={currentView !== 'content'}
									class:hover:bg-gray-100={currentView !== 'content'}
									on:click={() => (currentView = 'content')}
								>
									📄 内容
								</button>
							{/if}

							<button
								class="px-3 py-1.5 text-sm rounded transition-colors"
								class:bg-blue-100={currentView === 'history'}
								class:text-blue-700={currentView === 'history'}
								class:text-gray-600={currentView !== 'history'}
								class:hover:bg-gray-100={currentView !== 'history'}
								on:click={() => (currentView = 'history')}
							>
								📜 history
							</button>
							{#if isTextFile(fileInfo.filename)}
								<button
									class="px-3 py-1.5 text-sm rounded transition-colors"
									class:bg-blue-100={currentView === 'raw'}
									class:text-blue-700={currentView === 'raw'}
									class:text-gray-600={currentView !== 'raw'}
									class:hover:bg-gray-100={currentView !== 'raw'}
									on:click={() => (currentView = 'raw')}
								>
									📝 raw
								</button>
							{/if}
							<button
								class="px-3 py-1.5 text-sm rounded transition-colors text-gray-600 hover:bg-gray-100"
							>
								📋 Copy download link
							</button>
							<button
								class="px-3 py-1.5 text-sm rounded transition-colors text-gray-600 hover:bg-gray-100"
							>
								👤 blame
							</button>
							{#if canEdit}
								<button
									class="px-3 py-1.5 text-sm rounded transition-colors text-green-600 hover:bg-green-50"
									on:click={editFile}
								>
									✏️ contribute
								</button>
							{/if}
							{#if canEdit}
								<button
									class="px-3 py-1.5 text-sm rounded transition-colors text-red-600 hover:bg-red-50"
									on:click={deleteFile}
								>
									🗑️ delete
								</button>
							{/if}
						</div>
					</div>

					<!-- 文件内容 -->
					<div class="file-content">
						{#if currentView === 'content'}
							{#if isLargeFile(fileInfo.file_size)}
								<!-- 大文件LFS显示 -->
								<div class="p-6 text-center">
									<div class="mb-6">
										<div class="text-lg text-gray-700 mb-4">
											This file is stored with <a
												href="#"
												class="underline text-blue-600 hover:text-blue-800">LFS</a
											>. It is too big to display, but you can still
											<a
												href="#"
												class="underline text-blue-600 hover:text-blue-800"
												on:click={downloadFile}>download it</a
											>.
										</div>
									</div>

									<!-- 文件详细信息 -->
									<div class="border-t pt-6">
										<h3 class="text-lg font-semibold text-gray-900 mb-4">
											Large File Pointer Details
											<span class="text-sm font-normal text-gray-500">(📄 Raw pointer file)</span>
										</h3>

										<div class="space-y-3 font-mono text-sm bg-gray-50 p-4 rounded-lg">
											<div>
												<span class="font-semibold">Pointer size:</span>
												<span class="text-gray-700">134 Bytes · </span>
												<span class="font-semibold">Size of remote file:</span>
												<span class="text-gray-700">{formatFileSize(fileInfo.file_size)}</span>
											</div>
										</div>
									</div>
								</div>
							{:else if isImageFile(fileInfo.filename)}
								<!-- 图片文件信息显示 -->
								<div class="p-6">
									<!-- 图片预览 -->
									<div class="text-center mb-6">
										<img
											src="/api/repositories/{username}/{repositoryName}/raw/{filePath}"
											alt={fileInfo.filename}
											class="max-w-full h-auto max-h-96 mx-auto rounded shadow border"
										/>
									</div>

									<!-- 文件详细信息 -->
									<div class="border-t pt-6">
										<h3 class="text-lg font-semibold text-gray-900 mb-4">File Details</h3>

										<div class="space-y-3 font-mono text-sm bg-gray-50 p-4 rounded-lg">
											<div>
												<span class="font-semibold">File size:</span>
												<span class="text-gray-700">{formatFileSize(fileInfo.file_size)}</span>
											</div>
											<div>
												<span class="font-semibold">MIME type:</span>
												<span class="text-gray-700">{fileInfo.mime_type || 'N/A'}</span>
											</div>
										</div>
									</div>
								</div>
							{:else if isVideoFile(fileInfo.filename)}
								<!-- 视频文件显示 -->
								<div class="p-6">
									<!-- 视频预览 -->
									<div class="text-center mb-6">
										<video
											src="/api/repositories/{username}/{repositoryName}/raw/{filePath}"
											class="max-w-full h-auto max-h-96 mx-auto rounded shadow border"
											controls
											preload="metadata"
										>
											您的浏览器不支持视频播放。
										</video>
									</div>

									<!-- 文件详细信息 -->
									<div class="border-t pt-6">
										<h3 class="text-lg font-semibold text-gray-900 mb-4">Video File Details</h3>

										<div class="space-y-3 font-mono text-sm bg-gray-50 p-4 rounded-lg">
											<div>
												<span class="font-semibold">File size:</span>
												<span class="text-gray-700">{formatFileSize(fileInfo.file_size)}</span>
											</div>
											<div>
												<span class="font-semibold">MIME type:</span>
												<span class="text-gray-700">{fileInfo.mime_type || 'N/A'}</span>
											</div>
											<div>
												<span class="font-semibold">Format:</span>
												<span class="text-gray-700"
													>{fileInfo.filename.split('.').pop().toUpperCase()}</span
												>
											</div>
										</div>
									</div>
								</div>
							{:else if isModelFile(fileInfo.filename)}
								<!-- 模型文件显示 -->
								<div class="p-6">
									<!-- 模型图标 -->
									<div class="text-center mb-6">
										<div
											class="w-24 h-24 mx-auto bg-purple-100 rounded-lg flex items-center justify-center"
										>
											<span class="text-4xl">🤖</span>
										</div>
										<h3 class="text-xl font-semibold text-gray-900 mt-4">
											{getModelType(fileInfo.filename)} Model
										</h3>
									</div>

									<!-- 文件详细信息 -->
									<div class="border-t pt-6">
										<h3 class="text-lg font-semibold text-gray-900 mb-4">Model File Details</h3>

										<div class="space-y-3 font-mono text-sm bg-gray-50 p-4 rounded-lg">
											<div>
												<span class="font-semibold">Model type:</span>
												<span class="text-gray-700">{getModelType(fileInfo.filename)}</span>
											</div>
											<div>
												<span class="font-semibold">File size:</span>
												<span class="text-gray-700">{formatFileSize(fileInfo.file_size)}</span>
											</div>
											<div>
												<span class="font-semibold">Format:</span>
												<span class="text-gray-700"
													>{fileInfo.filename.split('.').pop().toUpperCase()}</span
												>
											</div>
											<div>
												<span class="font-semibold">MIME type:</span>
												<span class="text-gray-700"
													>{fileInfo.mime_type || 'application/octet-stream'}</span
												>
											</div>
										</div>

										<div class="mt-4 p-4 bg-purple-50 rounded-lg">
											<p class="text-sm text-gray-700">
												This is a machine learning model file. Download it to use in your ML
												projects.
											</p>
										</div>
									</div>
								</div>
							{:else if isDataFile(fileInfo.filename)}
								<!-- 数据文件显示 -->
								<div class="p-6">
									<!-- 数据图标 -->
									<div class="text-center mb-6">
										<div
											class="w-24 h-24 mx-auto bg-green-100 rounded-lg flex items-center justify-center"
										>
											<span class="text-4xl">📊</span>
										</div>
										<h3 class="text-xl font-semibold text-gray-900 mt-4">Dataset File</h3>
									</div>

									<!-- 数据预览（对于JSON和CSV小文件） -->
									{#if fileInfo.content && fileInfo.file_size < 1024 * 1024}
										<div class="mb-6">
											<h4 class="text-md font-semibold text-gray-900 mb-2">Data Preview</h4>
											<div class="bg-gray-50 p-4 rounded-lg overflow-x-auto">
												<pre
													class="text-sm text-gray-800 whitespace-pre-wrap">{fileInfo.content.substring(
														0,
														1000
													)}{fileInfo.content.length > 1000 ? '...' : ''}</pre>
											</div>
										</div>
									{/if}

									<!-- 文件详细信息 -->
									<div class="border-t pt-6">
										<h3 class="text-lg font-semibold text-gray-900 mb-4">Dataset Details</h3>

										<div class="space-y-3 font-mono text-sm bg-gray-50 p-4 rounded-lg">
											<div>
												<span class="font-semibold">File size:</span>
												<span class="text-gray-700">{formatFileSize(fileInfo.file_size)}</span>
											</div>
											<div>
												<span class="font-semibold">Format:</span>
												<span class="text-gray-700"
													>{fileInfo.filename.split('.').pop().toUpperCase()}</span
												>
											</div>
											<div>
												<span class="font-semibold">MIME type:</span>
												<span class="text-gray-700">{fileInfo.mime_type || 'N/A'}</span>
											</div>
										</div>

										<div class="mt-4 p-4 bg-green-50 rounded-lg">
											<p class="text-sm text-gray-700">
												This is a dataset file that can be used for machine learning training and
												analysis.
											</p>
										</div>
									</div>
								</div>
							{:else if isPdfFile(fileInfo.filename)}
								<!-- PDF文件显示 -->
								<div class="p-6">
									<!-- PDF图标 -->
									<div class="text-center mb-6">
										<div
											class="w-24 h-24 mx-auto bg-red-100 rounded-lg flex items-center justify-center"
										>
											<span class="text-4xl">📕</span>
										</div>
										<h3 class="text-xl font-semibold text-gray-900 mt-4">PDF Document</h3>
									</div>

									<!-- 文件详细信息 -->
									<div class="border-t pt-6">
										<h3 class="text-lg font-semibold text-gray-900 mb-4">Document Details</h3>

										<div class="space-y-3 font-mono text-sm bg-gray-50 p-4 rounded-lg">
											<div>
												<span class="font-semibold">File size:</span>
												<span class="text-gray-700">{formatFileSize(fileInfo.file_size)}</span>
											</div>
											<div>
												<span class="font-semibold">Format:</span>
												<span class="text-gray-700">PDF</span>
											</div>
											<div>
												<span class="font-semibold">MIME type:</span>
												<span class="text-gray-700">{fileInfo.mime_type || 'application/pdf'}</span>
											</div>
										</div>

										<div class="mt-4 p-4 bg-red-50 rounded-lg">
											<p class="text-sm text-gray-700">
												This is a PDF document. <button
													class="text-blue-600 hover:text-blue-800 underline"
													on:click={downloadFile}>Download</button
												> to view the content.
											</p>
										</div>
									</div>
								</div>
							{:else if isMarkdownFile(fileInfo.filename)}
								<!-- Markdown文件显示 -->
								{#if currentMarkdownView === 'preview'}
									<!-- Markdown预览模式 - 与仓库主页统一样式 -->
									<div class="prose prose-gray dark:prose-invert max-w-none overflow-hidden">
										<div class="model-card-content p-6">
											{@html renderMarkdown(fileContent)}
										</div>
									</div>
								{:else}
									<!-- Markdown代码模式 -->
									<div class="p-0">
										<pre
											class="overflow-x-auto p-6 text-sm bg-gray-50 border-0 font-mono leading-relaxed whitespace-pre-wrap"><code
												class="text-gray-800"
												>{@html applyBasicSyntaxHighlight(fileContent, 'markdown')}</code
											></pre>
									</div>
								{/if}
							{:else if isTextFile(fileInfo.filename)}
								<!-- 文本文件显示 -->
								<div class="p-0">
									<pre
										class="overflow-x-auto p-6 text-sm bg-gray-50 border-0 font-mono leading-relaxed whitespace-pre-wrap text-gray-800">{fileContent}</pre>
								</div>
							{:else}
								<!-- 二进制文件 -->
								<div class="p-6 text-center text-gray-500">
									<div class="text-4xl mb-4">📦</div>
									<p>这是一个二进制文件，无法在线预览</p>
									<Button variant="outline" size="sm" class="mt-4" on:click={downloadFile}>
										下载查看
									</Button>
								</div>
							{/if}
						{:else if currentView === 'history'}
							<!-- 版本历史 -->
							<div class="p-6">
								{#if versionHistory.length === 0}
									<div class="text-center text-gray-500 py-8">
										<div class="text-2xl mb-2">📜</div>
										<p>暂无版本历史</p>
									</div>
								{:else}
									<div class="space-y-4">
										{#each versionHistory as version}
											<div class="flex items-start space-x-4 p-4 bg-gray-50 rounded-lg">
												<div
													class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-medium"
												>
													v{version.version_number}
												</div>
												<div class="flex-1 min-w-0">
													<div class="flex items-center space-x-2 mb-1">
														<h4 class="text-sm font-medium text-gray-900">
															{version.commit_message || '版本 ' + version.version_number}
														</h4>
														<Badge variant="secondary" size="sm">
															{version.version_hash}
														</Badge>
													</div>
													<div class="text-sm text-gray-600">
														<span>{version.author?.username || 'Unknown'}</span>
														<span class="mx-2">•</span>
														<span>{formatDate(version.created_at)}</span>
														<span class="mx-2">•</span>
														<span>{formatFileSize(version.file_size)}</span>
													</div>
													{#if version.diff_summary}
														<div class="mt-2 text-xs text-gray-500">
															{#if version.diff_summary.lines_added > 0}
																<span class="text-green-600"
																	>+{version.diff_summary.lines_added}</span
																>
															{/if}
															{#if version.diff_summary.lines_removed > 0}
																<span class="text-red-600 ml-2"
																	>-{version.diff_summary.lines_removed}</span
																>
															{/if}
														</div>
													{/if}
												</div>
												<div class="flex space-x-2">
													<Button
														variant="outline"
														size="sm"
														on:click={() =>
															goto(
																`/${username}/${repositoryName}/blob/${filePath}?version=${version.id}`
															)}
													>
														查看
													</Button>
												</div>
											</div>
										{/each}
									</div>
								{/if}
							</div>
						{:else if currentView === 'raw'}
							<!-- 原始内容 -->
							<div class="p-0">
								<pre
									class="whitespace-pre-wrap font-mono text-sm p-6 overflow-x-auto bg-gray-50"><code
										class="text-gray-800"
										>{@html applyBasicSyntaxHighlight(
											fileContent,
											detectLanguage(fileInfo.filename)
										)}</code
									></pre>
							</div>
						{/if}
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.file-content :global(pre) {
		background: #f8f9fa;
		border-radius: 0;
		margin: 0;
	}

	/* Metadata块中的pre元素保持原始背景 */
	.file-content :global(.metadata-block pre) {
		background: transparent !important;
		margin: 0;
		line-height: 1.4;
	}

	.file-content :global(pre code) {
		background: none;
		padding: 0;
		font-size: inherit;
		color: inherit;
	}

	/* GitHub风格语法高亮 - 浅色主题 */
	.file-content :global(.yaml-frontmatter) {
		color: #6f42c1;
	}

	.file-content :global(.yaml-key) {
		color: #005cc5;
		font-weight: 600;
	}

	.file-content :global(.yaml-value) {
		color: #032f62;
	}

	.file-content :global(.yaml-comment) {
		color: #6a737d;
		font-style: italic;
	}

	/* Markdown语法高亮 - 浅色主题 */
	.file-content :global(.md-header) {
		color: #005cc5;
		font-weight: bold;
	}

	.file-content :global(.md-bold) {
		color: #d73a49;
		font-weight: bold;
	}

	.file-content :global(.md-italic) {
		color: #6f42c1;
		font-style: italic;
	}

	.file-content :global(.md-link) {
		color: #0366d6;
		text-decoration: none;
	}

	.file-content :global(.md-code-block) {
		color: #e36209;
		background: rgba(255, 229, 100, 0.2);
		padding: 2px 4px;
		border-radius: 3px;
	}

	.file-content :global(.md-inline-code) {
		color: #e36209;
		background: rgba(255, 229, 100, 0.2);
		padding: 1px 3px;
		border-radius: 2px;
		font-family: 'SFMono-Regular', Consolas, monospace;
	}

	.file-content :global(.md-list) {
		color: #22863a;
	}

	/* 浅色背景下的语法高亮 - 适用于Code模式 */
	.file-content :global(pre.bg-gray-50 .yaml-key) {
		color: #005cc5;
		font-weight: 600;
	}

	.file-content :global(pre.bg-gray-50 .yaml-value) {
		color: #032f62;
	}

	.file-content :global(pre.bg-gray-50 .yaml-comment) {
		color: #6a737d;
		font-style: italic;
	}

	.file-content :global(pre.bg-gray-50 .md-header) {
		color: #005cc5;
		font-weight: bold;
	}

	.file-content :global(pre.bg-gray-50 .md-bold) {
		color: #d73a49;
		font-weight: bold;
	}

	.file-content :global(pre.bg-gray-50 .md-italic) {
		color: #6f42c1;
		font-style: italic;
	}

	.file-content :global(pre.bg-gray-50 .md-link) {
		color: #0366d6;
	}

	.file-content :global(pre.bg-gray-50 .md-code-block) {
		color: #e36209;
		background: rgba(255, 229, 100, 0.2);
		padding: 2px 4px;
		border-radius: 3px;
	}

	.file-content :global(pre.bg-gray-50 .md-inline-code) {
		color: #e36209;
		background: rgba(255, 229, 100, 0.2);
		padding: 1px 3px;
		border-radius: 2px;
	}

	.file-content :global(pre.bg-gray-50 .md-list) {
		color: #22863a;
	}

	/* Metadata 块的深色主题样式 */
	.file-content :global(.metadata-block) {
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}

	.file-content :global(.metadata-block .yaml-key) {
		color: #9cdcfe;
		font-weight: 600;
	}

	.file-content :global(.metadata-block .yaml-value) {
		color: #ce9178;
	}

	.file-content :global(.metadata-block .yaml-comment) {
		color: #6a9955;
		font-style: italic;
	}

	/* Model Card Content Styles - 与仓库主页统一 */
	.model-card-content {
		width: 100%;
		overflow-wrap: break-word;
		word-wrap: break-word;
	}

	/* 表格滚动样式 */
	.model-card-content :global(table) {
		display: table;
		width: max-content;
		min-width: 100%;
		border-collapse: collapse;
		margin-bottom: 1rem;
		white-space: nowrap;
	}

	.model-card-content :global(.table-container) {
		overflow-x: auto;
		margin-bottom: 1rem;
		border: 1px solid #e5e7eb;
		border-radius: 0.375rem;
		scrollbar-width: thin;
		scrollbar-color: #64748b #f1f5f9;
	}

	.dark .model-card-content :global(.table-container) {
		border-color: #374151;
		scrollbar-color: #64748b #1f2937;
	}

	.model-card-content :global(.table-container)::-webkit-scrollbar {
		height: 8px;
	}

	.model-card-content :global(.table-container)::-webkit-scrollbar-track {
		background: #f1f5f9;
		border-radius: 4px;
	}

	.dark .model-card-content :global(.table-container)::-webkit-scrollbar-track {
		background: #1f2937;
	}

	.model-card-content :global(.table-container)::-webkit-scrollbar-thumb {
		background: #64748b;
		border-radius: 4px;
	}

	.model-card-content :global(.table-container)::-webkit-scrollbar-thumb:hover {
		background: #94a3b8;
	}

	.model-card-content :global(table th),
	.model-card-content :global(table td) {
		border: 1px solid #e5e7eb;
		padding: 0.75rem;
		text-align: left;
		white-space: nowrap;
		min-width: 120px;
	}

	.dark .model-card-content :global(table th),
	.dark .model-card-content :global(table td) {
		border-color: #374151;
	}

	.model-card-content :global(table th) {
		background-color: #f8fafc;
		font-weight: 600;
	}

	.dark .model-card-content :global(table th) {
		background-color: #1e293b;
	}

	/* 图片响应式 */
	.model-card-content :global(img) {
		max-width: 100%;
		height: auto;
	}

	/* 长文本换行 */
	.model-card-content :global(p),
	.model-card-content :global(div),
	.model-card-content :global(span) {
		word-wrap: break-word;
		overflow-wrap: break-word;
	}

	/* metadata块在model-card-content中的特殊处理 */
	.model-card-content :global(.metadata-block) {
		margin-bottom: 1.5rem;
	}

	/* Prose 自定义样式 - 与仓库主页保持一致 */
	.prose :global(code) {
		color: #1e293b;
		font-size: 0.875rem;
		font-family: 'Fira Code', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
	}

	.dark .prose :global(code) {
		color: #f1f5f9;
	}

	.prose :global(pre) {
		background-color: #f1f5f9;
		color: #1e293b;
		padding: 1.25rem;
		border-radius: 0.5rem;
		overflow-x: auto;
		margin-bottom: 1.5rem;
		border: 1px solid #e2e8f0;
		font-family: 'Fira Code', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
		line-height: 1.5;
	}

	.dark .prose :global(pre) {
		background-color: #374151;
		color: #f9fafb;
		border-color: #4b5563;
	}
</style>
