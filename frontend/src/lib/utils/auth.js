import { get } from 'svelte/store';
import { isAuthenticated, user, authToken, logout } from '$lib/stores/auth.js';
import { goto } from '$app/navigation';
import { browser } from '$app/environment';

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

/**
 * 解析JWT token
 */
export function parseJwtToken(token) {
    try {
        if (!token) return null;

        const parts = token.split('.');
        if (parts.length !== 3) return null;

        const payload = JSON.parse(atob(parts[1]));
        return payload;
    } catch (error) {
        console.error('Failed to parse JWT token:', error);
        return null;
    }
}

/**
 * 检查token是否过期
 */
export function isTokenExpired(token) {
    const payload = parseJwtToken(token);
    if (!payload || !payload.exp) return true;

    // exp是Unix时间戳(秒)，需要转换为毫秒
    const expirationTime = payload.exp * 1000;
    const currentTime = Date.now();

    return currentTime >= expirationTime;
}

/**
 * 获取token剩余有效时间(毫秒)
 */
export function getTokenRemainingTime(token) {
    const payload = parseJwtToken(token);
    if (!payload || !payload.exp) return 0;

    const expirationTime = payload.exp * 1000;
    const currentTime = Date.now();
    const remainingTime = expirationTime - currentTime;

    return Math.max(0, remainingTime);
}

/**
 * 检查token是否即将过期(默认30分钟内)
 */
export function isTokenExpiringSoon(token, thresholdMinutes = 30) {
    const remainingTime = getTokenRemainingTime(token);
    const thresholdMs = thresholdMinutes * 60 * 1000;

    return remainingTime <= thresholdMs && remainingTime > 0;
}

/**
 * 检查当前认证状态和token有效性
 */
export function checkTokenValidity() {
    if (!browser) return { valid: false, expired: true };

    const token = get(authToken) || localStorage.getItem('authToken');
    const isAuth = get(isAuthenticated);

    if (!token || !isAuth) {
        return { valid: false, expired: true, needsRefresh: false };
    }

    const expired = isTokenExpired(token);
    const expiringSoon = isTokenExpiringSoon(token);

    return {
        valid: !expired,
        expired: expired,
        needsRefresh: expiringSoon,
        remainingTime: getTokenRemainingTime(token)
    };
}

// 刷新状态跟踪
let refreshPromise = null;
let refreshTimer = null;

/**
 * 静默刷新token
 */
export async function refreshTokenSilently() {
    if (!browser) return { success: false, error: 'Not in browser environment' };

    // 如果已经在刷新中，返回同一个Promise
    if (refreshPromise) {
        return refreshPromise;
    }

    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) {
        console.warn('No refresh token found, user needs to login again');
        logout();
        return { success: false, error: 'No refresh token available' };
    }

    refreshPromise = performTokenRefresh(refreshToken);

    try {
        const result = await refreshPromise;
        return result;
    } finally {
        refreshPromise = null;
    }
}

/**
 * 执行token刷新
 */
async function performTokenRefresh(refreshToken) {
    try {
        // 动态导入API以避免循环依赖
        const { api } = await import('$lib/utils/api.js');

        const result = await api.refreshToken(refreshToken);

        if (result.success) {
            // 更新localStorage中的tokens
            localStorage.setItem('authToken', result.data.access_token);
            if (result.data.refresh_token) {
                localStorage.setItem('refreshToken', result.data.refresh_token);
            }

            // 更新stores
            const { login } = await import('$lib/stores/auth.js');
            const userData = JSON.parse(localStorage.getItem('user') || '{}');
            login(result.data.access_token, userData);

            console.log('Token refreshed successfully');
            return { success: true, data: result.data };
        } else {
            console.error('Token refresh failed:', result.error);
            logout();
            return { success: false, error: result.error };
        }
    } catch (error) {
        console.error('Token refresh error:', error);
        logout();
        return { success: false, error: error.message };
    }
}

/**
 * 自动检查并刷新token
 */
export async function autoRefreshToken() {
    if (!browser) return;

    const validity = checkTokenValidity();

    if (validity.expired) {
        console.log('Token已过期，尝试刷新...');
        return await refreshTokenSilently();
    } else if (validity.needsRefresh) {
        console.log('Token即将过期，提前刷新...');
        return await refreshTokenSilently();
    }

    return { success: true, message: 'Token still valid' };
}

/**
 * 设置定期token检查
 */
export function setupTokenRefreshTimer() {
    if (!browser) return;

    // 清除现有定时器
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }

    // 每5分钟检查一次token状态
    refreshTimer = setInterval(async () => {
        const validity = checkTokenValidity();

        if (validity.needsRefresh && !refreshPromise) {
            console.log('定期检查：Token即将过期，开始刷新...');
            await autoRefreshToken();
        } else if (validity.expired) {
            console.log('定期检查：Token已过期，停止定时器');
            clearInterval(refreshTimer);
            refreshTimer = null;
        }
    }, 5 * 60 * 1000); // 5分钟

    console.log('Token refresh timer started');
}

/**
 * 清除token刷新定时器
 */
export function clearTokenRefreshTimer() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
        console.log('Token refresh timer cleared');
    }
}

/**
 * 在页面可见性变化时检查token
 */
export function setupVisibilityChangeHandler() {
    if (!browser || typeof document === 'undefined') return;

    document.addEventListener('visibilitychange', async () => {
        if (document.visibilityState === 'visible') {
            // 页面变为可见时检查token状态
            const validity = checkTokenValidity();
            if (validity.expired || validity.needsRefresh) {
                console.log('页面恢复可见，检查token状态...');
                await autoRefreshToken();
            }
        }
    });
}