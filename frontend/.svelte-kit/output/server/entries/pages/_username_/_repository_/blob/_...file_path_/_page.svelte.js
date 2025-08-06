import { s as subscribe } from "../../../../../../chunks/utils.js";
import { c as create_ssr_component, e as escape, v as validate_component } from "../../../../../../chunks/ssr.js";
import { p as page } from "../../../../../../chunks/stores.js";
import { u as user } from "../../../../../../chunks/auth.js";
import "../../../../../../chunks/runtime.esm.js";
import { L as Loading } from "../../../../../../chunks/Loading.js";
const _page_svelte_svelte_type_style_lang = "";
const css = {
  code: ".file-content.svelte-74h4nk pre{background:#f8f9fa;border-radius:0;margin:0}.file-content.svelte-74h4nk .metadata-block pre{background:transparent !important;margin:0;line-height:1.4}.file-content.svelte-74h4nk pre code{background:none;padding:0;font-size:inherit;color:inherit}.file-content.svelte-74h4nk .yaml-frontmatter{color:#6f42c1}.file-content.svelte-74h4nk .yaml-key{color:#005cc5;font-weight:600}.file-content.svelte-74h4nk .yaml-value{color:#032f62}.file-content.svelte-74h4nk .yaml-comment{color:#6a737d;font-style:italic}.file-content.svelte-74h4nk .md-header{color:#005cc5;font-weight:bold}.file-content.svelte-74h4nk .md-bold{color:#d73a49;font-weight:bold}.file-content.svelte-74h4nk .md-italic{color:#6f42c1;font-style:italic}.file-content.svelte-74h4nk .md-link{color:#0366d6;text-decoration:none}.file-content.svelte-74h4nk .md-code-block{color:#e36209;background:rgba(255, 229, 100, 0.2);padding:2px 4px;border-radius:3px}.file-content.svelte-74h4nk .md-inline-code{color:#e36209;background:rgba(255, 229, 100, 0.2);padding:1px 3px;border-radius:2px;font-family:'SFMono-Regular', Consolas, monospace}.file-content.svelte-74h4nk .md-list{color:#22863a}.file-content.svelte-74h4nk pre.bg-gray-50 .yaml-key{color:#005cc5;font-weight:600}.file-content.svelte-74h4nk pre.bg-gray-50 .yaml-value{color:#032f62}.file-content.svelte-74h4nk pre.bg-gray-50 .yaml-comment{color:#6a737d;font-style:italic}.file-content.svelte-74h4nk pre.bg-gray-50 .md-header{color:#005cc5;font-weight:bold}.file-content.svelte-74h4nk pre.bg-gray-50 .md-bold{color:#d73a49;font-weight:bold}.file-content.svelte-74h4nk pre.bg-gray-50 .md-italic{color:#6f42c1;font-style:italic}.file-content.svelte-74h4nk pre.bg-gray-50 .md-link{color:#0366d6}.file-content.svelte-74h4nk pre.bg-gray-50 .md-code-block{color:#e36209;background:rgba(255, 229, 100, 0.2);padding:2px 4px;border-radius:3px}.file-content.svelte-74h4nk pre.bg-gray-50 .md-inline-code{color:#e36209;background:rgba(255, 229, 100, 0.2);padding:1px 3px;border-radius:2px}.file-content.svelte-74h4nk pre.bg-gray-50 .md-list{color:#22863a}.file-content.svelte-74h4nk .metadata-block{box-shadow:0 1px 3px rgba(0, 0, 0, 0.1)}.file-content.svelte-74h4nk .metadata-block .yaml-key{color:#9cdcfe;font-weight:600}.file-content.svelte-74h4nk .metadata-block .yaml-value{color:#ce9178}.file-content.svelte-74h4nk .metadata-block .yaml-comment{color:#6a9955;font-style:italic}",
  map: null
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let repositoryName;
  let $$unsubscribe_currentUser;
  let $page, $$unsubscribe_page;
  $$unsubscribe_currentUser = subscribe(user, (value) => value);
  $$unsubscribe_page = subscribe(page, (value) => $page = value);
  $$result.css.add(css);
  $page.params.username;
  repositoryName = $page.params.repository;
  $page.params.file_path;
  $$unsubscribe_currentUser();
  $$unsubscribe_page();
  return `${$$result.head += `<!-- HEAD_svelte-15hzk4u_START -->${$$result.title = `<title>${escape("文件查看")} - ${escape(repositoryName)} - GeoML-Hub</title>`, ""}<!-- HEAD_svelte-15hzk4u_END -->`, ""} ${``} <div class="file-viewer"> ${``} <div class="bg-white"><div class="container mx-auto px-4 py-6">${`${validate_component(Loading, "Loading").$$render($$result, { message: "加载文件中..." }, {}, {})}`}</div></div> </div>`;
});
export {
  Page as default
};
