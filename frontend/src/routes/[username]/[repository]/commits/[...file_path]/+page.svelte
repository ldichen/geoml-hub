<script>
	import { page } from '$app/stores';
	import { base } from '$app/paths';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api } from '$lib/utils/api.js';

	import RepositoryHeader from '$lib/components/RepositoryHeader.svelte';
	import VersionHistory from '$lib/components/version/VersionHistory.svelte';
	import VersionDiff from '$lib/components/version/VersionDiff.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Loading from '$lib/components/Loading.svelte';
	import Toast from '$lib/components/ui/Toast.svelte';

	// 路由参数
	$: username = $page.params.username;
	$: repositoryName = $page.params.repository;
	$: filePath = $page.params.file_path;

	// 状态
	let repository = null;
	let fileInfo = null;
	let isLoading = true;
	let error = null;
	let toast = null;
	let currentView = 'history'; // history, diff
	let selectedVersions = { from: null, to: null };

	// 加载数据
	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		isLoading = true;
		error = null;

		try {
			// 并行加载仓库信息和文件信息
			const [repoResponse, fileResponse] = await Promise.all([
				api.get(`/api/repositories/${username}/${repositoryName}`),
				api.get(`/api/files/${username}/${repositoryName}/info/${filePath}`)
			]);

			repository = repoResponse.data;
			fileInfo = fileResponse.data;
		} catch (err) {
			console.error('加载数据失败:', err);
			error = err.response?.data?.detail || '加载数据失败';
		} finally {
			isLoading = false;
		}
	}

	// 查看版本内容
	function handleViewVersion(event) {
		const { versionId, versionNumber, versionHash } = event.detail;
		goto(`${base}/${username}/${repositoryName}/blob/${filePath}?version=${versionId}`);
	}

	// 版本恢复成功
	function handleVersionRestored(event) {
		const { newVersionId, restoredFromVersion } = event.detail;
		toast = {
			type: 'success',
			message: `成功恢复到版本 ${restoredFromVersion}`
		};

		// 可选择：跳转到编辑页面查看恢复后的内容
		// goto(`${base}/${username}/${repositoryName}/edit/${filePath}`);
	}

	// 显示版本差异
	function handleShowDiff(event) {
		const { fromVersion, toVersion } = event.detail;
		selectedVersions = { from: fromVersion, to: toVersion };
		currentView = 'diff';
	}

	// 处理错误
	function handleError(event) {
		const { message } = event.detail;
		toast = { type: 'error', message };
	}

	// 返回文件查看
	function goToFile() {
		goto(`${base}/${username}/${repositoryName}/blob/${filePath}`);
	}

	// 编辑文件
	function editFile() {
		goto(`${base}/${username}/${repositoryName}/edit/${filePath}`);
	}

	// 返回版本历史
	function backToHistory() {
		currentView = 'history';
		selectedVersions = { from: null, to: null };
	}
</script>

<svelte:head>
	<title>版本历史 - {filePath} - {repositoryName} - GeoML-Hub</title>
</svelte:head>

{#if toast}
	<Toast type={toast.type} message={toast.message} on:close={() => (toast = null)} />
{/if}

<div class="commits-page">
	<!-- 仓库头部 -->
	{#if repository}
		<RepositoryHeader {repository} activeTab="files" />
	{/if}

	<!-- 页面头部 -->
	<div class="bg-white border-b border-gray-200">
		<div class="container mx-auto px-4 py-4">
			{#if isLoading}
				<div class="animate-pulse">
					<div class="h-6 bg-gray-200 rounded w-1/2 mb-2" />
					<div class="h-4 bg-gray-200 rounded w-1/3" />
				</div>
			{:else if error}
				<div class="text-red-500">
					<h1 class="text-xl font-semibold">❌ 加载失败</h1>
					<p class="text-sm mt-1">{error}</p>
				</div>
			{:else}
				<div class="flex items-center justify-between">
					<div>
						<nav class="flex items-center space-x-2 text-sm text-gray-600 mb-2">
							<a href="{base}/{username}/{repositoryName}" class="hover:text-blue-600">
								{repositoryName}
							</a>
							<span>/</span>
							<a href="{base}/{username}/{repositoryName}/tree" class="hover:text-blue-600"> 文件 </a>
							{#each filePath.split('/') as segment, i}
								<span>/</span>
								{#if i === filePath.split('/').length - 1}
									<span class="text-gray-900">{segment}</span>
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
							<span>/</span>
							<span class="text-blue-600 font-medium">
								{currentView === 'history' ? '版本历史' : '版本对比'}
							</span>
						</nav>

						<h1 class="text-2xl font-bold text-gray-900">
							{#if currentView === 'history'}
								版本历史
							{:else}
								版本对比
							{/if}
						</h1>
					</div>

					<div class="flex items-center space-x-2">
						{#if currentView === 'diff'}
							<Button variant="outline" size="sm" on:click={backToHistory}>← 返回历史</Button>
						{/if}

						<Button variant="outline" size="sm" on:click={goToFile}>📄 查看文件</Button>

						<Button variant="primary" size="sm" on:click={editFile}>✏️ 编辑文件</Button>
					</div>
				</div>
			{/if}
		</div>
	</div>

	<!-- 主要内容 -->
	<div class="flex-1">
		{#if isLoading}
			<Loading message="加载版本历史中..." />
		{:else if error}
			<div class="container mx-auto px-4 py-12">
				<div class="text-center">
					<div class="text-red-500 text-lg mb-4">❌ {error}</div>
					<Button on:click={loadData}>重试</Button>
				</div>
			</div>
		{:else if fileInfo}
			{#if currentView === 'history'}
				<VersionHistory
					fileId={fileInfo.id}
					{filePath}
					{repository}
					currentVersionId={fileInfo.current_version_id}
					on:viewVersion={handleViewVersion}
					on:versionRestored={handleVersionRestored}
					on:showDiff={handleShowDiff}
					on:error={handleError}
				/>
			{:else if currentView === 'diff' && selectedVersions.from && selectedVersions.to}
				<VersionDiff
					fileId={fileInfo.id}
					fromVersion={selectedVersions.from}
					toVersion={selectedVersions.to}
					{filePath}
				/>
			{/if}
		{/if}
	</div>
</div>

<style>
	.commits-page {
		min-height: 100vh;
		background: #f8f9fa;
		display: flex;
		flex-direction: column;
	}
</style>
