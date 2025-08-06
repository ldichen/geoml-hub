<script>
    import { onMount } from 'svelte';
    import { page } from '$app/stores';
    import { goto } from '$app/navigation';
    import { _ } from 'svelte-i18n';
    import { Upload, File, X, CheckCircle, AlertCircle, Info } from 'lucide-svelte';
    import { user as currentUser } from '$lib/stores/auth.js';
    import { requireAuth, isOwner } from '$lib/utils/auth.js';
    import { api } from '$lib/utils/api.js';
    import FileUpload from '$lib/components/FileUpload.svelte';
    import Loading from '$lib/components/Loading.svelte';
    
    let repository = null;
    let loading = true;
    let error = '';
    let uploadFiles = [];
    let uploading = false;
    let uploadProgress = {};
    let uploadResults = [];
    
    $: username = $page.params.username;
    $: repositoryName = $page.params.repository;
    $: isRepoOwner = $currentUser && repository && isOwner(repository.owner?.username || repository.owner?.id);
    
    onMount(async () => {
        // 检查认证状态
        if (!requireAuth('/login')) {
            return;
        }
        
        await loadRepository();
        
        // 检查是否是仓库所有者
        if (repository && !isRepoOwner) {
            goto(`/${username}/${repositoryName}`);
            return;
        }
    });
    
    async function loadRepository() {
        try {
            repository = await api.getRepository(username, repositoryName);
        } catch (err) {
            console.error('Failed to load repository:', err);
            error = $_('error.not_found');
        } finally {
            loading = false;
        }
    }
    
    function handleFilesSelected(event) {
        const newFiles = Array.from(event.detail);
        uploadFiles = [...uploadFiles, ...newFiles.map(file => ({
            file,
            id: Math.random().toString(36).substr(2, 9),
            status: 'pending', // pending, uploading, completed, error
            progress: 0,
            error: null
        }))];
    }
    
    function removeFile(fileId) {
        uploadFiles = uploadFiles.filter(f => f.id !== fileId);
    }
    
    async function startUpload() {
        if (uploadFiles.length === 0) return;
        
        uploading = true;
        uploadResults = [];
        
        for (const fileItem of uploadFiles) {
            if (fileItem.status !== 'pending') continue;
            
            fileItem.status = 'uploading';
            uploadFiles = [...uploadFiles]; // 触发响应式更新
            
            try {
                const result = await api.uploadRepositoryFile(
                    username,
                    repositoryName,
                    fileItem.file,
                    {
                        onProgress: (progress) => {
                            fileItem.progress = progress;
                            uploadFiles = [...uploadFiles];
                        }
                    }
                );
                
                fileItem.status = 'completed';
                fileItem.progress = 100;
                uploadResults.push({
                    filename: fileItem.file.name,
                    status: 'success',
                    message: $_('file.upload_success')
                });
                
            } catch (err) {
                console.error('Upload failed:', err);
                fileItem.status = 'error';
                fileItem.error = err.message || $_('file.upload_failed');
                uploadResults.push({
                    filename: fileItem.file.name,
                    status: 'error',
                    message: err.message || $_('file.upload_failed')
                });
            }
            
            uploadFiles = [...uploadFiles];
        }
        
        uploading = false;
        
        // 如果所有文件都上传成功，可以重定向到仓库页面
        const allCompleted = uploadFiles.every(f => f.status === 'completed');
        if (allCompleted) {
            setTimeout(() => {
                goto(`/${username}/${repositoryName}`);
            }, 2000);
        }
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
</script>

<svelte:head>
    <title>{$_('file.upload_files')} - {username}/{repositoryName} - GeoML-Hub</title>
</svelte:head>

{#if loading}
    <div class="flex items-center justify-center min-h-96">
        <Loading />
    </div>
{:else if error}
    <div class="max-w-2xl mx-auto px-4 py-8">
        <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <h2 class="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
                {$_('error.error')}
            </h2>
            <p class="text-red-700 dark:text-red-300">{error}</p>
        </div>
    </div>
{:else if repository}
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <!-- 页面头部 -->
        <div class="mb-6">
            <nav class="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400 mb-4">
                <a href="/" class="hover:text-gray-700 dark:hover:text-gray-300">{$_('navigation.home')}</a>
                <span>/</span>
                <a href="/{username}" class="hover:text-gray-700 dark:hover:text-gray-300">{username}</a>
                <span>/</span>
                <a href="/{username}/{repositoryName}" class="hover:text-gray-700 dark:hover:text-gray-300">{repositoryName}</a>
                <span>/</span>
                <span class="text-gray-900 dark:text-white">{$_('file.upload')}</span>
            </nav>
            
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
                {$_('file.upload_files')}
            </h1>
            <p class="text-gray-600 dark:text-gray-400 mt-2">
                {$_('file.upload_to')} {username}/{repositoryName}
            </p>
        </div>
        
        <!-- 上传区域 -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6 mb-6">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                {$_('file.select_files')}
            </h2>
            
            <!-- 文件上传组件 -->
            <FileUpload on:filesSelected={handleFilesSelected} />
            
            <!-- 上传限制说明 -->
            <div class="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <div class="flex items-start space-x-2">
                    <Info class="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
                    <div class="text-sm text-blue-700 dark:text-blue-300">
                        <p class="font-medium mb-1">{$_('file.upload_guidelines')}</p>
                        <ul class="list-disc list-inside space-y-1">
                            <li>{$_('file.max_file_size')}: 500MB</li>
                            <li>{$_('file.supported_formats')}: .pkl, .h5, .pt, .pth, .onnx, .csv, .txt, .md, .json, .yml, .png, .jpg, etc.</li>
                            <li>{$_('file.total_size_limit')}: 5GB {$_('common.per_user')}</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 文件列表 -->
        {#if uploadFiles.length > 0}
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6 mb-6">
                <div class="flex items-center justify-between mb-4">
                    <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
                        {$_('file.selected_files')} ({uploadFiles.length})
                    </h2>
                    {#if !uploading}
                        <button
                            on:click={startUpload}
                            disabled={uploadFiles.length === 0}
                            class="btn btn-primary flex items-center"
                        >
                            <Upload class="w-4 h-4 mr-2" />
                            {$_('file.start_upload')}
                        </button>
                    {/if}
                </div>
                
                <div class="space-y-3">
                    {#each uploadFiles as fileItem}
                        <div class="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-600 rounded-lg">
                            <div class="flex items-center space-x-3 flex-1 min-w-0">
                                <File class="w-5 h-5 text-gray-400 flex-shrink-0" />
                                <div class="flex-1 min-w-0">
                                    <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                                        {fileItem.file.name}
                                    </p>
                                    <p class="text-xs text-gray-500 dark:text-gray-400">
                                        {formatFileSize(fileItem.file.size)}
                                    </p>
                                    
                                    <!-- 进度条 -->
                                    {#if fileItem.status === 'uploading'}
                                        <div class="mt-2">
                                            <div class="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400">
                                                <span>{$_('file.uploading')}...</span>
                                                <span>{fileItem.progress}%</span>
                                            </div>
                                            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-1">
                                                <div 
                                                    class="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                                                    style="width: {fileItem.progress}%"
                                                ></div>
                                            </div>
                                        </div>
                                    {/if}
                                    
                                    <!-- 错误信息 -->
                                    {#if fileItem.status === 'error' && fileItem.error}
                                        <p class="text-xs text-red-600 dark:text-red-400 mt-1">
                                            {fileItem.error}
                                        </p>
                                    {/if}
                                </div>
                            </div>
                            
                            <div class="flex items-center space-x-2">
                                <!-- 状态图标 -->
                                {#if fileItem.status === 'completed'}
                                    <CheckCircle class="w-5 h-5 text-green-500" />
                                {:else if fileItem.status === 'error'}
                                    <AlertCircle class="w-5 h-5 text-red-500" />
                                {:else if fileItem.status === 'uploading'}
                                    <div class="w-5 h-5">
                                        <svg class="animate-spin h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24">
                                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                    </div>
                                {/if}
                                
                                <!-- 删除按钮 -->
                                {#if fileItem.status === 'pending' && !uploading}
                                    <button
                                        on:click={() => removeFile(fileItem.id)}
                                        class="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                                    >
                                        <X class="w-4 h-4 text-gray-500" />
                                    </button>
                                {/if}
                            </div>
                        </div>
                    {/each}
                </div>
            </div>
        {/if}
        
        <!-- 上传结果 -->
        {#if uploadResults.length > 0}
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
                <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    {$_('file.upload_results')}
                </h2>
                
                <div class="space-y-2">
                    {#each uploadResults as result}
                        <div class="flex items-center justify-between p-3 rounded-lg {result.status === 'success' ? 'bg-green-50 dark:bg-green-900/20' : 'bg-red-50 dark:bg-red-900/20'}">
                            <div class="flex items-center space-x-2">
                                {#if result.status === 'success'}
                                    <CheckCircle class="w-4 h-4 text-green-500" />
                                {:else}
                                    <AlertCircle class="w-4 h-4 text-red-500" />
                                {/if}
                                <span class="text-sm font-medium {result.status === 'success' ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'}">
                                    {result.filename}
                                </span>
                            </div>
                            <span class="text-xs {result.status === 'success' ? 'text-green-600 dark:text-green-300' : 'text-red-600 dark:text-red-300'}">
                                {result.message}
                            </span>
                        </div>
                    {/each}
                </div>
                
                {#if uploadResults.every(r => r.status === 'success')}
                    <div class="mt-4 text-center">
                        <p class="text-sm text-green-600 dark:text-green-400 mb-2">
                            {$_('file.all_uploads_successful')}
                        </p>
                        <a href="/{username}/{repositoryName}" class="btn btn-primary">
                            {$_('repository.view_repository')}
                        </a>
                    </div>
                {/if}
            </div>
        {/if}
    </div>
{/if}