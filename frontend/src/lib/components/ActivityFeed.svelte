<script>
    import { onMount } from 'svelte';
    import { _ } from 'svelte-i18n';
    import { Star, GitFork, Upload, UserPlus, MessageCircle, Eye, Download } from 'lucide-svelte';
    import { formatDistanceToNow } from 'date-fns';
    import { zhCN } from 'date-fns/locale';
    import { api } from '$lib/utils/api.js';
    import UserAvatar from './UserAvatar.svelte';
    import Loading from './Loading.svelte';
    
    export let userId = null; // 特定用户的活动，null表示全局活动
    export let limit = 20;
    export let showTypes = ['star', 'fork', 'upload', 'follow', 'comment', 'create_repo'];
    
    let activities = [];
    let loading = true;
    let error = '';
    let hasMore = false;
    let page = 1;
    
    onMount(() => {
        loadActivities();
    });
    
    async function loadActivities(loadMore = false) {
        if (!loadMore) {
            loading = true;
            page = 1;
        }
        
        error = '';
        
        try {
            const response = await api.activities.list({
                user_id: userId,
                types: showTypes.join(','),
                page,
                limit
            });
            
            const newActivities = response.data || response;
            
            if (loadMore) {
                activities = [...activities, ...newActivities];
            } else {
                activities = newActivities;
            }
            
            hasMore = newActivities.length === limit;
            
        } catch (err) {
            console.error('Failed to load activities:', err);
            error = $_('error.network_error');
        } finally {
            loading = false;
        }
    }
    
    async function loadMore() {
        if (hasMore && !loading) {
            page += 1;
            await loadActivities(true);
        }
    }
    
    function getActivityIcon(type) {
        switch (type) {
            case 'star':
                return Star;
            case 'fork':
                return GitFork;
            case 'upload':
                return Upload;
            case 'follow':
                return UserPlus;
            case 'comment':
                return MessageCircle;
            case 'view':
                return Eye;
            case 'download':
                return Download;
            default:
                return Star;
        }
    }
    
    function getActivityColor(type) {
        switch (type) {
            case 'star':
                return 'text-yellow-500 bg-yellow-50 dark:bg-yellow-900/20';
            case 'fork':
                return 'text-blue-500 bg-blue-50 dark:bg-blue-900/20';
            case 'upload':
                return 'text-green-500 bg-green-50 dark:bg-green-900/20';
            case 'follow':
                return 'text-purple-500 bg-purple-50 dark:bg-purple-900/20';
            case 'comment':
                return 'text-indigo-500 bg-indigo-50 dark:bg-indigo-900/20';
            case 'view':
                return 'text-gray-500 bg-gray-50 dark:bg-gray-900/20';
            case 'download':
                return 'text-orange-500 bg-orange-50 dark:bg-orange-900/20';
            default:
                return 'text-gray-500 bg-gray-50 dark:bg-gray-900/20';
        }
    }
    
    function getActivityMessage(activity) {
        const actor = activity.actor?.username || $_('user.unknown');
        
        switch (activity.type) {
            case 'star':
                return $_('activity.starred_repository', { 
                    values: { user: actor, repo: activity.target?.name } 
                });
            case 'fork':
                return $_('activity.forked_repository', { 
                    values: { user: actor, repo: activity.target?.name } 
                });
            case 'upload':
                return $_('activity.uploaded_to_repository', { 
                    values: { user: actor, repo: activity.target?.name } 
                });
            case 'follow':
                return $_('activity.followed_user', { 
                    values: { user: actor, target: activity.target?.username } 
                });
            case 'comment':
                return $_('activity.commented_on_repository', { 
                    values: { user: actor, repo: activity.target?.name } 
                });
            case 'create_repo':
                return $_('activity.created_repository', { 
                    values: { user: actor, repo: activity.target?.name } 
                });
            case 'view':
                return $_('activity.viewed_repository', { 
                    values: { user: actor, repo: activity.target?.name } 
                });
            case 'download':
                return $_('activity.downloaded_from_repository', { 
                    values: { user: actor, repo: activity.target?.name } 
                });
            default:
                return $_('activity.unknown_activity');
        }
    }
    
    function getActivityLink(activity) {
        switch (activity.type) {
            case 'star':
            case 'fork':
            case 'upload':
            case 'comment':
            case 'view':
            case 'download':
            case 'create_repo':
                if (activity.target?.owner && activity.target?.name) {
                    return `/${activity.target.owner.username}/${activity.target.name}`;
                }
                return null;
            case 'follow':
                if (activity.target?.username) {
                    return `/${activity.target.username}`;
                }
                return null;
            default:
                return null;
        }
    }
</script>

<div class="activity-feed">
    {#if loading && activities.length === 0}
        <div class="flex justify-center py-8">
            <Loading />
        </div>
    {:else if error && activities.length === 0}
        <div class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p class="text-red-800 dark:text-red-200">{error}</p>
        </div>
    {:else if activities.length > 0}
        <div class="space-y-4">
            {#each activities as activity}
                {@const Icon = getActivityIcon(activity.type)}
                {@const colorClasses = getActivityColor(activity.type)}
                {@const message = getActivityMessage(activity)}
                {@const link = getActivityLink(activity)}
                
                <div class="flex items-start space-x-3 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow">
                    <!-- 活动图标 -->
                    <div class="flex-shrink-0">
                        <div class="w-8 h-8 rounded-full flex items-center justify-center {colorClasses}">
                            <Icon class="w-4 h-4" />
                        </div>
                    </div>
                    
                    <!-- 活动内容 -->
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center space-x-2 mb-1">
                            <UserAvatar user={activity.actor} size="xs" />
                            <div class="flex-1 min-w-0">
                                {#if link}
                                    <a href={link} class="text-sm text-gray-900 dark:text-white hover:text-primary-600 dark:hover:text-primary-400">
                                        {message}
                                    </a>
                                {:else}
                                    <span class="text-sm text-gray-900 dark:text-white">
                                        {message}
                                    </span>
                                {/if}
                            </div>
                        </div>
                        
                        <!-- 活动描述 -->
                        {#if activity.description}
                            <p class="text-xs text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                                {activity.description}
                            </p>
                        {/if}
                        
                        <!-- 时间戳 -->
                        <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
                            {formatDistanceToNow(new Date(activity.created_at), { addSuffix: true, locale: zhCN })}
                        </p>
                    </div>
                </div>
            {/each}
        </div>
        
        <!-- 加载更多 -->
        {#if hasMore}
            <div class="text-center mt-6">
                <button
                    on:click={loadMore}
                    disabled={loading}
                    class="btn btn-secondary flex items-center mx-auto"
                >
                    {#if loading}
                        <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                    {/if}
                    {$_('common.load_more')}
                </button>
            </div>
        {/if}
    {:else}
        <!-- 无活动状态 -->
        <div class="text-center py-12">
            <div class="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <MessageCircle class="w-8 h-8 text-gray-400" />
            </div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {$_('activity.no_activities')}
            </h3>
            <p class="text-gray-500 dark:text-gray-400">
                {userId ? $_('activity.no_user_activities') : $_('activity.no_global_activities')}
            </p>
        </div>
    {/if}
</div>

<style>
    .line-clamp-2 {
        display: -webkit-box;
        -webkit-line-clamp: 2;
        line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
</style>