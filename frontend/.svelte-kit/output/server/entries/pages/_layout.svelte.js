import { s as subscribe } from "../../chunks/utils.js";
import { c as create_ssr_component } from "../../chunks/ssr.js";
import "../../chunks/index2.js";
import "../../chunks/runtime.js";
import { w as writable } from "../../chunks/index.js";
import { authToken } from "../../chunks/auth.js";
const app = "";
const theme = writable("light");
const ToastContainer_svelte_svelte_type_style_lang = "";
const Layout = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$unsubscribe_theme;
  let $$unsubscribe_authToken;
  $$unsubscribe_theme = subscribe(theme, (value) => value);
  $$unsubscribe_authToken = subscribe(authToken, (value) => value);
  $$unsubscribe_theme();
  $$unsubscribe_authToken();
  return `${`<div class="min-h-screen flex items-center justify-center" data-svelte-h="svelte-hhgcwc"><div class="text-center"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div> <p class="text-gray-600">Loading...</p></div></div>`}`;
});
export {
  Layout as default
};
