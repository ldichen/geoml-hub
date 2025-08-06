<script>
    import { onMount, onDestroy } from 'svelte';
    import { goto } from '$app/navigation';
    import { Bell } from 'lucide-svelte';
    import { api } from '$lib/utils/api.js';
    import { user } from '$lib/stores/auth.js';
    import NotificationCenter from './NotificationCenter.svelte';
    
    let isOpen = false;
    let unreadCount = 0;
    let polling = false;
    let pollInterval;
    
    onMount(() => {
        if ($user) {
            loadUnreadCount();
            startPolling();
        }
    });
    
    onDestroy(() => {
        stopPolling();
    });
    
    // 监听用户状态变化
    $: if ($user) {
        loadUnreadCount();
        startPolling();
    } else {
        unreadCount = 0;
        stopPolling();
    }
    
    async function loadUnreadCount() {
        if (!$user) return;
        
        try {
            const response = await api.getUnreadNotificationsCount();
            unreadCount = response.count || 0;
        } catch (err) {
            console.error('Failed to load unread count:', err);
        }
    }
    
    function startPolling() {
        if (polling || !$user) return;
        
        polling = true;
        pollInterval = setInterval(() => {
            loadUnreadCount();
        }, 30000); // 每30秒检查一次
    }
    
    function stopPolling() {
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
        polling = false;
    }
    
    function toggleNotifications() {
        if (!$user) {
            goto('/login');
            return;
        }
        
        isOpen = !isOpen;
    }
    
    function handleClose() {
        isOpen = false;
    }
    
    function handleNavigate(event) {
        const path = event.detail;
        isOpen = false;
        goto(path);
    }
    
    function handleUnreadCountChange(event) {
        unreadCount = event.detail;
    }
</script>

<div class="relative">
    <!-- 通知触发按钮 -->
    <button
        on:click={toggleNotifications}
        class="relative p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
        class:text-primary-600={isOpen}
        class:dark:text-primary-400={isOpen}
        aria-label="通知"
    >
        <Bell class="w-5 h-5" />
        
        <!-- 未读计数徽章 -->
        {#if unreadCount > 0}
            <span class="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full min-w-[1.25rem] h-5 flex items-center justify-center px-1">
                {unreadCount > 99 ? '99+' : unreadCount}
            </span>
        {/if}
    </button>
    
    <!-- 通知中心 -->
    <NotificationCenter
        {isOpen}
        {unreadCount}
        on:close={handleClose}
        on:navigate={handleNavigate}
        on:unreadCountChange={handleUnreadCountChange}
    />
</div>