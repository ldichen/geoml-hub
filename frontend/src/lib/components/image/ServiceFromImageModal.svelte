<script>
	import { createEventDispatcher } from 'svelte';
	import { api } from '$lib/utils/api.js';
	import LoadingSpinner from '$lib/components/common/LoadingSpinner.svelte';

	export let image;

	const dispatch = createEventDispatcher();

	let formData = {
		service_name: '',
		description: '',
		cpu_limit: '0.5',
		memory_limit: '512m',
		gradio_port: null,
		is_public: false,
		priority: 2
	};

	let creating = false;
	let error = null;

	// 资源配置预设
	const resourcePresets = {
		minimal: {
			label: '最小配置',
			cpu_limit: '0.3',
			memory_limit: '256m',
			description: '适合轻量级模型和演示'
		},
		recommended: {
			label: '推荐配置',
			cpu_limit: '0.5',
			memory_limit: '512m',
			description: '适合大多数模型应用'
		},
		high: {
			label: '高性能配置',
			cpu_limit: '1.0',
			memory_limit: '1024m',
			description: '适合复杂模型和高并发'
		},
		custom: {
			label: '自定义配置',
			cpu_limit: '',
			memory_limit: '',
			description: '手动设置资源限制'
		}
	};

	let selectedPreset = 'recommended';

	// 自动生成服务名称
	function generateServiceName() {
		if (!formData.service_name) {
			const timestamp = Date.now().toString().slice(-6);
			formData.service_name = `${image.name}-service-${timestamp}`;
		}
	}

	// 应用资源预设
	function applyPreset(preset) {
		selectedPreset = preset;
		if (preset !== 'custom') {
			formData.cpu_limit = resourcePresets[preset].cpu_limit;
			formData.memory_limit = resourcePresets[preset].memory_limit;
		}
	}

	// 验证表单
	function validateForm() {
		if (!formData.service_name.trim()) {
			throw new Error('请输入服务名称');
		}
		
		if (!/^[a-zA-Z0-9][a-zA-Z0-9-]*$/.test(formData.service_name)) {
			throw new Error('服务名称只能包含字母、数字和连字符，且必须以字母或数字开头');
		}
		
		if (!formData.cpu_limit.trim()) {
			throw new Error('请设置CPU限制');
		}
		
		if (!formData.memory_limit.trim()) {
			throw new Error('请设置内存限制');
		}

		// 验证CPU限制格式
		if (!/^\d+(\.\d+)?$/.test(formData.cpu_limit)) {
			throw new Error('CPU限制格式不正确，例如: 0.5, 1.0');
		}

		// 验证内存限制格式
		if (!/^\d+[Mm][Ii]?$/.test(formData.memory_limit)) {
			throw new Error('内存限制格式不正确，例如: 512Mi, 1Gi');
		}

		// 验证Gradio端口
		if (formData.gradio_port !== null) {
			const port = parseInt(formData.gradio_port);
			if (isNaN(port) || port < 1024 || port > 65535) {
				throw new Error('端口号必须在1024-65535之间');
			}
		}
	}

	// 创建服务
	async function handleSubmit() {
		try {
			error = null;
			validateForm();
			
			creating = true;

			// 构建 FormData
			const submitFormData = new FormData();
			Object.entries(formData).forEach(([key, value]) => {
				if (value !== null && value !== '') {
					submitFormData.append(key, value.toString());
				}
			});

			// 创建服务
			const response = await api.createServiceFromImage(image.id, submitFormData);
			
			if (response.success) {
				dispatch('created', {
					service: response.data,
					image: image
				});
			} else {
				throw new Error(response.error || '创建服务失败');
			}

		} catch (err) {
			console.error('创建服务失败:', err);
			error = err.message;
		} finally {
			creating = false;
		}
	}

	// 关闭模态框
	function handleClose() {
		if (!creating) {
			dispatch('close');
		}
	}

	// 初始化时生成服务名称
	generateServiceName();
</script>

