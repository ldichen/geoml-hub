<script>
	import { onMount } from 'svelte';
	import { locale, _ } from 'svelte-i18n';
	import { Search, Globe, Sun, Moon, Monitor, Menu, X, User, LogOut, Plus, Settings } from 'lucide-svelte';
	import { user, isAuthenticated, logout } from '$lib/stores/auth';
	import { api } from '$lib/utils/api';
	import UserAvatar from './UserAvatar.svelte';

	export let theme = 'light';
	export let applyTheme;

	let showLanguageDropdown = false;
	let showMobileMenu = false;
	let showUserDropdown = false;

	const languages = [
		{ value: 'zh-CN', label: '中文', flag: '🇨🇳' },
		{ value: 'en-US', label: 'English', flag: '🇺🇸' }
	];

	const themes = [
		{ value: 'light', label: $_('theme.light'), icon: Sun },
		{ value: 'dark', label: $_('theme.dark'), icon: Moon },
		{ value: 'system', label: $_('theme.system'), icon: Monitor }
	];

	$: currentLanguage = languages.find((lang) => lang.value === $locale) || languages[0];
	$: currentTheme = themes.find((t) => t.value === theme) || themes[0];

	function switchLanguage(lang) {
		locale.set(lang);
		if (typeof window !== 'undefined') {
			localStorage.setItem('geoml-locale', lang);
		}
		showLanguageDropdown = false;
	}

	function toggleTheme() {
		const themeOrder = ['light', 'dark', 'system'];
		const currentIndex = themeOrder.indexOf(theme);
		const nextIndex = (currentIndex + 1) % themeOrder.length;
		const nextTheme = themeOrder[nextIndex];
		applyTheme(nextTheme);
	}

	// Close dropdowns when clicking outside
	function handleClickOutside(event) {
		if (!event.target.closest('.dropdown')) {
			showLanguageDropdown = false;
			showUserDropdown = false;
		}
	}

	async function handleLogout() {
		try {
			await api.logout();
			logout();
			showUserDropdown = false;
			window.location.href = '/';
		} catch (error) {
			console.error('Logout failed:', error);
			// Clear local state anyway
			logout();
			window.location.href = '/';
		}
	}

	onMount(() => {
		if (typeof window !== 'undefined') {
			document.addEventListener('click', handleClickOutside);
			return () => document.removeEventListener('click', handleClickOutside);
		}
	});
</script>

