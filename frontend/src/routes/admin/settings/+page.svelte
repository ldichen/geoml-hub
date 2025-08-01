<script>
    import { onMount } from 'svelte';
    import { api } from '$lib/utils/api.js';

    let systemConfig = null;
    let systemInfo = null;
    let loading = true;
    let error = null;
    let saveLoading = false;
    let maintenanceLoading = false;
    let selectedCategory = 'general';
    let editingConfig = null;
    let editValue = '';
    let editDescription = '';
    let showEditModal = false;
    let maintenanceEnabled = false;
    let maintenanceMessage = '';

    const categories = [
        { id: 'general', name: '常规设置', icon: '⚙️' },
        { id: 'security', name: '安全设置', icon: '🔒' },
        { id: 'storage', name: '存储设置', icon: '💾' },
        { id: 'database', name: '数据库设置', icon: '🗄️' },
        { id: 'features', name: '功能设置', icon: '🚀' }
    ];

    onMount(async () => {
        await loadSystemData();
    });

    async function loadSystemData() {
        try {
            loading = true;
            const [configResponse, infoResponse] = await Promise.all([
                api.admin.getSystemConfig(),
                api.admin.getSystemInfo()
            ]);
            
            systemConfig = configResponse;
            systemInfo = infoResponse;
        } catch (err) {
            error = err.message;
        } finally {
            loading = false;
        }
    }

    function openEditModal(config) {
        editingConfig = config;
        editValue = config.value;
        editDescription = config.description;
        showEditModal = true;
    }

    async function saveConfig() {
        if (!editingConfig) return;

        try {
            saveLoading = true;
            await api.admin.updateSystemConfig({
                config_key: editingConfig.key,
                config_value: editingConfig.type === 'boolean' ? editValue === 'true' : 
                             editingConfig.type === 'integer' ? parseInt(editValue) : editValue,
                description: editDescription
            });

            // 更新本地数据
            const category = systemConfig.categories[selectedCategory];
            if (category) {
                const configIndex = category.findIndex(c => c.key === editingConfig.key);
                if (configIndex !== -1) {
                    category[configIndex] = {
                        ...category[configIndex],
                        value: editingConfig.type === 'boolean' ? editValue === 'true' : 
                               editingConfig.type === 'integer' ? parseInt(editValue) : editValue,
                        description: editDescription
                    };
                }
            }

            showEditModal = false;
            editingConfig = null;
        } catch (err) {
            error = err.message;
        } finally {
            saveLoading = false;
        }
    }

    async function toggleMaintenanceMode() {
        try {
            maintenanceLoading = true;
            await api.admin.setMaintenanceMode(maintenanceEnabled, maintenanceMessage);
            
            // 更新本地数据
            const generalCategory = systemConfig.categories['general'];
            if (generalCategory) {
                const maintenanceConfig = generalCategory.find(c => c.key === 'maintenance_mode');
                if (maintenanceConfig) {
                    maintenanceConfig.value = maintenanceEnabled;
                }
            }
        } catch (err) {
            error = err.message;
        } finally {
            maintenanceLoading = false;
        }
    }

    function formatValue(config) {
        if (config.type === 'boolean') {
            return config.value ? '是' : '否';
        } else if (config.type === 'integer') {
            if (config.key.includes('size') || config.key.includes('quota')) {
                return formatBytes(config.value);
            }
            return config.value.toLocaleString();
        }
        return config.value;
    }

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function getConfigIcon(config) {
        if (config.type === 'boolean') {
            return config.value ? '✅' : '❌';
        } else if (config.key.includes('size') || config.key.includes('quota')) {
            return '📏';
        } else if (config.key.includes('time') || config.key.includes('hours')) {
            return '⏰';
        } else if (config.key.includes('password') || config.key.includes('security')) {
            return '🔐';
        }
        return '⚙️';
    }

    $: currentConfigs = systemConfig?.categories?.[selectedCategory] || [];
    $: currentMaintenanceMode = systemConfig?.categories?.['general']?.find(c => c.key === 'maintenance_mode')?.value || false;
</script>

