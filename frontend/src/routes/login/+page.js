/*
 * @Author: DiChen
 * @Date: 2025-11-18
 * @LastEditors: DiChen
 * @LastEditTime: 2025-11-18
 */

// 登录页面 - 预渲染(静态页面)
export const prerender = true;

export async function load() {
	return {
		meta: {
			title: '登录 - GeoML-Hub',
			description: '登录 GeoML-Hub 账户',
			keywords: '登录,账户,GeoML-Hub'
		}
	};
}
