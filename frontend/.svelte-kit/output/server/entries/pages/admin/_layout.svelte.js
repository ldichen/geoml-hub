import { s as subscribe } from "../../../chunks/utils.js";
import { c as create_ssr_component } from "../../../chunks/ssr.js";
import { p as page } from "../../../chunks/stores.js";
const Layout = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$unsubscribe_page;
  $$unsubscribe_page = subscribe(page, (value) => value);
  $$unsubscribe_page();
  return `${`<div class="min-h-screen flex items-center justify-center bg-gray-50" data-svelte-h="svelte-1i7unxm"><div class="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div></div>`}`;
});
export {
  Layout as default
};
