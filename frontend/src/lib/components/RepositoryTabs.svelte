<script>
    import { createEventDispatcher } from 'svelte';
    import { _ } from 'svelte-i18n';
    import { FileText, Folder, GitCommit, Settings, BarChart3 } from 'lucide-svelte';
    import { isOwner } from '$lib/utils/auth.js';
    import { user as currentUser } from '$lib/stores/auth.js';
    
    export let activeTab = 'code';
    export let repository;
    
    const dispatch = createEventDispatcher();
    
    $: isRepoOwner = $currentUser && repository && isOwner(repository.owner?.username || repository.owner?.id);
    
    function handleTabClick(tab) {
        if (tab !== activeTab) {
            dispatch('tabChange', tab);
        }
    }
    
    const tabs = [
        {
            id: 'code',
            label: 'repository.code',
            icon: FileText,
            count: null,
            show: true
        },
        {
            id: 'files',
            label: 'file.files',
            icon: Folder,
            count: 'total_files',
            show: true
        },
        {
            id: 'commits',
            label: 'repository.commits',
            icon: GitCommit,
            count: 'commits_count',
            show: true
        },
        {
            id: 'analytics',
            label: 'admin.analytics',
            icon: BarChart3,
            count: null,
            show: true
        },
        {
            id: 'settings',
            label: 'repository.settings',
            icon: Settings,
            count: null,
            show: false // 仅所有者可见
        }
    ];
    
    $: visibleTabs = tabs.filter(tab => tab.show || (tab.id === 'settings' && isRepoOwner));
</script>

<div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
    <div class="border-b border-gray-200 dark:border-gray-700">
        <nav class="flex space-x-8 px-6" aria-label="Tabs">
            {#each visibleTabs as tab}
                <button
                    class="py-4 px-1 border-b-2 font-medium text-sm flex items-center transition-colors {activeTab === tab.id 
                        ? 'border-primary-500 text-primary-600 dark:text-primary-400' 
                        : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
                    on:click={() => handleTabClick(tab.id)}
                >
                    <svelte:component this={tab.icon} class="h-4 w-4 mr-2" />
                    {$_(tab.label)}
                    {#if tab.count && repository[tab.count] !== undefined}
                        <span class="ml-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 py-0.5 px-2 rounded-full text-xs">
                            {repository[tab.count]}
                        </span>
                    {/if}
                </button>
            {/each}
        </nav>
    </div>
</div>