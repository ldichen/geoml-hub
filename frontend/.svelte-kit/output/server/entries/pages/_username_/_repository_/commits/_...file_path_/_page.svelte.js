import { s as subscribe } from "../../../../../../chunks/utils.js";
import { c as create_ssr_component, e as escape, v as validate_component } from "../../../../../../chunks/ssr.js";
import { p as page } from "../../../../../../chunks/stores.js";
import "../../../../../../chunks/runtime.js";
import { L as Loading } from "../../../../../../chunks/Loading.js";
const VersionHistory_svelte_svelte_type_style_lang = "";
const VersionDiff_svelte_svelte_type_style_lang = "";
const _page_svelte_svelte_type_style_lang = "";
const css = {
  code: ".commits-page.svelte-73udgn{min-height:100vh;background:#f8f9fa;display:flex;flex-direction:column}",
  map: null
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let repositoryName;
  let filePath;
  let $page, $$unsubscribe_page;
  $$unsubscribe_page = subscribe(page, (value) => $page = value);
  $$result.css.add(css);
  $page.params.username;
  repositoryName = $page.params.repository;
  filePath = $page.params.file_path;
  $$unsubscribe_page();
  return `${$$result.head += `<!-- HEAD_svelte-1bm64vf_START -->${$$result.title = `<title>版本历史 - ${escape(filePath)} - ${escape(repositoryName)} - GeoML-Hub</title>`, ""}<!-- HEAD_svelte-1bm64vf_END -->`, ""} ${``} <div class="commits-page svelte-73udgn"> ${``}  <div class="bg-white border-b border-gray-200"><div class="container mx-auto px-4 py-4">${`<div class="animate-pulse" data-svelte-h="svelte-1f6xwox"><div class="h-6 bg-gray-200 rounded w-1/2 mb-2"></div> <div class="h-4 bg-gray-200 rounded w-1/3"></div></div>`}</div></div>  <div class="flex-1">${`${validate_component(Loading, "Loading").$$render($$result, { message: "加载版本历史中..." }, {}, {})}`}</div> </div>`;
});
export {
  Page as default
};
