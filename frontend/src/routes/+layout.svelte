<script>
  import '../app.css';
  import '$lib/i18n';
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { waitLocale } from 'svelte-i18n';
  import { theme, setTheme } from '$lib/stores/theme.js';
  import { authToken, user, isAuthenticated } from '$lib/stores/auth.js';
  import { authApi } from '$lib/utils/api.js';
  import Header from '$lib/components/Header.svelte';
  import Footer from '$lib/components/Footer.svelte';
  import ToastContainer from '$lib/components/ToastContainer.svelte';

  let localeReady = false;

  // 主题应用函数
  function applyTheme(newTheme) {
    setTheme(newTheme);
    updateDarkClass(newTheme);
  }

  // 更新dark类名
  function updateDarkClass(currentTheme) {
    if (browser) {
      const html = document.documentElement;
      if (currentTheme === 'dark') {
        html.classList.add('dark');
      } else if (currentTheme === 'light') {
        html.classList.remove('dark');
      } else if (currentTheme === 'system') {
        // 系统主题
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (prefersDark) {
          html.classList.add('dark');
        } else {
          html.classList.remove('dark');
        }
      }
    }
  }

  onMount(async () => {
    await waitLocale();
    localeReady = true;
    
    // 初始化主题
    updateDarkClass($theme);
    
    // 监听系统主题变化
    if (browser) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleSystemThemeChange = () => {
        if ($theme === 'system') {
          updateDarkClass('system');
        }
      };
      mediaQuery.addEventListener('change', handleSystemThemeChange);
      
      // 清理函数
      return () => mediaQuery.removeEventListener('change', handleSystemThemeChange);
    }
    
    // 验证已存储的认证信息
    if (browser && $authToken) {
      try {
        const response = await authApi.getCurrentUser();
        if (response.success) {
          // 用户信息仍然有效，更新store
          user.set(response.data);
          isAuthenticated.set(true);
          console.log('User authenticated:', response.data.username);
        } else {
          // Token无效，清除认证信息
          authApi.clearToken();
        }
      } catch (error) {
        console.error('Auth verification failed:', error);
        authApi.clearToken();
      }
    }
  });

  // 响应式更新主题
  $: if (browser && localeReady) {
    updateDarkClass($theme);
  }
</script>

{#if localeReady}
  <div class="min-h-screen flex flex-col">
    <Header theme={$theme} {applyTheme} />
    
    <main class="flex-1">
      <slot />
    </main>
    
    <Footer />
    
    <!-- Global Toast Container -->
    <ToastContainer />
  </div>
{:else}
  <div class="min-h-screen flex items-center justify-center">
    <div class="text-center">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
      <p class="text-gray-600">Loading...</p>
    </div>
  </div>
{/if}