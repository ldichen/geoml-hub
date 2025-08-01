import { c as create_ssr_component, v as validate_component, a as createEventDispatcher, b as add_attribute, e as escape, d as each } from "../../chunks/ssr.js";
import "../../chunks/api.js";
import { S as Search, C as ChevronRight, R as RepositoryCard } from "../../chunks/RepositoryCard.js";
import { s as subscribe } from "../../chunks/utils.js";
import { $ as $format } from "../../chunks/runtime.esm.js";
import { I as Icon } from "../../chunks/star.js";
import { L as Loading } from "../../chunks/Loading.js";
import { T as TrendingUp } from "../../chunks/trending-up.js";
const Chevron_down = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [["path", { "d": "m6 9 6 6 6-6" }]];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "chevron-down" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const ChevronDown = Chevron_down;
const Plus = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [["path", { "d": "M5 12h14" }], ["path", { "d": "M12 5v14" }]];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "plus" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Plus$1 = Plus;
const X = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [["path", { "d": "M18 6 6 18" }], ["path", { "d": "m6 6 12 12" }]];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "x" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const X$1 = X;
const SearchBar = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $_, $$unsubscribe__;
  $$unsubscribe__ = subscribe($format, (value2) => $_ = value2);
  let { value = "" } = $$props;
  let { placeholder = "" } = $$props;
  createEventDispatcher();
  if ($$props.value === void 0 && $$bindings.value && value !== void 0)
    $$bindings.value(value);
  if ($$props.placeholder === void 0 && $$bindings.placeholder && placeholder !== void 0)
    $$bindings.placeholder(placeholder);
  $$unsubscribe__();
  return `<div class="relative"><div class="relative"><div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">${validate_component(Search, "Search").$$render(
    $$result,
    {
      class: "h-5 w-5 text-secondary-400 dark:text-dark-400"
    },
    {},
    {}
  )}</div> <input type="text" class="input pl-10 pr-10 py-3 w-full"${add_attribute("placeholder", placeholder || $_("search.placeholder"), 0)}${add_attribute("value", value, 0)}> ${value ? `<div class="absolute inset-y-0 right-0 pr-3 flex items-center"><button type="button" class="p-1 rounded-full hover:bg-secondary-100 dark:hover:bg-secondary-800 transition-colors">${validate_component(X$1, "X").$$render(
    $$result,
    {
      class: "h-4 w-4 text-secondary-400 dark:text-dark-400"
    },
    {},
    {}
  )}</button></div>` : ``}</div> <div class="absolute right-2 top-2"><button type="button" class="btn-primary px-4 py-2">${escape($_("common.search"))}</button></div></div>`;
});
function hasChildren(node) {
  return node.children && node.children.length > 0;
}
const ClassificationFilter = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let { classificationTree = [] } = $$props;
  let { selectedClassificationId = null } = $$props;
  createEventDispatcher();
  let expandedNodes = /* @__PURE__ */ new Set();
  function isExpanded(nodeId) {
    return expandedNodes.has(nodeId);
  }
  function isSelected(nodeId) {
    return selectedClassificationId === nodeId;
  }
  if ($$props.classificationTree === void 0 && $$bindings.classificationTree && classificationTree !== void 0)
    $$bindings.classificationTree(classificationTree);
  if ($$props.selectedClassificationId === void 0 && $$bindings.selectedClassificationId && selectedClassificationId !== void 0)
    $$bindings.selectedClassificationId(selectedClassificationId);
  return `<div class="classification-filter"><div class="flex items-center justify-between mb-4"><h3 class="text-lg font-semibold text-secondary-900 dark:text-dark-700" data-svelte-h="svelte-btv102">分类筛选</h3> ${selectedClassificationId ? `<button class="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300" data-svelte-h="svelte-1i4id95">清除筛选</button>` : ``}</div> <div class="space-y-1">${each(classificationTree, (level1) => {
    return `<div class="classification-node border-l border-secondary-200 dark:border-secondary-700 pl-2"> <div class="flex items-center">${hasChildren(level1) ? `<button class="flex items-center justify-center w-6 h-6 rounded hover:bg-secondary-100 dark:hover:bg-secondary-700">${isExpanded(level1.id) ? `${validate_component(ChevronDown, "ChevronDown").$$render(
      $$result,
      {
        class: "w-4 h-4 text-secondary-600 dark:text-dark-500"
      },
      {},
      {}
    )}` : `${validate_component(ChevronRight, "ChevronRight").$$render(
      $$result,
      {
        class: "w-4 h-4 text-secondary-600 dark:text-dark-500"
      },
      {},
      {}
    )}`} </button>` : `<div class="w-6 h-6"></div>`} <button class="${"flex-1 text-left px-2 py-1 rounded text-sm font-medium transition-colors " + escape(
      isSelected(level1.id) ? "bg-primary-100 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300" : "text-secondary-700 dark:text-dark-600 hover:bg-secondary-50 dark:hover:bg-secondary-800",
      true
    )}">${escape(level1.name)} </button></div>  ${hasChildren(level1) && isExpanded(level1.id) ? `<div class="ml-6 mt-1 space-y-1">${each(level1.children, (level2) => {
      return `<div class="classification-node border-l border-secondary-200 dark:border-secondary-700 pl-2"> <div class="flex items-center">${hasChildren(level2) ? `<button class="flex items-center justify-center w-5 h-5 rounded hover:bg-secondary-100 dark:hover:bg-secondary-700">${isExpanded(level2.id) ? `${validate_component(ChevronDown, "ChevronDown").$$render(
        $$result,
        {
          class: "w-3 h-3 text-secondary-600 dark:text-dark-500"
        },
        {},
        {}
      )}` : `${validate_component(ChevronRight, "ChevronRight").$$render(
        $$result,
        {
          class: "w-3 h-3 text-secondary-600 dark:text-dark-500"
        },
        {},
        {}
      )}`} </button>` : `<div class="w-5 h-5"></div>`} <button class="${"flex-1 text-left px-2 py-1 rounded text-sm transition-colors " + escape(
        isSelected(level2.id) ? "bg-primary-100 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300" : "text-secondary-600 dark:text-dark-500 hover:bg-secondary-50 dark:hover:bg-secondary-800",
        true
      )}">${escape(level2.name)} </button></div>  ${hasChildren(level2) && isExpanded(level2.id) ? `<div class="ml-5 mt-1 space-y-1">${each(level2.children, (level3) => {
        return `<button class="${"w-full text-left px-2 py-1 rounded text-xs transition-colors " + escape(
          isSelected(level3.id) ? "bg-primary-100 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300" : "text-secondary-500 dark:text-dark-400 hover:bg-secondary-50 dark:hover:bg-secondary-800",
          true
        )}">${escape(level3.name)} </button>`;
      })} </div>` : ``} </div>`;
    })} </div>` : ``} </div>`;
  })}</div></div>`;
});
const _page_svelte_svelte_type_style_lang = "";
const css = {
  code: ".bg-gradient-to-r.svelte-21j419{background:linear-gradient(to right, var(--tw-gradient-stops))}",
  map: null
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let currentUser = null;
  let featuredRepositories = [];
  let classifications = [];
  let searchQuery = "";
  let selectedClassification = null;
  $$result.css.add(css);
  let $$settled;
  let $$rendered;
  let previous_head = $$result.head;
  do {
    $$settled = true;
    $$result.head = previous_head;
    $$rendered = `${$$result.head += `<!-- HEAD_svelte-81iioc_START -->${$$result.title = `<title>GeoML Hub - 地理科学机器学习模型库</title>`, ""}<meta name="description" content="第一个专为地理科学设计的机器学习模型库，发现、分享和部署地理空间AI模型"><!-- HEAD_svelte-81iioc_END -->`, ""} <div class="min-h-screen bg-gray-50 dark:bg-gray-900"> <div class="bg-gradient-to-r from-blue-600 to-indigo-700 dark:from-blue-800 dark:to-indigo-900 svelte-21j419"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12"><div class="text-center"><h1 class="text-4xl sm:text-5xl font-bold text-white mb-4" data-svelte-h="svelte-d38mhq">🌍 GeoML Hub</h1> <p class="text-xl text-blue-100 mb-8 max-w-3xl mx-auto" data-svelte-h="svelte-vym7eq">第一个专为地理科学设计的机器学习模型库 - 发现、分享和部署地理空间AI模型</p>  <div class="max-w-2xl mx-auto mb-8">${validate_component(SearchBar, "SearchBar").$$render(
      $$result,
      {
        placeholder: "搜索模型、数据集、用户...",
        value: searchQuery
      },
      {
        value: ($$value) => {
          searchQuery = $$value;
          $$settled = false;
        }
      },
      {}
    )}</div>  <div class="flex justify-center space-x-4"><button class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-blue-700 bg-white hover:bg-gray-50 transition-colors">${validate_component(Plus$1, "Plus").$$render($$result, { class: "h-5 w-5 mr-2" }, {}, {})}
            创建仓库</button> <a href="/search" class="inline-flex items-center px-6 py-3 border border-white text-base font-medium rounded-md text-white bg-transparent hover:bg-white hover:bg-opacity-10 transition-colors">${validate_component(Search, "Search").$$render($$result, { class: "h-5 w-5 mr-2" }, {}, {})}
            浏览模型</a></div></div></div></div> <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"> ${featuredRepositories.length > 0 ? `<div class="mb-12"><div class="flex items-center justify-between mb-6"><h2 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center">${validate_component(TrendingUp, "TrendingUp").$$render($$result, { class: "h-6 w-6 mr-2" }, {}, {})}
            精选仓库</h2></div> <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">${each(featuredRepositories, (repo) => {
      return `${validate_component(RepositoryCard, "RepositoryCard").$$render($$result, { repo, currentUser, compact: true }, {}, {})}`;
    })}</div></div>` : ``}  <div class="flex flex-col lg:flex-row gap-8"> <div class="lg:w-64 flex-shrink-0"><div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6"><h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-1rmbwuz">筛选</h3>  <div class="mb-6"><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-i0p7v1">仓库类型</label> <select class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"><option value="" data-svelte-h="svelte-1de29ji">全部</option><option value="model" data-svelte-h="svelte-s0uthp">模型</option><option value="dataset" data-svelte-h="svelte-tyvjsm">数据集</option><option value="space" data-svelte-h="svelte-tw53qg">空间</option></select></div>  <div class="mb-6"><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-1kptzne">分类</label> ${validate_component(ClassificationFilter, "ClassificationFilter").$$render(
      $$result,
      { classifications, selectedClassification },
      {
        selectedClassification: ($$value) => {
          selectedClassification = $$value;
          $$settled = false;
        }
      },
      {}
    )}</div>  <div class="mb-6"><label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-thvc8u">排序方式</label> <select class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"><option value="updated_at" data-svelte-h="svelte-lnxctg">最近更新</option><option value="created_at" data-svelte-h="svelte-hp3d75">最新创建</option><option value="stars_count" data-svelte-h="svelte-1b2r1sh">最多星标</option><option value="downloads_count" data-svelte-h="svelte-joemc3">最多下载</option><option value="views_count" data-svelte-h="svelte-1rqqrso">最多查看</option></select></div></div></div>  <div class="flex-1">${`<div class="flex items-center justify-center py-12">${validate_component(Loading, "Loading").$$render($$result, { size: "lg" }, {}, {})}</div>`}</div></div></div> </div>`;
  } while (!$$settled);
  return $$rendered;
});
export {
  Page as default
};
