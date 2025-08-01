<script>
    export let title = '';
    export let value = '';
    export let icon = 'default';
    export let description = '';
    export let color = 'blue';
    export let trend = null; // 'up', 'down', 'neutral'
    export let trendValue = '';

    function getIconPath(iconName) {
        const icons = {
            users: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z',
            repositories: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
            storage: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4',
            activity: 'M13 10V3L4 14h7v7l9-11h-7z',
            default: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
        };
        return icons[iconName] || icons.default;
    }

    function getColorClasses(colorName) {
        const colors = {
            blue: 'bg-blue-100 text-blue-600',
            green: 'bg-green-100 text-green-600',
            yellow: 'bg-yellow-100 text-yellow-600',
            purple: 'bg-purple-100 text-purple-600',
            red: 'bg-red-100 text-red-600',
            gray: 'bg-gray-100 text-gray-600'
        };
        return colors[colorName] || colors.blue;
    }

    function getTrendIcon(trendType) {
        switch (trendType) {
            case 'up':
                return 'M7 14l3-3 3 3 5-5m0 0l-4 0m4 0l0 4';
            case 'down':
                return 'M7 10l3 3 3-3 5 5m0 0l-4 0m4 0l0-4';
            default:
                return 'M5 12h14';
        }
    }

    function getTrendColor(trendType) {
        switch (trendType) {
            case 'up':
                return 'text-green-600';
            case 'down':
                return 'text-red-600';
            default:
                return 'text-gray-600';
        }
    }
</script>

<div class="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow">
    <div class="flex items-center">
        <div class="p-3 rounded-full {getColorClasses(color)}">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={getIconPath(icon)}></path>
            </svg>
        </div>
        <div class="ml-4 flex-1">
            <p class="text-sm font-medium text-gray-600">{title}</p>
            <p class="text-2xl font-semibold text-gray-900">{value}</p>
        </div>
    </div>
    
    {#if description || trend}
        <div class="mt-4 flex items-center justify-between">
            {#if description}
                <p class="text-sm text-gray-500">{description}</p>
            {/if}
            
            {#if trend && trendValue}
                <div class="flex items-center {getTrendColor(trend)}">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={getTrendIcon(trend)}></path>
                    </svg>
                    <span class="text-sm font-medium">{trendValue}</span>
                </div>
            {/if}
        </div>
    {/if}
</div>