<header class="bg-gray-900 shadow-sm border-b border-gray-700">
	<div class="container">
		<div class="flex items-center justify-between h-16">
			<!-- Logo -->
			<div class="flex items-center">
				<a href="/" class="flex items-center space-x-3">
					<img src="/logo.png" alt="GeoML Hub" class="h-12 object-contain" />
					<div class="hidden sm:block">
						<h1 class="text-xl font-bold text-white">
							{$_('app.name')}
						</h1>
						<p class="text-xs text-gray-300">
							{$_('app.description')}
						</p>
					</div>
				</a>
			</div>

			<!-- Right Side Controls -->
			<div class="flex items-center space-x-4">
				<!-- Theme Toggle -->
				<button
					class="flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-md bg-gray-700 hover:bg-gray-600 text-white transition-colors"
					on:click={toggleTheme}
					title="切换主题模式"
				>
					<svelte:component this={currentTheme.icon} class="w-4 h-4" />
					<span class="hidden sm:inline">{currentTheme.label}</span>
				</button>

				<!-- Language Toggle -->
				<div class="relative dropdown">
					<button
						class="flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-md bg-gray-700 hover:bg-gray-600 text-white transition-colors"
						on:click={() => (showLanguageDropdown = !showLanguageDropdown)}
					>
						<Globe class="w-4 h-4" />
						<span class="hidden sm:inline">{currentLanguage.label}</span>
					</button>

					{#if showLanguageDropdown}
						<div
							class="absolute right-0 mt-2 w-40 bg-gray-800 rounded-md shadow-lg ring-1 ring-black ring-opacity-5 z-50"
						>
							<div class="py-1">
								{#each languages as lang}
									<button
										class="flex items-center space-x-3 w-full px-4 py-2 text-sm text-left hover:bg-gray-700 transition-colors text-white {$locale ===
										lang.value
											? 'bg-primary-600 text-white'
											: ''}"
										on:click={() => switchLanguage(lang.value)}
									>
										<span class="text-lg">{lang.flag}</span>
										<span>{lang.label}</span>
									</button>
								{/each}
							</div>
						</div>
					{/if}
				</div>

				<!-- Authentication Section -->
				{#if $isAuthenticated && $user}
					<!-- User Dropdown -->
					<div class="relative dropdown">
						<button
							class="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-700 transition-colors"
							on:click={() => (showUserDropdown = !showUserDropdown)}
						>
							<UserAvatar user={$user} size="sm" />
							<span class="hidden sm:inline text-sm font-medium text-white">{$user.username}</span>
						</button>

						{#if showUserDropdown}
							<div
								class="absolute right-0 mt-2 w-48 bg-gray-800 rounded-md shadow-lg ring-1 ring-black ring-opacity-5 z-50"
							>
								<div class="py-1">
									<a
										href="/{$user.username}"
										class="flex items-center space-x-3 px-4 py-2 text-sm text-white hover:bg-gray-700 transition-colors"
									>
										<User class="w-4 h-4" />
										<span>个人主页</span>
									</a>
									<a
										href="/new"
										class="flex items-center space-x-3 px-4 py-2 text-sm text-white hover:bg-gray-700 transition-colors"
									>
										<Plus class="w-4 h-4" />
										<span>新建仓库</span>
									</a>
									{#if $user.is_admin}
										<a
											href="/admin"
											class="flex items-center space-x-3 px-4 py-2 text-sm text-white hover:bg-gray-700 transition-colors"
										>
											<Settings class="w-4 h-4" />
											<span>管理控制台</span>
										</a>
									{/if}
									<hr class="my-1 border-gray-600" />
									<button
										class="flex items-center space-x-3 w-full px-4 py-2 text-sm text-left text-white hover:bg-gray-700 transition-colors"
										on:click={handleLogout}
									>
										<LogOut class="w-4 h-4" />
										<span>退出登录</span>
									</button>
								</div>
							</div>
						{/if}
					</div>
				{:else}
					<!-- Login/Register Buttons -->
					<div class="flex items-center space-x-2">
						<a
							href="/login"
							class="px-4 py-2 text-sm font-medium text-white hover:text-primary-300 transition-colors"
						>
							登录
						</a>
						<a
							href="/register"
							class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded-md transition-colors"
						>
							注册
						</a>
					</div>
				{/if}

				<!-- Mobile Menu Button -->
				<button
					class="md:hidden p-2 rounded-md text-white hover:bg-gray-700"
					on:click={() => (showMobileMenu = !showMobileMenu)}
				>
					{#if showMobileMenu}
						<X class="w-6 h-6" />
					{:else}
						<Menu class="w-6 h-6" />
					{/if}
				</button>
			</div>
		</div>

		<!-- Mobile Menu -->
		{#if showMobileMenu}
			<div class="md:hidden border-t border-gray-600 py-4">
				<div class="flex flex-col space-y-2">
					{#if $isAuthenticated && $user}
						<a href="/new" class="block px-3 py-2 text-white hover:bg-gray-700 rounded-md">
							新建仓库
						</a>
						{#if $user.is_admin}
							<a href="/admin" class="block px-3 py-2 text-white hover:bg-gray-700 rounded-md">
								管理控制台
							</a>
						{/if}
						<a
							href="/{$user.username}"
							class="block px-3 py-2 text-white hover:bg-gray-700 rounded-md"
						>
							个人主页
						</a>
						<button
							class="block w-full text-left px-3 py-2 text-white hover:bg-gray-700 rounded-md"
							on:click={handleLogout}
						>
							退出登录
						</button>
					{:else}
						<a href="/login" class="block px-3 py-2 text-white hover:bg-gray-700 rounded-md">
							登录
						</a>
						<a
							href="/register"
							class="block px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-md"
						>
							注册
						</a>
					{/if}
				</div>
			</div>
		{/if}
	</div>
</header>
