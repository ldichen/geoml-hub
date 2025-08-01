<script>
  import { User } from 'lucide-svelte';

  export let user = null;
  export let size = 'md';
  export let showName = false;
  export let showUsername = false;
  export let clickable = true;

  // 缓存计算结果，避免重复计算
  const sizeClassMap = {
    xs: 'h-6 w-6',
    sm: 'h-8 w-8', 
    md: 'h-10 w-10',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16'
  };

  const iconSizeClassMap = {
    xs: 'h-3 w-3',
    sm: 'h-4 w-4',
    md: 'h-5 w-5', 
    lg: 'h-6 w-6',
    xl: 'h-8 w-8'
  };

  const textSizeClassMap = {
    xs: 'text-xs',
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg', 
    xl: 'text-xl'
  };

  const colors = [
    'bg-red-500', 'bg-yellow-500', 'bg-green-500', 'bg-blue-500', 'bg-indigo-500',
    'bg-purple-500', 'bg-pink-500', 'bg-orange-500', 'bg-teal-500', 'bg-cyan-500'
  ];

  // 使用缓存的计算属性
  $: sizeClasses = sizeClassMap[size] || sizeClassMap.md;
  $: iconSizeClasses = iconSizeClassMap[size] || iconSizeClassMap.md;
  $: textSizeClasses = textSizeClassMap[size] || textSizeClassMap.md;
  
  // 缓存用户相关的计算结果
  $: userInitials = user?.full_name ? 
    user.full_name.split(' ').map(word => word.charAt(0)).join('').toUpperCase().slice(0, 2) :
    user?.username?.charAt(0).toUpperCase() || '';
    
  $: userColor = user?.username ? (() => {
    let hash = 0;
    for (let i = 0; i < user.username.length; i++) {
      hash = user.username.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  })() : 'bg-gray-500';


  // 图片加载状态
  let imageLoaded = false;
  let imageError = false;

  function handleImageLoad() {
    imageLoaded = true;
    imageError = false;
  }

  function handleImageError() {
    imageError = true;
    imageLoaded = false;
  }
</script>

<div class="flex items-center space-x-2">
  <!-- Avatar -->
  <div class="relative">
    {#if clickable && user}
      <a href="/{user.username}" class="block">
        <div class="relative {sizeClasses} rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
          {#if user?.avatar_url && !imageError}
            <!-- 图片加载状态管理 -->
            <div class="h-full w-full relative">
              {#if !imageLoaded}
                <!-- 加载占位符 -->
                <div class="h-full w-full flex items-center justify-center text-white font-semibold {userColor} {textSizeClasses}">
                  {userInitials}
                </div>
              {/if}
              <img 
                src={user.avatar_url} 
                alt={user.full_name || user.username}
                class="h-full w-full object-cover {imageLoaded ? 'opacity-100' : 'opacity-0'} transition-opacity duration-200"
                loading="lazy"
                on:load={handleImageLoad}
                on:error={handleImageError}
              />
            </div>
          {:else if user}
            <!-- 用户名初始化背景 -->
            <div class="h-full w-full flex items-center justify-center text-white font-semibold {userColor} {textSizeClasses}">
              {userInitials}
            </div>
          {:else}
            <!-- 默认用户图标 -->
            <User class="text-gray-500 dark:text-gray-400 {iconSizeClasses}" />
          {/if}
        </div>
      </a>
    {:else}
      <div class="relative {sizeClasses} rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
        {#if user?.avatar_url && !imageError}
          <!-- 图片加载状态管理 -->
          <div class="h-full w-full relative">
            {#if !imageLoaded}
              <!-- 加载占位符 -->
              <div class="h-full w-full flex items-center justify-center text-white font-semibold {userColor} {textSizeClasses}">
                {userInitials}
              </div>
            {/if}
            <img 
              src={user.avatar_url} 
              alt={user.full_name || user.username}
              class="h-full w-full object-cover {imageLoaded ? 'opacity-100' : 'opacity-0'} transition-opacity duration-200"
              loading="lazy"
              on:load={handleImageLoad}
              on:error={handleImageError}
            />
          </div>
        {:else if user}
          <!-- 用户名初始化背景 -->
          <div class="h-full w-full flex items-center justify-center text-white font-semibold {userColor} {textSizeClasses}">
            {userInitials}
          </div>
        {:else}
          <!-- 默认用户图标 -->
          <User class="text-gray-500 dark:text-gray-400 {iconSizeClasses}" />
        {/if}
      </div>
    {/if}

  </div>

  <!-- Name and Username -->
  {#if (showName || showUsername) && user}
    <div class="flex flex-col">
      {#if showName && user.full_name}
        <span class="font-medium text-gray-900 dark:text-white {textSizeClasses}">
          {user.full_name}
        </span>
      {/if}
      {#if showUsername}
        <span class="text-gray-500 dark:text-gray-400 {size === 'xs' ? 'text-xs' : 'text-sm'}">
          @{user.username}
        </span>
      {/if}
    </div>
  {/if}
</div>