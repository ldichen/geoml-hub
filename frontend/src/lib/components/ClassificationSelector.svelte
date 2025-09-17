<script>
	import { createEventDispatcher } from 'svelte';
	import { ChevronRight, ChevronDown } from 'lucide-svelte';

	export let classifications = [];
	export let selectedClassificationId = null;
	export let loading = false;

	const dispatch = createEventDispatcher();

	let expandedNodes = new Set();

	// 直接使用API返回的树形数据
	$: classificationTree = getClassificationTree(classifications);

	// 调试信息
	$: {
		console.log('Classifications data:', classifications);
		console.log('Classification tree:', classificationTree);
	}

	function getClassificationTree(data) {
		// API返回的数据结构：{ classifications: [...] }
		if (data && data.classifications && Array.isArray(data.classifications)) {
			return data.classifications;
		} else if (Array.isArray(data)) {
			return data;
		} else {
			return [];
		}
	}

	function toggleExpand(nodeId) {
		// 创建新的Set来触发响应式更新
		const newExpandedNodes = new Set(expandedNodes);
		if (newExpandedNodes.has(nodeId)) {
			newExpandedNodes.delete(nodeId);
		} else {
			newExpandedNodes.add(nodeId);
		}
		expandedNodes = newExpandedNodes;
	}

	function selectClassification(classification) {
		selectedClassificationId = classification.id;
		dispatch('select', classification);
	}

	// 使用响应式语句来确保UI更新
	$: isNodeExpanded = (nodeId) => {
		return expandedNodes.has(nodeId);
	};

	function hasChildren(node) {
		return node.children && node.children.length > 0;
	}

	function getIndentClass(level) {
		return `ml-${level * 4}`;
	}
</script>

<div class="classification-selector">
	{#if loading}
		<div class="flex items-center justify-center py-4">
			<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
			<span class="ml-2 text-sm text-slate-500 dark:text-slate-400">加载分类中...</span>
		</div>
	{:else if classificationTree.length === 0}
		<div class="text-center py-4">
			<p class="text-sm text-slate-500 dark:text-slate-400">暂无分类数据</p>
		</div>
	{:else}
		<div
			class="max-h-64 overflow-y-auto border border-slate-200/70 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-800 shadow-sm"
		>
			{#each classificationTree as node}
				<div class="classification-node">
					<!-- 一级分类 -->
					<div
						class="flex items-center px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer border-b border-slate-100 dark:border-slate-700 {selectedClassificationId ===
						node.id
							? 'bg-blue-50 dark:bg-blue-900/20'
							: ''}"
					>
						{#if hasChildren(node)}
							<button
								type="button"
								class="mr-2 p-1 hover:bg-slate-200 dark:hover:bg-slate-600 rounded flex items-center justify-center w-6 h-6"
								on:click|stopPropagation={() => toggleExpand(node.id)}
							>
								{#if isNodeExpanded(node.id)}
									<span class="text-sm">▼</span>
								{:else}
									<span class="text-sm">▶</span>
								{/if}
							</button>
						{:else}
							<div class="w-6 h-6 mr-2" />
						{/if}

						<label class="flex-1 cursor-pointer flex items-center">
							<input
								type="radio"
								name="classification"
								value={node.id}
								checked={selectedClassificationId === node.id}
								on:change={() => selectClassification(node)}
								class="mr-2 text-blue-600 focus:ring-blue-500"
							/>
							<span class="text-sm font-medium text-slate-900 dark:text-white">
								{node.name}
							</span>
							{#if hasChildren(node)}
								<span class="text-xs text-slate-400 ml-1">(可选择或展开查看子分类)</span>
							{/if}
						</label>
					</div>

					<!-- 二级和三级分类 -->
					{#if hasChildren(node) && isNodeExpanded(node.id)}
						{#each node.children as childNode}
							<div class="ml-4">
								<div
									class="flex items-center px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer border-b border-slate-100 dark:border-slate-700 {selectedClassificationId ===
									childNode.id
										? 'bg-blue-50 dark:bg-blue-900/20'
										: ''}"
								>
									{#if hasChildren(childNode)}
										<button
											type="button"
											class="mr-2 p-1 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 rounded flex items-center justify-center w-6 h-6"
											on:click|stopPropagation={() => toggleExpand(childNode.id)}
											style="z-index: 10; position: relative;"
										>
											{#if isNodeExpanded(childNode.id)}
												<span class="text-xs">▼</span>
											{:else}
												<span class="text-xs">▶</span>
											{/if}
										</button>
									{:else}
										<div class="w-6 h-6 mr-2" />
									{/if}

									<!-- 二级分类可以选择 -->
									<label class="flex-1 cursor-pointer flex items-center">
										<input
											type="radio"
											name="classification"
											value={childNode.id}
											checked={selectedClassificationId === childNode.id}
											on:change={() => selectClassification(childNode)}
											class="mr-2 text-blue-600 focus:ring-blue-500"
										/>
										<span class="text-sm font-medium text-slate-700 dark:text-slate-300">
											{childNode.name}
										</span>
										{#if hasChildren(childNode)}
											<span class="text-xs text-slate-400 ml-1">(可选择或展开查看三级分类)</span>
										{/if}
									</label>
								</div>

								<!-- 三级分类 -->
								{#if hasChildren(childNode) && isNodeExpanded(childNode.id)}
									{#each childNode.children as grandChildNode}
										<div class="ml-4">
											<div
												class="flex items-center px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer {selectedClassificationId ===
												grandChildNode.id
													? 'bg-blue-50 dark:bg-blue-900/20'
													: ''}"
											>
												<div class="w-6 h-6 mr-2" />

												<!-- 三级分类可以选择 -->
												<label class="flex-1 cursor-pointer flex items-center">
													<input
														type="radio"
														name="classification"
														value={grandChildNode.id}
														checked={selectedClassificationId === grandChildNode.id}
														on:change={() => selectClassification(grandChildNode)}
														class="mr-2 text-blue-600 focus:ring-blue-500"
													/>
													<span class="text-sm text-slate-600 dark:text-slate-400">
														{grandChildNode.name}
													</span>
												</label>
											</div>
										</div>
									{/each}
								{/if}
							</div>
						{/each}
					{/if}
				</div>
			{/each}
		</div>

	{/if}
</div>

<style>
	.classification-selector :global(input[type='radio']) {
		width: 16px;
		height: 16px;
	}
</style>
