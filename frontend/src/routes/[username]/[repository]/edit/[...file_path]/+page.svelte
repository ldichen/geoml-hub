<script>
	import { page } from '$app/stores';
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/utils/api.js';
	
	import { Star, Download, Eye, Calendar, FileText, ChevronRight, Edit2, Check, X } from 'lucide-svelte';
	import { formatDistanceToNow } from 'date-fns';
	import { zhCN } from 'date-fns/locale';
	import { user as currentUser } from '$lib/stores/auth.js';
	import UserAvatar from '$lib/components/UserAvatar.svelte';
	import SocialButton from '$lib/components/SocialButton.svelte';
	import FileEditor from '$lib/components/editor/FileEditor.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Modal from '$lib/components/ui/Modal.svelte';
	import Loading from '$lib/components/Loading.svelte';
	import Toast from '$lib/components/ui/Toast.svelte';
	
	// 路由参数
	$: username = $page.params.username;
	$: repositoryName = $page.params.repository;
	$: filePath = $page.params.file_path;
	
	// 状态
	let repository = null;
	let fileInfo = null;
	let fileContent = '';
	let isLoading = true;
	let error = null;
	let toast = null;
	let isModified = false;
	let isSaving = false;
	let editSession = null;
	let activeCollaborators = [];
	
	// 模态框状态
	let showCommitModal = false;
	let showUnsavedChangesModal = false;
	let commitMessage = '';
	let pendingNavigation = null;
	
	// 编辑器设置
	let editorTheme = 'light';
	let autoSave = true;
	let showPreview = false;
	let currentEditorView = 'edit'; // 'edit' or 'preview'
	
	// 文件名编辑状态
	let isEditingFileName = false;
	let newFileName = '';
	let originalFileName = '';
	
	// 加载数据
	onMount(async () => {
		console.log('📝 编辑页面组件已挂载，开始加载数据');
		await loadData();
		await startEditSession();
		
		console.log('✅ 数据加载完成，组件状态:', { 
			hasRepository: !!repository, 
			hasFileInfo: !!fileInfo, 
			contentLength: fileContent.length,
			isModified,
			editSession: !!editSession
		});
		
		// 页面离开前确认
		window.addEventListener('beforeunload', handleBeforeUnload);
	});
	
	onDestroy(() => {
		window.removeEventListener('beforeunload', handleBeforeUnload);
		if (editSession) {
			endEditSession();
		}
	});
	
	async function loadData() {
		isLoading = true;
		error = null;
		
		try {
			// 并行加载仓库信息和文件内容
			const [repoResponse, fileResponse] = await Promise.all([
				api.getRepository(username, repositoryName),
				api.repositories.getFileContent(username, repositoryName, filePath)
			]);
			
			console.log('🔍 API响应调试信息:');
			console.log('仓库响应:', repoResponse);
			console.log('文件响应:', fileResponse);
			console.log('文件内容字段:', fileResponse?.content);
			console.log('文件内容长度:', fileResponse?.content?.length || 0);
			
			repository = repoResponse;
			fileInfo = fileResponse;
			fileContent = fileInfo.content || '';
			
			// 初始化文件名
			originalFileName = fileInfo.filename || '';
			newFileName = originalFileName;
			
			console.log('📝 设置后的 fileContent:', fileContent);
			console.log('📝 fileContent 长度:', fileContent.length);
			
			// 检查编辑权限
			await checkEditPermission();
			
		} catch (err) {
			console.error('加载文件失败:', err);
			error = err.response?.data?.detail || '加载文件失败';
		} finally {
			isLoading = false;
		}
	}
	
	async function checkEditPermission() {
		// 临时简化：假设所有用户都有编辑权限（实际应用中需要权限检查）
		return true;
	}
	
	async function startEditSession() {
		if (!fileInfo) return;
		
		try {
			// 临时简化：创建一个假的编辑会话（实际应用中需要实现编辑会话API）
			editSession = {
				session_id: 'temp-session-' + Date.now(),
				file_id: fileInfo.id,
				created_at: new Date().toISOString()
			};
			
			// 开始监听协作状态
			pollCollaborationStatus();
			
		} catch (err) {
			console.error('创建编辑会话失败:', err);
			toast = { type: 'error', message: '无法创建编辑会话' };
		}
	}
	
	async function endEditSession() {
		if (!editSession) return;
		
		// 临时简化：直接清理编辑会话（实际应用中需要调用删除会话API）
		console.log('结束编辑会话:', editSession.session_id);
	}
	
	async function pollCollaborationStatus() {
		if (!fileInfo) return;
		
		// 临时简化：不获取协作状态（实际应用中需要实现协作API）
		activeCollaborators = [];
		
		// 每30秒检查一次
		setTimeout(pollCollaborationStatus, 30000);
	}
	
	// 内容变更处理
	function handleContentChange(event) {
		const { content, isModified: modified } = event.detail;
		fileContent = content;
		isModified = modified;
		
		console.log('文件内容已更改:', { 
			isModified: modified, 
			contentLength: content.length,
			originalLength: fileInfo?.content?.length || 0
		});
		
		// 更新编辑会话
		if (editSession && modified) {
			updateEditSession(content);
		}
	}
	
	async function updateEditSession(content) {
		if (!editSession) return;
		
		// 临时简化：在控制台记录会话更新（实际应用中需要更新会话API）
		console.log('更新编辑会话:', editSession.session_id, 'content length:', content.length);
	}
	
	// 保存草稿
	async function handleSaveDraft(event) {
		const { content, cursorPosition, filePath } = event.detail;
		
		// 临时简化：在控制台记录草稿保存（实际应用中需要实现草稿保存API）
		console.log('自动保存草稿:', { 
			filename: fileInfo.filename,
			content: content.slice(0, 100) + '...', 
			cursorPosition 
		});
	}
	
	// 手动保存文件
	function handleSaveFile() {
		console.log('点击保存按钮:', { isModified, fileContentLength: fileContent.length });
		if (!isModified) {
			console.log('文件未修改，无需保存');
			toast = { type: 'info', message: '文件未修改，无需保存' };
			return;
		}
		console.log('显示提交模态框');
		showCommitModal = true;
		console.log('模态框状态已设置:', { showCommitModal });
		
		// 延迟确认状态
		setTimeout(() => {
			console.log('1秒后模态框状态:', { showCommitModal });
		}, 1000);
	}
	
	// 提交保存
	async function commitChanges() {
		if (!commitMessage.trim()) {
			toast = { type: 'error', message: '请输入提交信息' };
			return;
		}
		
		isSaving = true;
		try {
			console.log('💾 开始保存文件到服务器...', { 
				fileId: fileInfo.id, 
				contentLength: fileContent.length, 
				commitMessage 
			});
			
			// 调用真实的API保存文件
			const response = await api.request(`/api/repositories/${username}/${repositoryName}/blob/${filePath}`, {
				method: 'PUT',
				body: {
					content: fileContent,
					commit_message: commitMessage
				}
			});
			
			console.log('✅ 文件保存成功，服务器响应:', response);
			
			isModified = false;
			showCommitModal = false;
			commitMessage = '';
			toast = { type: 'success', message: '✅ 文件已成功保存到服务器！' };
			
			// 更新文件信息
			if (response.file_info) {
				fileInfo.file_size = response.file_info.file_size;
				fileInfo.updated_at = response.file_info.updated_at;
			}
			
			alert(`🎉 文件保存成功！\n提交信息: ${commitMessage}\n文件大小: ${response.file_info?.file_size} 字节`);
			
		} catch (err) {
			console.error('❌ 保存文件失败:', err);
			const errorMessage = err.response?.data?.detail || err.detail || err.message || '保存文件失败';
			toast = { type: 'error', message: '❌ ' + errorMessage };
			alert('❌ 保存失败: ' + errorMessage);
		} finally {
			isSaving = false;
		}
	}
	
	// 取消编辑
	function cancelEdit() {
		if (isModified) {
			showUnsavedChangesModal = true;
			pendingNavigation = () => goto(`/${username}/${repositoryName}/blob/${filePath}`);
		} else {
			goto(`/${username}/${repositoryName}/blob/${filePath}`);
		}
	}
	
	// 页面离开前确认
	function handleBeforeUnload(event) {
		if (isModified) {
			event.preventDefault();
			event.returnValue = '您有未保存的更改，确定要离开吗？';
		}
	}
	
	// 处理未保存更改的确认
	function handleUnsavedChanges(action) {
		showUnsavedChangesModal = false;
		if (action === 'save') {
			showCommitModal = true;
		} else if (action === 'discard') {
			isModified = false;
			if (pendingNavigation) {
				pendingNavigation();
				pendingNavigation = null;
			}
		}
	}
	
	// 预览切换
	function togglePreview() {
		showPreview = !showPreview;
	}
	
	// 版本历史
	function showHistory() {
		goto(`/${username}/${repositoryName}/commits/${filePath}`);
	}
	
	// 格式化代码
	async function handleFormatCode(event) {
		const { content, language } = event.detail;
		
		// 临时简化：基本的代码格式化（实际应用中需要实现格式化API）
		try {
			// 简单的格式化：去除多余空行和空格
			let formatted = content
				.replace(/\n\s*\n\s*\n/g, '\n\n') // 多个空行变为两个
				.replace(/\t/g, '    ') // 制表符转为4个空格
				.trim();
			
			fileContent = formatted;
			toast = { type: 'success', message: '代码格式化完成（基础版）' };
		} catch (err) {
			console.error('格式化失败:', err);
			toast = { type: 'error', message: '代码格式化失败' };
		}
	}
	
	// 检测文件语言
	function detectLanguage(filename) {
		const ext = filename.split('.').pop().toLowerCase();
		const languageMap = {
			py: 'python',
			js: 'javascript',
			ts: 'typescript',
			json: 'json',
			md: 'markdown',
			yaml: 'yaml',
			yml: 'yaml'
		};
		return languageMap[ext] || '';
	}
	
	// 检测是否为Markdown文件
	function isMarkdownFile(filename) {
		const markdownExtensions = ['md', 'markdown'];
		const ext = filename.split('.').pop().toLowerCase();
		return markdownExtensions.includes(ext);
	}
	
	// 简单的Markdown渲染函数（用于Preview模式）
	function renderMarkdown(content) {
		if (!content) return '';
		
		// 处理metadata块（YAML front matter）
		let html = content;
		const metadataMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
		
		if (metadataMatch) {
			const metadata = metadataMatch[1];
			const bodyContent = metadataMatch[2];
			
			// 渲染metadata
			const metadataHtml = `<div class="metadata-block bg-gray-800 text-gray-100 p-4 rounded-lg mb-6 font-mono text-sm border border-gray-600">
				<div class="inline-block bg-gray-700 text-gray-200 px-2 py-1 rounded text-xs mb-3 font-semibold">metadata</div>
				<pre class="whitespace-pre-wrap text-gray-100">${highlightYaml(metadata.trim())}</pre>
			</div>`;
			
			// 渲染markdown内容
			html = metadataHtml + renderMarkdownContent(bodyContent);
		} else {
			html = renderMarkdownContent(content);
		}
		
		return html;
	}
	
	// 渲染markdown内容（不包括metadata）
	function renderMarkdownContent(content) {
		let html = content
			// 标题
			.replace(/^### (.*$)/gim, '<h3 class="text-lg font-semibold text-gray-900 mt-6 mb-3">$1</h3>')
			.replace(/^## (.*$)/gim, '<h2 class="text-xl font-semibold text-gray-900 mt-8 mb-4">$1</h2>')
			.replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold text-gray-900 mt-8 mb-6">$1</h1>')
			// 链接
			.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-blue-600 hover:text-blue-800 underline">$1</a>')
			// 代码块
			.replace(/```[\s\S]*?```/g, (match) => {
				const code = match.replace(/```/g, '').trim();
				return `<pre class="bg-gray-100 p-4 rounded-lg overflow-x-auto my-4"><code class="text-sm">${code}</code></pre>`;
			})
			// 行内代码
			.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>')
			// 列表项
			.replace(/^\s*[-*+]\s+(.*)$/gim, '<li class="ml-4">$1</li>')
			// 数字列表
			.replace(/^\s*\d+\.\s+(.*)$/gim, '<li class="ml-4">$1</li>')
			// 段落
			.replace(/\n\n/g, '</p><p class="mb-4">');
		
		// 包装段落
		if (html && !html.startsWith('<')) {
			html = '<p class="mb-4">' + html + '</p>';
		}
		
		return html;
	}
	
	// YAML语法高亮
	function highlightYaml(yaml) {
		return yaml
			// Keys
			.replace(/^(\s*)([^:\s]+)(\s*:)/gm, '$1<span class="yaml-key">$2</span>$3')
			// String values
			.replace(/:\s*([^\s].*)/g, ': <span class="yaml-value">$1</span>')
			// Comments
			.replace(/(#.*)/g, '<span class="yaml-comment">$1</span>');
	}
	
	// 格式化文件大小
	function formatFileSize(bytes) {
		if (!bytes) return '0 B';
		const sizes = ['B', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(1024));
		return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
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
	
	// 文件名编辑相关函数
	function startEditingFileName() {
		isEditingFileName = true;
		newFileName = originalFileName;
	}
	
	function cancelFileNameEdit() {
		isEditingFileName = false;
		newFileName = originalFileName;
	}
	
	async function saveFileName() {
		if (!newFileName.trim()) {
			toast = { type: 'error', message: '文件名不能为空' };
			return;
		}
		
		if (newFileName === originalFileName) {
			isEditingFileName = false;
			return;
		}
		
		try {
			// 调用API重命名文件
			const response = await api.request(`/api/repositories/${username}/${repositoryName}/files/rename`, {
				method: 'POST',
				body: {
					old_path: filePath,
					new_filename: newFileName,
					commit_message: `重命名文件: ${originalFileName} -> ${newFileName}`
				}
			});
			
			// 更新文件信息
			originalFileName = newFileName;
			fileInfo.filename = newFileName;
			isEditingFileName = false;
			
			toast = { type: 'success', message: '文件名修改成功' };
			
			// 如果需要，可以重定向到新的文件路径
			const newPath = filePath.replace(originalFileName, newFileName);
			if (newPath !== filePath) {
				// 注意：这里可能需要根据实际的URL结构调整
				// goto(`/${username}/${repositoryName}/edit/${newPath}`);
			}
			
		} catch (err) {
			console.error('重命名文件失败:', err);
			const errorMessage = err.response?.data?.detail || err.message || '重命名文件失败';
			toast = { type: 'error', message: errorMessage };
		}
	}
	
	// 检查文件名是否有效
	function isValidFileName(filename) {
		// 基本的文件名验证
		const invalidChars = /[<>:"/\\|?*]/;
		return filename && filename.trim() && !invalidChars.test(filename);
	}
</script>

<svelte:head>
	<title>编辑 {fileInfo?.filename || '文件'} - {repositoryName} - GeoML-Hub</title>
</svelte:head>

{#if toast}
	<Toast type={toast.type} message={toast.message} on:close={() => toast = null} />
{/if}

<div class="file-edit-page h-screen flex flex-col">
	<!-- 仓库头部 -->
	{#if repository}
		<div class="bg-linear-to-t from-blue-500/8 dark:from-blue-500/20 to-white to-70% dark:to-gray-950 border-b border-gray-100 dark:border-gray-800 pt-6 sm:pt-9">
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
										<a href="/{repository.owner?.username}" class="text-blue-600 dark:text-blue-300 hover:text-blue-700 dark:hover:text-blue-200 hover:underline">
											{repository.owner?.username}
										</a>
										<span class="text-gray-500 dark:text-gray-400">/</span>
										<h1 class="text-xl font-bold text-gray-900 dark:text-white">
											{repository.name}
										</h1>
										{#if repository.visibility === 'private'}
											<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
												私有
											</span>
										{/if}
									</div>
									
									<!-- Stats next to repository name with proper spacing -->
									<div class="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400 ml-6">
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
										创建于 {formatDistanceToNow(new Date(repository.created_at), { addSuffix: true, locale: zhCN })}
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
										<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
											{tag}
										</span>
									{/each}
								</div>
							{/if}

							<!-- Classification Row (Blue) -->
							{#if repository.classification_path && repository.classification_path.length > 0}
								<div class="flex items-center space-x-1 mb-2">
									{#each repository.classification_path as classification, index}
										<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200">
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
							href="/{repository.owner?.username}/{repository.name}"
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
	
	<!-- 编辑器操作区域 -->
	<div class="bg-white border-b border-gray-200">
		
		<!-- Edit/Preview 标签切换 -->
		{#if fileInfo && isMarkdownFile(fileInfo.filename)}
			<div class="container px-4 py-2 flex items-center justify-between">
				<div class="flex space-x-1">
					<button
						class="px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors"
						class:border-blue-500={currentEditorView === 'edit'}
						class:text-blue-600={currentEditorView === 'edit'}
						class:bg-white={currentEditorView === 'edit'}
						class:border-transparent={currentEditorView !== 'edit'}
						class:text-gray-500={currentEditorView !== 'edit'}
						class:hover:text-gray-700={currentEditorView !== 'edit'}
						on:click={() => currentEditorView = 'edit'}
					>
						Edit
					</button>
					<button
						class="px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors"
						class:border-blue-500={currentEditorView === 'preview'}
						class:text-blue-600={currentEditorView === 'preview'}
						class:bg-white={currentEditorView === 'preview'}
						class:border-transparent={currentEditorView !== 'preview'}
						class:text-gray-500={currentEditorView !== 'preview'}
						class:hover:text-gray-700={currentEditorView !== 'preview'}
						on:click={() => currentEditorView = 'preview'}
					>
						Preview
					</button>
				</div>
				
				<!-- 简化的操作按钮 -->
				<div class="flex items-center space-x-2">
					<Button
						variant="outline"
						size="sm"
						on:click={cancelEdit}
					>
						取消
					</Button>
					<Button
						variant="primary"
						size="sm"
						disabled={!isModified || isSaving}
						on:click={handleSaveFile}
					>
						{isSaving ? '保存中...' : '保存更改'}
					</Button>
				</div>
			</div>
		{:else}
			<!-- 非Markdown文件的简化头部 -->
			<div class="container px-4 py-2 flex items-center justify-between">
				<div class="flex items-center space-x-4">
					<div class="text-sm text-gray-600">
						编辑模式
					</div>
					
					<!-- 文件名编辑区域 -->
					{#if fileInfo}
						<div class="flex items-center space-x-2">
							<span class="text-xs text-gray-500">文件名:</span>
							{#if isEditingFileName}
								<div class="flex items-center space-x-2">
									<input
										type="text"
										bind:value={newFileName}
										class="px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
										class:border-red-300={!isValidFileName(newFileName)}
										style="min-width: 150px;"
										on:keydown={(e) => {
											if (e.key === 'Enter') saveFileName();
											if (e.key === 'Escape') cancelFileNameEdit();
										}}
									/>
									<button
										class="p-1 text-green-600 hover:text-green-700 hover:bg-green-50 rounded"
										on:click={saveFileName}
										disabled={!isValidFileName(newFileName)}
									>
										<Check class="h-3 w-3" />
									</button>
									<button
										class="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded"
										on:click={cancelFileNameEdit}
									>
										<X class="h-3 w-3" />
									</button>
								</div>
								{#if !isValidFileName(newFileName)}
									<span class="text-xs text-red-500">无效字符</span>
								{/if}
							{:else}
								<div class="flex items-center space-x-1">
									<span class="text-xs font-medium text-gray-900">{originalFileName}</span>
									<button
										class="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded"
										on:click={startEditingFileName}
										title="编辑文件名"
									>
										<Edit2 class="h-3 w-3" />
									</button>
								</div>
							{/if}
						</div>
					{/if}
				</div>
				
				<div class="flex items-center space-x-2">
					<Button
						variant="outline"
						size="sm"
						on:click={cancelEdit}
					>
						返回
					</Button>
					<Button
						variant="primary"
						size="sm"
						disabled={!isModified || isSaving}
						on:click={handleSaveFile}
					>
						{isSaving ? '保存中...' : '保存更改'}
					</Button>
				</div>
			</div>
		{/if}
	</div>
	
	<!-- 编辑器主体 -->
	<div class="container border-r border-l border-b rounded-lg flex-1 mb-4 overflow-hidden" style="padding-right: 0;">
		{#if isLoading}
			<Loading message="加载编辑器中..." />
		{:else if error}
			<div class="flex items-center justify-center h-full">
				<div class="text-center">
					<div class="text-red-500 text-lg mb-4">❌ {error}</div>
					<Button on:click={loadData}>重试</Button>
				</div>
			</div>
		{:else if fileInfo}
			{#if isMarkdownFile(fileInfo.filename) && currentEditorView === 'preview'}
				<!-- Markdown预览模式 -->
				<div class="h-full overflow-y-auto bg-white">
					<div class="p-6 prose prose-gray max-w-none">
						{@html renderMarkdown(fileContent)}
					</div>
				</div>
			{:else}
				<!-- 编辑模式 -->
				<FileEditor
					{fileContent}
					fileName={fileInfo.filename}
					{filePath}
					language={detectLanguage(fileInfo.filename)}
					readonly={false}
					theme={editorTheme}
					showToolbar={false}
					showStatusBar={false}
					showSidebar={false}
					{autoSave}
					{repository}
					on:contentChange={handleContentChange}
					on:saveDraft={handleSaveDraft}
					on:saveFile={handleSaveFile}
					on:preview={togglePreview}
					on:history={showHistory}
					on:formatCode={handleFormatCode}
					on:error={(e) => {
						console.error('FileEditor error:', e.detail);
						toast = { type: 'error', message: e.detail.message };
					}}
				/>
			{/if}
		{/if}
	</div>
</div>

<!-- 提交模态框 -->
{#if showCommitModal}
	<Modal
		show={true}
		title="提交更改"
		on:close={() => showCommitModal = false}
	>
		<div class="space-y-4">
			<div>
				<label for="commit-message" class="block text-sm font-medium text-gray-700 mb-2">
					提交信息 *
				</label>
				<textarea
					id="commit-message"
					bind:value={commitMessage}
					placeholder="描述你的更改..."
					rows="3"
					class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
				></textarea>
			</div>
			
			<div class="text-sm text-gray-600">
				<p class="mb-2">更改摘要:</p>
				<ul class="list-disc list-inside space-y-1">
					<li>文件: {fileInfo.filename}</li>
					<li>大小: {Math.round(new Blob([fileContent]).size / 1024 * 100) / 100} KB</li>
				</ul>
			</div>
		</div>
		
		<div slot="footer" class="flex justify-end space-x-3">
			<Button
				variant="outline"
				on:click={() => showCommitModal = false}
			>
				取消
			</Button>
			<Button
				variant="primary"
				disabled={!commitMessage.trim() || isSaving}
				on:click={commitChanges}
			>
				{isSaving ? '提交中...' : '提交更改'}
			</Button>
		</div>
	</Modal>
{/if}

<!-- 未保存更改确认模态框 -->
{#if showUnsavedChangesModal}
	<Modal
		show={true}
		title="未保存的更改"
		on:close={() => showUnsavedChangesModal = false}
	>
		<div class="space-y-4">
			<p class="text-gray-700">
				您有未保存的更改。要保存更改还是丢弃它们？
			</p>
		</div>
		
		<div slot="footer" class="flex justify-end space-x-3">
			<Button
				variant="outline"
				on:click={() => handleUnsavedChanges('cancel')}
			>
				取消
			</Button>
			<Button
				variant="secondary"
				on:click={() => handleUnsavedChanges('discard')}
			>
				丢弃更改
			</Button>
			<Button
				variant="primary"
				on:click={() => handleUnsavedChanges('save')}
			>
				保存更改
			</Button>
		</div>
	</Modal>
{/if}

<!-- Toast 消息提示 -->
{#if toast}
	<Toast
		type={toast.type}
		message={toast.message}
		on:close={() => toast = null}
	/>
{/if}

<style>
	.file-edit-page {
		background: #f8f9fa;
	}
	
	/* YAML 语法高亮样式 - Metadata深色背景 */
	:global(.metadata-block .yaml-key) {
		color: #9cdcfe;
		font-weight: 600;
	}
	
	:global(.metadata-block .yaml-value) {
		color: #ce9178;
	}
	
	:global(.metadata-block .yaml-comment) {
		color: #6a9955;
		font-style: italic;
	}
	
	/* Metadata 块的样式改进 */
	:global(.metadata-block) {
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}
	
	:global(.metadata-block pre) {
		margin: 0;
		line-height: 1.4;
	}
</style>