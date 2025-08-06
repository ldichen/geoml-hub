import { c as create_ssr_component } from "../../../../chunks/ssr.js";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  return `<div class="space-y-6"><div class="flex justify-between items-center"><h1 class="text-3xl font-bold text-gray-900" data-svelte-h="svelte-n2f5g9">存储管理</h1> <button class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors" data-svelte-h="svelte-1yqi5he">刷新数据</button></div> ${`<div class="flex justify-center items-center h-64" data-svelte-h="svelte-2x2oyq"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>`}</div>`;
});
export {
  Page as default
};
