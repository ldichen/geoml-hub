/*
 * @Author: DiChen
 * @Date: 2025-07-26 15:58:59
 * @LastEditors: DiChen
 * @LastEditTime: 2025-10-10 15:31:28
 */
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
	const env = loadEnv(mode, process.cwd(), '');

	return {
		plugins: [sveltekit()],
		server: {
			host: true,
			port: 5173,
			proxy: {
				'/api': {
					target: 'http://localhost:8000', // 代理指向本地后端
					changeOrigin: true,
					secure: false
				}
			}
		}
	};
});
