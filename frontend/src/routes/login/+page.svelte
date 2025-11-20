<script>
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { login as authLogin, isLoading } from '$lib/stores/auth.js';
    import { redirectIfAuthenticated } from '$lib/utils/auth.js';
    import { api } from '$lib/utils/api.js';
    import { PATHS } from '$lib/utils/paths.js';
    import { _ } from 'svelte-i18n';
    
    let email = '';
    let password = '';
    let error = '';
    let loading = false;
    
    onMount(() => {
        // 如果已登录，重定向到首页
        redirectIfAuthenticated(PATHS.HOME);
    });
    
    async function handleLogin() {
        if (!email || !password) {
            error = 'Please fill in all fields';
            return;
        }
        
        loading = true;
        error = '';
        
        try {
            // 使用OpenGMS用户服务器登录
            const response = await api.loginWithCredentials(email, password);
            
            if (response.success) {
                // 登录成功，保存token和用户信息
                authLogin(response.data.access_token, response.data.user, response.data.refresh_token);

                // 重定向到原来想访问的页面或首页
                const redirectTo = new URLSearchParams(window.location.search).get('redirect') || PATHS.HOME;
                goto(redirectTo);
            } else {
                error = response.error || 'Login failed';
            }
        } catch (err) {
            console.error('Login error:', err);
            error = 'Network error or login failed';
        } finally {
            loading = false;
        }
    }
    
    function handleKeyPress(event) {
        if (event.key === 'Enter') {
            handleLogin();
        }
    }
</script>

<svelte:head>
    <title>{$_('auth.login')} - GeoML-Hub</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center px-4">
    <div class="max-w-md w-full space-y-8">
        <!-- Logo和标题 -->
        <div class="text-center">
            <div class="mx-auto h-12 w-12 bg-primary-600 rounded-lg flex items-center justify-center">
                <svg class="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
            </div>
            <h2 class="mt-6 text-3xl font-bold text-gray-900 dark:text-white">
                {$_('auth.welcome_back')}
            </h2>
            <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
                {$_('auth.login_subtitle')}
            </p>
        </div>

        <!-- 登录表单 -->
        <div class="bg-white dark:bg-gray-800 py-8 px-4 shadow-xl rounded-lg sm:px-10">
            <form class="space-y-6" on:submit|preventDefault={handleLogin}>
                <!-- 邮箱输入 -->
                <div>
                    <label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        {$_('auth.email')}
                    </label>
                    <div class="mt-1">
                        <input
                            id="email"
                            name="email"
                            type="email"
                            autocomplete="email"
                            required
                            bind:value={email}
                            on:keypress={handleKeyPress}
                            class="input w-full"
                            placeholder={$_('auth.email_placeholder')}
                            disabled={loading}
                        />
                    </div>
                </div>

                <!-- 密码输入 -->
                <div>
                    <label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        {$_('auth.password')}
                    </label>
                    <div class="mt-1">
                        <input
                            id="password"
                            name="password"
                            type="password"
                            autocomplete="current-password"
                            required
                            bind:value={password}
                            on:keypress={handleKeyPress}
                            class="input w-full"
                            placeholder={$_('auth.password_placeholder')}
                            disabled={loading}
                        />
                    </div>
                </div>

                <!-- 错误提示 -->
                {#if error}
                    <div class="rounded-md bg-red-50 dark:bg-red-900/20 p-4">
                        <div class="flex">
                            <div class="flex-shrink-0">
                                <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                                </svg>
                            </div>
                            <div class="ml-3">
                                <p class="text-sm text-red-800 dark:text-red-200">{error}</p>
                            </div>
                        </div>
                    </div>
                {/if}

                <!-- 登录按钮 -->
                <div>
                    <button
                        type="submit"
                        disabled={loading}
                        class="btn btn-primary w-full flex justify-center items-center"
                    >
                        {#if loading}
                            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            {$_('auth.logging_in')}
                        {:else}
                            {$_('auth.login')}
                        {/if}
                    </button>
                </div>

                <!-- 其他选项 -->
                <div class="flex items-center justify-between">
                    <div class="text-sm">
                        <a href="{PATHS.HOME}/forgot-password" class="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400">
                            {$_('auth.forgot_password')}
                        </a>
                    </div>
                </div>
            </form>

            <!-- 注册链接 -->
            <div class="mt-6">
                <div class="relative">
                    <div class="absolute inset-0 flex items-center">
                        <div class="w-full border-t border-gray-300 dark:border-gray-600" />
                    </div>
                    <div class="relative flex justify-center text-sm">
                        <span class="px-2 bg-white dark:bg-gray-800 text-gray-500">
                            {$_('auth.or')}
                        </span>
                    </div>
                </div>

                <div class="mt-6 text-center">
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                        {$_('auth.no_account')}
                        <a href={PATHS.REGISTER} class="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400">
                            {$_('auth.sign_up')}
                        </a>
                    </p>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
    :global(body) {
        overflow-x: hidden;
    }
</style>