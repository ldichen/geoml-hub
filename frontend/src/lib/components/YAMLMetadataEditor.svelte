<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import { Code, Eye, Edit, Save, X, AlertCircle, CheckCircle } from 'lucide-svelte';
  import { load as yamlLoad, dump as yamlDump } from 'js-yaml';

  const dispatch = createEventDispatcher<{
    save: { metadata: Record<string, any>; content: string };
    cancel: void;
  }>();

  export let initialContent: string = '';
  export let title: string = 'YAML 元数据编辑器';
  export let editable: boolean = true;
  export let showPreview: boolean = true;

  let mode: 'edit' | 'preview' = 'edit';
  let content: string = initialContent;
  let parsedMetadata: Record<string, any> = {};
  let parseError: string | null = null;
  let isDirty: boolean = false;

  // Common metadata fields for geospatial ML models
  const commonFields = [
    { key: 'title', label: '标题', type: 'text', required: true },
    { key: 'description', label: '描述', type: 'textarea', required: true },
    { key: 'version', label: '版本', type: 'text', required: true },
    { key: 'authors', label: '作者', type: 'array', required: true },
    { key: 'tags', label: '标签', type: 'array', required: false },
    { key: 'license', label: '许可证', type: 'select', options: ['MIT', 'Apache-2.0', 'GPL-3.0', 'BSD-3-Clause', 'CC-BY-4.0', 'CC-BY-SA-4.0'], required: false },
    { key: 'model_type', label: '模型类型', type: 'select', options: ['classification', 'regression', 'detection', 'segmentation', 'clustering', 'other'], required: false },
    { key: 'framework', label: '框架', type: 'select', options: ['PyTorch', 'TensorFlow', 'Scikit-learn', 'XGBoost', 'Keras', 'ONNX', 'Other'], required: false },
    { key: 'dataset', label: '数据集', type: 'text', required: false },
    { key: 'base_model', label: '基础模型', type: 'text', required: false },
    { key: 'input_size', label: '输入尺寸', type: 'text', required: false },
    { key: 'output_size', label: '输出尺寸', type: 'text', required: false },
    { key: 'metrics', label: '评估指标', type: 'object', required: false },
    { key: 'training_data', label: '训练数据', type: 'object', required: false },
    { key: 'hardware_requirements', label: '硬件要求', type: 'object', required: false },
    { key: 'usage_example', label: '使用示例', type: 'textarea', required: false },
    { key: 'doi', label: 'DOI', type: 'text', required: false },
    { key: 'paper_url', label: '论文链接', type: 'url', required: false },
    { key: 'github_url', label: 'GitHub链接', type: 'url', required: false },
  ];

  onMount(() => {
    parseYAML();
  });

  $: if (content !== initialContent) {
    isDirty = true;
  }

  $: if (content) {
    parseYAML();
  }

  function parseYAML() {
    try {
      if (content.trim()) {
        parsedMetadata = yamlLoad(content) as Record<string, any> || {};
        parseError = null;
      } else {
        parsedMetadata = {};
        parseError = null;
      }
    } catch (error) {
      parseError = error instanceof Error ? error.message : 'YAML 解析错误';
      parsedMetadata = {};
    }
  }

  function generateYAML() {
    try {
      content = yamlDump(parsedMetadata, { 
        indent: 2, 
        noRefs: true,
        sortKeys: true
      });
      parseError = null;
    } catch (error) {
      parseError = error instanceof Error ? error.message : 'YAML 生成错误';
    }
  }

  function handleFieldChange(key: string, value: any) {
    if (value === '' || value === null || value === undefined) {
      delete parsedMetadata[key];
    } else {
      parsedMetadata[key] = value;
    }
    parsedMetadata = { ...parsedMetadata };
    generateYAML();
  }

  function handleArrayFieldChange(key: string, index: number, value: string) {
    if (!parsedMetadata[key]) {
      parsedMetadata[key] = [];
    }
    parsedMetadata[key][index] = value;
    parsedMetadata = { ...parsedMetadata };
    generateYAML();
  }

  function addArrayItem(key: string) {
    if (!parsedMetadata[key]) {
      parsedMetadata[key] = [];
    }
    parsedMetadata[key].push('');
    parsedMetadata = { ...parsedMetadata };
    generateYAML();
  }

  function removeArrayItem(key: string, index: number) {
    if (parsedMetadata[key]) {
      parsedMetadata[key].splice(index, 1);
      parsedMetadata = { ...parsedMetadata };
      generateYAML();
    }
  }

  function handleObjectFieldChange(key: string, subKey: string, value: any) {
    if (!parsedMetadata[key]) {
      parsedMetadata[key] = {};
    }
    if (value === '' || value === null || value === undefined) {
      delete parsedMetadata[key][subKey];
    } else {
      parsedMetadata[key][subKey] = value;
    }
    parsedMetadata = { ...parsedMetadata };
    generateYAML();
  }

  function handleSave() {
    if (parseError) {
      return;
    }
    dispatch('save', { metadata: parsedMetadata, content });
  }

  function handleCancel() {
    dispatch('cancel');
  }

  function loadTemplate() {
    const template = {
      title: '',
      description: '',
      version: '1.0.0',
      authors: [''],
      tags: [],
      license: 'MIT',
      model_type: 'classification',
      framework: 'PyTorch',
      dataset: '',
      base_model: '',
      input_size: '',
      output_size: '',
      metrics: {
        accuracy: 0.0,
        precision: 0.0,
        recall: 0.0,
        f1_score: 0.0
      },
      training_data: {
        size: '',
        source: '',
        preprocessing: ''
      },
      hardware_requirements: {
        min_ram: '4GB',
        min_gpu: 'GTX 1060',
        recommended_gpu: 'RTX 3080'
      },
      usage_example: '',
      doi: '',
      paper_url: '',
      github_url: ''
    };
    
    parsedMetadata = template;
    generateYAML();
  }
