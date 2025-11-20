/*
 * @Author: DiChen
 * @Date: 2025-07-09 21:01:24
 * @LastEditors: DiChen
 * @LastEditTime: 2025-11-18 23:43:07
 */
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/kit/vite';

// 判断是否为开发环境
const dev = process.env.NODE_ENV === 'development';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),

	kit: {
		adapter: adapter({
			pages: 'build', // 输出目录
			assets: 'build', // 静态资源目录
			fallback: 'index.html', // SPA 模式回退页面
			precompress: true, // 是否预压缩（gzip/brotli）
			strict: false
		}),
		paths: {
			base: dev ? '' : '/geoml-hub' // 开发环境无前缀，生产环境有前缀
		},
		alias: {
			$lib: './src/lib',
			$components: './src/lib/components',
			$stores: './src/lib/stores',
			$utils: './src/lib/utils',
			$types: './src/lib/types',
			$i18n: './src/lib/i18n'
		}
	}
};

export default config;
