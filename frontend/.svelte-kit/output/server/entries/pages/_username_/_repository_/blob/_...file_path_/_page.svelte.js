import { s as subscribe } from "../../../../../../chunks/utils.js";
import { c as create_ssr_component, e as escape, v as validate_component } from "../../../../../../chunks/ssr.js";
import { p as page } from "../../../../../../chunks/stores.js";
import "marked";
import { user } from "../../../../../../chunks/auth.js";
import "../../../../../../chunks/runtime.js";
import { L as Loading } from "../../../../../../chunks/Loading.js";
const _page_svelte_svelte_type_style_lang = "";
const css = {
  code: ".file-content.svelte-yxfuvu pre{background:#f8f9fa;border-radius:0;margin:0}.file-content.svelte-yxfuvu .metadata-block pre{background:transparent !important;margin:0;line-height:1.4}.file-content.svelte-yxfuvu pre code{background:none;padding:0;font-size:inherit;color:inherit}.file-content.svelte-yxfuvu .yaml-frontmatter{color:#6f42c1}.file-content.svelte-yxfuvu .yaml-key{color:#005cc5;font-weight:600}.file-content.svelte-yxfuvu .yaml-value{color:#032f62}.file-content.svelte-yxfuvu .yaml-comment{color:#6a737d;font-style:italic}.file-content.svelte-yxfuvu .md-header{color:#005cc5;font-weight:bold}.file-content.svelte-yxfuvu .md-bold{color:#d73a49;font-weight:bold}.file-content.svelte-yxfuvu .md-italic{color:#6f42c1;font-style:italic}.file-content.svelte-yxfuvu .md-link{color:#0366d6;text-decoration:none}.file-content.svelte-yxfuvu .md-code-block{color:#e36209;background:rgba(255, 229, 100, 0.2);padding:2px 4px;border-radius:3px}.file-content.svelte-yxfuvu .md-inline-code{color:#e36209;background:rgba(255, 229, 100, 0.2);padding:1px 3px;border-radius:2px;font-family:'SFMono-Regular', Consolas, monospace}.file-content.svelte-yxfuvu .md-list{color:#22863a}.file-content.svelte-yxfuvu pre.bg-gray-50 .yaml-key{color:#005cc5;font-weight:600}.file-content.svelte-yxfuvu pre.bg-gray-50 .yaml-value{color:#032f62}.file-content.svelte-yxfuvu pre.bg-gray-50 .yaml-comment{color:#6a737d;font-style:italic}.file-content.svelte-yxfuvu pre.bg-gray-50 .md-header{color:#005cc5;font-weight:bold}.file-content.svelte-yxfuvu pre.bg-gray-50 .md-bold{color:#d73a49;font-weight:bold}.file-content.svelte-yxfuvu pre.bg-gray-50 .md-italic{color:#6f42c1;font-style:italic}.file-content.svelte-yxfuvu pre.bg-gray-50 .md-link{color:#0366d6}.file-content.svelte-yxfuvu pre.bg-gray-50 .md-code-block{color:#e36209;background:rgba(255, 229, 100, 0.2);padding:2px 4px;border-radius:3px}.file-content.svelte-yxfuvu pre.bg-gray-50 .md-inline-code{color:#e36209;background:rgba(255, 229, 100, 0.2);padding:1px 3px;border-radius:2px}.file-content.svelte-yxfuvu pre.bg-gray-50 .md-list{color:#22863a}.file-content.svelte-yxfuvu .metadata-block{box-shadow:0 1px 3px rgba(0, 0, 0, 0.1)}.file-content.svelte-yxfuvu .metadata-block .yaml-key{color:#9cdcfe;font-weight:600}.file-content.svelte-yxfuvu .metadata-block .yaml-value{color:#ce9178}.file-content.svelte-yxfuvu .metadata-block .yaml-comment{color:#6a9955;font-style:italic}.model-card-content.svelte-yxfuvu{width:100%;overflow-wrap:break-word;word-wrap:break-word}.model-card-content.svelte-yxfuvu table{display:table;width:max-content;min-width:100%;border-collapse:collapse;margin-bottom:1rem;white-space:nowrap}.model-card-content.svelte-yxfuvu .table-container{overflow-x:auto;margin-bottom:1rem;border:1px solid #e5e7eb;border-radius:0.375rem;scrollbar-width:thin;scrollbar-color:#64748b #f1f5f9}.model-card-content.svelte-yxfuvu .table-container::-webkit-scrollbar{height:8px}.model-card-content.svelte-yxfuvu .table-container::-webkit-scrollbar-track{background:#f1f5f9;border-radius:4px}.model-card-content.svelte-yxfuvu .table-container::-webkit-scrollbar-thumb{background:#64748b;border-radius:4px}.model-card-content.svelte-yxfuvu .table-container::-webkit-scrollbar-thumb:hover{background:#94a3b8}.model-card-content.svelte-yxfuvu table th,.model-card-content.svelte-yxfuvu table td{border:1px solid #e5e7eb;padding:0.75rem;text-align:left;white-space:nowrap;min-width:120px}.model-card-content.svelte-yxfuvu table th{background-color:#f8fafc;font-weight:600}.model-card-content.svelte-yxfuvu img{max-width:100%;height:auto}.model-card-content.svelte-yxfuvu p,.model-card-content.svelte-yxfuvu div,.model-card-content.svelte-yxfuvu span{word-wrap:break-word;overflow-wrap:break-word}.model-card-content.svelte-yxfuvu .metadata-block{margin-bottom:1.5rem}.prose.svelte-yxfuvu code{color:#1e293b;font-size:0.875rem;font-family:'Fira Code', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace}.prose.svelte-yxfuvu pre{background-color:#f1f5f9;color:#1e293b;padding:1.25rem;border-radius:0.5rem;overflow-x:auto;margin-bottom:1.5rem;border:1px solid #e2e8f0;font-family:'Fira Code', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;line-height:1.5}",
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
