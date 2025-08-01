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
            authToken.set(storedToken);
            user.set(JSON.parse(storedUser));
            isAuthenticated.set(true);
        } catch (error) {
            console.error('Failed to parse stored user data:', error);
            logout();
        }
    }
}

// 认证函数
export function login(token, userData) {
    if (browser) {
        localStorage.setItem('authToken', token);
        localStorage.setItem('user', JSON.stringify(userData));
    }
    
    authToken.set(token);
    user.set(userData);
    isAuthenticated.set(true);
}

export function logout() {
    if (browser) {
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
    }
    
    authToken.set(null);
    user.set(null);
    isAuthenticated.set(false);
}

export function updateUser(userData) {
    if (browser) {
        localStorage.setItem('user', JSON.stringify(userData));
    }
    user.set(userData);
}