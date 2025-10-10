<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/utils/api';
	import Loading from '$lib/components/Loading.svelte';

	// 状态
	let loading = true;
	let loadingTasks = true;
	let saving = false;
	let error: string | null = null;
	let successMessage: string | null = null;

	// 分类数据
	let classifications: any[] = [];
	let taskClassifications: any[] = [];
	let expandedNodes = new Set<number>();

	// 编辑状态
	let editingType: 'sphere' | 'task' | null = null;
	let editingId: number | null = null;
	let editingName: string = '';
	let editingNameZh: string = '';
	let editingDescription: string = '';
	let editingIcon: string = '';

	// 加载分类树
	async function loadClassifications() {
		try {
			loading = true;
			error = null;
			const response = await api.getClassificationTree();
			classifications = response.classifications || [];
		} catch (err: any) {
			error = err.message || '加载分类失败';
		} finally {
			loading = false;
		}
	}

	// 加载任务分类列表
	async function loadTaskClassifications() {
		try {
			loadingTasks = true;
			error = null;
			const response = await fetch('/api/task-classifications/')
				.then((res) => res.json())
				.catch(() => ({ task_classifications: [] }));
			taskClassifications = response.task_classifications || [];
		} catch (err: any) {
			error = err.message || '加载任务分类失败';
		} finally {
			loadingTasks = false;
		}
	}

	// 展开/收起节点
	function toggleNode(id: number) {
		if (expandedNodes.has(id)) {
			expandedNodes.delete(id);
		} else {
			expandedNodes.add(id);
		}
		expandedNodes = expandedNodes;
	}

	// 开始编辑
	function startEdit(classification: any, type: 'sphere' | 'task' = 'sphere') {
		editingType = type;
		editingId = classification.id;
		editingName = classification.name;
		editingNameZh = classification.name_zh || '';
		editingDescription = classification.description || '';
		editingIcon = classification.icon || '';
	}

	// 取消编辑
	function cancelEdit() {
		editingType = null;
		editingId = null;
		editingName = '';
		editingNameZh = '';
		editingDescription = '';
		editingIcon = '';
	}

	// 保存编辑
	async function saveEdit(classificationId: number) {
		if (!editingName.trim()) {
			error = '分类名称不能为空';
			return;
		}

		try {
			saving = true;
			error = null;
			successMessage = null;

			if (editingType === 'sphere') {
				// 保存科学领域分类
				await api.request(`/api/classifications/${classificationId}`, {
					method: 'PUT',
					body: {
						name: editingName.trim(),
						name_zh: editingNameZh.trim() || null,
						description: editingDescription.trim() || null
					}
				});
				successMessage = '科学领域分类更新成功';
				await loadClassifications();
			} else if (editingType === 'task') {
				// 保存任务分类
				await api.request(`/api/task-classifications/${classificationId}`, {
					method: 'PUT',
					body: {
						name: editingName.trim(),
						name_zh: editingNameZh.trim() || null,
						description: editingDescription.trim() || null,
						icon: editingIcon.trim() || null
					}
				});
				successMessage = '任务分类更新成功';
				await loadTaskClassifications();
			}

			cancelEdit();

			// 3秒后清除成功消息
			setTimeout(() => {
				successMessage = null;
			}, 3000);
		} catch (err: any) {
			error = err.message || '保存失败';
		} finally {
			saving = false;
		}
	}

	// 递归渲染分类树
	function renderClassificationTree(items: any[], level: number = 0) {
		return items;
	}

	onMount(() => {
		loadClassifications();
		loadTaskClassifications();
	});
</script>

