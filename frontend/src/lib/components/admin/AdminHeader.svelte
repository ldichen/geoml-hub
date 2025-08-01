<script>
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { api } from '$lib/utils/api.js';

    export let user = null;
    
    async function handleLogout() {
        try {
            await api.auth.logout();
            await goto('/');
        } catch (err) {
            console.error('Logout error:', err);
        }
    }

    function getInitials(name) {
        if (!name) return 'A';
        return name.split(' ').map(word => word[0]).join('').toUpperCase().slice(0, 2);
    }
</script>

<header class="bg-white shadow-sm border-b border-gray-200">
    <div class="flex items-center justify-between h-16 px-6">
        <div class="flex items-center">
            <h1 class="text-2xl font-bold text-gray-800">GeoML-Hub 管理后台</h1>
        </div>
        
        <div class="flex items-center space-x-4">
            <!-- 通知按钮 -->
            <button class="p-2 text-gray-400 hover:text-gray-600 transition-colors">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
                </svg>
            </button>
            
            <!-- 用户菜单 -->
            <div class="flex items-center space-x-3">
                <div class="flex items-center">
                    <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                        {getInitials(user?.full_name || user?.username)}
                    </div>
                    <div class="ml-3">
                        <div class="text-sm font-medium text-gray-900">
                            {user?.full_name || user?.username}
                        </div>
                        <div class="text-xs text-gray-500">管理员</div>
                    </div>
                </div>
                
                <button 
                    on:click={handleLogout}
                    class="text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded px-3 py-1 hover:bg-gray-50 transition-colors"
                >
                    退出
                </button>
            </div>
        </div>
    </div>
</header>