<div class="space-y-6">
    <div class="flex justify-between items-center">
        <h1 class="text-3xl font-bold text-gray-900">系统设置</h1>
        <button 
            on:click={loadSystemData}
            class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
        >
            刷新配置
        </button>
    </div>

    {#if loading}
        <div class="flex justify-center items-center h-64">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
    {:else if error}
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            错误: {error}
        </div>
    {:else if systemConfig}
        <div class="flex flex-col lg:flex-row gap-6">
            <!-- 侧边栏 -->
            <div class="w-full lg:w-64">
                <div class="bg-white rounded-lg shadow p-4">
                    <h3 class="font-semibold text-gray-900 mb-4">配置分类</h3>
                    <nav class="space-y-2">
                        {#each categories as category}
                            <button
                                on:click={() => selectedCategory = category.id}
                                class="w-full flex items-center px-3 py-2 text-left text-sm font-medium rounded-lg transition-colors {selectedCategory === category.id ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-500' : 'text-gray-600 hover:bg-gray-50'}"
                            >
                                <span class="mr-3">{category.icon}</span>
                                {category.name}
                            </button>
                        {/each}
                    </nav>
                </div>
            </div>

            <!-- 主要内容 -->
            <div class="flex-1 space-y-6">
                <!-- 维护模式快捷控制 -->
                <div class="bg-white rounded-lg shadow p-6">
                    <div class="flex items-center justify-between">
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900">维护模式</h3>
                            <p class="text-sm text-gray-600">启用维护模式将限制用户访问系统</p>
                        </div>
                        <div class="flex items-center space-x-4">
                            <label class="flex items-center">
                                <input 
                                    type="checkbox"
                                    bind:checked={maintenanceEnabled}
                                    class="form-checkbox h-5 w-5 text-blue-600"
                                />
                                <span class="ml-2 text-sm font-medium text-gray-700">启用维护模式</span>
                            </label>
                        </div>
                    </div>
                    
                    {#if maintenanceEnabled}
                        <div class="mt-4">
                            <label for="maintenance-message" class="block text-sm font-medium text-gray-700 mb-2">维护消息</label>
                            <textarea
                                id="maintenance-message"
                                bind:value={maintenanceMessage}
                                placeholder="系统维护中，请稍后再试"
                                class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                rows="3"
                            ></textarea>
                        </div>
                    {/if}
                    
                    <div class="mt-4 flex justify-end">
                        <button
                            on:click={toggleMaintenanceMode}
                            disabled={maintenanceLoading}
                            class="bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition-colors disabled:opacity-50"
                        >
                            {maintenanceLoading ? '应用中...' : '应用设置'}
                        </button>
                    </div>
                </div>

                <!-- 配置项列表 -->
                <div class="bg-white rounded-lg shadow">
                    <div class="px-6 py-4 border-b border-gray-200">
                        <h3 class="text-lg font-semibold text-gray-900">
                            {categories.find(c => c.id === selectedCategory)?.name}
                        </h3>
                    </div>
                    
                    <div class="divide-y divide-gray-200">
                        {#each currentConfigs as config}
                            <div class="px-6 py-4 hover:bg-gray-50">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center">
                                        <span class="text-2xl mr-3">{getConfigIcon(config)}</span>
                                        <div>
                                            <h4 class="text-sm font-medium text-gray-900">{config.key}</h4>
                                            <p class="text-sm text-gray-500">{config.description}</p>
                                        </div>
                                    </div>
                                    <div class="flex items-center space-x-4">
                                        <div class="text-right">
                                            <div class="text-sm font-medium text-gray-900">{formatValue(config)}</div>
                                            <div class="text-xs text-gray-500">{config.type}</div>
                                        </div>
                                        {#if config.editable}
                                            <button
                                                on:click={() => openEditModal(config)}
                                                class="text-blue-600 hover:text-blue-800 text-sm font-medium"
                                            >
                                                编辑
                                            </button>
                                        {:else}
                                            <span class="text-gray-400 text-sm">只读</span>
                                        {/if}
                                    </div>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>

                <!-- 系统信息 -->
                {#if systemInfo}
                    <div class="bg-white rounded-lg shadow p-6">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">系统信息</h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <h4 class="font-medium text-gray-900 mb-2">应用信息</h4>
                                <div class="space-y-1 text-sm text-gray-600">
                                    <div class="flex justify-between">
                                        <span>名称:</span>
                                        <span>{systemInfo.application?.name}</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>版本:</span>
                                        <span>{systemInfo.application?.version}</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>环境:</span>
                                        <span>{systemInfo.application?.environment}</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>调试模式:</span>
                                        <span>{systemInfo.application?.debug_mode ? '开启' : '关闭'}</span>
                                    </div>
                                </div>
                            </div>
                            <div>
                                <h4 class="font-medium text-gray-900 mb-2">系统信息</h4>
                                <div class="space-y-1 text-sm text-gray-600">
                                    <div class="flex justify-between">
                                        <span>操作系统:</span>
                                        <span>{systemInfo.system?.platform}</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>架构:</span>
                                        <span>{systemInfo.system?.architecture}</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>主机名:</span>
                                        <span>{systemInfo.system?.hostname}</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>CPU 核心:</span>
                                        <span>{systemInfo.system?.cpu_cores}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                {/if}
            </div>
        </div>
    {/if}
</div>

<!-- 编辑配置模态框 -->
{#if showEditModal && editingConfig}
    <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div class="mt-3">
                <h3 class="text-lg font-medium text-gray-900 mb-4">编辑配置: {editingConfig.key}</h3>
                
                <div class="space-y-4">
                    <div>
                        <label for="config-value" class="block text-sm font-medium text-gray-700 mb-2">配置值</label>
                        {#if editingConfig.type === 'boolean'}
                            <select
                                id="config-value"
                                bind:value={editValue}
                                class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="true">是</option>
                                <option value="false">否</option>
                            </select>
                        {:else if editingConfig.type === 'integer'}
                            <input
                                id="config-value"
                                type="number"
                                bind:value={editValue}
                                class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        {:else}
                            <input
                                id="config-value"
                                type="text"
                                bind:value={editValue}
                                class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        {/if}
                    </div>
                    
                    <div>
                        <label for="config-description" class="block text-sm font-medium text-gray-700 mb-2">描述</label>
                        <textarea
                            id="config-description"
                            bind:value={editDescription}
                            rows="3"
                            class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        ></textarea>
                    </div>
                </div>
                
                <div class="mt-6 flex justify-end space-x-3">
                    <button
                        on:click={() => { showEditModal = false; editingConfig = null; }}
                        class="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
                    >
                        取消
                    </button>
                    <button
                        on:click={saveConfig}
                        disabled={saveLoading}
                        class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors disabled:opacity-50"
                    >
                        {saveLoading ? '保存中...' : '保存'}
                    </button>
                </div>
            </div>
        </div>
    </div>
{/if}