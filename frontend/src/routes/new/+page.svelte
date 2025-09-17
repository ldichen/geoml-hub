<script>
	import { goto } from '$app/navigation';
	import { _ } from 'svelte-i18n';
	import { LICENSE_OPTIONS } from '$lib/utils/constants';
	import { api } from '$lib/utils/api';
	import { user as currentUser } from '$lib/stores/auth.js';
	import Loading from '$lib/components/Loading.svelte';
	import ClassificationSelector from '$lib/components/ClassificationSelector.svelte';
	import { ErrorHandler, getUserFriendlyMessage } from '$lib/utils/error-handler.js';

	let loading = false;
	let error = null;
	let classifications = [];
	let loadingClassifications = false;

	// Creation mode selection
	let creationMode = 'config'; // 'config' or 'readme'

	// README file upload
	let readmeFile = null;
	let fileInput = null;

	// v2.0 Repository creation form data
	let formData = {
		name: '',
		description: '',
		repo_type: 'model',
		visibility: 'public',
		license: '',
		tags: [],
		base_model: '',
		classification_id: null,
		readme_content: ''
	};

	// Validation errors
	let errors = {};

	// Tag input
	let tagInput = '';

	function validateForm() {
		errors = {};

		if (!formData.name.trim()) {
			errors.name = '仓库名称不能为空';
		} else if (!/^[a-zA-Z0-9._-]+$/.test(formData.name)) {
			errors.name = '仓库名称只能包含字母、数字、点号、下划线和连字符';
		}

		if (formData.description && formData.description.length > 500) {
			errors.description = '描述不能超过500个字符';
		}

		// README upload mode validation
		if (creationMode === 'readme' && !readmeFile) {
			errors.readme = '请选择README.md文件';
		}

		return Object.keys(errors).length === 0;
	}

	function handleFileSelect(event) {
		const files = event.target.files;
		if (files && files.length > 0) {
			const file = files[0];
			if (file.name.toLowerCase().endsWith('.md')) {
				readmeFile = file;
				errors.readme = null;
			} else {
				errors.readme = '请选择.md格式的文件';
				readmeFile = null;
			}
		}
	}

	function removeFile() {
		readmeFile = null;
		if (fileInput) {
			fileInput.value = '';
		}
	}

	// 拖拽上传相关状态
	let isDragOver = false;

	// 拖拽处理函数
	function handleDragEnter(event) {
		event.preventDefault();
		isDragOver = true;
	}

	function handleDragLeave(event) {
		event.preventDefault();
		isDragOver = false;
	}

	function handleDragOver(event) {
		event.preventDefault();
	}

	function handleDrop(event) {
		event.preventDefault();
		isDragOver = false;

		const files = event.dataTransfer?.files;
		if (files && files.length > 0) {
			const file = files[0];
			if (file.name.toLowerCase().endsWith('.md')) {
				readmeFile = file;
				errors.readme = null;
			} else {
				errors.readme = '请选择.md格式的文件';
				readmeFile = null;
			}
		}
	}

	function addTag() {
		if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
			formData.tags = [...formData.tags, tagInput.trim()];
			tagInput = '';
		}
	}

	function removeTag(tag) {
		formData.tags = formData.tags.filter((t) => t !== tag);
	}

	function handleTagKeydown(event) {
		if (event.key === 'Enter') {
			event.preventDefault();
			addTag();
		}
	}

	async function loadClassifications() {
		try {
			loadingClassifications = true;
			const response = await api.getClassificationTree();
			console.log('response:');
			console.log(response);
			classifications = response;
		} catch (err) {
			console.error('Failed to load classifications:', err);
		} finally {
			loadingClassifications = false;
		}
	}

	function handleClassificationSelect(event) {
		const selectedClassification = event.detail;
		formData.classification_id = selectedClassification.id;
	}

	// Load classifications on component mount
	import { onMount } from 'svelte';

	onMount(() => {
		loadClassifications();
	});

	async function handleSubmit() {
		if (!validateForm()) {
			return;
		}

		loading = true;
		error = null;

		// 验证用户登录状态
		if (!$currentUser) {
			error = '请先登录';
			loading = false;
			return;
		}

		try {
			let response;

			if (creationMode === 'readme' && readmeFile) {
				// Create repository with README file
				const formDataObj = new FormData();

				// Add basic repository data
				const repoData = {
					name: formData.name.trim(),
					description: formData.description.trim() || null,
					repo_type: formData.repo_type,
					visibility: formData.visibility
				};

				formDataObj.append('repo_data', JSON.stringify(repoData));
				formDataObj.append('readme_file', readmeFile);

				response = await api.createRepositoryWithReadme(formDataObj);
			} else {
				// Create repository with config data
				const submitData = {
					name: formData.name.trim(),
					description: formData.description.trim() || null,
					repo_type: formData.repo_type,
					visibility: formData.visibility,
					license: formData.license || null,
					tags: formData.tags,
					base_model: formData.base_model || null,
					classification_id: formData.classification_id || null,
					readme_content: formData.readme_content || null
				};

				response = await api.createRepository(submitData);
			}

			// Success - redirect to repository page
			goto(`/${$currentUser.username}/${response.name}`);
		} catch (err) {
			// 使用统一错误处理器
			const apiError = ErrorHandler.handleApiError(err, {
				showNotification: false,
				logError: true
			});

			// 处理表单验证错误
			const validationErrors = ErrorHandler.handleValidationError(apiError);
			if (Object.keys(validationErrors).length > 0) {
				errors = { ...errors, ...validationErrors };
			}

			// 显示用户友好的错误消息
			error = getUserFriendlyMessage(apiError);

			console.error('Failed to create repository:', {
				message: apiError.message,
				code: apiError.code,
				status: apiError.status,
				context: apiError.context
			});
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>创建新仓库 - GeoML Hub</title>
</svelte:head>

<div
	class="min-h-[70vh] bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900"
>
	<div class="max-w-3xl mx-auto pt-4 px-4 pb-4">
		<div class="text-center mb-4">
			<!-- Repository Icon -->
			<div
				class="mx-auto w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center mb-2 shadow-xl border border-white/20"
			>
				<svg class="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 16 16">
					<path
						d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"
					/>
				</svg>
			</div>

			<h1 class="text-3xl font-bold text-slate-900 dark:text-white mb-0.5 tracking-tight">
				创建新仓库
			</h1>
			<p class="text-slate-600 dark:text-slate-400 text-base">
				支持模型、数据集和相关资源的版本控制与协作开发
			</p>
		</div>

		<div
			class="bg-white/90 dark:bg-slate-800/95 backdrop-blur-2xl rounded-3xl shadow-2xl border border-white/20 dark:border-slate-700/50"
		>
			<form on:submit|preventDefault={handleSubmit} class="p-6 space-y-3">
				<!-- Repository Name -->
				<div
					class="bg-slate-50/60 dark:bg-slate-700/40 rounded-2xl p-3 border border-slate-200/60 dark:border-slate-600/50"
				>
					<div class="flex items-center space-x-24 ml-2">
						<label class=" block text-sm font-semibold text-slate-800 dark:text-slate-200 mb-1">
							所有者
						</label>
						<label class="block text-sm font-semibold text-slate-800 dark:text-slate-200 mb-1">
							仓库名
						</label>
					</div>
					<div class="flex items-center space-x-2">
						<!-- Owner (current user) -->
						<div
							class="flex items-center bg-white dark:bg-slate-800 rounded-xl px-4 py-2 border border-slate-200/70 dark:border-slate-600 shadow-sm"
						>
							<span class="text-m font-medium text-slate-700 dark:text-slate-300"
								>{$currentUser?.username || 'loading...'}</span
							>
						</div>

						<span class="text-slate-800 text-lg font-medium">/</span>

						<!-- Repository Name Input -->
						<div class="flex-1">
							<input
								id="repo-name-input"
								type="text"
								bind:value={formData.name}
								class="w-full px-4 py-2 border border-slate-200/70 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/70 focus:border-blue-400 transition-all duration-200 {errors.name
									? 'border-red-400 focus:ring-red-400/70'
									: ''}"
								placeholder="my-awesome-model"
								required
							/>
						</div>
					</div>
					{#if errors.name}
						<p class="text-red-500 text-sm mt-2 ml-1 font-medium">{errors.name}</p>
					{/if}
				</div>

				<!-- Description -->
				<div>
					<label
						for="description-input"
						class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1"
					>
						<span class="flex items-center">
							描述
							<span class="text-xs text-slate-500 ml-1">(可选)</span>
						</span>
					</label>
					<textarea
						id="description-input"
						bind:value={formData.description}
						rows="2"
						class="w-full px-4 py-3 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 resize-none {errors.description
							? 'border-red-500 focus:ring-red-500'
							: ''}"
						placeholder="简要描述您的模型或数据集..."
					/>
					{#if errors.description}
						<p class="text-red-500 text-sm mt-1">{errors.description}</p>
					{/if}
				</div>
				<!-- Creation Mode Selection -->
				<div class="flex items-center justify-center">
					<div
						class="flex bg-gradient-to-r from-slate-100/80 mb-2 to-slate-50/60 dark:from-slate-800/70 dark:to-slate-700/60 rounded-2xl border border-slate-200/60 dark:border-slate-600/50 shadow-inner"
					>
						<input
							type="radio"
							id="config-mode"
							bind:group={creationMode}
							value="config"
							class="sr-only"
						/>
						<label
							for="config-mode"
							class="flex items-center px-3 py-2 rounded-xl cursor-pointer transition-all duration-300 text-sm font-semibold min-w-[140px] justify-center {creationMode ===
							'config'
								? 'bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-xl border border-white/60 dark:border-slate-600/60 transform scale-[1.02]'
								: 'text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-white/60 dark:hover:bg-slate-700/60'}"
						>
							<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4a2 2 0 014 0m2-4a2 2 0 110 4m0-4a2 2 0 110 4m0 4v2m0-6V4"
								/>
							</svg>
							手动配置信息
						</label>

						<input
							type="radio"
							id="readme-mode"
							bind:group={creationMode}
							value="readme"
							class="sr-only"
						/>
						<label
							for="readme-mode"
							class="flex items-center px-3 py-2 rounded-xl cursor-pointer transition-all duration-300 text-sm font-semibold min-w-[140px] justify-center {creationMode ===
							'readme'
								? 'bg-white dark:bg-slate-700 text-green-600 dark:text-green-400 shadow-xl border border-white/60 dark:border-slate-600/60 transform scale-[1.02]'
								: 'text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-white/60 dark:hover:bg-slate-700/60'}"
						>
							<svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
								/>
							</svg>
							上传 README
						</label>
					</div>
				</div>

				<!-- README File Upload (only show in readme mode) -->
				{#if creationMode === 'readme'}
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							README.md 文件 <span class="text-red-500">*</span>
						</label>

						{#if !readmeFile}
							<div
								class="border-2 border-dashed rounded-lg p-6 text-center transition-all duration-200 cursor-pointer {isDragOver
									? 'border-blue-500 dark:border-blue-400 bg-blue-50/50 dark:bg-blue-950/30'
									: 'border-gray-300 dark:border-gray-600 hover:border-blue-500 dark:hover:border-blue-400'}"
								on:dragenter={handleDragEnter}
								on:dragleave={handleDragLeave}
								on:dragover={handleDragOver}
								on:drop={handleDrop}
								on:click={() => fileInput?.click()}
								role="button"
								tabindex="0"
								on:keydown={(e) => {
									if (e.key === 'Enter' || e.key === ' ') {
										e.preventDefault();
										fileInput?.click();
									}
								}}
							>
								<input
									type="file"
									accept=".md"
									on:change={handleFileSelect}
									bind:this={fileInput}
									class="hidden"
								/>

								{#if isDragOver}
									<!-- 拖拽状态图标 -->
									<svg
										class="mx-auto h-12 w-12 text-blue-500 dark:text-blue-400"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
										/>
									</svg>
									<div class="mt-4">
										<p class="text-blue-600 dark:text-blue-400 font-medium">
											松开鼠标上传文件
										</p>
									</div>
								{:else}
									<!-- 默认状态图标 -->
									<svg
										class="mx-auto h-12 w-12 text-slate-400"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
										/>
									</svg>
									<div class="mt-4">
										<button
											type="button"
											class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-blue-600 bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-400 dark:hover:bg-blue-800 transition-colors"
											on:click|stopPropagation={() => fileInput?.click()}
										>
											选择 README.md 文件
										</button>
									</div>
									<p class="mt-2 text-xs text-gray-500 dark:text-gray-400">
										支持 .md 格式，可点击选择或拖拽文件到此处上传
									</p>
									<p class="mt-1 text-xs text-gray-400 dark:text-gray-500">
										系统将自动解析 YAML 前言获取配置信息
									</p>
								{/if}
							</div>
						{:else}
							<div
								class="border border-gray-300 dark:border-gray-600 rounded-lg p-4 bg-gray-50 dark:bg-gray-700"
							>
								<div class="flex items-center justify-between">
									<div class="flex items-center">
										<svg
											class="h-8 w-8 text-blue-500"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
											/>
										</svg>
										<div class="ml-3">
											<div class="text-sm font-medium text-gray-900 dark:text-white">
												{readmeFile.name}
											</div>
											<div class="text-xs text-gray-500 dark:text-gray-400">
												{Math.round(readmeFile.size / 1024)} KB
											</div>
										</div>
									</div>
									<button
										type="button"
										class="text-red-500 hover:text-red-700 dark:hover:text-red-400"
										on:click={removeFile}
									>
										<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M6 18L18 6M6 6l12 12"
											/>
										</svg>
									</button>
								</div>
							</div>
						{/if}

						{#if errors.readme}
							<p class="text-red-500 text-sm mt-1">{errors.readme}</p>
						{/if}
					</div>
				{/if}
				<!-- License, Base Model and Tags (only show in config mode) -->
				{#if creationMode === 'config'}
					<div class="grid grid-cols-1 md:grid-cols-8 gap-4">
						<!-- License -->
						<div class="md:col-span-2">
							<label
								for="license-select"
								class="block text-sm ml-2 font-semibold text-slate-700 dark:text-slate-300 mb-1"
							>
								许可证 (可选)
							</label>
							<select
								id="license-select"
								bind:value={formData.license}
								class="w-full px-4 py-2 border border-slate-200/70 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/70 focus:border-blue-400 transition-all duration-200"
							>
								<option value="">选择许可证...</option>
								<option value="mit">MIT</option>
								<option value="apache-2.0">Apache 2.0</option>
								<option value="gpl-3.0">GPL 3.0</option>
								<option value="bsd-3-clause">BSD 3-Clause</option>
								<option value="lgpl-2.1">LGPL 2.1</option>
								<option value="mpl-2.0">MPL 2.0</option>
								<option value="cc0-1.0">CC0 1.0</option>
								<option value="cc-by-4.0">CC BY 4.0</option>
								<option value="unlicense">Unlicense</option>
								<option value="other">其他</option>
							</select>
						</div>

						<!-- Base Model -->
						<div class="md:col-span-3">
							<label
								for="base-model-input"
								class="block text-sm ml-2 font-semibold text-slate-700 dark:text-slate-300 mb-1"
							>
								基础模型 (可选)
							</label>
							<input
								id="base-model-input"
								type="text"
								bind:value={formData.base_model}
								class="w-full px-4 py-2 border border-slate-200/70 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/70 focus:border-blue-400 transition-all duration-200"
								placeholder="例如: bert-base-uncased"
							/>
						</div>

						<!-- Tags -->
						<div class="md:col-span-3">
							<label
								for="tags-input"
								class="block text-sm ml-2 font-semibold text-slate-700 dark:text-slate-300 mb-1"
							>
								标签 (可选)
							</label>
							<div class="relative">
								<input
									id="tags-input"
									type="text"
									bind:value={tagInput}
									on:keydown={handleTagKeydown}
									class="w-full px-4 py-2 border border-slate-200/70 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/70 focus:border-blue-400 transition-all duration-200"
									placeholder="输入标签按回车"
								/>
							</div>
							<!-- Tag display -->
							{#if formData.tags.length > 0}
								<div class="flex flex-wrap gap-1 mt-2">
									{#each formData.tags as tag}
										<span
											class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
										>
											{tag}
											<button
												type="button"
												class="ml-1 h-3 w-3 rounded-full hover:bg-blue-200 dark:hover:bg-blue-800 flex items-center justify-center"
												on:click={() => removeTag(tag)}
											>
												<svg class="h-2 w-2" fill="currentColor" viewBox="0 0 8 8">
													<path
														d="M1.41 0l-1.41 1.41.72.72 1.78 1.81-1.78 1.78-.72.69 1.41 1.44.72-.72 1.81-1.81 1.78 1.81.69.72 1.44-1.44-.72-.69-1.81-1.78 1.81-1.81.72-.72-1.44-1.41-.69.72-1.78 1.78-1.81-1.78-.72-.72z"
													/>
												</svg>
											</button>
										</span>
									{/each}
								</div>
							{/if}
						</div>
					</div>

					<!-- Classifications (only show in config mode) -->
					<div>
						<div class="flex items-center space-x-2 mb-1">
							<label class="text-sm font-semibold text-slate-700 dark:text-slate-300">
								分类 (可选)
							</label>
							{#if formData.classification_id !== null}
								<button
									type="button"
									class="inline-flex items-center px-2 py-1 text-xs font-medium text-slate-600 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-300 bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 rounded-lg transition-all duration-200"
									on:click={() => {
										formData.classification_id = null;
									}}
								>
									<svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M6 18L18 6M6 6l12 12"
										/>
									</svg>
									清除选择
								</button>
							{/if}
						</div>
						<ClassificationSelector
							{classifications}
							selectedClassificationId={formData.classification_id}
							loading={loadingClassifications}
							on:select={handleClassificationSelect}
						/>
					</div>
				{/if}

				<!-- Visibility -->
				<div>
					<div class="flex space-x-4">
						<div class="flex items-center">
							<input
								type="radio"
								id="public"
								bind:group={formData.visibility}
								value="public"
								class="h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-slate-300 dark:border-slate-600"
							/>
							<label for="public" class="ml-3 flex items-center">
								<div
									class="w-6 h-6 bg-emerald-100 dark:bg-emerald-900/50 rounded-lg flex items-center justify-center mr-2"
								>
									<svg
										class="w-3 h-3 text-emerald-600 dark:text-emerald-400"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
										/>
									</svg>
								</div>
								<span class="text-sm font-medium text-slate-700 dark:text-slate-300">公开仓库</span>
							</label>
						</div>
						<div class="flex items-center">
							<input
								type="radio"
								id="private"
								bind:group={formData.visibility}
								value="private"
								class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-slate-300 dark:border-slate-600"
							/>
							<label for="private" class="ml-3 flex items-center">
								<div
									class="w-6 h-6 bg-blue-100 dark:bg-blue-900/50 rounded-lg flex items-center justify-center mr-2"
								>
									<svg
										class="w-3 h-3 text-blue-600 dark:text-blue-400"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
										/>
									</svg>
								</div>
								<span class="text-sm font-medium text-slate-700 dark:text-slate-300">私有仓库</span>
							</label>
						</div>
					</div>
				</div>

				<!-- Error Display -->
				{#if error}
					<div
						class="bg-red-50/80 dark:bg-red-900/30 border border-red-200/70 dark:border-red-800/70 rounded-2xl p-4 backdrop-blur-sm"
					>
						<p class="text-red-700 dark:text-red-400 font-medium">{error}</p>
					</div>
				{/if}

				<!-- Submit Button -->
				<div
					class="flex flex-col sm:flex-row justify-center sm:justify-end space-y-3 sm:space-y-0 sm:space-x-4"
				>
					<button
						type="submit"
						class="w-full sm:w-auto px-5 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 disabled:from-slate-400 disabled:to-slate-500 text-white font-semibold rounded-2xl transition-all duration-200 flex items-center justify-center space-x-2 shadow-xl hover:shadow-2xl transform hover:scale-[1.02] disabled:transform-none disabled:shadow-lg"
						disabled={loading}
					>
						{#if loading}
							<span>创建中...</span>
						{:else}
							<span>创建仓库</span>
						{/if}
					</button>
					<button
						type="button"
						class="w-full sm:w-auto px-5 py-2 border border-slate-300/70 dark:border-slate-600 rounded-2xl text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all duration-200 font-semibold shadow-sm hover:shadow-md"
						on:click={() => goto('/')}
					>
						取消
					</button>
				</div>
			</form>
		</div>
	</div>
</div>
