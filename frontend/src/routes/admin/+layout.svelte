<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { api } from '$lib/utils/api.js';
	import { PATHS } from '$lib/utils/paths.js';

	let user = null;
	let loading = true;
	let error = null;

	onMount(async () => {
		try {
			const response = await api.getCurrentUser();
			user = response.data;

			// Check if user is admin
			if (!user.is_admin) {
				await goto(PATHS.LOGIN);
				return;
			}

			loading = false;
		} catch (err) {
			error = err.message;
			await goto(PATHS.LOGIN);
		}
	});

	const sidebarItems = [
		{ path: `${PATHS.ADMIN}/dashboard`, label: '仪表板', icon: 'dashboard' },
		{ path: `${PATHS.ADMIN}/users`, label: '用户管理', icon: 'users' },
		{ path: `${PATHS.ADMIN}/repositories`, label: '仓库管理', icon: 'repositories' },
		{ path: `${PATHS.ADMIN}/classifications`, label: '分类管理', icon: 'classifications' },
		{ path: `${PATHS.ADMIN}/storage`, label: '存储管理', icon: 'storage' },
		{ path: `${PATHS.ADMIN}/system`, label: '系统监控', icon: 'system' },
		{ path: `${PATHS.ADMIN}/settings`, label: '系统设置', icon: 'settings' }
	];

	async function handleLogout() {
		try {
			await api.logout();
			await goto(PATHS.HOME);
		} catch (err) {
			console.error('Logout error:', err);
		}
	}
</script>

{#if loading}
	<div class="min-h-screen flex items-center justify-center bg-gray-50">
		<div class="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500" />
	</div>
{:else if error}
	<div class="min-h-screen flex items-center justify-center bg-gray-50">
		<div class="text-red-500 text-center">
			<p class="text-xl mb-4">访问被拒绝</p>
			<p>{error}</p>
		</div>
	</div>
{:else}
	<div class="min-h-screen bg-gray-50 container">
		<!-- 顶部导航栏 -->
		<!-- <header class="bg-white shadow-sm border-b border-gray-200">
			<div class="flex items-center justify-between h-16 px-6">
				<div class="flex items-center">
					<h1 class="text-2xl font-bold text-gray-800">GeoML-Hub 管理后台</h1>
				</div>
				<div class="flex items-center space-x-4">
					<div class="text-sm text-gray-600">
						<span>欢迎, {user.full_name || user.username}</span>
					</div>
					<button
						on:click={handleLogout}
						class="text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded px-3 py-1 hover:bg-gray-50"
					>
						退出
					</button>
				</div>
			</div>
		</header> -->

		<div class="flex">
			<!-- 侧边栏 -->
			<nav class="w-48 bg-white shadow-sm h-screen">
				<div class="p-4">
					<ul class="space-y-2">
						{#each sidebarItems as item}
							<li>
								<a
									href={item.path}
									class="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors duration-200 {$page
										.url.pathname === item.path
										? 'bg-blue-50 text-blue-700 border-r-2 border-blue-500'
										: ''}"
								>
									<span class="mr-3">
										{#if item.icon === 'dashboard'}
											<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"
												/>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M8 5a2 2 0 012-2h4a2 2 0 012 2v6H8V5z"
												/>
											</svg>
										{:else if item.icon === 'users'}
											<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"
												/>
											</svg>
										{:else if item.icon === 'repositories'}
											<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
												/>
											</svg>
										{:else if item.icon === 'classifications'}
											<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
												/>
											</svg>
										{:else if item.icon === 'storage'}
											<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
												/>
											</svg>
										{:else if item.icon === 'system'}
											<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
												/>
											</svg>
										{:else if item.icon === 'settings'}
											<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
												/>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
												/>
											</svg>
										{/if}
									</span>
									{item.label}
								</a>
							</li>
						{/each}
					</ul>
				</div>
			</nav>

			<!-- 主要内容区域 -->
			<main class="flex-1 overflow-y-auto p-6">
				<slot />
			</main>
		</div>
	</div>
{/if}