<div class="max-w-7xl mx-auto">
	<!-- 页面标题 -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900 dark:text-white">分类管理</h1>
		<p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
			管理地球科学领域分类和任务类型分类的名称、图标和描述
		</p>
	</div>

	<!-- 消息提示 -->
	{#if successMessage}
		<div
			class="mb-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-4 animate-in fade-in duration-200"
		>
			<p class="text-sm font-medium text-green-800 dark:text-green-200">
				{successMessage}
			</p>
		</div>
	{/if}

	{#if error}
		<div
			class="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg p-4"
		>
			<p class="text-sm font-medium text-red-800 dark:text-red-200">
				{error}
			</p>
		</div>
	{/if}

	<!-- 科学领域分类列表 -->
	<div class="mb-8">
		<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">科学领域分类</h2>

		<div
			class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700"
		>
			{#if loading}
				<div class="flex items-center justify-center py-12">
					<Loading />
				</div>
			{:else if classifications.length === 0}
				<div class="text-center py-12">
					<p class="text-gray-500 dark:text-gray-400">暂无分类数据</p>
				</div>
			{:else}
				<div class="divide-y divide-gray-200 dark:divide-gray-700">
					{#each classifications as classification}
						<div class="p-4">
							<!-- 一级分类 -->
							<div class="flex items-start space-x-3">
								<!-- 展开/收起按钮 -->
								{#if classification.children && classification.children.length > 0}
									<button
										type="button"
										on:click={() => toggleNode(classification.id)}
										class="mt-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
									>
										{#if expandedNodes.has(classification.id)}
											<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M19 9l-7 7-7-7"
												/>
											</svg>
										{:else}
											<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M9 5l7 7-7 7"
												/>
											</svg>
										{/if}
									</button>
								{:else}
									<div class="w-5" />
								{/if}

								<!-- 分类信息 -->
								<div class="flex-1">
									{#if editingId === classification.id}
										<!-- 编辑模式 -->
										<div class="space-y-3">
											<div class="grid grid-cols-2 gap-3">
												<div>
													<label
														class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
													>
														英文名称
													</label>
													<input
														type="text"
														bind:value={editingName}
														class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
														placeholder="英文名称"
													/>
												</div>
												<div>
													<label
														class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
													>
														中文名称
													</label>
													<input
														type="text"
														bind:value={editingNameZh}
														class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
														placeholder="中文名称（可选）"
													/>
												</div>
											</div>
											<div>
												<label
													class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
												>
													描述
												</label>
												<textarea
													bind:value={editingDescription}
													rows="2"
													class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
													placeholder="描述（可选）"
												/>
											</div>
											<div class="flex items-center space-x-2">
												<button
													type="button"
													on:click={() => saveEdit(classification.id)}
													disabled={saving}
													class="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
												>
													{saving ? '保存中...' : '保存'}
												</button>
												<button
													type="button"
													on:click={cancelEdit}
													disabled={saving}
													class="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
												>
													取消
												</button>
											</div>
										</div>
									{:else}
										<!-- 显示模式 -->
										<div class="flex items-start justify-between">
											<div class="flex-1">
												<div class="flex items-center space-x-2 mb-1">
													<h3 class="text-base font-semibold text-gray-900 dark:text-white">
														{classification.name_zh || classification.name}
													</h3>
													{#if classification.name_zh}
														<span class="text-sm text-gray-500 dark:text-gray-400">
															({classification.name})
														</span>
													{/if}
													<span
														class="px-2 py-0.5 text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded"
													>
														Level {classification.level}
													</span>
												</div>
												{#if classification.description}
													<p class="text-sm text-gray-600 dark:text-gray-400">
														{classification.description}
													</p>
												{/if}
											</div>
											<button
												type="button"
												on:click={() => startEdit(classification)}
												class="ml-4 px-3 py-1 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 border border-blue-600 dark:border-blue-400 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
											>
												编辑
											</button>
										</div>
									{/if}
								</div>
							</div>

							<!-- 子分类 -->
							{#if expandedNodes.has(classification.id) && classification.children && classification.children.length > 0}
								<div class="ml-8 mt-4 space-y-4">
									{#each classification.children as child}
										<div class="border-l-2 border-gray-200 dark:border-gray-700 pl-4">
											<!-- 二级分类 -->
											<div class="flex items-start space-x-3">
												{#if child.children && child.children.length > 0}
													<button
														type="button"
														on:click={() => toggleNode(child.id)}
														class="mt-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
													>
														{#if expandedNodes.has(child.id)}
															<svg
																class="w-4 h-4"
																fill="none"
																stroke="currentColor"
																viewBox="0 0 24 24"
															>
																<path
																	stroke-linecap="round"
																	stroke-linejoin="round"
																	stroke-width="2"
																	d="M19 9l-7 7-7-7"
																/>
															</svg>
														{:else}
															<svg
																class="w-4 h-4"
																fill="none"
																stroke="currentColor"
																viewBox="0 0 24 24"
															>
																<path
																	stroke-linecap="round"
																	stroke-linejoin="round"
																	stroke-width="2"
																	d="M9 5l7 7-7 7"
																/>
															</svg>
														{/if}
													</button>
												{:else}
													<div class="w-4" />
												{/if}

												<div class="flex-1">
													{#if editingId === child.id}
														<!-- 编辑模式 -->
														<div class="space-y-3">
															<div class="grid grid-cols-2 gap-3">
																<div>
																	<label
																		class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
																	>
																		英文名称
																	</label>
																	<input
																		type="text"
																		bind:value={editingName}
																		class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
																		placeholder="英文名称"
																	/>
																</div>
																<div>
																	<label
																		class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
																	>
																		中文名称
																	</label>
																	<input
																		type="text"
																		bind:value={editingNameZh}
																		class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
																		placeholder="中文名称（可选）"
																	/>
																</div>
															</div>
															<div>
																<label
																	class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
																>
																	描述
																</label>
																<textarea
																	bind:value={editingDescription}
																	rows="2"
																	class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
																	placeholder="描述（可选）"
																/>
															</div>
															<div class="flex items-center space-x-2">
																<button
																	type="button"
																	on:click={() => saveEdit(child.id)}
																	disabled={saving}
																	class="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
																>
																	{saving ? '保存中...' : '保存'}
																</button>
																<button
																	type="button"
																	on:click={cancelEdit}
																	disabled={saving}
																	class="px-3 py-1.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
																>
																	取消
																</button>
															</div>
														</div>
													{:else}
														<!-- 显示模式 -->
														<div class="flex items-start justify-between">
															<div class="flex-1">
																<div class="flex items-center space-x-2 mb-1">
																	<h4 class="text-sm font-medium text-gray-900 dark:text-white">
																		{child.name_zh || child.name}
																	</h4>
																	{#if child.name_zh}
																		<span class="text-xs text-gray-500 dark:text-gray-400">
																			({child.name})
																		</span>
																	{/if}
																	<span
																		class="px-1.5 py-0.5 text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded"
																	>
																		Level {child.level}
																	</span>
																</div>
																{#if child.description}
																	<p class="text-xs text-gray-600 dark:text-gray-400">
																		{child.description}
																	</p>
																{/if}
															</div>
															<button
																type="button"
																on:click={() => startEdit(child)}
																class="ml-4 px-2 py-1 text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 border border-blue-600 dark:border-blue-400 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
															>
																编辑
															</button>
														</div>
													{/if}
												</div>
											</div>

											<!-- 三级分类 -->
											{#if expandedNodes.has(child.id) && child.children && child.children.length > 0}
												<div class="ml-8 mt-3 space-y-3">
													{#each child.children as grandchild}
														<div class="border-l-2 border-gray-200 dark:border-gray-700 pl-4">
															{#if editingId === grandchild.id}
																<!-- 编辑模式 -->
																<div class="space-y-2">
																	<div class="grid grid-cols-2 gap-2">
																		<div>
																			<label
																				class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
																			>
																				英文名称
																			</label>
																			<input
																				type="text"
																				bind:value={editingName}
																				class="w-full px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded text-xs dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
																				placeholder="英文名称"
																			/>
																		</div>
																		<div>
																			<label
																				class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
																			>
																				中文名称
																			</label>
																			<input
																				type="text"
																				bind:value={editingNameZh}
																				class="w-full px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded text-xs dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
																				placeholder="中文名称（可选）"
																			/>
																		</div>
																	</div>
																	<div>
																		<label
																			class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1"
																		>
																			描述
																		</label>
																		<textarea
																			bind:value={editingDescription}
																			rows="2"
																			class="w-full px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded text-xs dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
																			placeholder="描述（可选）"
																		/>
																	</div>
																	<div class="flex items-center space-x-2">
																		<button
																			type="button"
																			on:click={() => saveEdit(grandchild.id)}
																			disabled={saving}
																			class="px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
																		>
																			{saving ? '保存中...' : '保存'}
																		</button>
																		<button
																			type="button"
																			on:click={cancelEdit}
																			disabled={saving}
																			class="px-2 py-1 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
																		>
																			取消
																		</button>
																	</div>
																</div>
															{:else}
																<!-- 显示模式 -->
																<div class="flex items-start justify-between">
																	<div class="flex-1">
																		<div class="flex items-center space-x-2 mb-0.5">
																			<h5 class="text-xs font-medium text-gray-900 dark:text-white">
																				{grandchild.name_zh || grandchild.name}
																			</h5>
																			{#if grandchild.name_zh}
																				<span class="text-xs text-gray-500 dark:text-gray-400">
																					({grandchild.name})
																				</span>
																			{/if}
																			<span
																				class="px-1 py-0.5 text-xs font-medium bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 rounded"
																			>
																				Level {grandchild.level}
																			</span>
																		</div>
																		{#if grandchild.description}
																			<p class="text-xs text-gray-600 dark:text-gray-400">
																				{grandchild.description}
																			</p>
																		{/if}
																	</div>
																	<button
																		type="button"
																		on:click={() => startEdit(grandchild)}
																		class="ml-4 px-2 py-0.5 text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 border border-blue-600 dark:border-blue-400 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
																	>
																		编辑
																	</button>
																</div>
															{/if}
														</div>
													{/each}
												</div>
											{/if}
										</div>
									{/each}
								</div>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	<!-- 任务分类列表 -->
	<div class="mt-8">
		<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">任务类型分类</h2>

		<div
			class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700"
		>
			{#if loadingTasks}
				<div class="flex items-center justify-center py-12">
					<Loading />
				</div>
			{:else if taskClassifications.length === 0}
				<div class="text-center py-12">
					<p class="text-gray-500 dark:text-gray-400">暂无任务分类数据</p>
				</div>
			{:else}
				<div class="divide-y divide-gray-200 dark:divide-gray-700">
					{#each taskClassifications as task}
						<div class="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
							{#if editingType === 'task' && editingId === task.id}
								<!-- 编辑模式 -->
								<div class="space-y-4">
									<div class="grid grid-cols-2 gap-4">
										<div>
											<label
												class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
											>
												英文名称 *
											</label>
											<input
												type="text"
												bind:value={editingName}
												class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
												placeholder="英文名称"
											/>
										</div>
										<div>
											<label
												class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
											>
												中文名称
											</label>
											<input
												type="text"
												bind:value={editingNameZh}
												class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
												placeholder="中文名称（可选）"
											/>
										</div>
									</div>
									<div>
										<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
											图标（Emoji）
										</label>
										<input
											type="text"
											bind:value={editingIcon}
											class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
											placeholder="例如：🔍 📊 🌍"
											maxlength="4"
										/>
									</div>
									<div>
										<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
											描述
										</label>
										<textarea
											bind:value={editingDescription}
											rows="3"
											class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm dark:bg-gray-700 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
											placeholder="描述（可选）"
										/>
									</div>
									<div class="flex items-center space-x-3">
										<button
											type="button"
											on:click={() => saveEdit(task.id)}
											disabled={saving}
											class="px-5 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors shadow-sm"
										>
											{saving ? '保存中...' : '保存'}
										</button>
										<button
											type="button"
											on:click={cancelEdit}
											disabled={saving}
											class="px-5 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
										>
											取消
										</button>
									</div>
								</div>
							{:else}
								<!-- 显示模式 -->
								<div class="flex items-center justify-between">
									<div class="flex items-start space-x-4 flex-1">
										<!-- 图标 -->
										<!-- {#if task.icon}
											<div class="text-3xl mt-1">
												{task.icon}
											</div>
										{:else}
											<div
												class="w-12 h-12 bg-gradient-to-br from-purple-400 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-lg shadow-sm"
											>
												{task.name.charAt(0).toUpperCase()}
											</div>
										{/if} -->

										<!-- 内容 -->
										<div class="flex-1">
											<div class="flex items-center space-x-3">
												<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
													{task.name}
												</h3>
												<!-- {#if task.name_zh}
													<span class="text-sm text-gray-500 dark:text-gray-400">
														({task.name})
													</span>
												{/if} -->
												<span
													class="px-2.5 py-0.5 text-xs font-medium bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 rounded-full"
												>
													Task
												</span>
											</div>
											{#if task.description}
												<p class="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
													{task.description}
												</p>
											{/if}
											<!-- <div class="mt-2 flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
												<span>排序: {task.sort_order}</span>
												<span>•</span>
												<span>创建于: {new Date(task.created_at).toLocaleDateString('zh-CN')}</span>
											</div> -->
										</div>
									</div>

									<!-- 编辑按钮 -->
									<button
										type="button"
										on:click={() => startEdit(task, 'task')}
										class="ml-4 px-4 py-2 text-sm font-medium text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 border border-purple-600 dark:border-purple-400 rounded-lg hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-colors"
									>
										编辑
									</button>
								</div>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>
</div>
