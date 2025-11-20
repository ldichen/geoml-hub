import { c as create_ssr_component, v as validate_component } from "../../../../chunks/ssr.js";
import { L as Loading } from "../../../../chunks/Loading.js";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  return `<div class="max-w-7xl mx-auto"> <div class="mb-8" data-svelte-h="svelte-fnkk7z"><h1 class="text-3xl font-bold text-gray-900 dark:text-white">分类管理</h1> <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">管理地球科学领域分类和任务类型分类的名称、图标和描述</p></div>  ${``} ${``}  <div class="mb-8"><h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6" data-svelte-h="svelte-tlslp5">科学领域分类</h2> <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">${`<div class="flex items-center justify-center py-12">${validate_component(Loading, "Loading").$$render($$result, {}, {}, {})}</div>`}</div></div>  <div class="mt-8"><h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6" data-svelte-h="svelte-1a35yn7">任务类型分类</h2> <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">${`<div class="flex items-center justify-center py-12">${validate_component(Loading, "Loading").$$render($$result, {}, {}, {})}</div>`}</div></div></div>`;
});
export {
  Page as default
};
