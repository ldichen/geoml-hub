/*
 * @Author: DiChen
 * @Date: 2025-11-18
 * @LastEditors: DiChen
 * @LastEditTime: 2025-11-18
 */

// 注册页面 - 预渲染(静态页面)
export const prerender = true;

export async function load() {
	return {
		meta: {
			title: '注册 - GeoML-Hub',
			description: '创建 GeoML-Hub 账户',
			keywords: '注册,创建账户,GeoML-Hub'
		}
	};
}
