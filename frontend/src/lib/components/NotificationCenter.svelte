<script>
    import { onMount, createEventDispatcher } from 'svelte';
    import { _ } from 'svelte-i18n';
    import { Bell, X, Check, Star, UserPlus, MessageCircle, Upload, GitFork, Settings } from 'lucide-svelte';
    import { formatDistanceToNow } from 'date-fns';
    import { zhCN } from 'date-fns/locale';
    import { api } from '$lib/utils/api.js';
    import UserAvatar from './UserAvatar.svelte';
    import Loading from './Loading.svelte';
    
    export let isOpen = false;
    export let unreadCount = 0;
    
    const dispatch = createEventDispatcher();
    
    let notifications = [];
    let loading = true;
    let error = '';
    let hasMore = false;
    let page = 1;
    let markingAsRead = false;
    
    onMount(() => {
        if (isOpen) {
            loadNotifications();
        }
    });
    
    $: if (isOpen && notifications.length === 0) {
        loadNotifications();
    }
    
    async function loadNotifications(loadMore = false) {
        if (!loadMore) {
            loading = true;
            page = 1;
        }
        
        error = '';
        
        try {
            const response = await api.getNotifications({
                page,
                limit: 20,
                include_read: true
            });
            
            const newNotifications = response.data || response;
            
            if (loadMore) {
                notifications = [...notifications, ...newNotifications];
            } else {
                notifications = newNotifications;
            }
            
            hasMore = newNotifications.length === 20;
            
        } catch (err) {
            console.error('Failed to load notifications:', err);
            error = $_('error.network_error');
        } finally {
            loading = false;
        }
    }
    
    async function loadMoreNotifications() {
        if (hasMore && !loading) {
            page += 1;
            await loadNotifications(true);
        }
    }
    
    async function markAsRead(notificationId) {
        try {
            await api.markNotificationAsRead(notificationId);
            
            notifications = notifications.map(n => 
                n.id === notificationId ? { ...n, is_read: true } : n
            );
            
            // 更新未读计数
            const newUnreadCount = notifications.filter(n => !n.is_read).length;
            dispatch('unreadCountChange', newUnreadCount);
            
        } catch (err) {
            console.error('Failed to mark notification as read:', err);
        }
    }
    
    async function markAllAsRead() {
        if (markingAsRead) return;
        
        markingAsRead = true;
        
        try {
            await api.markAllNotificationsAsRead();
            
            notifications = notifications.map(n => ({ ...n, is_read: true }));
            dispatch('unreadCountChange', 0);
            
        } catch (err) {
            console.error('Failed to mark all notifications as read:', err);
        } finally {
            markingAsRead = false;
        }
    }
    
    async function deleteNotification(notificationId) {
        try {
            await api.deleteNotification(notificationId);
            notifications = notifications.filter(n => n.id !== notificationId);
        } catch (err) {
            console.error('Failed to delete notification:', err);
        }
    }
    
    function getNotificationIcon(type) {
        switch (type) {
            case 'star':
                return Star;
            case 'follow':
                return UserPlus;
            case 'comment':
                return MessageCircle;
            case 'upload':
                return Upload;
            case 'fork':
                return GitFork;
            default:
                return Bell;
        }
    }
    
    function getNotificationColor(type) {
        switch (type) {
            case 'star':
                return 'text-yellow-500 bg-yellow-50 dark:bg-yellow-900/20';
            case 'follow':
                return 'text-blue-500 bg-blue-50 dark:bg-blue-900/20';
            case 'comment':
                return 'text-green-500 bg-green-50 dark:bg-green-900/20';
            case 'upload':
                return 'text-purple-500 bg-purple-50 dark:bg-purple-900/20';
            case 'fork':
                return 'text-orange-500 bg-orange-50 dark:bg-orange-900/20';
            default:
                return 'text-gray-500 bg-gray-50 dark:bg-gray-900/20';
        }
    }
    
    function getNotificationMessage(notification) {
        const actor = notification.actor?.username || $_('user.unknown');
        
        switch (notification.type) {
            case 'star':
                return $_('notification.starred_your_repository', { 
                    values: { user: actor, repo: notification.target?.name } 
                });
            case 'follow':
                return $_('notification.followed_you', { 
                    values: { user: actor } 
                });
            case 'comment':
                return $_('notification.commented_on_your_repository', { 
                    values: { user: actor, repo: notification.target?.name } 
                });
            case 'upload':
                return $_('notification.uploaded_to_your_repository', { 
                    values: { user: actor, repo: notification.target?.name } 
                });
            case 'fork':
                return $_('notification.forked_your_repository', { 
                    values: { user: actor, repo: notification.target?.name } 
                });
            default:
                return notification.message || $_('notification.unknown');
        }
    }
    
    function getNotificationLink(notification) {
        switch (notification.type) {
            case 'star':
            case 'upload':
            case 'comment':
            case 'fork':
                if (notification.target?.owner && notification.target?.name) {
                    return `/${notification.target.owner.username}/${notification.target.name}`;
                }
                return null;
            case 'follow':
                if (notification.actor?.username) {
                    return `/${notification.actor.username}`;
                }
                return null;
            default:
                return notification.link || null;
        }
    }
    
    function handleNotificationClick(notification) {
        if (!notification.is_read) {
            markAsRead(notification.id);
        }
        
        const link = getNotificationLink(notification);
        if (link) {
            dispatch('navigate', link);
        }
    }
    
    function handleClose() {
        dispatch('close');
    }
