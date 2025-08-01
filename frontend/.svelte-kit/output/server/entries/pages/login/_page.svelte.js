import { s as subscribe } from "../../../chunks/utils.js";
import { c as create_ssr_component, e as escape, b as add_attribute } from "../../../chunks/ssr.js";
import "../../../chunks/api.js";
import { $ as $format } from "../../../chunks/runtime.esm.js";
const _page_svelte_svelte_type_style_lang = "";
const css = {
  code: "body{overflow-x:hidden}",
  map: null
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $_, $$unsubscribe__;
  $$unsubscribe__ = subscribe($format, (value) => $_ = value);
  let email = "";
  let password = "";
  $$result.css.add(css);
  $$unsubscribe__();
  return `${$$result.head += `<!-- HEAD_svelte-5axj8v_START -->${$$result.title = `<title>${escape($_("auth.login"))} - GeoML-Hub</title>`, ""}<!-- HEAD_svelte-5axj8v_END -->`, ""} <div class="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center px-4"><div class="max-w-md w-full space-y-8"> <div class="text-center"><div class="mx-auto h-12 w-12 bg-primary-600 rounded-lg flex items-center justify-center" data-svelte-h="svelte-v406zk"><svg class="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path></svg></div> <h2 class="mt-6 text-3xl font-bold text-gray-900 dark:text-white">${escape($_("auth.welcome_back"))}</h2> <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">${escape($_("auth.login_subtitle"))}</p></div>  <div class="bg-white dark:bg-gray-800 py-8 px-4 shadow-xl rounded-lg sm:px-10"><form class="space-y-6"> <div><label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300">${escape($_("auth.email"))}</label> <div class="mt-1"><input id="email" name="email" type="email" autocomplete="email" required class="input w-full"${add_attribute("placeholder", $_("auth.email_placeholder"), 0)} ${""}${add_attribute("value", email, 0)}></div></div>  <div><label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300">${escape($_("auth.password"))}</label> <div class="mt-1"><input id="password" name="password" type="password" autocomplete="current-password" required class="input w-full"${add_attribute("placeholder", $_("auth.password_placeholder"), 0)} ${""}${add_attribute("value", password, 0)}></div></div>  ${``}  <div><button type="submit" ${""} class="btn btn-primary w-full flex justify-center items-center">${`${escape($_("auth.login"))}`}</button></div>  <div class="flex items-center justify-between"><div class="text-sm"><a href="/forgot-password" class="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400">${escape($_("auth.forgot_password"))}</a></div></div></form>  <div class="mt-6"><div class="relative"><div class="absolute inset-0 flex items-center" data-svelte-h="svelte-18vhlcr"><div class="w-full border-t border-gray-300 dark:border-gray-600"></div></div> <div class="relative flex justify-center text-sm"><span class="px-2 bg-white dark:bg-gray-800 text-gray-500">${escape($_("auth.or"))}</span></div></div> <div class="mt-6 text-center"><p class="text-sm text-gray-600 dark:text-gray-400">${escape($_("auth.no_account"))} <a href="/register" class="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400">${escape($_("auth.sign_up"))}</a></p></div></div></div></div> </div>`;
});
export {
  Page as default
};
