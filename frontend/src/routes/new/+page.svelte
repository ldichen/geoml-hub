<script>
  import { goto } from '$app/navigation';
  import { _ } from 'svelte-i18n';
  import { 
    LICENSE_OPTIONS 
  } from '$lib/utils/constants';
  import { api } from '$lib/utils/api';
  import { user as currentUser } from '$lib/stores/auth.js';
  import Loading from '$lib/components/Loading.svelte';
  import ClassificationSelector from '$lib/components/ClassificationSelector.svelte';
  
  let loading = false;
  let error = null;
  let classifications = [];
  let loadingClassifications = false;
  
  // v2.0 Repository creation form data
  let formData = {
    name: '',
    description: '',
    repo_type: 'model',
    visibility: 'public',
    license: '',
    tags: [],
    base_model: '',
    classification_id: null,
    readme_content: ''
  };
  
  // Validation errors
  let errors = {};
  
  // Tag input
  let tagInput = '';
  
  function validateForm() {
    errors = {};
    
    if (!formData.name.trim()) {
      errors.name = '仓库名称不能为空';
    } else if (!/^[a-zA-Z0-9._-]+$/.test(formData.name)) {
      errors.name = '仓库名称只能包含字母、数字、点号、下划线和连字符';
    }
    
    if (formData.description && formData.description.length > 500) {
      errors.description = '描述不能超过500个字符';
    }
    
    return Object.keys(errors).length === 0;
  }
  
  function addTag() {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      formData.tags = [...formData.tags, tagInput.trim()];
      tagInput = '';
    }
  }
  
  function removeTag(tag) {
    formData.tags = formData.tags.filter(t => t !== tag);
  }
  
  function handleTagKeydown(event) {
    if (event.key === 'Enter') {
      event.preventDefault();
      addTag();
    }
  }
  
  async function loadClassifications() {
    try {
      loadingClassifications = true;
      const response = await api.getClassifications();
      classifications = response;
    } catch (err) {
      console.error('Failed to load classifications:', err);
    } finally {
      loadingClassifications = false;
    }
  }
  
  function handleClassificationSelect(event) {
    const selectedClassification = event.detail;
    formData.classification_id = selectedClassification.id;
  }
  
  // Load classifications on component mount
  import { onMount } from 'svelte';
  
  onMount(() => {
    loadClassifications();
  });
  
  async function handleSubmit() {
    if (!validateForm()) {
      return;
    }
    
    loading = true;
    error = null;
    
    // 验证用户登录状态
    if (!$currentUser) {
      error = '请先登录';
      loading = false;
      return;
    }
    
    try {
      const submitData = {
        name: formData.name.trim(),
        description: formData.description.trim() || null,
        repo_type: formData.repo_type,
        visibility: formData.visibility,
        license: formData.license || null,
        tags: formData.tags,
        base_model: formData.base_model || null,
        classification_id: formData.classification_id || null,
        readme_content: formData.readme_content || null
      };
      
      const response = await api.createRepository(submitData);
      
      // Success - redirect to repository page
      goto(`/${$currentUser.username}/${response.name}`);
    } catch (err) {
      error = err.message || '创建仓库失败';
      console.error('Failed to create repository:', err);
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>创建新仓库 - GeoML Hub</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <div class="max-w-2xl mx-auto pt-16 px-4">
    <div class="text-center mb-8">
      <!-- Icon -->
      <div class="mx-auto w-16 h-16 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center mb-6">
        <svg class="w-8 h-8 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
        </svg>
      </div>
      
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        创建新仓库
      </h1>
      <p class="text-gray-600 dark:text-gray-400">
        仓库包含您的模型文件、数据集和相关资源，支持版本控制和协作开发。
      </p>
    </div>
    
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      <form on:submit|preventDefault={handleSubmit} class="p-6 space-y-6">
        <!-- Repository Name -->
        <div>
          <div class="flex justify-between items-center mb-2">
            <label for="owner-select" class="text-sm font-medium text-gray-700 dark:text-gray-300">所有者</label>
            <label for="repo-name-input" class="text-sm font-medium text-gray-700 dark:text-gray-300">仓库名称</label>
          </div>
          <div class="flex space-x-2">
            <!-- Owner (current user) -->
            <div class="relative">
              <div class="bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-2 text-gray-600 dark:text-gray-300 cursor-not-allowed flex items-center justify-between">
                <span>{$currentUser?.username || 'loading...'}</span>
                <svg class="w-4 h-4 fill-current text-gray-500 dark:text-gray-400 ml-2" viewBox="0 0 20 20">
                  <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"/>
                </svg>
              </div>
            </div>
            
            <span class="flex items-center text-gray-500 dark:text-gray-400">/</span>
            
            <!-- Repository Name Input -->
            <div class="flex-1">
              <input
                id="repo-name-input"
                type="text"
                bind:value={formData.name}
                class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent {errors.name ? 'border-red-500' : ''}"
                placeholder="my-awesome-model"
                required
              />
              {#if errors.name}
                <p class="text-red-500 text-sm mt-1">{errors.name}</p>
              {/if}
            </div>
          </div>
        </div>
        
        <!-- Description -->
        <div>
          <label for="description-input" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            描述 (可选)
          </label>
          <textarea
            id="description-input"
            bind:value={formData.description}
            rows="3"
            class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent {errors.description ? 'border-red-500' : ''}"
            placeholder="简要描述您的模型或数据集..."
          />
          {#if errors.description}
            <p class="text-red-500 text-sm mt-1">{errors.description}</p>
          {/if}
        </div>
        
        
        <!-- License -->
        <div>
          <label for="license-select" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            许可证 (可选)
          </label>
          <select
            id="license-select"
            bind:value={formData.license}
            class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">选择许可证...</option>
            <option value="mit">MIT</option>
            <option value="apache-2.0">Apache 2.0</option>
            <option value="gpl-3.0">GPL 3.0</option>
            <option value="bsd-3-clause">BSD 3-Clause</option>
            <option value="lgpl-2.1">LGPL 2.1</option>
            <option value="mpl-2.0">MPL 2.0</option>
            <option value="cc0-1.0">CC0 1.0</option>
            <option value="cc-by-4.0">CC BY 4.0</option>
            <option value="unlicense">Unlicense</option>
            <option value="other">其他</option>
          </select>
        </div>
        
        <!-- Tags -->
        <div>
          <label for="tags-input" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            标签 (可选)
          </label>
          <div class="flex flex-wrap gap-2 mb-2">
            {#each formData.tags as tag}
              <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                {tag}
                <button
                  type="button"
                  class="ml-1 h-4 w-4 rounded-full hover:bg-blue-200 dark:hover:bg-blue-800 flex items-center justify-center"
                  on:click={() => removeTag(tag)}
                >
                  <svg class="h-2 w-2" fill="currentColor" viewBox="0 0 8 8">
                    <path d="M1.41 0l-1.41 1.41.72.72 1.78 1.81-1.78 1.78-.72.69 1.41 1.44.72-.72 1.81-1.81 1.78 1.81.69.72 1.44-1.44-.72-.69-1.81-1.78 1.81-1.81.72-.72-1.44-1.41-.69.72-1.78 1.78-1.81-1.78-.72-.72z"/>
                  </svg>
                </button>
              </span>
            {/each}
          </div>
          <input
            id="tags-input"
            type="text"
            bind:value={tagInput}
            on:keydown={handleTagKeydown}
            class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="输入标签后按回车键添加"
          />
        </div>

        <!-- Base Model -->
        <div>
          <label for="base-model-input" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            基础模型 (可选)
          </label>
          <input
            id="base-model-input"
            type="text"
            bind:value={formData.base_model}
            class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="例如: bert-base-uncased, resnet50"
          />
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
            如果您的模型基于现有模型构建，请输入基础模型名称
          </p>
        </div>

        <!-- Classifications -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            分类 (可选)
          </label>
          <ClassificationSelector 
            {classifications}
            selectedClassificationId={formData.classification_id}
            loading={loadingClassifications}
            on:select={handleClassificationSelect}
          />
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
            选择最适合您仓库内容的分类，可以选择一级、二级或三级分类
          </p>
        </div>
        
        <!-- Visibility -->
        <div class="space-y-4">
          <fieldset>
            <legend class="block text-sm font-medium text-gray-700 dark:text-gray-300">
              可见性
            </legend>
          
          <div class="flex items-start space-x-3">
            <input
              type="radio"
              id="public"
              bind:group={formData.visibility}
              value="public"
              class="mt-1 w-4 h-4 text-blue-600 border-gray-300 dark:border-gray-600 focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700"
            />
            <div class="flex-1">
              <label for="public" class="flex items-center cursor-pointer">
                <svg class="w-5 h-5 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span class="font-medium text-gray-900 dark:text-white">公开</span>
              </label>
              <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                任何人都可以查看此仓库。只有您或您的组织成员可以提交更改。
              </p>
            </div>
          </div>
          
          <div class="flex items-start space-x-3">
            <input
              type="radio"
              id="private"
              bind:group={formData.visibility}
              value="private"
              class="mt-1 w-4 h-4 text-blue-600 border-gray-300 dark:border-gray-600 focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700"
            />
            <div class="flex-1">
              <label for="private" class="flex items-center cursor-pointer">
                <svg class="w-5 h-5 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                </svg>
                <span class="font-medium text-gray-900 dark:text-white">私有</span>
              </label>
              <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                只有您或您的组织成员可以查看和提交到此仓库。
              </p>
            </div>
          </div>
          </fieldset>
        </div>
        
        <!-- Info note -->
        <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <p class="text-sm text-blue-800 dark:text-blue-200">
            创建仓库后，您可以通过网页界面或 Git 上传文件和管理版本。
          </p>
        </div>
        
        <!-- Error Display -->
        {#if error}
          <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <p class="text-red-700 dark:text-red-400">{error}</p>
          </div>
        {/if}
        
        <!-- Submit Button -->
        <div class="flex justify-end space-x-3">
          <button
            type="button"
            class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            on:click={() => goto('/')}
          >
            取消
          </button>
          <button
            type="submit"
            class="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium rounded-lg transition-colors flex items-center space-x-2"
            disabled={loading}
          >
            {#if loading}
              <Loading size="sm" />
              <span>创建中...</span>
            {:else}
              <span>创建仓库</span>
            {/if}
          </button>
        </div>
      </form>
    </div>
  </div>
</div>