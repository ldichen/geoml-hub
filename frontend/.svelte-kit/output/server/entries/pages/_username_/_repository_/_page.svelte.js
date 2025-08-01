import { s as subscribe, n as noop } from "../../../../chunks/utils.js";
import { c as create_ssr_component, e as escape, b as add_attribute, v as validate_component } from "../../../../chunks/ssr.js";
import { p as page } from "../../../../chunks/stores.js";
import "marked";
import "../../../../chunks/runtime.esm.js";
import "../../../../chunks/api.js";
import { u as user } from "../../../../chunks/auth.js";
import { i as isOwner } from "../../../../chunks/auth2.js";
import { L as Loading } from "../../../../chunks/Loading.js";
const _page_svelte_svelte_type_style_lang = "";
const css = {
  code: ".prose.svelte-9a9yia{max-width:none}.prose.svelte-9a9yia h1{font-size:1.875rem;line-height:2.25rem;font-weight:700;margin-top:2rem;margin-bottom:1rem}.prose.svelte-9a9yia h2{font-size:1.5rem;line-height:2rem;font-weight:600;margin-top:1.5rem;margin-bottom:0.75rem}.prose.svelte-9a9yia h3{font-size:1.25rem;line-height:1.75rem;font-weight:600;margin-top:1.25rem;margin-bottom:0.5rem}.prose.svelte-9a9yia p{margin-bottom:1rem;line-height:1.75}.prose.svelte-9a9yia ul{margin-bottom:1rem;padding-left:1.5rem}.prose.svelte-9a9yia li{margin-bottom:0.5rem}.prose.svelte-9a9yia code{background-color:#f1f5f9;padding:0.125rem 0.25rem;border-radius:0.25rem;font-size:0.875rem}.prose.svelte-9a9yia pre{background-color:#f1f5f9;padding:1rem;border-radius:0.375rem;overflow-x:auto;margin-bottom:1rem}",
  map: null
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let username;
  let repoName;
  let $currentUser, $$unsubscribe_currentUser = noop;
  let $page, $$unsubscribe_page;
  $$unsubscribe_currentUser = subscribe(user, (value) => $currentUser = value);
  $$unsubscribe_page = subscribe(page, (value) => $page = value);
  let repository = null;
  $$result.css.add(css);
  username = $page.params.username;
  repoName = $page.params.repository;
  $currentUser && repository && isOwner(repository.owner?.username || repository.owner?.id);
  $$unsubscribe_currentUser();
  $$unsubscribe_page();
  return `${$$result.head += `<!-- HEAD_svelte-dliw8c_START -->${$$result.title = `<title>${escape(username)}/${escape(repoName)} - GeoML Hub</title>`, ""}<meta name="description"${add_attribute("content", `${username}/${repoName} 仓库`, 0)}><!-- HEAD_svelte-dliw8c_END -->`, ""} <div class="min-h-screen bg-gray-50 dark:bg-gray-900">${`<div class="flex items-center justify-center py-12">${validate_component(Loading, "Loading").$$render($$result, { size: "lg" }, {}, {})}</div>`} </div>`;
});
export {
  Page as default
};
