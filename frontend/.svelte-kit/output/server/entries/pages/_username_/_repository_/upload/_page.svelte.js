import { s as subscribe } from "../../../../../chunks/utils.js";
import { c as create_ssr_component, e as escape, v as validate_component } from "../../../../../chunks/ssr.js";
import { p as page } from "../../../../../chunks/stores.js";
import { $ as $format } from "../../../../../chunks/runtime.js";
import { user } from "../../../../../chunks/auth.js";
import { i as isOwner } from "../../../../../chunks/auth2.js";
import { L as Loading } from "../../../../../chunks/Loading.js";
const FileUpload_svelte_svelte_type_style_lang = "";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let repositoryName;
  let $$unsubscribe__;
  let $currentUser, $$unsubscribe_currentUser;
  let $page, $$unsubscribe_page;
  $$unsubscribe__ = subscribe($format, (value) => value);
  $$unsubscribe_currentUser = subscribe(user, (value) => $currentUser = value);
  $$unsubscribe_page = subscribe(page, (value) => $page = value);
  let repository = null;
  $page.params.username;
  repositoryName = $page.params.repository;
  $currentUser && repository && isOwner(repository.owner?.username || repository.owner?.id);
  $$unsubscribe__();
  $$unsubscribe_currentUser();
  $$unsubscribe_page();
  return `${$$result.head += `<!-- HEAD_svelte-qknquw_START -->${$$result.title = `<title>上传文件 - ${escape(repositoryName)} - GeoML-Hub</title>`, ""}<!-- HEAD_svelte-qknquw_END -->`, ""} ${`${validate_component(Loading, "Loading").$$render($$result, { message: "加载仓库信息..." }, {}, {})}`}  ${``}`;
});
export {
  Page as default
};