</script>

<div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
  <!-- Header -->
  <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
      {title}
    </h3>
    
    <div class="flex items-center space-x-2">
      {#if showPreview}
        <div class="flex items-center space-x-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          <button
            class="px-3 py-1 text-sm rounded {mode === 'edit' ? 'bg-white dark:bg-gray-600 shadow-sm' : ''}"
            on:click={() => mode = 'edit'}
          >
            <Edit class="h-4 w-4 inline mr-1" />
            编辑
          </button>
          <button
            class="px-3 py-1 text-sm rounded {mode === 'preview' ? 'bg-white dark:bg-gray-600 shadow-sm' : ''}"
            on:click={() => mode = 'preview'}
          >
            <Eye class="h-4 w-4 inline mr-1" />
            预览
          </button>
        </div>
      {/if}
      
      <button
        class="px-3 py-1 text-sm text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded"
        on:click={loadTemplate}
      >
        加载模板
      </button>
    </div>
  </div>

  <!-- Content -->
  <div class="p-4">
    {#if mode === 'edit'}
      <div class="space-y-6">
        <!-- Form Fields -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          {#each commonFields as field}
            <div class="md:col-span-{field.type === 'textarea' ? '2' : '1'}">
              <label for="field-{field.key}" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                {field.label}
                {#if field.required}
                  <span class="text-red-500">*</span>
                {/if}
              </label>
              
              {#if field.type === 'text' || field.type === 'url'}
                <input
                  id="field-{field.key}"
                  type={field.type}
                  value={parsedMetadata[field.key] || ''}
                  on:input={(e) => handleFieldChange(field.key, e.currentTarget.value)}
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              {:else if field.type === 'textarea'}
                <textarea
                  id="field-{field.key}"
                  value={parsedMetadata[field.key] || ''}
                  on:input={(e) => handleFieldChange(field.key, e.currentTarget.value)}
                  rows="3"
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                ></textarea>
              {:else if field.type === 'select'}
                <select
                  id="field-{field.key}"
                  value={parsedMetadata[field.key] || ''}
                  on:change={(e) => handleFieldChange(field.key, e.currentTarget.value)}
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="">选择{field.label}</option>
                  {#each field.options as option}
                    <option value={option}>{option}</option>
                  {/each}
                </select>
              {:else if field.type === 'array'}
                <div class="space-y-2">
                  {#each (parsedMetadata[field.key] || []) as item, index}
                    <div class="flex items-center space-x-2">
                      <input
                        type="text"
                        value={item}
                        on:input={(e) => handleArrayFieldChange(field.key, index, e.currentTarget.value)}
                        class="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                      />
                      <button
                        type="button"
                        on:click={() => removeArrayItem(field.key, index)}
                        class="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                      >
                        <X class="h-4 w-4" />
                      </button>
                    </div>
                  {/each}
                  <button
                    type="button"
                    on:click={() => addArrayItem(field.key)}
                    class="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    + 添加{field.label}
                  </button>
                </div>
              {:else if field.type === 'object'}
                <div class="space-y-2">
                  {#each Object.entries(parsedMetadata[field.key] || {}) as [subKey, subValue]}
                    <div class="flex items-center space-x-2">
                      <input
                        type="text"
                        value={subKey}
                        disabled
                        class="w-1/3 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-600 text-gray-500 dark:text-gray-400"
                      />
                      <input
                        type="text"
                        value={subValue}
                        on:input={(e) => handleObjectFieldChange(field.key, subKey, e.currentTarget.value)}
                        class="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          {/each}
        </div>

        <!-- Raw YAML Editor -->
        <div>
          <label for="yaml-editor" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            原始 YAML
          </label>
          <textarea
            id="yaml-editor"
            bind:value={content}
            rows="10"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white font-mono text-sm"
            placeholder="输入 YAML 格式的元数据..."
          ></textarea>
        </div>

        <!-- Parse Error -->
        {#if parseError}
          <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
            <div class="flex items-center space-x-2">
              <AlertCircle class="h-5 w-5 text-red-500" />
              <span class="text-sm font-medium text-red-800 dark:text-red-200">
                YAML 解析错误
              </span>
            </div>
            <p class="text-sm text-red-700 dark:text-red-300 mt-1">
              {parseError}
            </p>
          </div>
        {/if}

        <!-- Success Message -->
        {#if !parseError && Object.keys(parsedMetadata).length > 0}
          <div class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
            <div class="flex items-center space-x-2">
              <CheckCircle class="h-5 w-5 text-green-500" />
              <span class="text-sm font-medium text-green-800 dark:text-green-200">
                YAML 解析成功
              </span>
            </div>
          </div>
        {/if}
      </div>
    {:else if mode === 'preview'}
      <!-- Preview Mode -->
      <div class="space-y-6">
        <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
          <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-3">解析结果</h4>
          <pre class="text-sm text-gray-700 dark:text-gray-300 overflow-x-auto">{JSON.stringify(parsedMetadata, null, 2)}</pre>
        </div>
        
        <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
          <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-3">生成的 YAML</h4>
          <pre class="text-sm text-gray-700 dark:text-gray-300 overflow-x-auto">{content}</pre>
        </div>
      </div>
    {/if}
  </div>

  <!-- Footer -->
  {#if editable}
    <div class="flex items-center justify-end space-x-3 p-4 border-t border-gray-200 dark:border-gray-700">
      <button
        type="button"
        on:click={handleCancel}
        class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-md"
      >
        取消
      </button>
      <button
        type="button"
        on:click={handleSave}
        disabled={!!parseError}
        class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-md"
      >
        <Save class="h-4 w-4 mr-2" />
        保存
      </button>
    </div>
  {/if}
</div>