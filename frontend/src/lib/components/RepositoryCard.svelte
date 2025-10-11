<script lang="ts">
	import { Star, Download, Eye, GitFork, Calendar, Lock, ChevronRight } from 'lucide-svelte';
	import { formatDistanceToNow } from 'date-fns';
	import { zhCN } from 'date-fns/locale';
	import type { Repository, User } from '$lib/types';
	import UserAvatar from './UserAvatar.svelte';
	import SocialButton from './SocialButton.svelte';
	import { api } from '$lib/utils/api';

	export let repo: Repository;
	export let currentUser: User | null = null;
	export let showOwner: boolean = true;
	export let compact: boolean = false;
	console.log(repo);
	async function handleStar() {
		if (!currentUser) return;

		try {
			if (repo.is_starred) {
				await api.unstarRepository(repo.owner?.username || '', repo.name);
				repo.is_starred = false;
				repo.stars_count -= 1;
			} else {
				await api.starRepository(repo.owner?.username || '', repo.name);
				repo.is_starred = true;
				repo.stars_count += 1;
			}
		} catch (err) {
			console.error('Error starring/unstarring repository:', err);
		}
	}

	function formatFileSize(bytes: number) {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
	}
</script>

<div
	class="repository-card group rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 transition-all duration-200"
>
	<div class="flex items-start justify-between">
		<div class="flex-1 min-w-0">
			<!-- Repository Header -->
			<div class="flex items-center mb-2">
				{#if showOwner && repo.owner}
					<UserAvatar user={repo.owner} size="sm" />
					<span
						class=" text-lg font-mono text-black ml-3 truncate group-hover:text-blue-500 transition-colors"
					>
						{repo.owner.username}
					</span>
					<span
						class=" text-lg font-mono text-black truncate group-hover:text-blue-500 transition-colors"
						>/</span
					>
				{/if}

				<a
					href="/{repo.owner?.username || 'unknown'}/{repo.name}"
					class="text-lg font-mono text-black truncate group-hover:text-blue-500 transition-colors"
				>
					{repo.name}
				</a>

				{#if repo.visibility === 'private'}
					<Lock class="h-4 w-4 text-gray-400" />
				{/if}
			</div>

			<!-- Description -->
			{#if repo.description}
				<p
					class="text-gray-700 dark:text-gray-300 text-sm mb-3 {compact
						? 'line-clamp-2'
						: 'line-clamp-3'}"
				>
					{repo.description}
				</p>
			{/if}
		</div>
	</div>

	<!-- Tasks, Classifications, Stats and Updated Time (full width row) -->
	<div class="flex items-center justify-between gap-4">
		<!-- Tasks and Classifications -->
		<div class="flex items-center gap-2 flex-wrap flex-1 min-w-0">
			<!-- Tasks -->
			{#if repo.task_classifications_data && repo.task_classifications_data.length > 0}
				{#each repo.task_classifications_data as task}
					<span
						class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-purple-50 text-purple-700 border border-purple-100 dark:bg-purple-950 dark:text-purple-300 dark:border-purple-900 shadow-sm"
					>
						{task.name}
					</span>
				{/each}
			{/if}

			<!-- Classifications -->
			{#if repo.classification_path && repo.classification_path.length > 0}
				<div class="flex items-center">
					{#each repo.classification_path as classification, index}
						<span
							class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-900 dark:hover:bg-blue-900 shadow-sm"
						>
							{classification}
						</span>
						{#if index < repo.classification_path.length - 1}
							<ChevronRight class="h-4 w-4 font-medium text-gray-900" />
						{/if}
					{/each}
				</div>
			{/if}

			<!-- License -->
			{#if repo.license}
				<span
					class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-green-50 hover:bg-green-100 transition-colors duration-200 dark:bg-green-950 dark:hover:bg-green-900 shadow-sm border border-green-100 dark:border-green-900"
				>
					<svg
						class="w-3 h-3 text-gray-500 dark:text-gray-400"
						fill="currentColor"
						viewBox="0 0 16 16"
					>
						<path
							d="M8.75.75V2h.985c.304 0 .603.08.867.231l1.29.736c.038.022.08.033.124.033h2.234a.75.75 0 0 1 0 1.5h-.427l2.111 4.692a.75.75 0 0 1-.154.838l-.53-.53.529.531-.001.002-.002.002-.006.006-.006.005-.01.01-.045.04c-.21.176-.441.327-.686.45C14.556 10.78 13.88 11 13 11a4.498 4.498 0 0 1-2.023-.454 3.544 3.544 0 0 1-.686-.45l-.045-.04-.016-.015-.006-.006-.004-.004v-.001a.75.75 0 0 1-.154-.838L12.178 4.5h-.162c-.305 0-.604-.079-.868-.231l-1.29-.736a.245.245 0 0 0-.124-.033H8.75V13h2.5a.75.75 0 0 1 0 1.5h-6.5a.75.75 0 0 1 0-1.5h2.5V3.5h-.984a.245.245 0 0 0-.124.033l-1.289.737c-.265.15-.564.23-.869.23h-.162l2.112 4.692a.75.75 0 0 1-.154.838l-.53-.53.529.531-.001.002-.002.002-.006.006-.016.015-.045.04c-.21.176-.441.327-.686.45C4.556 10.78 3.88 11 3 11a4.498 4.498 0 0 1-2.023-.454 3.544 3.544 0 0 1-.686-.45l-.045-.04-.016-.015-.006-.006-.004-.004v-.001a.75.75 0 0 1-.154-.838L2.178 4.5H1.75a.75.75 0 0 1 0-1.5h2.234a.249.249 0 0 0 .125-.033l1.288-.737c.265-.15.564-.23.869-.23h.984V.75a.75.75 0 0 1 1.5 0Zm2.945 8.477c.285.135.718.273 1.305.273s1.02-.138 1.305-.273L13 6.327Zm-10 0c.285.135.718.273 1.305.273s1.02-.138 1.305-.273L3 6.327Z"
						/>
					</svg>
					<!-- <span class="text-gray-500 dark:text-gray-400">License:</span> -->
					<span class="text-green-700 dark:text-green-300">{repo.license}</span>
				</span>
			{/if}
		</div>

		<!-- Stats and Updated Time -->
		<div class="flex items-center gap-4 flex-shrink-0">
			<!-- Stats -->
			<div class="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
				<div class="flex items-center space-x-1">
					<Star class="h-4 w-4" />
					<span>{repo.stars_count}</span>
				</div>
				<div class="flex items-center space-x-1">
					<Download class="h-4 w-4" />
					<span>{repo.downloads_count}</span>
				</div>
				<div class="flex items-center space-x-1">
					<Eye class="h-4 w-4" />
					<span>{repo.views_count}</span>
				</div>
				{#if repo.total_size > 0}
					<div class="flex items-center space-x-1">
						<span>{formatFileSize(repo.total_size)}</span>
					</div>
				{/if}
			</div>

			<!-- Updated Time -->
			<div class="flex items-center space-x-1 text-xs text-gray-500 dark:text-gray-400">
				<Calendar class="h-3 w-3" />
				<span>
					{formatDistanceToNow(new Date(repo.updated_at), { addSuffix: true, locale: zhCN })}
				</span>
			</div>
		</div>
	</div>
</div>

<style>
	.repository-card {
		background: linear-gradient(to right, var(--color-gray-100), var(--color-white));
	}

	.repository-card:hover {
		background: linear-gradient(to right, var(--color-gray-200), var(--color-gray-50));
		box-shadow: var(--tw-shadow-hover);
		cursor: pointer;
	}

	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.line-clamp-3 {
		display: -webkit-box;
		-webkit-line-clamp: 3;
		line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
