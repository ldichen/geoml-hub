<script>
	import { createEventDispatcher } from 'svelte';
	import { api } from '$lib/utils/api.js';
	import DropZone from '$lib/components/common/DropZone.svelte';
	import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte';

	export let repositoryId;

	const dispatch = createEventDispatcher();

	let selectedFile = null;
	let uploading = false;
	let uploadProgress = 0;
	let error = null;
	let isDragOver = false;

	// 处理文件选择
	function handleFileSelect(event) {
		const files = event.detail?.files || event.target.files;
		if (files && files.length > 0) {
			const file = files[0];
			
			// 验证文件类型
			const allowedTypes = ['.tar', '.tar.gz', '.tgz'];
			const isValidType = allowedTypes.some(type => file.name.toLowerCase().endsWith(type));
			if (!isValidType) {
				error = '只支持 .tar, .tar.gz, .tgz 格式的镜像文件';
				return;
			}

			// 验证文件大小 (5GB)
			const maxSize = 5 * 1024 * 1024 * 1024;
			if (file.size > maxSize) {
				error = '文件过大，最大支持5GB';
				return;
			}

			selectedFile = file;
			error = null;
		}
	}

	// 拖拽处理函数
	function handleDragEnter(e) {
		e.preventDefault();
		e.stopPropagation();
		isDragOver = true;
	}

	function handleDragLeave(e) {
		e.preventDefault();
		e.stopPropagation();
		const rect = e.currentTarget.getBoundingClientRect();
		const x = e.clientX;
		const y = e.clientY;
		
		if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
			isDragOver = false;
		}
	}

	function handleDragOver(e) {
		e.preventDefault();
		e.stopPropagation();
	}

	function handleDrop(e) {
		e.preventDefault();
		e.stopPropagation();
		isDragOver = false;
		
		const files = Array.from(e.dataTransfer.files);
		if (files.length > 0) {
			handleFileSelect({ target: { files } });
		}
	}

	// 上传镜像
	async function handleSubmit() {
		if (!selectedFile) {
			error = '请选择要上传的Docker镜像文件';
			return;
		}

		try {
			error = null;
			uploading = true;
			uploadProgress = 0;

			// 构建 FormData
			const uploadFormData = new FormData();
			uploadFormData.append('image_file', selectedFile);

			// 上传镜像，带进度回调
			const response = await api.uploadImage(repositoryId, uploadFormData, (progress) => {
				uploadProgress = progress;
			});
			
			if (response.success) {
				uploadProgress = 100;
				dispatch('uploaded', {
					image: response.data
				});
			} else {
				throw new Error(response.error || '上传失败');
			}

		} catch (err) {
			console.error('上传镜像失败:', err);
			error = err.message;
		} finally {
			uploading = false;
			uploadProgress = 0;
		}
	}

	// 关闭模态框
	function handleClose() {
		if (!uploading) {
			dispatch('close');
		}
	}

	// 清除文件选择
	function clearFile() {
		selectedFile = null;
		error = null;
	}

	// 格式化文件大小
	function formatFileSize(bytes) {
		if (bytes === 0) return '0 Bytes';
		const k = 1024;
		const sizes = ['Bytes', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
	}
</script>

<!-- 模态框背景 -->
<div class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50" on:click={handleClose}>
	<!-- 模态框内容 -->
	<div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden border border-gray-200 dark:border-gray-700" on:click|stopPropagation>
		<!-- 头部 -->
		<div class="relative bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700 px-6 py-4 border-b border-gray-200 dark:border-gray-600">
			<div class="flex items-center space-x-3">
				<div class="flex items-center justify-center w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-xl">
					<svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
					</svg>
				</div>
				<div>
					<h3 class="text-xl font-bold text-gray-900 dark:text-white">
						上传Docker镜像
					</h3>
					<p class="text-sm text-gray-600 dark:text-gray-300 mt-1">
						直接拖拽tar包即可完成镜像上传
					</p>
				</div>
			</div>
			<button
				class="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-all duration-200"
				on:click={handleClose}
				disabled={uploading}
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
				</svg>
			</button>
		</div>

		<!-- 表单内容 -->
		<form on:submit|preventDefault={handleSubmit}>
			<div class="overflow-y-auto max-h-[calc(90vh-120px)]">
				<div class="p-6 space-y-6">
					<!-- 文件上传区域 -->
					<div class="bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-gray-800 dark:to-gray-700 rounded-xl p-6 border border-indigo-200 dark:border-gray-600">
						<h4 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Docker镜像文件</h4>
						
						{#if !selectedFile}
							<!-- 拖拽上传区域 -->
							<div 
								class="border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 cursor-pointer {isDragOver ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20' : error ? 'border-red-500' : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'}"
								on:click={() => {if (!uploading) document.getElementById('fileInput')?.click()}}
								on:dragenter={handleDragEnter}
								on:dragleave={handleDragLeave}
								on:dragover={handleDragOver}
								on:drop={handleDrop}
								role="button"
								tabindex="0"
								on:keydown={(e) => {if (e.key === 'Enter' || e.key === ' ') document.getElementById('fileInput')?.click()}}
							>
								<input
									id="fileInput"
									type="file"
									accept=".tar,.tar.gz,.tgz"
									on:change={handleFileSelect}
									class="hidden"
									disabled={uploading}
								/>
								<svg class="mx-auto h-16 w-16 text-gray-400 dark:text-gray-500 mb-4" stroke="currentColor" fill="none" viewBox="0 0 48 48">
									<path d="M24 8v24m8-12l-8-8-8 8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
								</svg>
								<div class="space-y-2">
									<p class="text-lg font-medium text-gray-900 dark:text-white">
										{isDragOver ? '释放文件到此处' : '点击选择或拖拽Docker镜像tar包'}
									</p>
									<p class="text-sm text-gray-600 dark:text-gray-400">
										支持 .tar, .tar.gz, .tgz 格式，最大5GB
									</p>
									<p class="text-xs text-gray-500 dark:text-gray-400">
										镜像将自动识别名称和标签
									</p>
								</div>
							</div>
						{:else}
							<!-- 已选择文件显示 -->
							<div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
								<div class="flex items-center justify-between">
									<div class="flex items-center">
										<div class="flex-shrink-0 w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mr-3">
											<svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
											</svg>
										</div>
										<div>
											<p class="text-sm font-medium text-gray-900 dark:text-white">{selectedFile.name}</p>
											<p class="text-xs text-gray-500 dark:text-gray-400">{formatFileSize(selectedFile.size)}</p>
										</div>
									</div>
									<button
										type="button"
										class="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 transition-colors p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
										on:click={clearFile}
										disabled={uploading}
									>
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
										</svg>
									</button>
								</div>
							</div>
						{/if}
					</div>

					<!-- 错误信息 -->
					{#if error}
						<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-xl p-4">
							<div class="flex items-start space-x-3">
								<svg class="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.268 15.5c-.77.833.192 2.5 1.732 2.5z"></path>
								</svg>
								<p class="text-sm text-red-800 dark:text-red-200">{error}</p>
							</div>
						</div>
					{/if}

					<!-- 上传进度 -->
					{#if uploading}
						<div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-xl p-4">
							<div class="flex items-center justify-between text-sm text-blue-800 dark:text-blue-200 mb-3">
								<span class="font-medium">正在上传镜像到Harbor...</span>
								<div class="flex items-center space-x-2">
									<div class="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
									<span>{uploadProgress}%</span>
								</div>
							</div>
							<div class="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2">
								<div 
									class="bg-blue-500 dark:bg-blue-400 h-2 rounded-full transition-all duration-300" 
									style="width: {uploadProgress}%"
								></div>
							</div>
							<p class="text-xs text-blue-600 dark:text-blue-300 mt-2">
								镜像上传可能需要几分钟时间，请耐心等待
							</p>
						</div>
					{/if}
				</div>
			</div>

			<!-- 底部按钮 -->
			<div class="sticky bottom-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 px-6 py-4">
				<div class="flex items-center justify-between">
					<div class="text-sm text-gray-500 dark:text-gray-400">
						{#if uploading}
							<div class="flex items-center space-x-2">
								<div class="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
								<span>正在上传镜像...</span>
							</div>
						{:else}
							选择tar包后点击上传
						{/if}
					</div>
					<div class="flex space-x-3">
						<button
							type="button"
							class="px-6 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-600 hover:bg-gray-200 dark:hover:bg-gray-500 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
							on:click={handleClose}
							disabled={uploading}
						>
							取消
						</button>
						<button
							type="submit"
							class="px-6 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] flex items-center space-x-2"
							disabled={uploading || !selectedFile}
						>
							{#if uploading}
								<div class="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
								<span>上传中...</span>
							{:else}
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
								</svg>
								<span>上传镜像</span>
							{/if}
						</button>
					</div>
				</div>
			</div>
		</form>
	</div>
</div>

