<script>
    import { marked } from 'marked';
    import { onMount } from 'svelte';
    
    export let content = '';
    
    let htmlContent = '';
    
    $: if (content) {
        // 配置marked选项
        marked.setOptions({
            gfm: true, // 启用GitHub风格的Markdown
            breaks: true, // 启用换行符
            sanitize: false, // 不清理HTML（需要小心XSS攻击）
            highlight: function(code, lang) {
                // 简单的代码高亮（可以集成更好的高亮库）
                return `<pre class="language-${lang}"><code>${code}</code></pre>`;
            }
        });
        
        htmlContent = marked(content);
    }
    
    onMount(() => {
        // 处理代码块的复制功能等
        const codeBlocks = document.querySelectorAll('pre code');
        codeBlocks.forEach(block => {
            // 可以添加复制按钮等功能
        });
    });
</script>

<div class="readme-viewer prose dark:prose-invert max-w-none">
    {@html htmlContent}
</div>

<style>
    :global(.readme-viewer) {
        line-height: 1.6;
    }
    
    :global(.readme-viewer h1) {
        font-size: 2rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #e5e7eb;
    }
    
    :global(.dark .readme-viewer h1) {
        border-bottom-color: #374151;
    }
    
    :global(.readme-viewer h2) {
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        padding-bottom: 0.25rem;
        border-bottom: 1px solid #e5e7eb;
    }
    
    :global(.dark .readme-viewer h2) {
        border-bottom-color: #4b5563;
    }
    
    :global(.readme-viewer h3) {
        font-size: 1.25rem;
        font-weight: 600;
        margin-top: 1.25rem;
        margin-bottom: 0.5rem;
    }
    
    :global(.readme-viewer h4) {
        font-size: 1.125rem;
        font-weight: 600;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    
    :global(.readme-viewer p) {
        margin-bottom: 1rem;
        color: #374151;
    }
    
    :global(.dark .readme-viewer p) {
        color: #d1d5db;
    }
    
    :global(.readme-viewer ul, .readme-viewer ol) {
        margin-bottom: 1rem;
        padding-left: 1.5rem;
    }
    
    :global(.readme-viewer li) {
        margin-bottom: 0.25rem;
    }
    
    :global(.readme-viewer blockquote) {
        border-left: 4px solid #e5e7eb;
        padding-left: 1rem;
        margin: 1rem 0;
        font-style: italic;
        color: #6b7280;
    }
    
    :global(.dark .readme-viewer blockquote) {
        border-left-color: #4b5563;
        color: #9ca3af;
    }
    
    :global(.readme-viewer code) {
        background-color: #f3f4f6;
        color: #ef4444;
        padding: 0.125rem 0.25rem;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        font-family: 'Courier New', Courier, monospace;
    }
    
    :global(.dark .readme-viewer code) {
        background-color: #374151;
        color: #fca5a5;
    }
    
    :global(.readme-viewer pre) {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 0.5rem;
        padding: 1rem;
        overflow-x: auto;
        margin: 1rem 0;
    }
    
    :global(.dark .readme-viewer pre) {
        background-color: #1f2937;
        border-color: #374151;
    }
    
    :global(.readme-viewer pre code) {
        background: transparent;
        color: inherit;
        padding: 0;
        border-radius: 0;
        font-size: 0.875rem;
    }
    
    :global(.readme-viewer table) {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        border: 1px solid #e5e7eb;
    }
    
    :global(.dark .readme-viewer table) {
        border-color: #374151;
    }
    
    :global(.readme-viewer th, .readme-viewer td) {
        padding: 0.75rem;
        text-align: left;
        border-bottom: 1px solid #e5e7eb;
    }
    
    :global(.dark .readme-viewer th, .dark .readme-viewer td) {
        border-bottom-color: #374151;
    }
    
    :global(.readme-viewer th) {
        background-color: #f9fafb;
        font-weight: 600;
    }
    
    :global(.dark .readme-viewer th) {
        background-color: #111827;
    }
    
    :global(.readme-viewer img) {
        max-width: 100%;
        height: auto;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    :global(.readme-viewer a) {
        color: #3b82f6;
        text-decoration: underline;
    }
    
    :global(.readme-viewer a:hover) {
        color: #1d4ed8;
    }
    
    :global(.dark .readme-viewer a) {
        color: #60a5fa;
    }
    
    :global(.dark .readme-viewer a:hover) {
        color: #93c5fd;
    }
    
    :global(.readme-viewer hr) {
        border: none;
        border-top: 1px solid #e5e7eb;
        margin: 2rem 0;
    }
    
    :global(.dark .readme-viewer hr) {
        border-top-color: #374151;
    }
    
    /* 警告框样式 */
    :global(.readme-viewer .alert) {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid;
    }
    
    :global(.readme-viewer .alert-info) {
        background-color: #eff6ff;
        border-left-color: #3b82f6;
        color: #1e40af;
    }
    
    :global(.readme-viewer .alert-warning) {
        background-color: #fffbeb;
        border-left-color: #f59e0b;
        color: #92400e;
    }
    
    :global(.readme-viewer .alert-error) {
        background-color: #fef2f2;
        border-left-color: #ef4444;
        color: #dc2626;
    }
    
    :global(.readme-viewer .alert-success) {
        background-color: #f0f9f9;
        border-left-color: #10b981;
        color: #047857;
    }
</style>