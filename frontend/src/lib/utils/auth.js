import { get } from 'svelte/store';
import { isAuthenticated, user } from '$lib/stores/auth.js';
import { goto } from '$app/navigation';

/**
 * 检查用户是否已认证
 */
export function checkAuth() {
    return get(isAuthenticated);
}

/**
 * 获取当前用户
 */
export function getCurrentUser() {
    return get(user);
}

/**
 * 需要认证的路由保护
 */
export function requireAuth(redirectTo = '/login') {
    if (!checkAuth()) {
        goto(redirectTo);
        return false;
    }
    return true;
}

/**
 * 需要管理员权限
 */
export function requireAdmin(redirectTo = '/') {
    const currentUser = getCurrentUser();
    if (!checkAuth() || !currentUser?.is_admin) {
        goto(redirectTo);
        return false;
    }
    return true;
}

/**
 * 检查是否是资源所有者
 */
export function isOwner(resourceOwner) {
    const currentUser = getCurrentUser();
    return currentUser && (
        currentUser.username === resourceOwner || 
        currentUser.id === resourceOwner ||
        currentUser.is_admin
    );
}

/**
 * 重定向已认证用户
 */
export function redirectIfAuthenticated(redirectTo = '/') {
    if (checkAuth()) {
        goto(redirectTo);
        return true;
    }
    return false;
}

/**
 * 格式化用户头像URL
 */
export function getUserAvatarUrl(user, size = 'md') {
    if (user?.avatar_url) {
        return user.avatar_url;
    }
    
    // 使用Gravatar作为默认头像
    const email = user?.email || 'default@example.com';
    const hash = btoa(email.toLowerCase());
    const sizes = {
        sm: 32,
        md: 64,
        lg: 128,
        xl: 256
    };
    
    return `https://www.gravatar.com/avatar/${hash}?s=${sizes[size]}&d=identicon`;
}

/**
 * 格式化用户显示名称
 */
export function getUserDisplayName(user) {
    return user?.full_name || user?.username || 'Anonymous User';
}

/**
 * 检查用户权限
 */
export function hasPermission(permission, resource = null) {
    const currentUser = getCurrentUser();
    
    if (!currentUser) return false;
    
    // 管理员拥有所有权限
    if (currentUser.is_admin) return true;
    
    switch (permission) {
        case 'read':
            return true; // 所有认证用户都可以读取
        
        case 'write':
        case 'delete':
            return resource ? isOwner(resource.owner_id || resource.owner?.id) : false;
        
        case 'admin':
            return currentUser.is_admin;
        
        default:
            return false;
    }
}