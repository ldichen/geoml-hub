import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export const theme = writable('light');

// 初始化主题
if (browser) {
    const storedTheme = localStorage.getItem('theme') || 'light';
    theme.set(storedTheme);
    document.documentElement.setAttribute('data-theme', storedTheme);
}

// 主题切换函数（三种模式循环切换）
export function toggleTheme() {
    theme.update(current => {
        const themeOrder = ['light', 'dark', 'system'];
        const currentIndex = themeOrder.indexOf(current);
        const nextIndex = (currentIndex + 1) % themeOrder.length;
        const newTheme = themeOrder[nextIndex];
        
        if (browser) {
            localStorage.setItem('theme', newTheme);
            document.documentElement.setAttribute('data-theme', newTheme);
        }
        
        return newTheme;
    });
}

export function setTheme(newTheme) {
    if (browser) {
        localStorage.setItem('theme', newTheme);
        document.documentElement.setAttribute('data-theme', newTheme);
    }
    theme.set(newTheme);
}