import { s as subscribe } from "../../../chunks/utils.js";
import { c as create_ssr_component, a as createEventDispatcher, d as each, e as escape, b as add_attribute, v as validate_component } from "../../../chunks/ssr.js";
import "../../../chunks/runtime.esm.js";
import { u as user } from "../../../chunks/auth.js";
const ClassificationSelector_svelte_svelte_type_style_lang = "";
const css = {
  code: '.classification-selector.svelte-1352sn0 input[type="radio"]{width:16px;height:16px}',
  map: null
};
function buildTree(flatList) {
  const tree = [];
  const map = /* @__PURE__ */ new Map();
  if (!flatList || flatList.length === 0) {
    return tree;
  }
  flatList.forEach((item) => {
    map.set(item.id, { ...item, children: [] });
  });
  flatList.forEach((item) => {
    const node = map.get(item.id);
    if (item.parent_id === null || item.parent_id === void 0) {
      tree.push(node);
    } else {
      const parent = map.get(item.parent_id);
      if (parent) {
        parent.children.push(node);
      }
    }
  });
  return tree;
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
  classificationTree = buildTree(classifications);
  isNodeExpanded = (nodeId) => {
    return expandedNodes.has(nodeId);
  };
  return `<div class="classification-selector svelte-1352sn0">${loading ? `<div class="flex items-center justify-center py-4" data-svelte-h="svelte-15j1abw"><div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div> <span class="ml-2 text-sm text-gray-500 dark:text-gray-400">加载分类中...</span></div>` : `${classificationTree.length === 0 ? `<div class="text-center py-4" data-svelte-h="svelte-15ncmza"><p class="text-sm text-gray-500 dark:text-gray-400">暂无分类数据</p></div>` : `<div class="max-h-64 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800">${each(classificationTree, (node) => {
    return `<div class="classification-node"> <div class="${"flex items-center px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-100 dark:border-gray-700 " + escape(
      selectedClassificationId === node.id ? "bg-blue-50 dark:bg-blue-900/20" : "",
      true
    )}">${hasChildren(node) ? `<button type="button" class="mr-2 p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded flex items-center justify-center w-6 h-6">${isNodeExpanded(node.id) ? `<span class="text-sm" data-svelte-h="svelte-11a4sbr">▼</span>` : `<span class="text-sm" data-svelte-h="svelte-1f66a3h">▶</span>`} </button>` : `<div class="w-6 h-6 mr-2"></div>`} <label class="flex-1 cursor-pointer flex items-center"><input type="radio" name="classification"${add_attribute("value", node.id, 0)} ${selectedClassificationId === node.id ? "checked" : ""} class="mr-2 text-blue-600 focus:ring-blue-500"> <span class="text-sm font-medium text-gray-900 dark:text-white">${escape(node.name)}</span> ${hasChildren(node) ? `<span class="text-xs text-gray-400 ml-1" data-svelte-h="svelte-zxw70j">(可选择或展开查看子分类)</span>` : ``} </label></div>  ${hasChildren(node) && isNodeExpanded(node.id) ? `${each(node.children, (childNode) => {
      return `<div class="ml-4"><div class="${"flex items-center px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-100 dark:border-gray-700 " + escape(
        selectedClassificationId === childNode.id ? "bg-blue-50 dark:bg-blue-900/20" : "",
        true
      )}">${hasChildren(childNode) ? `<button type="button" class="mr-2 p-1 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded flex items-center justify-center w-6 h-6 border border-gray-300" style="z-index: 10; position: relative;">${isNodeExpanded(childNode.id) ? `<span class="text-xs" data-svelte-h="svelte-1bxfonq">▼</span>` : `<span class="text-xs" data-svelte-h="svelte-8z391g">▶</span>`} </button>` : `<div class="w-6 h-6 mr-2"></div>`}  <label class="flex-1 cursor-pointer flex items-center"><input type="radio" name="classification"${add_attribute("value", childNode.id, 0)} ${selectedClassificationId === childNode.id ? "checked" : ""} class="mr-2 text-blue-600 focus:ring-blue-500"> <span class="text-sm font-medium text-gray-700 dark:text-gray-300">${escape(childNode.name)}</span> ${hasChildren(childNode) ? `<span class="text-xs text-gray-400 ml-1" data-svelte-h="svelte-kp7gbn">(可选择或展开查看三级分类)</span>` : ``} </label></div>  ${hasChildren(childNode) && isNodeExpanded(childNode.id) ? `${each(childNode.children, (grandChildNode) => {
        return `<div class="ml-4"><div class="${"flex items-center px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer " + escape(
          selectedClassificationId === grandChildNode.id ? "bg-blue-50 dark:bg-blue-900/20" : "",
          true
        )}"><div class="w-6 h-6 mr-2"></div>  <label class="flex-1 cursor-pointer flex items-center"><input type="radio" name="classification"${add_attribute("value", grandChildNode.id, 0)} ${selectedClassificationId === grandChildNode.id ? "checked" : ""} class="mr-2 text-blue-600 focus:ring-blue-500"> <span class="text-sm text-gray-600 dark:text-gray-400">${escape(grandChildNode.name)}</span> </label></div> </div>`;
      })}` : ``} </div>`;
    })}` : ``} </div>`;
  })}</div>  ${selectedClassificationId !== null ? `<div class="mt-2"><button type="button" class="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200" data-svelte-h="svelte-18xgl2j">清除选择</button></div>` : ``}`}`} </div>`;
});
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $currentUser, $$unsubscribe_currentUser;
  $$unsubscribe_currentUser = subscribe(user, (value) => $currentUser = value);
  let classifications = [];
  let loadingClassifications = false;
  let formData = {
    name: "",
    description: "",
    repo_type: "model",
    visibility: "public",
    license: "",
    tags: [],
    base_model: "",
    classification_id: null,
    readme_content: ""
  };
  let errors = {};
  let tagInput = "";
  $$unsubscribe_currentUser();
  return `${$$result.head += `<!-- HEAD_svelte-70f6x8_START -->${$$result.title = `<title>创建新仓库 - GeoML Hub</title>`, ""}<!-- HEAD_svelte-70f6x8_END -->`, ""} <div class="min-h-screen bg-gray-50 dark:bg-gray-900"><div class="max-w-2xl mx-auto pt-16 px-4"><div class="text-center mb-8" data-svelte-h="svelte-spdopq"> <div class="mx-auto w-16 h-16 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center mb-6"><svg class="w-8 h-8 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg></div> <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">创建新仓库</h1> <p class="text-gray-600 dark:text-gray-400">仓库包含您的模型文件、数据集和相关资源，支持版本控制和协作开发。</p></div> <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700"><form class="p-6 space-y-6"> <div><div class="flex justify-between items-center mb-2" data-svelte-h="svelte-t4fx8x"><label for="owner-select" class="text-sm font-medium text-gray-700 dark:text-gray-300">所有者</label> <label for="repo-name-input" class="text-sm font-medium text-gray-700 dark:text-gray-300">仓库名称</label></div> <div class="flex space-x-2"> <div class="relative"><div class="bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-2 text-gray-600 dark:text-gray-300 cursor-not-allowed flex items-center justify-between"><span>${escape($currentUser?.username || "loading...")}</span> <svg class="w-4 h-4 fill-current text-gray-500 dark:text-gray-400 ml-2" viewBox="0 0 20 20"><path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"></path></svg></div></div> <span class="flex items-center text-gray-500 dark:text-gray-400" data-svelte-h="svelte-1bhxk9e">/</span>  <div class="flex-1"><input id="repo-name-input" type="text" class="${"w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent " + escape(errors.name ? "border-red-500" : "", true)}" placeholder="my-awesome-model" required${add_attribute("value", formData.name, 0)}> ${errors.name ? `<p class="text-red-500 text-sm mt-1">${escape(errors.name)}</p>` : ``}</div></div></div>  <div><label for="description-input" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-1yg6aiw">描述 (可选)</label> <textarea id="description-input" rows="3" class="${"w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent " + escape(errors.description ? "border-red-500" : "", true)}" placeholder="简要描述您的模型或数据集...">${escape("")}</textarea> ${errors.description ? `<p class="text-red-500 text-sm mt-1">${escape(errors.description)}</p>` : ``}</div>  <div><label for="license-select" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-6eua9e">许可证 (可选)</label> <select id="license-select" class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"><option value="" data-svelte-h="svelte-g9wbxm">选择许可证...</option><option value="mit" data-svelte-h="svelte-2rnjty">MIT</option><option value="apache-2.0" data-svelte-h="svelte-1af3bwp">Apache 2.0</option><option value="gpl-3.0" data-svelte-h="svelte-6zvm53">GPL 3.0</option><option value="bsd-3-clause" data-svelte-h="svelte-vxo5tn">BSD 3-Clause</option><option value="lgpl-2.1" data-svelte-h="svelte-1bszy19">LGPL 2.1</option><option value="mpl-2.0" data-svelte-h="svelte-1p7bryd">MPL 2.0</option><option value="cc0-1.0" data-svelte-h="svelte-2krpsp">CC0 1.0</option><option value="cc-by-4.0" data-svelte-h="svelte-1kf18hu">CC BY 4.0</option><option value="unlicense" data-svelte-h="svelte-6f2u">Unlicense</option><option value="other" data-svelte-h="svelte-dk3oti">其他</option></select></div>  <div><label for="tags-input" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-1bkm0xt">标签 (可选)</label> <div class="flex flex-wrap gap-2 mb-2">${each(formData.tags, (tag) => {
    return `<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">${escape(tag)} <button type="button" class="ml-1 h-4 w-4 rounded-full hover:bg-blue-200 dark:hover:bg-blue-800 flex items-center justify-center" data-svelte-h="svelte-14l0zz9"><svg class="h-2 w-2" fill="currentColor" viewBox="0 0 8 8"><path d="M1.41 0l-1.41 1.41.72.72 1.78 1.81-1.78 1.78-.72.69 1.41 1.44.72-.72 1.81-1.81 1.78 1.81.69.72 1.44-1.44-.72-.69-1.81-1.78 1.81-1.81.72-.72-1.44-1.41-.69.72-1.78 1.78-1.81-1.78-.72-.72z"></path></svg></button> </span>`;
  })}</div> <input id="tags-input" type="text" class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" placeholder="输入标签后按回车键添加"${add_attribute("value", tagInput, 0)}></div>  <div><label for="base-model-input" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-1524byg">基础模型 (可选)</label> <input id="base-model-input" type="text" class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" placeholder="例如: bert-base-uncased, resnet50"${add_attribute("value", formData.base_model, 0)}> <p class="text-sm text-gray-500 dark:text-gray-400 mt-1" data-svelte-h="svelte-18c5794">如果您的模型基于现有模型构建，请输入基础模型名称</p></div>  <div><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-1g53j6r">分类 (可选)</label> ${validate_component(ClassificationSelector, "ClassificationSelector").$$render(
    $$result,
    {
      classifications,
      selectedClassificationId: formData.classification_id,
      loading: loadingClassifications
    },
    {},
    {}
  )} <p class="text-sm text-gray-500 dark:text-gray-400 mt-1" data-svelte-h="svelte-4wlo8o">选择最适合您仓库内容的分类，可以选择一级、二级或三级分类</p></div>  <div class="space-y-4"><fieldset><legend class="block text-sm font-medium text-gray-700 dark:text-gray-300" data-svelte-h="svelte-1ofwbqg">可见性</legend> <div class="flex items-start space-x-3"><input type="radio" id="public" value="public" class="mt-1 w-4 h-4 text-blue-600 border-gray-300 dark:border-gray-600 focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700"${add_attribute("checked", true, 1)}> <div class="flex-1" data-svelte-h="svelte-k0x8zu"><label for="public" class="flex items-center cursor-pointer"><svg class="w-5 h-5 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> <span class="font-medium text-gray-900 dark:text-white">公开</span></label> <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">任何人都可以查看此仓库。只有您或您的组织成员可以提交更改。</p></div></div> <div class="flex items-start space-x-3"><input type="radio" id="private" value="private" class="mt-1 w-4 h-4 text-blue-600 border-gray-300 dark:border-gray-600 focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700"${""}> <div class="flex-1" data-svelte-h="svelte-1r4xa06"><label for="private" class="flex items-center cursor-pointer"><svg class="w-5 h-5 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg> <span class="font-medium text-gray-900 dark:text-white">私有</span></label> <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">只有您或您的组织成员可以查看和提交到此仓库。</p></div></div></fieldset></div>  <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4" data-svelte-h="svelte-y5kj5g"><p class="text-sm text-blue-800 dark:text-blue-200">创建仓库后，您可以通过网页界面或 Git 上传文件和管理版本。</p></div>  ${``}  <div class="flex justify-end space-x-3"><button type="button" class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors" data-svelte-h="svelte-2rsaiw">取消</button> <button type="submit" class="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium rounded-lg transition-colors flex items-center space-x-2" ${""}>${`<span data-svelte-h="svelte-1oyca1l">创建仓库</span>`}</button></div></form></div></div></div>`;
});
export {
  Page as default
};
