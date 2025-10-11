<script lang="ts">
	import { Star, Download, Eye } from 'lucide-svelte';
	import { formatDistanceToNow } from 'date-fns';
	import { zhCN } from 'date-fns/locale';
	import type { Repository, User } from '$lib/types';

	export let repo: Repository;

	function formatFileSize(bytes: number) {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
	}
</script>

<a
	href="/{repo.owner?.username || 'unknown'}/{repo.name}"
	class="mini-repository-card group block rounded-lg border border-gray-200 dark:border-gray-700 p-3 transition-all duration-200"
>
	<!-- Repository Name -->
	<div class="flex items-center mb-2">
		<span
			class="text-sm font-mono font-medium text-gray-700 dark:text-gray-300 truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors"
		>
			{repo.name}
		</span>
	</div>

	<!-- Description -->
	{#if repo.description}
		<p class="text-xs text-gray-600 dark:text-gray-400 mb-2 line-clamp-2">
			{repo.description}
		</p>
	{/if}

	<!-- Tasks, Stats and Updated Time -->
	<div class="flex items-center justify-between gap-4">
		<!-- Tasks -->
		<div class="flex items-center gap-1.5 flex-wrap flex-1 min-w-0">
			{#if repo.task_classifications_data && repo.task_classifications_data.length > 0}
				{#each repo.task_classifications_data as task}
					<span
						class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-purple-50 text-purple-700 border border-purple-100 dark:bg-purple-950 dark:text-purple-300 dark:border-purple-900 shadow-sm"
					>
						{task.name}
					</span>
				{/each}
			{/if}
		</div>

		<!-- Stats and Updated Time -->
		<div class="flex items-center gap-3 flex-shrink-0">
			<!-- Stats -->
			<div class="flex items-center space-x-3 text-xs text-gray-500 dark:text-gray-400">
				<div class="flex items-center space-x-1">
					<Star class="h-3 w-3" />
					<span>{repo.stars_count}</span>
				</div>
				<div class="flex items-center space-x-1">
					<Download class="h-3 w-3" />
					<span>{repo.downloads_count}</span>
				</div>
				<div class="flex items-center space-x-1">
					<Eye class="h-3 w-3" />
					<span>{repo.views_count}</span>
				</div>
			</div>

			<!-- Updated Time -->
			<span class="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
				{formatDistanceToNow(new Date(repo.updated_at), { addSuffix: true, locale: zhCN })}
			</span>
		</div>
	</div>
</a>

<style>
	.mini-repository-card {
		background: linear-gradient(to right, var(--color-gray-50), var(--color-white));
	}

	.mini-repository-card:hover {
		background: linear-gradient(to right, var(--color-gray-100), var(--color-gray-50));
	}

	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
