import { s as subscribe } from "../../../chunks/utils.js";
import { c as create_ssr_component, b as createEventDispatcher, a as each, e as escape, d as add_attribute, v as validate_component } from "../../../chunks/ssr.js";
import "../../../chunks/runtime.js";
import { user } from "../../../chunks/auth.js";
/* empty css                                                                    */const css = {
  code: ".classification-selector.svelte-1ho3etc input[type='radio']{width:16px;height:16px}",
  map: null
};
function getClassificationTree(data) {
  if (data && data.classifications && Array.isArray(data.classifications)) {
    return data.classifications;
  } else if (Array.isArray(data)) {
    return data;
  } else {
    return [];
  }
}
function hasChildren(node) {
  return node.children && node.children.length > 0;
}
const ClassificationSelector = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let classificationTree;
  let isNodeExpanded;
  let { classifications = [] } = $$props;
  let { selectedClassificationId = null } = $$props;
  let { loading = false } = $$props;
  createEventDispatcher();
  let expandedNodes = /* @__PURE__ */ new Set();
  if ($$props.classifications === void 0 && $$bindings.classifications && classifications !== void 0)
    $$bindings.classifications(classifications);
  if ($$props.selectedClassificationId === void 0 && $$bindings.selectedClassificationId && selectedClassificationId !== void 0)
    $$bindings.selectedClassificationId(selectedClassificationId);
  if ($$props.loading === void 0 && $$bindings.loading && loading !== void 0)
    $$bindings.loading(loading);
  $$result.css.add(css);
  classificationTree = getClassificationTree(classifications);
  {
    {
      console.log("Classifications data:", classifications);
      console.log("Classification tree:", classificationTree);
    }
  }
  isNodeExpanded = (nodeId) => {
    return expandedNodes.has(nodeId);
  };
  return `<div class="classification-selector svelte-1ho3etc">${loading ? `<div class="flex items-center justify-center py-4" data-svelte-h="svelte-f2d0lz"><div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div> <span class="ml-2 text-sm text-slate-500 dark:text-slate-400">加载分类中...</span></div>` : `${classificationTree.length === 0 ? `<div class="text-center py-4" data-svelte-h="svelte-oc2uv1"><p class="text-sm text-slate-500 dark:text-slate-400">暂无分类数据</p></div>` : `<div class="max-h-64 overflow-y-auto border border-slate-200/70 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-800 shadow-sm">${each(classificationTree, (node) => {
    return `<div class="classification-node"> <div class="${"flex items-center px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer border-b border-slate-100 dark:border-slate-700 " + escape(
      selectedClassificationId === node.id ? "bg-blue-50 dark:bg-blue-900/20" : "",
      true
    )}">${hasChildren(node) ? `<button type="button" class="mr-2 p-1 hover:bg-slate-200 dark:hover:bg-slate-600 rounded flex items-center justify-center w-6 h-6">${isNodeExpanded(node.id) ? `<span class="text-sm" data-svelte-h="svelte-11a4sbr">▼</span>` : `<span class="text-sm" data-svelte-h="svelte-1f66a3h">▶</span>`} </button>` : `<div class="w-6 h-6 mr-2"></div>`} <label class="flex-1 cursor-pointer flex items-center"><input type="radio" name="classification"${add_attribute("value", node.id, 0)} ${selectedClassificationId === node.id ? "checked" : ""} class="mr-2 text-blue-600 focus:ring-blue-500"> <span class="text-sm font-medium text-slate-900 dark:text-white">${escape(node.name)}</span> ${hasChildren(node) ? `<span class="text-xs text-slate-400 ml-1" data-svelte-h="svelte-yp1nqz">(可选择或展开查看子分类)</span>` : ``} </label></div>  ${hasChildren(node) && isNodeExpanded(node.id) ? `${each(node.children, (childNode) => {
      return `<div class="ml-4"><div class="${"flex items-center px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer border-b border-slate-100 dark:border-slate-700 " + escape(
        selectedClassificationId === childNode.id ? "bg-blue-50 dark:bg-blue-900/20" : "",
        true
      )}">${hasChildren(childNode) ? `<button type="button" class="mr-2 p-1 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 rounded flex items-center justify-center w-6 h-6" style="z-index: 10; position: relative;">${isNodeExpanded(childNode.id) ? `<span class="text-xs" data-svelte-h="svelte-1bxfonq">▼</span>` : `<span class="text-xs" data-svelte-h="svelte-8z391g">▶</span>`} </button>` : `<div class="w-6 h-6 mr-2"></div>`}  <label class="flex-1 cursor-pointer flex items-center"><input type="radio" name="classification"${add_attribute("value", childNode.id, 0)} ${selectedClassificationId === childNode.id ? "checked" : ""} class="mr-2 text-blue-600 focus:ring-blue-500"> <span class="text-sm font-medium text-slate-700 dark:text-slate-300">${escape(childNode.name)}</span> ${hasChildren(childNode) ? `<span class="text-xs text-slate-400 ml-1" data-svelte-h="svelte-1nt1s2j">(可选择或展开查看三级分类)</span>` : ``} </label></div>  ${hasChildren(childNode) && isNodeExpanded(childNode.id) ? `${each(childNode.children, (grandChildNode) => {
        return `<div class="ml-4"><div class="${"flex items-center px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer " + escape(
          selectedClassificationId === grandChildNode.id ? "bg-blue-50 dark:bg-blue-900/20" : "",
          true
        )}"><div class="w-6 h-6 mr-2"></div>  <label class="flex-1 cursor-pointer flex items-center"><input type="radio" name="classification"${add_attribute("value", grandChildNode.id, 0)} ${selectedClassificationId === grandChildNode.id ? "checked" : ""} class="mr-2 text-blue-600 focus:ring-blue-500"> <span class="text-sm text-slate-600 dark:text-slate-400">${escape(grandChildNode.name)}</span> </label></div> </div>`;
      })}` : ``} </div>`;
    })}` : ``} </div>`;
  })}</div>`}`} </div>`;
});
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $currentUser, $$unsubscribe_currentUser;
  $$unsubscribe_currentUser = subscribe(user, (value) => $currentUser = value);
  let classifications = [];
  let loadingClassifications = false;
  let taskClassifications = [];
  let formData = {
    name: "",
    description: "",
    repo_type: "model",
    visibility: "public",
    license: "",
    tags: [],
    base_model: "",
    classification_id: null,
    task_classification_ids: [],
    readme_content: ""
  };
  let errors = {};
  let tagInput = "";
  $$unsubscribe_currentUser();
  return `${$$result.head += `<!-- HEAD_svelte-zcnj9j_START -->${$$result.title = `<title>创建新仓库 - GeoML Hub</title>`, ""}<!-- HEAD_svelte-zcnj9j_END -->`, ""} <div class="min-h-[70vh] bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900"><div class="max-w-3xl mx-auto pt-4 px-4 pb-4"><div class="text-center mb-4" data-svelte-h="svelte-e93uy4"> <div class="mx-auto w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center mb-2 shadow-xl border border-white/20"><svg class="w-7 h-7 text-white" fill="currentColor" viewBox="0 0 16 16"><path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"></path></svg></div> <h1 class="text-3xl font-bold text-slate-900 dark:text-white mb-0.5 tracking-tight">创建新仓库</h1> <p class="text-slate-600 dark:text-slate-400 text-base">支持模型、数据集和相关资源的版本控制与协作开发</p></div> <div class="bg-white/90 dark:bg-slate-800/95 backdrop-blur-2xl rounded-3xl shadow-2xl border border-white/20 dark:border-slate-700/50"><form class="p-6 space-y-3"> <div class="bg-slate-50/60 dark:bg-slate-700/40 rounded-2xl p-3 border border-slate-200/60 dark:border-slate-600/50"><div class="flex items-center space-x-24 ml-2" data-svelte-h="svelte-pa6ddy"><label class="block text-sm font-semibold text-slate-800 dark:text-slate-200 mb-1">所有者</label> <label class="block text-sm font-semibold text-slate-800 dark:text-slate-200 mb-1">仓库名</label></div> <div class="flex items-center space-x-2"> <div class="flex items-center bg-white dark:bg-slate-800 rounded-xl px-4 py-2 border border-slate-200/70 dark:border-slate-600 shadow-sm"><span class="text-m font-medium text-slate-700 dark:text-slate-300">${escape($currentUser?.username || "loading...")}</span></div> <span class="text-slate-800 text-lg font-medium" data-svelte-h="svelte-18qwzaq">/</span>  <div class="flex-1"><input id="repo-name-input" type="text" class="${"w-full px-4 py-2 border border-slate-200/70 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/70 focus:border-blue-400 transition-all duration-200 " + escape(
    errors.name ? "border-red-400 focus:ring-red-400/70" : "",
    true
  )}" placeholder="my-awesome-model" required${add_attribute("value", formData.name, 0)}></div></div> ${errors.name ? `<p class="text-red-500 text-sm mt-2 ml-1 font-medium">${escape(errors.name)}</p>` : ``}</div>  <div><label for="description-input" class="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-1" data-svelte-h="svelte-1hw0zr7"><span class="flex items-center">描述
							<span class="text-xs text-slate-500 ml-1">(可选)</span></span></label> <textarea id="description-input" rows="2" class="${"w-full px-4 py-3 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 resize-none " + escape(
    errors.description ? "border-red-500 focus:ring-red-500" : "",
    true
  )}" placeholder="简要描述您的模型或数据集...">${escape("")}</textarea> ${errors.description ? `<p class="text-red-500 text-sm mt-1">${escape(errors.description)}</p>` : ``}</div>  <div class="flex items-center justify-center"><div class="flex bg-gradient-to-r from-slate-100/80 mb-2 to-slate-50/60 dark:from-slate-800/70 dark:to-slate-700/60 rounded-2xl border border-slate-200/60 dark:border-slate-600/50 shadow-inner"><input type="radio" id="config-mode" value="config" class="sr-only"${add_attribute("checked", true, 1)}> <label for="config-mode" class="${"flex items-center px-3 py-2 rounded-xl cursor-pointer transition-all duration-300 text-sm font-semibold min-w-[140px] justify-center " + escape(
    "bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-xl border border-white/60 dark:border-slate-600/60 transform scale-[1.02]",
    true
  )}"><svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4a2 2 0 014 0m2-4a2 2 0 110 4m0-4a2 2 0 110 4m0 4v2m0-6V4"></path></svg>
							手动配置信息</label> <input type="radio" id="readme-mode" value="readme" class="sr-only"${""}> <label for="readme-mode" class="${"flex items-center px-3 py-2 rounded-xl cursor-pointer transition-all duration-300 text-sm font-semibold min-w-[140px] justify-center " + escape(
    "text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-white/60 dark:hover:bg-slate-700/60",
    true
  )}"><svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
							上传 README</label></div></div>  ${``}  ${`<div class="grid grid-cols-1 md:grid-cols-8 gap-4"> <div class="md:col-span-2"><label for="license-select" class="block text-sm ml-2 font-semibold text-slate-700 dark:text-slate-300 mb-1" data-svelte-h="svelte-1pzawkd">许可证 (可选)</label> <select id="license-select" class="w-full px-4 py-2 border border-slate-200/70 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/70 focus:border-blue-400 transition-all duration-200"><option value="" data-svelte-h="svelte-g9wbxm">选择许可证...</option><option value="mit" data-svelte-h="svelte-2rnjty">MIT</option><option value="apache-2.0" data-svelte-h="svelte-1af3bwp">Apache 2.0</option><option value="gpl-3.0" data-svelte-h="svelte-6zvm53">GPL 3.0</option><option value="bsd-3-clause" data-svelte-h="svelte-vxo5tn">BSD 3-Clause</option><option value="lgpl-2.1" data-svelte-h="svelte-1bszy19">LGPL 2.1</option><option value="mpl-2.0" data-svelte-h="svelte-1p7bryd">MPL 2.0</option><option value="cc0-1.0" data-svelte-h="svelte-2krpsp">CC0 1.0</option><option value="cc-by-4.0" data-svelte-h="svelte-1kf18hu">CC BY 4.0</option><option value="unlicense" data-svelte-h="svelte-6f2u">Unlicense</option><option value="other" data-svelte-h="svelte-dk3oti">其他</option></select></div>  <div class="md:col-span-3"><label for="base-model-input" class="block text-sm ml-2 font-semibold text-slate-700 dark:text-slate-300 mb-1" data-svelte-h="svelte-1sjc51x">基础模型 (可选)</label> <input id="base-model-input" type="text" class="w-full px-4 py-2 border border-slate-200/70 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/70 focus:border-blue-400 transition-all duration-200" placeholder="例如: bert-base-uncased"${add_attribute("value", formData.base_model, 0)}></div>  <div class="md:col-span-3"><label for="tags-input" class="block text-sm ml-2 font-semibold text-slate-700 dark:text-slate-300 mb-1" data-svelte-h="svelte-1fbw3sy">标签 (可选)</label> <div class="relative"><input id="tags-input" type="text" class="w-full px-4 py-2 border border-slate-200/70 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/70 focus:border-blue-400 transition-all duration-200" placeholder="输入标签按回车"${add_attribute("value", tagInput, 0)}></div>  ${formData.tags.length > 0 ? `<div class="flex flex-wrap gap-1 mt-2">${each(formData.tags, (tag) => {
    return `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">${escape(tag)} <button type="button" class="ml-1 h-3 w-3 rounded-full hover:bg-blue-200 dark:hover:bg-blue-800 flex items-center justify-center" data-svelte-h="svelte-1skdv2h"><svg class="h-2 w-2" fill="currentColor" viewBox="0 0 8 8"><path d="M1.41 0l-1.41 1.41.72.72 1.78 1.81-1.78 1.78-.72.69 1.41 1.44.72-.72 1.81-1.81 1.78 1.81.69.72 1.44-1.44-.72-.69-1.81-1.78 1.81-1.81.72-.72-1.44-1.41-.69.72-1.78 1.78-1.81-1.78-.72-.72z"></path></svg></button> </span>`;
  })}</div>` : ``}</div></div>  <div><div class="flex items-center space-x-2 mb-1"><label class="text-sm font-semibold text-slate-700 dark:text-slate-300" data-svelte-h="svelte-1w2wwjd">分类 (可选)</label> ${``}</div> ${validate_component(ClassificationSelector, "ClassificationSelector").$$render(
    $$result,
    {
      classifications,
      selectedClassificationId: formData.classification_id,
      loading: loadingClassifications
    },
    {},
    {}
  )}</div>  <div><div class="flex items-center space-x-2 mb-1"><label class="text-sm font-semibold text-slate-700 dark:text-slate-300" data-svelte-h="svelte-5dpr99">任务分类 (可选)</label> ${formData.task_classification_ids.length > 0 ? `<button type="button" class="inline-flex items-center px-2 py-1 text-xs font-medium text-slate-600 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-300 bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 rounded-lg transition-all duration-200" data-svelte-h="svelte-jis3x5"><svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
									清除选择</button>` : ``}</div> ${`<div class="flex flex-wrap gap-2">${each(taskClassifications, (task) => {
    return `<button type="button" class="${"inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 border " + escape(
      formData.task_classification_ids.includes(task.id) ? "bg-purple-50 text-purple-700 border-purple-300 hover:bg-purple-100 dark:bg-purple-900 dark:text-purple-300 dark:border-purple-700 dark:hover:bg-purple-800" : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-600 dark:hover:bg-slate-700",
      true
    )}"> <span>${escape(task.name)}</span> </button>`;
  })} ${taskClassifications.length === 0 ? `<p class="text-sm text-slate-500 dark:text-slate-400" data-svelte-h="svelte-1gfuxc3">暂无任务分类</p>` : ``}</div>`}</div>`}  <div><div class="flex space-x-4"><div class="flex items-center"><input type="radio" id="public" value="public" class="h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-slate-300 dark:border-slate-600"${add_attribute("checked", true, 1)}> <label for="public" class="ml-3 flex items-center" data-svelte-h="svelte-4px19g"><div class="w-6 h-6 bg-emerald-100 dark:bg-emerald-900/50 rounded-lg flex items-center justify-center mr-2"><svg class="w-3 h-3 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg></div> <span class="text-sm font-medium text-slate-700 dark:text-slate-300">公开仓库</span></label></div> <div class="flex items-center"><input type="radio" id="private" value="private" class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-slate-300 dark:border-slate-600"${""}> <label for="private" class="ml-3 flex items-center" data-svelte-h="svelte-1hiag7o"><div class="w-6 h-6 bg-blue-100 dark:bg-blue-900/50 rounded-lg flex items-center justify-center mr-2"><svg class="w-3 h-3 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg></div> <span class="text-sm font-medium text-slate-700 dark:text-slate-300">私有仓库</span></label></div></div></div>  ${``}  <div class="flex flex-col sm:flex-row justify-center sm:justify-end space-y-3 sm:space-y-0 sm:space-x-4"><button type="submit" class="w-full sm:w-auto px-5 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 disabled:from-slate-400 disabled:to-slate-500 text-white font-semibold rounded-2xl transition-all duration-200 flex items-center justify-center space-x-2 shadow-xl hover:shadow-2xl transform hover:scale-[1.02] disabled:transform-none disabled:shadow-lg" ${""}>${`<span data-svelte-h="svelte-1oyca1l">创建仓库</span>`}</button> <button type="button" class="w-full sm:w-auto px-5 py-2 border border-slate-300/70 dark:border-slate-600 rounded-2xl text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all duration-200 font-semibold shadow-sm hover:shadow-md" data-svelte-h="svelte-15b8fae">取消</button></div></form></div></div></div>`;
});
export {
  Page as default
};
