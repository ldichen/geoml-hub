<script>
    import { _ } from 'svelte-i18n';
    import { Star, Download, Eye, GitFork, Users, TrendingUp } from 'lucide-svelte';
    
    export let repository;
    
    const stats = [
        {
            label: 'repository.stars',
            value: repository.stars_count || 0,
            icon: Star,
            color: 'text-yellow-500',
            bg: 'bg-yellow-50 dark:bg-yellow-900/20'
        },
        {
            label: 'repository.downloads',
            value: repository.downloads_count || 0,
            icon: Download,
            color: 'text-green-500',
            bg: 'bg-green-50 dark:bg-green-900/20'
        },
        {
            label: 'repository.views',
            value: repository.views_count || 0,
            icon: Eye,
            color: 'text-blue-500',
            bg: 'bg-blue-50 dark:bg-blue-900/20'
        },
        {
            label: 'repository.forks',
            value: repository.forks_count || 0,
            icon: GitFork,
            color: 'text-purple-500',
            bg: 'bg-purple-50 dark:bg-purple-900/20'
        }
    ];
    
    function formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
</script>

<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
    {#each stats as stat}
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4">
            <div class="flex items-center">
                <div class="flex-shrink-0">
                    <div class="w-8 h-8 {stat.bg} rounded-full flex items-center justify-center">
                        <svelte:component this={stat.icon} class="w-4 h-4 {stat.color}" />
                    </div>
                </div>
                <div class="ml-3 flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                        {$_(stat.label)}
                    </p>
                    <p class="text-lg font-semibold text-gray-900 dark:text-white">
                        {formatNumber(stat.value)}
                    </p>
                </div>
            </div>
        </div>
    {/each}
</div>

<!-- 趋势图表区域 (可选) -->
{#if repository.analytics_enabled}
    <div class="mt-6 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
        <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                <TrendingUp class="w-5 h-5 mr-2 text-green-500" />
                {$_('admin.analytics')}
            </h3>
            <button class="text-sm text-primary-600 dark:text-primary-400 hover:underline">
                {$_('common.view')} {$_('admin.analytics')}
            </button>
        </div>
        
        <div class="text-center py-8 text-gray-500 dark:text-gray-400">
            <TrendingUp class="w-8 h-8 mx-auto mb-2 text-gray-300" />
            <p class="text-sm">{$_('admin.analytics')} {$_('common.coming_soon')}</p>
        </div>
    </div>
{/if}