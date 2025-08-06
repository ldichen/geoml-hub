<script>
	import { createEventDispatcher } from 'svelte';
	import { api } from '$lib/utils/api.js';
	import DropZone from '$lib/components/common/DropZone.svelte';
	import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte';

	export let repositoryId;

	const dispatch = createEventDispatcher();

	let formData = {
		name: '',
		tag: 'latest',
		description: ''
	};

	let selectedFile = null;
	let uploading = false;
	let uploadProgress = 0;
	let error = null;

	// 验证表单
	function validateForm() {
		if (!formData.name.trim()) {
			throw new Error('请输入镜像名称');
		}
		
		if (!/^[a-zA-Z0-9][a-zA-Z0-9._-]*$/.test(formData.name)) {
			throw new Error('镜像名称只能包含字母、数字、点、连字符和下划线，且必须以字母或数字开头');
		}
		
		if (!formData.tag.trim()) {
			throw new Error('请输入镜像标签');
		}
		
		if (!/^[a-zA-Z0-9][a-zA-Z0-9._-]*$/.test(formData.tag)) {
			throw new Error('镜像标签格式不正确');
		}
		
		if (!selectedFile) {
			throw new Error('请选择要上传的Docker镜像文件');
		}

		// 验证文件类型
		const allowedTypes = ['.tar', '.tar.gz', '.tgz'];
		const isValidType = allowedTypes.some(type => selectedFile.name.toLowerCase().endsWith(type));
		if (!isValidType) {
			throw new Error('只支持 .tar, .tar.gz, .tgz 格式的镜像文件');
		}

		// 验证文件大小 (5GB)
		const maxSize = 5 * 1024 * 1024 * 1024;
		if (selectedFile.size > maxSize) {
			throw new Error('文件过大，最大支持5GB');
		}
	}

	// 处理文件选择
	function handleFileSelect(event) {
		const files = event.detail.files || event.target.files;
		if (files && files.length > 0) {
			selectedFile = files[0];
			error = null;
			
			// 自动从文件名提取镜像名称
			if (!formData.name) {
				let filename = selectedFile.name;
				// 移除扩展名
				filename = filename.replace(/\.(tar|tar\.gz|tgz)$/i, '');
				// 清理文件名，使其符合镜像名称规范
				filename = filename.toLowerCase().replace(/[^a-z0-9._-]/g, '-');
				if (filename) {
					formData.name = filename;
				}
			}
		}
	}

	// 上传镜像
	async function handleSubmit() {
		try {
			error = null;
			validateForm();
			
			uploading = true;
			uploadProgress = 0;

			// 构建 FormData
			const uploadFormData = new FormData();
			uploadFormData.append('image_file', selectedFile);
			uploadFormData.append('name', formData.name.trim());
			uploadFormData.append('tag', formData.tag.trim());
			uploadFormData.append('description', formData.description.trim());

			// 上传镜像
			const response = await api.uploadImage(repositoryId, uploadFormData);
			
			if (response.success) {
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
<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" on:click={handleClose}>
	<!-- 模态框内容 -->
	<div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-screen overflow-y-auto" on:click|stopPropagation>
		<!-- 头部 -->
		<div class="flex items-center justify-between p-6 border-b border-gray-200">
			<h2 class="text-xl font-semibold text-gray-900">上传Docker镜像</h2>
			<button
				class="text-gray-400 hover:text-gray-600 transition-colors"
				on:click={handleClose}
				disabled={uploading}
			>
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
				</svg>
			</button>
		</div>

		<!-- 表单内容 -->
		<form on:submit|preventDefault={handleSubmit} class="p-6">
			<!-- 文件上传区域 -->
			<div class="mb-6">
				<label class="block text-sm font-medium text-gray-700 mb-2">
					Docker镜像文件
					<span class="text-red-500">*</span>
				</label>
				
				{#if !selectedFile}
					<DropZone
						accept=".tar,.tar.gz,.tgz"
						maxSize={5 * 1024 * 1024 * 1024}
						on:files={handleFileSelect}
					>
						<div class="text-center py-8">
							<svg class="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
							</svg>
							<p class="text-sm text-gray-600 mb-2">
								拖拽Docker镜像文件到此处，或点击选择文件
							</p>
							<p class="text-xs text-gray-500">
								支持 .tar, .tar.gz, .tgz 格式，最大5GB
							</p>
						</div>
					</DropZone>
				{:else}
					<div class="border border-gray-300 rounded-lg p-4 bg-gray-50">
						<div class="flex items-center justify-between">
							<div class="flex items-center">
								<svg class="w-8 h-8 text-blue-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
								</svg>
								<div>
									<p class="text-sm font-medium text-gray-900">{selectedFile.name}</p>
									<p class="text-xs text-gray-500">{formatFileSize(selectedFile.size)}</p>
								</div>
							</div>
							<button
								type="button"
								class="text-red-500 hover:text-red-700 transition-colors"
								on:click={clearFile}
								disabled={uploading}
							>
								<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
								</svg>
							</button>
						</div>
					</div>
				{/if}
			</div>

			<!-- 镜像信息 -->
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
				<div>
					<label for="imageName" class="block text-sm font-medium text-gray-700 mb-2">
						镜像名称
						<span class="text-red-500">*</span>
					</label>
					<input
						id="imageName"
						type="text"
						bind:value={formData.name}
						class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
						placeholder="例如: my-model"
						disabled={uploading}
						required
					/>
					<p class="mt-1 text-xs text-gray-500">
						只能包含字母、数字、点、连字符和下划线
					</p>
				</div>

				<div>
					<label for="imageTag" class="block text-sm font-medium text-gray-700 mb-2">
						镜像标签
						<span class="text-red-500">*</span>
					</label>
					<input
						id="imageTag"
						type="text"
						bind:value={formData.tag}
						class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
						placeholder="例如: latest, v1.0"
						disabled={uploading}
						required
					/>
				</div>
			</div>

			<!-- 描述 -->
			<div class="mb-6">
				<label for="description" class="block text-sm font-medium text-gray-700 mb-2">
					描述信息
				</label>
				<textarea
					id="description"
					bind:value={formData.description}
					rows="3"
					class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
					placeholder="描述这个镜像的用途和特性..."
					disabled={uploading}
				></textarea>
			</div>

			<!-- 错误信息 -->
			{#if error}
				<div class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
					<p class="text-sm text-red-600">{error}</p>
				</div>
			{/if}

			<!-- 上传进度 -->
			{#if uploading}
				<div class="mb-4">
					<div class="flex items-center justify-between text-sm text-gray-600 mb-2">
						<span>正在上传镜像...</span>
					</div>
					<div class="w-full bg-gray-200 rounded-full h-2">
						<div class="bg-blue-500 h-2 rounded-full transition-all duration-300 animate-pulse"></div>
					</div>
					<p class="text-xs text-gray-500 mt-2">
						镜像正在上传到Harbor仓库，这可能需要几分钟时间
					</p>
				</div>
			{/if}

			<!-- 按钮区域 -->
			<div class="flex justify-end space-x-3 pt-4 border-t border-gray-200">
				<button
					type="button"
					class="btn btn-outline"
					on:click={handleClose}
					disabled={uploading}
				>
					取消
				</button>
				<button
					type="submit"
					class="btn btn-primary"
					disabled={uploading || !selectedFile}
				>
					{#if uploading}
						<LoadingSpinner size="sm" />
						<span class="ml-2">上传中...</span>
					{:else}
						上传镜像
					{/if}
				</button>
			</div>
		</form>
	</div>
</div>

<style>
	.btn {
		@apply px-4 py-2 rounded-lg font-medium transition-colors duration-200;
	}
	
	.btn:disabled {
		@apply opacity-50 cursor-not-allowed;
	}

	.btn-primary {
		@apply bg-blue-600 text-white flex items-center;
	}
	
	.btn-primary:hover {
		@apply bg-blue-700;
	}

	.btn-outline {
		@apply border border-gray-300 text-gray-700;
	}
	
	.btn-outline:hover {
		@apply bg-gray-50;
	}
</style>