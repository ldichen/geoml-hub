import { s as subscribe } from "../../../chunks/utils.js";
import { c as create_ssr_component, e as escape, b as add_attribute, v as validate_component, d as each } from "../../../chunks/ssr.js";
import { $ as $format } from "../../../chunks/runtime.esm.js";
import "../../../chunks/api.js";
/* empty css                                                            */import { L as Loading } from "../../../chunks/Loading.js";
import { T as TrendingUp } from "../../../chunks/trending-up.js";
import { F as Filter } from "../../../chunks/filter.js";
import { C as Calendar, S as Star, D as Download, E as Eye } from "../../../chunks/star.js";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let $_, $$unsubscribe__;
  $$unsubscribe__ = subscribe($format, (value) => $_ = value);
  let repositories = [];
  let period = "week";
  const periods = [
    { value: "day", label: "time.today" },
    { value: "week", label: "time.this_week" },
    { value: "month", label: "time.this_month" },
    { value: "year", label: "time.this_year" }
  ];
  const repoTypes = [
    { value: "", label: "common.all" },
    {
      value: "model",
      label: "repository.model"
    },
    {
      value: "dataset",
      label: "repository.dataset"
    },
    {
      value: "space",
      label: "repository.space"
    }
  ];
  function getPeriodDisplay(period2) {
    switch (period2) {
      case "day":
        return $_("time.today");
      case "week":
        return $_("time.this_week");
      case "month":
        return $_("time.this_month");
      case "year":
        return $_("time.this_year");
      default:
        return period2;
    }
  }
  $$unsubscribe__();
  return `${$$result.head += `<!-- HEAD_svelte-6zevb1_START -->${$$result.title = `<title>${escape($_("search.trending"))} - GeoML-Hub</title>`, ""}<meta name="description"${add_attribute("content", $_("search.trending_description"), 0)}><!-- HEAD_svelte-6zevb1_END -->`, ""} <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"> <div class="mb-8"><div class="flex items-center space-x-2 mb-4">${validate_component(TrendingUp, "TrendingUp").$$render($$result, { class: "w-8 h-8 text-primary-600" }, {}, {})} <h1 class="text-3xl font-bold text-gray-900 dark:text-white">${escape($_("search.trending"))}</h1></div> <p class="text-lg text-gray-600 dark:text-gray-400">${escape($_("search.trending_subtitle"))} ${escape(getPeriodDisplay(period))}</p></div>  <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6 mb-6"><div class="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0"><div class="flex items-center space-x-2">${validate_component(Filter, "Filter").$$render($$result, { class: "w-5 h-5 text-gray-400" }, {}, {})} <span class="text-sm font-medium text-gray-700 dark:text-gray-300">${escape($_("search.filters"))}:</span></div> <div class="flex flex-wrap items-center gap-4"> <div class="flex items-center space-x-2">${validate_component(Calendar, "Calendar").$$render($$result, { class: "w-4 h-4 text-gray-400" }, {}, {})} <select class="input-sm">${each(periods, (periodOption) => {
    return `<option${add_attribute("value", periodOption.value, 0)}>${escape($_(periodOption.label))} </option>`;
  })}</select></div>  <div class="flex items-center space-x-2"><span class="text-sm text-gray-600 dark:text-gray-400">${escape($_("repository.type"))}:</span> <select class="input-sm">${each(repoTypes, (type) => {
    return `<option${add_attribute("value", type.value, 0)}>${escape($_(type.label))} </option>`;
  })}</select></div></div></div></div>  ${`<div class="flex justify-center py-12">${validate_component(Loading, "Loading").$$render($$result, {}, {}, {})}</div>`}</div>  ${repositories.length > 0 ? `<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"><div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6"><h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">${escape($_("search.trending_stats"))}</h2> <div class="grid grid-cols-1 md:grid-cols-3 gap-4"> <div class="text-center"><div class="flex items-center justify-center w-12 h-12 bg-yellow-100 dark:bg-yellow-900/20 rounded-full mx-auto mb-2">${validate_component(Star, "Star").$$render($$result, { class: "w-6 h-6 text-yellow-600" }, {}, {})}</div> <p class="text-2xl font-bold text-gray-900 dark:text-white">${escape(Math.round(repositories.reduce((sum, r) => sum + (r.stars_count || 0), 0) / repositories.length))}</p> <p class="text-sm text-gray-600 dark:text-gray-400">${escape($_("search.avg_stars"))}</p></div>  <div class="text-center"><div class="flex items-center justify-center w-12 h-12 bg-green-100 dark:bg-green-900/20 rounded-full mx-auto mb-2">${validate_component(Download, "Download").$$render($$result, { class: "w-6 h-6 text-green-600" }, {}, {})}</div> <p class="text-2xl font-bold text-gray-900 dark:text-white">${escape(Math.round(repositories.reduce((sum, r) => sum + (r.downloads_count || 0), 0) / repositories.length))}</p> <p class="text-sm text-gray-600 dark:text-gray-400">${escape($_("search.avg_downloads"))}</p></div>  <div class="text-center"><div class="flex items-center justify-center w-12 h-12 bg-blue-100 dark:bg-blue-900/20 rounded-full mx-auto mb-2">${validate_component(Eye, "Eye").$$render($$result, { class: "w-6 h-6 text-blue-600" }, {}, {})}</div> <p class="text-2xl font-bold text-gray-900 dark:text-white">${escape(Math.round(repositories.reduce((sum, r) => sum + (r.views_count || 0), 0) / repositories.length))}</p> <p class="text-sm text-gray-600 dark:text-gray-400">${escape($_("search.avg_views"))}</p></div></div></div></div>` : ``}`;
});
export {
  Page as default
};
