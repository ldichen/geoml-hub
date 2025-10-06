import { writable } from 'svelte/store';
import { browser } from '$app/environment';

// 创建用户状态store
export const user = writable(null);
export const isAuthenticated = writable(false);
export const isLoading = writable(false);

// 创建token管理store
export const authToken = writable(null);

// 初始化认证状态
if (browser) {
    const storedToken = localStorage.getItem('authToken');
    const storedUser = localStorage.getItem('user');

    if (storedToken && storedUser) {
        try {
            // 动态检查token是否过期
            import('$lib/utils/auth.js').then(({ isTokenExpired, setupTokenRefreshTimer, setupVisibilityChangeHandler, autoRefreshToken }) => {
                if (isTokenExpired(storedToken)) {
                    console.log('Stored token is expired, attempting auto refresh...');
                    autoRefreshToken();
                } else {
                    // Token有效，设置状态和监听器
                    authToken.set(storedToken);
                    user.set(JSON.parse(storedUser));
                    isAuthenticated.set(true);

                    // 启动自动刷新机制
                    setupTokenRefreshTimer();
                    setupVisibilityChangeHandler();
                }
            });
        } catch (error) {
            console.error('Failed to parse stored user data:', error);
            logout();
        }
    }
}

// 认证函数
export function login(token, userData, refreshToken = null) {
    if (browser) {
        localStorage.setItem('authToken', token);
        localStorage.setItem('user', JSON.stringify(userData));
        if (refreshToken) {
            localStorage.setItem('refreshToken', refreshToken);
        }
    }

    authToken.set(token);
    user.set(userData);
    isAuthenticated.set(true);

    // 启动自动刷新机制
    if (browser) {
        import('$lib/utils/auth.js').then(({ setupTokenRefreshTimer, setupVisibilityChangeHandler }) => {
            setupTokenRefreshTimer();
            setupVisibilityChangeHandler();
        });
    }
}

export function logout() {
    if (browser) {
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        localStorage.removeItem('refreshToken');
    }

    authToken.set(null);
    user.set(null);
    isAuthenticated.set(false);

    // 清除token刷新定时器
    if (browser) {
        import('$lib/utils/auth.js').then(({ clearTokenRefreshTimer }) => {
            clearTokenRefreshTimer();
        });
    }
}

export function updateUser(userData) {
    if (browser) {
        localStorage.setItem('user', JSON.stringify(userData));
    }
    user.set(userData);
}