<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { _ } from 'svelte-i18n';
	import { Upload, File, X, CheckCircle, AlertCircle, Info } from 'lucide-svelte';
	import { user as currentUser } from '$lib/stores/auth.js';
	import { requireAuth, isOwner } from '$lib/utils/auth.js';
	import { api } from '$lib/utils/api.js';
	import FileUpload from '$lib/components/FileUpload.svelte';
	import Loading from '$lib/components/Loading.svelte';

	let repository = null;
	let loading = true;
	let error = '';
	let uploadFiles = [];
	let uploading = false;
	let uploadProgress = {};
	let uploadResults = [];
	let showConfirmDialog = false;
	let confirmDialogData = null;

	$: username = $page.params.username;
	$: repositoryName = $page.params.repository;
	$: isRepoOwner =
		$currentUser && repository && isOwner(repository.owner?.username || repository.owner?.id);

	onMount(async () => {
		// 检查认证状态
		if (!requireAuth('/login')) {
			return;
		}

		await loadRepository();

		// 检查是否是仓库所有者
		if (repository && !isRepoOwner) {
			goto(`${base}/${username}/${repositoryName}`);
			return;
		}
	});

	async function loadRepository() {
		try {
			repository = await api.getRepository(username, repositoryName);
		} catch (err) {
			console.error('Failed to load repository:', err);
			error = $_('error.not_found');
		} finally {
			loading = false;
		}
	}

	function handleFilesSelected(event) {
		const newFiles = Array.from(event.detail);
		uploadFiles = [
			...uploadFiles,
			...newFiles.map((file) => ({
				file,
				id: Math.random().toString(36).substr(2, 9),
				status: 'pending', // pending, uploading, completed, error
				progress: 0,
				error: null
			}))
		];
	}

	function removeFile(fileId) {
		uploadFiles = uploadFiles.filter((f) => f.id !== fileId);
	}

	async function startUpload() {
		if (uploadFiles.length === 0) return;

		uploading = true;
		uploadResults = [];

		try {
			await performUploads();
		} finally {
			uploading = false;
		}
	}

	async function uploadSingleFile(fileItem, confirmed = false) {
		try {
			const result = await api.uploadRepositoryFile(username, repositoryName, fileItem.file, {
				onProgress: (progress) => {
					fileItem.progress = progress;
					uploadFiles = [...uploadFiles];
				},
				confirmed: confirmed
			});

			// 处理成功的上传
			const uploadInfo = result.upload_info || {};
			let message = result.message || '上传成功';

			// 根据上传动作提供更详细的反馈
			if (uploadInfo.action === 'renamed') {
				message = `文件已重命名为 ${uploadInfo.final_filename} 并上传成功`;
			} else if (uploadInfo.action === 'replaced') {
				message = `已替换现有的 ${uploadInfo.original_filename} 文件`;
			}

			uploadResults.push({
				filename: fileItem.file.name,
				finalFilename: uploadInfo.final_filename || fileItem.file.name,
				status: 'success',
				message: message,
				action: uploadInfo.action || 'uploaded'
			});

			return result;
		} catch (err) {
			console.error('Upload failed:', err);

			// 检查是否是特殊文件冲突错误
			if (err.status === 409 && err.data?.error === 'special_file_conflict') {
				// 显示确认对话框
				confirmDialogData = {
					fileItem: fileItem,
					conflictData: err.data
				};
				showConfirmDialog = true;

				// 暂停上传流程，等待用户确认
				throw new Error('PENDING_CONFIRMATION');
			} else {
				// 其他错误，记录失败
				fileItem.status = 'error';
				fileItem.error = err.message || '上传失败';
				uploadFiles = [...uploadFiles];

				uploadResults.push({
					filename: fileItem.file.name,
					status: 'error',
					message: err.message || '上传失败'
				});

				throw err;
			}
		}
	}

	async function handleConfirmReplace() {
		showConfirmDialog = false;
		const { fileItem } = confirmDialogData;

		try {
			await uploadSingleFile(fileItem, true);
			fileItem.status = 'completed';
			fileItem.progress = 100;
			uploadFiles = [...uploadFiles];
		} catch (err) {
			if (err.message !== 'PENDING_CONFIRMATION') {
				fileItem.status = 'error';
				fileItem.error = err.message || '上传失败';
				uploadFiles = [...uploadFiles];
			}
		}

		confirmDialogData = null;
	}

	function handleCancelReplace() {
		showConfirmDialog = false;
		const { fileItem } = confirmDialogData;

		fileItem.status = 'error';
		fileItem.error = '用户取消了替换操作';
		uploadFiles = [...uploadFiles];

		uploadResults.push({
			filename: fileItem.file.name,
			status: 'error',
			message: '用户取消了替换操作'
		});

		confirmDialogData = null;
	}

	async function performUploads() {
		// 传统上传模式
		for (const fileItem of uploadFiles) {
			if (fileItem.status !== 'pending') continue;

			fileItem.status = 'uploading';
			uploadFiles = [...uploadFiles];

			try {
				await uploadSingleFile(fileItem, false);

				fileItem.status = 'completed';
				fileItem.progress = 100;
				uploadFiles = [...uploadFiles];
			} catch (err) {
				// uploadSingleFile 已经处理了错误和确认逻辑
				if (err.message !== 'PENDING_CONFIRMATION') {
					console.error('Upload failed:', err);
				}
			}
		}

		// 如果所有文件都成功上传，重定向到仓库页面
		const allSuccess = uploadResults.every((result) => result.status === 'success');
		if (allSuccess && uploadResults.length > 0) {
			setTimeout(() => {
				goto(`${base}/${username}/${repositoryName}`);
			}, 2000);
		}
	}

	function getFileIcon(file) {
		const ext = file.name.split('.').pop()?.toLowerCase();
		if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(ext)) return '🖼️';
		if (['mp4', 'avi', 'mov', 'wmv'].includes(ext)) return '🎬';
		if (['mp3', 'wav', 'ogg', 'flac'].includes(ext)) return '🎵';
		if (['pdf'].includes(ext)) return '📄';
		if (['doc', 'docx'].includes(ext)) return '📝';
		if (['xls', 'xlsx'].includes(ext)) return '📊';
		if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return '📦';
		if (['py', 'js', 'html', 'css', 'json', 'xml'].includes(ext)) return '💻';
		return '📁';
	}

	function getStatusIcon(status) {
		switch (status) {
			case 'completed':
				return CheckCircle;
			case 'error':
				return AlertCircle;
			case 'uploading':
				return Upload;
			default:
				return File;
		}
	}

	function getStatusColor(status) {
		switch (status) {
			case 'completed':
				return 'text-green-500';
			case 'error':
				return 'text-red-500';
			case 'uploading':
				return 'text-blue-500';
			default:
				return 'text-gray-500';
		}
	}