<!-- 模态框背景 -->
<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" on:click={handleClose}>
	<!-- 模态框内容 -->
	<div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-screen overflow-y-auto" on:click|stopPropagation>
		<!-- 头部 -->
		<div class="flex items-center justify-between p-6 border-b border-gray-200">
			<div>
				<h2 class="text-xl font-semibold text-gray-900">创建模型服务</h2>
				<p class="text-sm text-gray-500 mt-1">
					基于镜像 <code class="bg-gray-100 px-2 py-1 rounded text-xs">{image.name}:{image.tag}</code>
				</p>
			</div>
			<button
				class="text-gray-400 hover:text-gray-600 transition-colors"
				on:click={handleClose}
				disabled={creating}
			>
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
				</svg>
			</button>
		</div>

		<!-- 表单内容 -->
		<form on:submit|preventDefault={handleSubmit} class="p-6">
			<!-- 服务基本信息 -->
			<div class="mb-6">
				<h3 class="text-lg font-medium text-gray-900 mb-4">基本信息</h3>
				
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div>
						<label for="serviceName" class="block text-sm font-medium text-gray-700 mb-2">
							服务名称
							<span class="text-red-500">*</span>
						</label>
						<input
							id="serviceName"
							type="text"
							bind:value={formData.service_name}
							class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
							placeholder="例如: my-model-service"
							disabled={creating}
							required
						/>
						<p class="mt-1 text-xs text-gray-500">
							只能包含字母、数字和连字符
						</p>
					</div>

					<div>
						<label for="priority" class="block text-sm font-medium text-gray-700 mb-2">
							启动优先级
						</label>
						<select
							id="priority"
							bind:value={formData.priority}
							class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
							disabled={creating}
						>
							<option value={0}>最高 (0)</option>
							<option value={1}>高 (1)</option>
							<option value={2}>普通 (2)</option>
							<option value={3}>低 (3)</option>
						</select>
					</div>
				</div>

				<div class="mt-4">
					<label for="description" class="block text-sm font-medium text-gray-700 mb-2">
						服务描述
					</label>
					<textarea
						id="description"
						bind:value={formData.description}
						rows="3"
						class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
						placeholder="描述这个服务的功能和用途..."
						disabled={creating}
					></textarea>
				</div>
			</div>

			<!-- 资源配置 -->
			<div class="mb-6">
				<h3 class="text-lg font-medium text-gray-900 mb-4">资源配置</h3>
				
				<!-- 预设选择 -->
				<div class="mb-4">
					<label class="block text-sm font-medium text-gray-700 mb-2">配置预设</label>
					<div class="grid grid-cols-2 md:grid-cols-4 gap-2">
						{#each Object.entries(resourcePresets) as [key, preset]}
							<button
								type="button"
								class="p-3 text-left border rounded-lg transition-colors {selectedPreset === key ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}"
								on:click={() => applyPreset(key)}
								disabled={creating}
							>
								<div class="text-sm font-medium">{preset.label}</div>
								<div class="text-xs text-gray-500 mt-1">{preset.description}</div>
							</button>
						{/each}
					</div>
				</div>

				<!-- 自定义资源设置 -->
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div>
						<label for="cpuLimit" class="block text-sm font-medium text-gray-700 mb-2">
							CPU限制
							<span class="text-red-500">*</span>
						</label>
						<input
							id="cpuLimit"
							type="text"
							bind:value={formData.cpu_limit}
							class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
							placeholder="例如: 0.5, 1.0"
							disabled={creating}
							required
						/>
						<p class="mt-1 text-xs text-gray-500">
							CPU核心数，支持小数
						</p>
					</div>

					<div>
						<label for="memoryLimit" class="block text-sm font-medium text-gray-700 mb-2">
							内存限制
							<span class="text-red-500">*</span>
						</label>
						<input
							id="memoryLimit"
							type="text"
							bind:value={formData.memory_limit}
							class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
							placeholder="例如: 512Mi, 1Gi"
							disabled={creating}
							required
						/>
						<p class="mt-1 text-xs text-gray-500">
							内存大小，支持Mi/Gi单位
						</p>
					</div>
				</div>
			</div>

			<!-- 网络配置 -->
			<div class="mb-6">
				<h3 class="text-lg font-medium text-gray-900 mb-4">网络配置</h3>
				
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<div>
						<label for="gradioPort" class="block text-sm font-medium text-gray-700 mb-2">
							Gradio端口 (可选)
						</label>
						<input
							id="gradioPort"
							type="number"
							bind:value={formData.gradio_port}
							min="1024"
							max="65535"
							class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
							placeholder="留空自动分配"
							disabled={creating}
						/>
						<p class="mt-1 text-xs text-gray-500">
							1024-65535之间，留空则自动分配
						</p>
					</div>

					<div class="flex items-center">
						<div>
							<label for="isPublic" class="flex items-center">
								<input
									id="isPublic"
									type="checkbox"
									bind:checked={formData.is_public}
									class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
									disabled={creating}
								/>
								<span class="ml-2 text-sm font-medium text-gray-700">公开访问</span>
							</label>
							<p class="text-xs text-gray-500 mt-1">
								允许其他用户访问此服务
							</p>
						</div>
					</div>
				</div>
			</div>

			<!-- 服务限制提示 -->
			<div class="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
				<div class="flex items-start">
					<svg class="w-5 h-5 text-amber-400 mr-3 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 15.5c-.77.833.192 2.5 1.732 2.5z"></path>
					</svg>
					<div>
						<p class="text-sm font-medium text-amber-800">服务创建限制</p>
						<p class="text-xs text-amber-600 mt-1">
							每个镜像最多可创建 2 个服务实例。当前镜像已创建 {image.service_count}/2 个服务。
						</p>
					</div>
				</div>
			</div>

			<!-- 错误信息 -->
			{#if error}
				<div class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
					<p class="text-sm text-red-600">{error}</p>
				</div>
			{/if}

			<!-- 按钮区域 -->
			<div class="flex justify-end space-x-3 pt-4 border-t border-gray-200">
				<button
					type="button"
					class="btn btn-outline"
					on:click={handleClose}
					disabled={creating}
				>
					取消
				</button>
				<button
					type="submit"
					class="btn btn-primary"
					disabled={creating}
				>
					{#if creating}
						<LoadingSpinner size="sm" />
						<span class="ml-2">创建中...</span>
					{:else}
						创建服务
					{/if}
				</button>
			</div>
		</form>
	</div>
</div>

<style>
	.btn {
		@apply px-4 py-2 rounded-lg font-medium transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed;
	}

	.btn-primary {
		@apply bg-blue-600 text-white hover:bg-blue-700 flex items-center;
	}

	.btn-outline {
		@apply border border-gray-300 text-gray-700 hover:bg-gray-50;
	}
</style>