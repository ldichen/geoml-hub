<script>
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { login as authLogin } from '$lib/stores/auth.js';
    import { redirectIfAuthenticated } from '$lib/utils/auth.js';
    import { api } from '$lib/utils/api.js';
    import { _ } from 'svelte-i18n';
    
    let formData = {
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        full_name: '',
        bio: '',
        website: '',
        location: ''
    };
    
    let error = '';
    let loading = false;
    let step = 1; // 1: 基础信息, 2: 详细信息
    
    onMount(() => {
        // 如果已登录，重定向到首页
        redirectIfAuthenticated('/');
    });
    
    function validateStep1() {
        const { username, email, password, confirmPassword } = formData;
        
        if (!username || !email || !password || !confirmPassword) {
            error = $_('auth.please_fill_required_fields');
            return false;
        }
        
        if (username.length < 3) {
            error = $_('auth.username_too_short');
            return false;
        }
        
        if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
            error = $_('auth.username_invalid_chars');
            return false;
        }
        
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            error = $_('auth.email_invalid');
            return false;
        }
        
        if (password.length < 8) {
            error = $_('auth.password_too_short');
            return false;
        }
        
        if (password !== confirmPassword) {
            error = $_('auth.passwords_not_match');
            return false;
        }
        
        error = '';
        return true;
    }
    
    function nextStep() {
        if (validateStep1()) {
            step = 2;
        }
    }
    
    function prevStep() {
        step = 1;
        error = '';
    }
    
    async function handleRegister() {
        if (!validateStep1()) return;
        
        loading = true;
        error = '';
        
        try {
            // 使用新的OpenGMS注册API
            const response = await api.register(
                formData.email,
                formData.password,
                formData.username,
                formData.full_name || formData.username
            );
            
            if (response.success) {
                // 注册成功，自动登录
                authLogin(response.data.access_token, response.data.user);
                goto('/');
            } else {
                error = response.error || $_('auth.registration_failed');
            }
        } catch (err) {
            console.error('Registration error:', err);
            error = $_('auth.network_error');
        } finally {
            loading = false;
        }
    }
</script>

