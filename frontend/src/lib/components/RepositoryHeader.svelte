<script>
	import { createEventDispatcher } from 'svelte';
	import { _ } from 'svelte-i18n';
	import { base } from '$app/paths';
	import {
		Star,
		Download,
		Eye,
		Calendar,
		Settings,
		GitFork,
		Users,
		Lock,
		Upload
	} from 'lucide-svelte';
	import { formatDistanceToNow } from 'date-fns';
	import zhCN from 'date-fns/locale/zh-CN/index.js';
	import UserAvatar from './UserAvatar.svelte';

	export let repository;
	export let isRepoOwner = false;
	export let activeTab = 'readme';

	const dispatch = createEventDispatcher();

	function handleStar() {
		dispatch('star');
	}

	function handleWatch() {
		dispatch('watch');
	}

	function getRepoTypeLabel(type) {
		switch (type) {
			case 'model':
				return $_('repository.model');
			case 'dataset':
				return $_('repository.dataset');
			case 'space':
				return $_('repository.space');
			default:
				return type;
		}
	}

	function getRepoTypeColor(type) {
		switch (type) {
			case 'model':
				return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
			case 'dataset':
				return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
			case 'space':
				return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
			default:
				return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
		}
	}

	function formatFileSize(bytes) {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
	}
</script>

<div
	class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700"
>
	<div class="p-6">
		<div class="flex items-start justify-between">
			<div class="flex-1 min-w-0">
				<!-- Repository title -->
				<div class="flex items-center space-x-2 mb-2">
					<UserAvatar user={repository.owner} size="sm" />
					<a
						href="{base}/{repository.owner?.username}"
						class="text-primary-600 dark:text-primary-400 hover:underline"
					>
						{repository.owner?.username}
					</a>
					<span class="text-gray-400 dark:text-gray-600">/</span>
					<h1 class="text-xl font-bold text-gray-900 dark:text-white">
						{repository.name}
					</h1>
					<span
						class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getRepoTypeColor(
							repository.repo_type
						)}"
					>
						{getRepoTypeLabel(repository.repo_type)}
					</span>
					{#if repository.visibility === 'private'}
						<span
							class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
						>
							<Lock class="w-3 h-3 mr-1" />
							{$_('repository.private')}
						</span>
					{/if}
				</div>

				<!-- Description -->
				{#if repository.description}
					<p class="text-gray-700 dark:text-gray-300 mb-4">
						{repository.description}
					</p>
				{:else}
					<p class="text-gray-500 dark:text-gray-400 italic mb-4">
						{$_('repository.no_description')}
					</p>
				{/if}

				<!-- Tags -->
				{#if repository.tags && repository.tags.length > 0}
					<div class="flex flex-wrap gap-1 mb-4">
						{#each repository.tags as tag}
							<span
								class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 dark:bg-blue-900 dark:text-blue-200"
							>
								#{tag}
							</span>
						{/each}
					</div>
				{/if}

				<!-- Stats -->
				<div class="flex items-center space-x-6 text-sm text-gray-600 dark:text-gray-400">
					<div class="flex items-center space-x-1">
						<Star class="h-4 w-4" />
						<span>{repository.stars_count || 0}</span>
						<span class="hidden sm:inline">{$_('repository.stars')}</span>
					</div>
					<div class="flex items-center space-x-1">
						<Download class="h-4 w-4" />
						<span>{repository.downloads_count || 0}</span>
						<span class="hidden sm:inline">{$_('repository.downloads')}</span>
					</div>
					<div class="flex items-center space-x-1">
						<Eye class="h-4 w-4" />
						<span>{repository.views_count || 0}</span>
						<span class="hidden sm:inline">{$_('repository.views')}</span>
					</div>
					{#if repository.total_files}
						<div class="flex items-center space-x-1">
							<span>{repository.total_files}</span>
							<span class="hidden sm:inline">{$_('file.files')}</span>
						</div>
					{/if}
					{#if repository.total_size && repository.total_size > 0}
						<div class="flex items-center space-x-1">
							<span>{formatFileSize(repository.total_size)}</span>
						</div>
					{/if}
				</div>

				<!-- Updated time and license -->
				<div class="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400 mt-2">
					<div class="flex items-center space-x-1">
						<Calendar class="h-3 w-3" />
						<span>
							{$_('repository.last_updated')}
							{formatDistanceToNow(new Date(repository.updated_at), {
								addSuffix: true,
								locale: zhCN
							})}
						</span>
					</div>
					{#if repository.license}
						<div class="flex items-center space-x-1">
							<span>{$_('repository.license')}: {repository.license}</span>
						</div>
					{/if}
				</div>
			</div>

			<!-- Actions -->
			<div class="flex items-center space-x-2 ml-6">
				{#if !isRepoOwner}
					<button
						on:click={handleStar}
						class="btn {repository.is_starred ? 'btn-primary' : 'btn-secondary'} flex items-center"
					>
						<Star class="w-4 h-4 mr-1 {repository.is_starred ? 'fill-current' : ''}" />
						{repository.is_starred ? $_('repository.unstar') : $_('repository.star')}
						<span class="ml-1 text-xs">({repository.stars_count || 0})</span>
					</button>

					<button on:click={handleWatch} class="btn btn-secondary flex items-center">
						<Eye class="w-4 h-4 mr-1" />
						{repository.is_watching ? $_('repository.unwatch') : $_('repository.watch')}
					</button>
				{/if}

				{#if isRepoOwner}
					<a
						href="{base}/{repository.owner?.username}/{repository.name}/upload"
						class="btn btn-primary flex items-center"
					>
						<Upload class="w-4 h-4 mr-1" />
						{$_('file.upload')}
					</a>

					<a
						href="{base}/{repository.owner?.username}/{repository.name}/settings"
						class="btn btn-secondary flex items-center"
					>
						<Settings class="w-4 h-4 mr-1" />
						{$_('repository.settings')}
					</a>
				{/if}

				<!-- More actions dropdown -->
				<div class="relative">
					<button class="btn btn-secondary">
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
							/>
						</svg>
					</button>
				</div>
			</div>
		</div>
	</div>
</div>
