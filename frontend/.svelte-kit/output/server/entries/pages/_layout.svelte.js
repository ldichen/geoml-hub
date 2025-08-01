import { s as subscribe } from "../../chunks/utils.js";
import { c as create_ssr_component } from "../../chunks/ssr.js";
import "../../chunks/index2.js";
import "../../chunks/runtime.esm.js";
import { a as authToken } from "../../chunks/auth.js";
import "../../chunks/api.js";
const app = "";
const ToastContainer_svelte_svelte_type_style_lang = "";
const Layout = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $$unsubscribe_authToken;
  $$unsubscribe_authToken = subscribe(authToken, (value) => value);
  $$unsubscribe_authToken();
  return `${`<div class="min-h-screen flex items-center justify-center" data-svelte-h="svelte-hhgcwc"><div class="text-center"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div> <p class="text-gray-600">Loading...</p></div></div>`}`;
});
export {
  Layout as default
};