<svelte:head>
    <title>{$_('auth.sign_up')} - GeoML-Hub</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center px-4 py-12">
    <div class="max-w-md w-full space-y-8">
        <!-- Logo和标题 -->
        <div class="text-center">
            <div class="mx-auto h-12 w-12 bg-primary-600 rounded-lg flex items-center justify-center">
                <svg class="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
            </div>
            <h2 class="mt-6 text-3xl font-bold text-gray-900 dark:text-white">
                {$_('auth.create_account')}
            </h2>
            <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
                {$_('auth.register_subtitle')}
            </p>
        </div>

        <!-- 进度指示器 -->
        <div class="flex items-center justify-center space-x-4">
            <div class="flex items-center">
                <div class="flex items-center justify-center w-8 h-8 rounded-full {step >= 1 ? 'bg-primary-600' : 'bg-gray-300'} text-white text-sm font-medium">
                    1
                </div>
                <span class="ml-2 text-sm {step >= 1 ? 'text-primary-600' : 'text-gray-500'}">{$_('auth.basic_info')}</span>
            </div>
            <div class="w-8 h-px {step >= 2 ? 'bg-primary-600' : 'bg-gray-300'}"></div>
            <div class="flex items-center">
                <div class="flex items-center justify-center w-8 h-8 rounded-full {step >= 2 ? 'bg-primary-600' : 'bg-gray-300'} text-white text-sm font-medium">
                    2
                </div>
                <span class="ml-2 text-sm {step >= 2 ? 'text-primary-600' : 'text-gray-500'}">{$_('auth.profile_info')}</span>
            </div>
        </div>

        <!-- 注册表单 -->
        <div class="bg-white dark:bg-gray-800 py-8 px-4 shadow-xl rounded-lg sm:px-10">
            <form class="space-y-6" on:submit|preventDefault={step === 1 ? nextStep : handleRegister}>
                {#if step === 1}
                    <!-- 第一步：基础信息 -->
                    <div class="space-y-6">
                        <!-- 用户名 -->
                        <div>
                            <label for="username" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                {$_('auth.username')} <span class="text-red-500">*</span>
                            </label>
                            <div class="mt-1">
                                <input
                                    id="username"
                                    name="username"
                                    type="text"
                                    required
                                    bind:value={formData.username}
                                    class="input w-full"
                                    placeholder={$_('auth.username_placeholder')}
                                />
                            </div>
                            <p class="mt-1 text-xs text-gray-500">
                                {$_('auth.username_hint')}
                            </p>
                        </div>

                        <!-- 邮箱 -->
                        <div>
                            <label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                {$_('auth.email')} <span class="text-red-500">*</span>
                            </label>
                            <div class="mt-1">
                                <input
                                    id="email"
                                    name="email"
                                    type="email"
                                    required
                                    bind:value={formData.email}
                                    class="input w-full"
                                    placeholder={$_('auth.email_placeholder')}
                                />
                            </div>
                        </div>

                        <!-- 密码 -->
                        <div>
                            <label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                {$_('auth.password')} <span class="text-red-500">*</span>
                            </label>
                            <div class="mt-1">
                                <input
                                    id="password"
                                    name="password"
                                    type="password"
                                    required
                                    bind:value={formData.password}
                                    class="input w-full"
                                    placeholder={$_('auth.password_placeholder')}
                                />
                            </div>
                            <p class="mt-1 text-xs text-gray-500">
                                {$_('auth.password_hint')}
                            </p>
                        </div>

                        <!-- 确认密码 -->
                        <div>
                            <label for="confirmPassword" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                {$_('auth.confirm_password')} <span class="text-red-500">*</span>
                            </label>
                            <div class="mt-1">
                                <input
                                    id="confirmPassword"
                                    name="confirmPassword"
                                    type="password"
                                    required
                                    bind:value={formData.confirmPassword}
                                    class="input w-full"
                                    placeholder={$_('auth.confirm_password_placeholder')}
                                />
                            </div>
                        </div>
                    </div>
                {/if}

                {#if step === 2}
                    <!-- 第二步：详细信息 -->
                    <div class="space-y-6">
                        <!-- 真实姓名 -->
                        <div>
                            <label for="full_name" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                {$_('auth.full_name')}
                            </label>
                            <div class="mt-1">
                                <input
                                    id="full_name"
                                    name="full_name"
                                    type="text"
                                    bind:value={formData.full_name}
                                    class="input w-full"
                                    placeholder={$_('auth.full_name_placeholder')}
                                />
                            </div>
                        </div>

                        <!-- 个人简介 -->
                        <div>
                            <label for="bio" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                {$_('auth.bio')}
                            </label>
                            <div class="mt-1">
                                <textarea
                                    id="bio"
                                    name="bio"
                                    rows="3"
                                    bind:value={formData.bio}
                                    class="input w-full resize-none"
                                    placeholder={$_('auth.bio_placeholder')}
                                ></textarea>
                            </div>
                        </div>

                        <!-- 个人网站 -->
                        <div>
                            <label for="website" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                {$_('auth.website')}
                            </label>
                            <div class="mt-1">
                                <input
                                    id="website"
                                    name="website"
                                    type="url"
                                    bind:value={formData.website}
                                    class="input w-full"
                                    placeholder={$_('auth.website_placeholder')}
                                />
                            </div>
                        </div>

                        <!-- 所在地 -->
                        <div>
                            <label for="location" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                {$_('auth.location')}
                            </label>
                            <div class="mt-1">
                                <input
                                    id="location"
                                    name="location"
                                    type="text"
                                    bind:value={formData.location}
                                    class="input w-full"
                                    placeholder={$_('auth.location_placeholder')}
                                />
                            </div>
                        </div>
                    </div>
                {/if}

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

                <!-- 按钮组 -->
                <div class="flex space-x-4">
                    {#if step === 2}
                        <button
                            type="button"
                            on:click={prevStep}
                            class="btn btn-secondary flex-1"
                        >
                            {$_('common.previous')}
                        </button>
                    {/if}
                    
                    <button
                        type="submit"
                        disabled={loading}
                        class="btn btn-primary flex-1 flex justify-center items-center"
                    >
                        {#if loading}
                            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            {$_('auth.creating_account')}
                        {:else if step === 1}
                            {$_('common.next')}
                        {:else}
                            {$_('auth.create_account')}
                        {/if}
                    </button>
                </div>
            </form>

            <!-- 登录链接 -->
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
                        {$_('auth.already_have_account')}
                        <a href="/login" class="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400">
                            {$_('auth.login')}
                        </a>
                    </p>
                </div>
            </div>
        </div>
    </div>
</div>