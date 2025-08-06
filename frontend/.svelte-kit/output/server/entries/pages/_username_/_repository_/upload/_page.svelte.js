import { s as subscribe } from "../../../../../chunks/utils.js";
import { c as create_ssr_component, e as escape, v as validate_component } from "../../../../../chunks/ssr.js";
import { p as page } from "../../../../../chunks/stores.js";
import { $ as $format } from "../../../../../chunks/runtime.esm.js";
import { u as user } from "../../../../../chunks/auth.js";
import { i as isOwner } from "../../../../../chunks/auth2.js";
import { L as Loading } from "../../../../../chunks/Loading.js";
const FileUpload_svelte_svelte_type_style_lang = "";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let username;
  let repositoryName;
  let $_, $$unsubscribe__;
  let $currentUser, $$unsubscribe_currentUser;
  let $page, $$unsubscribe_page;
  $$unsubscribe__ = subscribe($format, (value) => $_ = value);
  $$unsubscribe_currentUser = subscribe(user, (value) => $currentUser = value);
  $$unsubscribe_page = subscribe(page, (value) => $page = value);
  let repository = null;
  username = $page.params.username;
  repositoryName = $page.params.repository;
  $currentUser && repository && isOwner(repository.owner?.username || repository.owner?.id);
  $$unsubscribe__();
  $$unsubscribe_currentUser();
  $$unsubscribe_page();
  return `${$$result.head += `<!-- HEAD_svelte-180j70a_START -->${$$result.title = `<title>${escape($_("file.upload_files"))} - ${escape(username)}/${escape(repositoryName)} - GeoML-Hub</title>`, ""}<!-- HEAD_svelte-180j70a_END -->`, ""} ${`<div class="flex items-center justify-center min-h-96">${validate_component(Loading, "Loading").$$render($$result, {}, {}, {})}</div>`}`;
});
export {
  Page as default
};
