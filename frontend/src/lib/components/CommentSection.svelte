<script>
    import { onMount, createEventDispatcher } from 'svelte';
    import { _ } from 'svelte-i18n';
    import { MessageCircle, Send, Reply, MoreHorizontal, Heart, Flag } from 'lucide-svelte';
    import { formatDistanceToNow } from 'date-fns';
    import { zhCN } from 'date-fns/locale';
    import { user as currentUser } from '$lib/stores/auth.js';
    import { api } from '$lib/utils/api.js';
    import UserAvatar from './UserAvatar.svelte';
    import Loading from './Loading.svelte';
    
    export let resourceType = 'repository'; // repository, model, etc.
    export let resourceId;
    export let allowReplies = true;
    export const maxDepth = 3;
    
    const dispatch = createEventDispatcher();
    
    let comments = [];
    let loading = true;
    let error = '';
    let newComment = '';
    let posting = false;
    let replyingTo = null;
    let replyText = '';
    
    onMount(() => {
        loadComments();
    });
    
    async function loadComments() {
        loading = true;
        error = '';
        
        try {
            const response = await api.getComments(resourceType, resourceId);
            comments = buildCommentTree(response.data || response);
        } catch (err) {
            console.error('Failed to load comments:', err);
            error = $_('error.network_error');
        } finally {
            loading = false;
        }
    }
    
    function buildCommentTree(flatComments) {
        const commentMap = new Map();
        const rootComments = [];
        
        // 首先创建所有评论的映射
        flatComments.forEach(comment => {
            comment.replies = [];
            commentMap.set(comment.id, comment);
        });
        
        // 然后构建树结构
        flatComments.forEach(comment => {
            if (comment.parent_id) {
                const parent = commentMap.get(comment.parent_id);
                if (parent) {
                    parent.replies.push(comment);
                }
            } else {
                rootComments.push(comment);
            }
        });
        
        return rootComments;
    }
    
    async function postComment() {
        if (!newComment.trim() || !$currentUser) return;
        
        posting = true;
        
        try {
            const response = await api.createComment(resourceType, resourceId, {
                content: newComment.trim()
            });
            
            // 添加到评论列表顶部
            comments = [response, ...comments];
            newComment = '';
            
            dispatch('commentAdded', response);
        } catch (err) {
            console.error('Failed to post comment:', err);
            error = $_('comment.post_failed');
        } finally {
            posting = false;
        }
    }
    
    async function postReply(parentId) {
        if (!replyText.trim() || !$currentUser) return;
        
        posting = true;
        
        try {
            const response = await api.createComment(resourceType, resourceId, {
                content: replyText.trim(),
                parent_id: parentId
            });
            
            // 找到父评论并添加回复
            const parent = findCommentById(comments, parentId);
            if (parent) {
                parent.replies.push(response);
                comments = [...comments]; // 触发响应式更新
            }
            
            replyText = '';
            replyingTo = null;
            
            dispatch('replyAdded', response);
        } catch (err) {
            console.error('Failed to post reply:', err);
            error = $_('comment.reply_failed');
        } finally {
            posting = false;
        }
    }
    
    function findCommentById(commentList, id) {
        for (const comment of commentList) {
            if (comment.id === id) return comment;
            const found = findCommentById(comment.replies, id);
            if (found) return found;
        }
        return null;
    }
    
    async function toggleLike(comment) {
        if (!$currentUser) return;
        
        try {
            if (comment.is_liked) {
                await api.unlikeComment(comment.id);
                comment.is_liked = false;
                comment.likes_count -= 1;
            } else {
                await api.likeComment(comment.id);
                comment.is_liked = true;
                comment.likes_count += 1;
            }
            
            comments = [...comments]; // 触发响应式更新
        } catch (err) {
            console.error('Failed to toggle like:', err);
        }
    }
    
    function startReply(commentId) {
        replyingTo = commentId;
        replyText = '';
    }
    
    function cancelReply() {
        replyingTo = null;
        replyText = '';
    }
    
    function handleKeyPress(event, action) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            if (action === 'comment') {
                postComment();
            } else if (action === 'reply') {
                postReply(replyingTo);
            }
        }
    }
