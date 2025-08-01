// @ts-nocheck
import { register, init, getLocaleFromNavigator } from 'svelte-i18n';
import { browser } from '$app/environment';

register('en-US', () => import('./locales/en-US.json'));
register('zh-CN', () => import('./locales/zh-CN.json'));

function getInitialLocale() {
  if (browser) {
    const stored = localStorage.getItem('geoml-locale');
    if (stored) return stored;
  }
  return getLocaleFromNavigator() || 'zh-CN';
}

init({
  fallbackLocale: 'zh-CN',
  initialLocale: getInitialLocale(),
});

export function switchLocale(locale) {
  if (browser) {
    localStorage.setItem('geoml-locale', locale);
    window.location.reload();
  }
}