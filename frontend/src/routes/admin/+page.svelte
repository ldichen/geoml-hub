<script>
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { PATHS } from '$lib/utils/paths.js';

    onMount(() => {
        // 管理员首页重定向到仪表板
        goto(`${PATHS.ADMIN}/dashboard`);
    });
</script>

<div class="flex items-center justify-center min-h-screen">
    <div class="text-center">
        <div class="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <p class="text-gray-600">正在跳转到管理员仪表板...</p>
    </div>
</div>