</script>

{#if isOpen}
    <!-- 覆盖层 -->
    <div 
        class="fixed inset-0 bg-black bg-opacity-25 dark:bg-opacity-50 z-40"
        role="button"
        tabindex="0"
        on:click={handleClose}
        on:keydown={(e) => e.key === 'Escape' && handleClose()}
    ></div>
    
    <!-- 通知面板 -->
    <div class="fixed top-16 right-4 w-96 max-w-[calc(100vw-2rem)] bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50 max-h-[80vh] flex flex-col">
        <!-- 头部 -->
        <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center space-x-2">
                <Bell class="w-5 h-5 text-gray-600 dark:text-gray-400" />
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                    {$_('notification.notifications')}
                </h3>
                {#if unreadCount > 0}
                    <span class="bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                        {unreadCount > 99 ? '99+' : unreadCount}
                    </span>
                {/if}
            </div>
            
            <div class="flex items-center space-x-2">
                {#if notifications.some(n => !n.is_read)}
                    <button
                        on:click={markAllAsRead}
                        disabled={markingAsRead}
                        class="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 flex items-center space-x-1"
                    >
                        {#if markingAsRead}
                            <div class="animate-spin rounded-full h-3 w-3 border-b-2 border-current"></div>
                        {:else}
                            <Check class="w-3 h-3" />
                        {/if}
                        <span>{$_('notification.mark_all_read')}</span>
                    </button>
                {/if}
                
                <button
                    on:click={handleClose}
                    class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                    <X class="w-5 h-5" />
                </button>
            </div>
        </div>
        
        <!-- 通知列表 -->
        <div class="flex-1 overflow-y-auto">
            {#if loading && notifications.length === 0}
                <div class="flex justify-center py-8">
                    <Loading />
                </div>
            {:else if error && notifications.length === 0}
                <div class="p-4 text-center">
                    <p class="text-red-600 dark:text-red-400">{error}</p>
                </div>
            {:else if notifications.length > 0}
                <div class="divide-y divide-gray-100 dark:divide-gray-700">
                    {#each notifications as notification}
                        {@const Icon = getNotificationIcon(notification.type)}
                        {@const colorClasses = getNotificationColor(notification.type)}
                        {@const message = getNotificationMessage(notification)}
                        {@const link = getNotificationLink(notification)}
                        
                        <div 
                            class="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer relative {!notification.is_read ? 'bg-blue-50 dark:bg-blue-900/20' : ''}"
                            role="button"
                            tabindex="0"
                            on:click={() => handleNotificationClick(notification)}
                            on:keydown={(e) => e.key === 'Enter' && handleNotificationClick(notification)}
                        >
                            <!-- 未读指示器 -->
                            {#if !notification.is_read}
                                <div class="absolute left-2 top-1/2 transform -translate-y-1/2 w-2 h-2 bg-blue-500 rounded-full"></div>
                            {/if}
                            
                            <div class="flex items-start space-x-3 {!notification.is_read ? 'ml-4' : ''}">
                                <!-- 通知图标 -->
                                <div class="flex-shrink-0">
                                    <div class="w-8 h-8 rounded-full flex items-center justify-center {colorClasses}">
                                        <Icon class="w-4 h-4" />
                                    </div>
                                </div>
                                
                                <!-- 通知内容 -->
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center space-x-2 mb-1">
                                        {#if notification.actor}
                                            <UserAvatar user={notification.actor} size="xs" />
                                        {/if}
                                        <p class="text-sm text-gray-900 dark:text-white line-clamp-2">
                                            {message}
                                        </p>
                                    </div>
                                    
                                    <!-- 通知描述 -->
                                    {#if notification.description}
                                        <p class="text-xs text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                                            {notification.description}
                                        </p>
                                    {/if}
                                    
                                    <!-- 时间戳 -->
                                    <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
                                        {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true, locale: zhCN })}
                                    </p>
                                </div>
                                
                                <!-- 操作按钮 -->
                                <div class="flex-shrink-0">
                                    <button
                                        on:click|stopPropagation={() => deleteNotification(notification.id)}
                                        class="text-gray-400 hover:text-red-500 p-1"
                                        title={$_('common.delete')}
                                    >
                                        <X class="w-3 h-3" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    {/each}
                </div>
                
                <!-- 加载更多 -->
                {#if hasMore}
                    <div class="p-4 border-t border-gray-200 dark:border-gray-700">
                        <button
                            on:click={loadMoreNotifications}
                            disabled={loading}
                            class="w-full text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 flex items-center justify-center space-x-2"
                        >
                            {#if loading}
                                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                            {/if}
                            <span>{$_('common.load_more')}</span>
                        </button>
                    </div>
                {/if}
            {:else}
                <!-- 无通知状态 -->
                <div class="text-center py-12">
                    <Bell class="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        {$_('notification.no_notifications')}
                    </h3>
                    <p class="text-gray-500 dark:text-gray-400">
                        {$_('notification.no_notifications_hint')}
                    </p>
                </div>
            {/if}
        </div>
        
        <!-- 底部设置 -->
        <div class="border-t border-gray-200 dark:border-gray-700 p-4">
            <a 
                href="/settings/notifications" 
                class="text-sm text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 flex items-center space-x-2"
            >
                <Settings class="w-4 h-4" />
                <span>{$_('notification.settings')}</span>
            </a>
        </div>
    </div>
{/if}

<style>
    .line-clamp-2 {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
</style>