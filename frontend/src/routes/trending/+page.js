/*
 * @Author: DiChen
 * @Date: 2025-11-18
 * @LastEditors: DiChen
 * @LastEditTime: 2025-11-18
 */

// 趋势/探索页面预渲染配置
export const prerender = true;

export async function load() {
	return {
		meta: {
			title: '探索模型 - GeoML-Hub',
			description: '探索最新和最热门的地理科学机器学习模型',
			keywords: '模型探索,热门模型,趋势,GeoML'
		}
	};
}
