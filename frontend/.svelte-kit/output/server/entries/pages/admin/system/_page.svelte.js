import { c as create_ssr_component, o as onDestroy, e as escape } from "../../../../chunks/ssr.js";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  onDestroy(() => {
  });
  return `<div class="space-y-6"><div class="flex justify-between items-center"><h1 class="text-3xl font-bold text-gray-900" data-svelte-h="svelte-15whpoe">系统监控</h1> <div class="flex space-x-2"><button class="${"px-4 py-2 rounded-lg transition-colors " + escape(
    "bg-gray-200 text-gray-700 hover:bg-gray-300",
    true
  )}">${escape("开启自动刷新")}</button> <button class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors" data-svelte-h="svelte-q94kzf">立即刷新</button></div></div> ${`<div class="flex justify-center items-center h-64" data-svelte-h="svelte-2x2oyq"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>`}</div>`;
});
export {
  Page as default
};