</script>

<svelte:head>
	<title>上传文件 - {repositoryName} - GeoML-Hub</title>
</svelte:head>

{#if loading}
	<Loading message="加载仓库信息..." />
{:else if error}
	<div class="container mx-auto px-4 py-8">
		<div class="max-w-4xl mx-auto">
			<div
				class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center"
			>
				<AlertCircle class="w-12 h-12 text-red-500 mx-auto mb-4" />
				<h2 class="text-xl font-semibold text-red-800 dark:text-red-200 mb-2">加载失败</h2>
				<p class="text-red-600 dark:text-red-300">{error}</p>
				<button
					on:click={() => goto(`${base}/${username}/${repositoryName}`)}
					class="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
				>
					返回仓库
				</button>
			</div>
		</div>
	</div>
{:else if !isRepoOwner}
	<div class="container mx-auto px-4 py-8">
		<div class="max-w-4xl mx-auto">
			<div
				class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6 text-center"
			>
				<AlertCircle class="w-12 h-12 text-yellow-500 mx-auto mb-4" />
				<h2 class="text-xl font-semibold text-yellow-800 dark:text-yellow-200 mb-2">无权限</h2>
				<p class="text-yellow-600 dark:text-yellow-300">你没有权限上传文件到这个仓库</p>
				<button
					on:click={() => goto(`${base}/${username}/${repositoryName}`)}
					class="mt-4 px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors"
				>
					返回仓库
				</button>
			</div>
		</div>
	</div>
{:else}
	<div class="container mx-auto px-4 py-8">
		<div class="max-w-4xl mx-auto">
			<!-- 页面标题 -->
			<div class="mb-8">
				<nav class="text-sm breadcrumbs mb-4">
					<a href="{base}/" class="text-blue-600 dark:text-blue-400 hover:underline">首页</a>
					<span class="mx-2 text-gray-400">/</span>
					<a href="{base}/{username}" class="text-blue-600 dark:text-blue-400 hover:underline"
						>{username}</a
					>
					<span class="mx-2 text-gray-400">/</span>
					<a
						href="{base}/{username}/{repositoryName}"
						class="text-blue-600 dark:text-blue-400 hover:underline">{repositoryName}</a
					>
					<span class="mx-2 text-gray-400">/</span>
					<span class="text-gray-700 dark:text-gray-300">上传文件</span>
				</nav>

				<h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">📁 上传文件</h1>
				<p class="text-gray-600 dark:text-gray-400">
					向 <span class="font-medium">{repository?.full_name}</span> 仓库上传文件
				</p>
			</div>

			<!-- 上传区域 -->
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
				<h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
					<Upload class="w-5 h-5 mr-2" />
					选择文件
				</h2>

				<FileUpload
					on:filesSelected={handleFilesSelected}
					multiple={true}
					accept="*/*"
					maxSize={100}
				/>

				{#if uploadFiles.length > 0}
					<div class="mt-6">
						<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
							待上传文件 ({uploadFiles.length})
						</h3>

						<div class="space-y-3">
							{#each uploadFiles as fileItem (fileItem.id)}
								<div
									class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
								>
									<div class="flex items-center space-x-3 flex-1">
										<span class="text-2xl">{getFileIcon(fileItem.file)}</span>

										<div class="flex-1 min-w-0">
											<p class="text-sm font-medium text-gray-900 dark:text-white truncate">
												{fileItem.file.name}
											</p>
											<p class="text-sm text-gray-500 dark:text-gray-400">
												{(fileItem.file.size / 1024 / 1024).toFixed(2)} MB
											</p>

											{#if fileItem.status === 'uploading'}
												<div class="mt-2">
													<div class="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
														<div
															class="bg-blue-600 h-2 rounded-full transition-all duration-300"
															style="width: {fileItem.progress}%"
														/>
													</div>
													<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
														{fileItem.progress}%
													</p>
												</div>
											{/if}

											{#if fileItem.error}
												<p class="text-sm text-red-500 mt-1">{fileItem.error}</p>
											{/if}
										</div>

										<svelte:component
											this={getStatusIcon(fileItem.status)}
											class="w-5 h-5 {getStatusColor(fileItem.status)}"
										/>
									</div>

									{#if fileItem.status === 'pending'}
										<button
											on:click={() => removeFile(fileItem.id)}
											class="ml-3 p-1 text-gray-400 hover:text-red-500 transition-colors"
										>
											<X class="w-4 h-4" />
										</button>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</div>

			<!-- 上传按钮 -->
			{#if uploadFiles.length > 0}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
					<div class="flex justify-end space-x-4">
						<button
							on:click={() => (uploadFiles = [])}
							disabled={uploading}
							class="px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
						>
							清空列表
						</button>

						<button
							on:click={startUpload}
							disabled={uploadFiles.length === 0 || uploading}
							class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
						>
							{#if uploading}
								<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
								<span>上传中...</span>
							{:else}
								<Upload class="w-4 h-4" />
								<span>开始上传</span>
							{/if}
						</button>
					</div>
				</div>
			{/if}

			<!-- 上传结果 -->
			{#if uploadResults.length > 0}
				<div class="mt-6 bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
					<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">上传结果</h3>

					<div class="space-y-2">
						{#each uploadResults as result}
							<div
								class="flex items-center justify-between p-3 rounded-lg {result.status === 'success'
									? 'bg-green-50 dark:bg-green-900/20'
									: 'bg-red-50 dark:bg-red-900/20'}"
							>
								<div class="flex items-center space-x-3">
									{#if result.status === 'success'}
										<CheckCircle class="w-5 h-5 text-green-500" />
									{:else}
										<AlertCircle class="w-5 h-5 text-red-500" />
									{/if}
									<div class="flex flex-col">
										<span
											class="font-medium {result.status === 'success'
												? 'text-green-800 dark:text-green-200'
												: 'text-red-800 dark:text-red-200'}"
										>
											{result.finalFilename || result.filename}
										</span>
										{#if result.finalFilename && result.finalFilename !== result.filename}
											<span
												class="text-xs {result.status === 'success'
													? 'text-green-600 dark:text-green-300'
													: 'text-red-600 dark:text-red-300'}"
											>
												原文件名: {result.filename}
											</span>
										{/if}
									</div>
								</div>
								<span
									class="text-sm {result.status === 'success'
										? 'text-green-600 dark:text-green-300'
										: 'text-red-600 dark:text-red-300'}"
								>
									{result.message}
								</span>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	</div>
{/if}

<!-- 确认替换对话框 -->
{#if showConfirmDialog && confirmDialogData}
	<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
		<div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
			<div class="flex items-center mb-4">
				<AlertCircle class="w-6 h-6 text-orange-500 mr-3" />
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white">确认替换文件</h3>
			</div>

			<div class="mb-6">
				<p class="text-gray-600 dark:text-gray-300 mb-3">
					{confirmDialogData.conflictData.message}
				</p>

				<div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
					<p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">现有文件：</p>
					<ul class="list-disc list-inside text-sm text-gray-600 dark:text-gray-400 mb-3">
						{#each confirmDialogData.conflictData.existing_files as filename}
							<li>{filename}</li>
						{/each}
					</ul>

					<p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">新文件：</p>
					<p class="text-sm text-gray-600 dark:text-gray-400">
						{confirmDialogData.conflictData.uploaded_file}
					</p>
				</div>
			</div>

			<div class="flex justify-end space-x-3">
				<button
					on:click={handleCancelReplace}
					class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
				>
					取消
				</button>
				<button
					on:click={handleConfirmReplace}
					class="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors"
				>
					确认替换
				</button>
			</div>
		</div>
	</div>
{/if}