</script>

<div class="comment-section">
    <!-- 评论输入区 -->
    {#if $currentUser}
        <div class="mb-6">
            <div class="flex space-x-3">
                <UserAvatar user={$currentUser} size="sm" />
                <div class="flex-1">
                    <textarea
                        bind:value={newComment}
                        placeholder={$_('comment.write_comment')}
                        on:keypress={e => handleKeyPress(e, 'comment')}
                        class="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg resize-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:text-white"
                        rows="3"
                        disabled={posting}
                    ></textarea>
                    
                    <div class="flex items-center justify-between mt-2">
                        <p class="text-xs text-gray-500 dark:text-gray-400">
                            {$_('comment.markdown_supported')}
                        </p>
                        <button
                            on:click={postComment}
                            disabled={!newComment.trim() || posting}
                            class="btn btn-primary btn-sm flex items-center"
                        >
                            {#if posting}
                                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            {:else}
                                <Send class="w-4 h-4 mr-2" />
                            {/if}
                            {$_('comment.post')}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    {:else}
        <div class="mb-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <p class="text-center text-gray-600 dark:text-gray-400">
                <a href="/login" class="text-primary-600 dark:text-primary-400 hover:underline">
                    {$_('auth.login')}
                </a>
                {$_('comment.login_to_comment')}
            </p>
        </div>
    {/if}
    
    <!-- 评论列表 -->
    {#if loading}
        <div class="flex justify-center py-8">
            <Loading />
        </div>
    {:else if error}
        <div class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p class="text-red-800 dark:text-red-200">{error}</p>
        </div>
    {:else if comments.length > 0}
        <div class="space-y-6">
            <!-- 评论统计 -->
            <div class="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                <MessageCircle class="w-4 h-4" />
                <span>{comments.length} {$_('comment.comments')}</span>
            </div>
            
            <!-- 评论树 -->
            {#each comments as comment}
                <div class="comment-item" data-depth="0">
                    <div class="flex space-x-3">
                        <UserAvatar user={comment.author} size="sm" />
                        <div class="flex-1 min-w-0">
                            <!-- 评论头部 -->
                            <div class="flex items-center space-x-2 mb-2">
                                <span class="font-medium text-gray-900 dark:text-white">
                                    {comment.author.username}
                                </span>
                                {#if comment.author.is_verified}
                                    <span class="text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 px-1.5 py-0.5 rounded">
                                        {$_('user.verified')}
                                    </span>
                                {/if}
                                <span class="text-xs text-gray-500 dark:text-gray-400">
                                    {formatDistanceToNow(new Date(comment.created_at), { addSuffix: true, locale: zhCN })}
                                </span>
                            </div>
                            
                            <!-- 评论内容 -->
                            <div class="prose prose-sm dark:prose-invert max-w-none mb-3">
                                <p>{comment.content}</p>
                            </div>
                            
                            <!-- 评论操作 -->
                            <div class="flex items-center space-x-4 text-sm">
                                <!-- 点赞 -->
                                <button
                                    on:click={() => toggleLike(comment)}
                                    class="flex items-center space-x-1 text-gray-500 hover:text-red-500 transition-colors"
                                    class:text-red-500={comment.is_liked}
                                >
                                    <Heart class="w-4 h-4" fill={comment.is_liked ? 'currentColor' : 'none'} />
                                    <span>{comment.likes_count || 0}</span>
                                </button>
                                
                                <!-- 回复 -->
                                {#if allowReplies && $currentUser}
                                    <button
                                        on:click={() => startReply(comment.id)}
                                        class="flex items-center space-x-1 text-gray-500 hover:text-primary-500 transition-colors"
                                    >
                                        <Reply class="w-4 h-4" />
                                        <span>{$_('comment.reply')}</span>
                                    </button>
                                {/if}
                                
                                <!-- 更多操作 -->
                                <button class="text-gray-500 hover:text-gray-700 p-1">
                                    <MoreHorizontal class="w-4 h-4" />
                                </button>
                            </div>
                            
                            <!-- 回复输入框 -->
                            {#if replyingTo === comment.id}
                                <div class="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                                    <textarea
                                        bind:value={replyText}
                                        placeholder={$_('comment.write_reply')}
                                        on:keypress={(e) => handleKeyPress(e, 'reply')}
                                        class="w-full p-2 border border-gray-300 dark:border-gray-600 rounded resize-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                                        rows="2"
                                        disabled={posting}
                                    ></textarea>
                                    
                                    <div class="flex items-center justify-end space-x-2 mt-2">
                                        <button
                                            on:click={cancelReply}
                                            class="btn btn-secondary btn-sm"
                                            disabled={posting}
                                        >
                                            {$_('common.cancel')}
                                        </button>
                                        <button
                                            on:click={() => postReply(comment.id)}
                                            disabled={!replyText.trim() || posting}
                                            class="btn btn-primary btn-sm flex items-center"
                                        >
                                            {#if posting}
                                                <div class="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                                            {:else}
                                                <Send class="w-3 h-3 mr-1" />
                                            {/if}
                                            {$_('comment.reply')}
                                        </button>
                                    </div>
                                </div>
                            {/if}
                            
                            <!-- 嵌套回复 -->
                            {#if comment.replies && comment.replies.length > 0}
                                <div class="mt-4 space-y-4 border-l-2 border-gray-100 dark:border-gray-700 pl-4">
                                    {#each comment.replies as reply}
                                        <div class="comment-item" data-depth="1">
                                            <div class="flex space-x-3">
                                                <UserAvatar user={reply.author} size="sm" />
                                                <div class="flex-1 min-w-0">
                                                    <div class="flex items-center space-x-2 mb-2">
                                                        <span class="font-medium text-gray-900 dark:text-white">
                                                            {reply.author.username}
                                                        </span>
                                                        <span class="text-xs text-gray-500 dark:text-gray-400">
                                                            {formatDistanceToNow(new Date(reply.created_at), { addSuffix: true, locale: zhCN })}
                                                        </span>
                                                    </div>
                                                    <div class="prose prose-sm dark:prose-invert max-w-none mb-3">
                                                        <p>{reply.content}</p>
                                                    </div>
                                                    <div class="flex items-center space-x-4 text-sm">
                                                        <button
                                                            on:click={() => toggleLike(reply)}
                                                            class="flex items-center space-x-1 text-gray-500 hover:text-red-500 transition-colors"
                                                            class:text-red-500={reply.is_liked}
                                                        >
                                                            <Heart class="w-4 h-4" fill={reply.is_liked ? 'currentColor' : 'none'} />
                                                            <span>{reply.likes_count || 0}</span>
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    {/each}
                                </div>
                            {/if}
                        </div>
                    </div>
                </div>
            {/each}
        </div>
    {:else}
        <div class="text-center py-12">
            <MessageCircle class="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p class="text-gray-500 dark:text-gray-400">
                {$_('comment.no_comments')}
            </p>
            {#if $currentUser}
                <p class="text-sm text-gray-400 dark:text-gray-500 mt-2">
                    {$_('comment.be_first')}
                </p>
            {/if}
        </div>
    {/if}
</div>

<style>
    .comment-section {
        max-width: none;
    }
    
    .comment-item {
        position: relative;
    }
    
    .comment-item[data-depth="0"] {
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    .dark .comment-item[data-depth="0"] {
        border-bottom-color: #374151;
    }
    
    .comment-item[data-depth="0"]:last-child {
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
    }
    
    :global(.prose p) {
        margin-bottom: 0.75rem;
    }
    
    :global(.prose p:last-child) {
        margin-bottom: 0;
    }
</style>