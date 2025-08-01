import { s as subscribe } from "./utils.js";
import { c as create_ssr_component, e as escape } from "./ssr.js";
import { $ as $format } from "./runtime.esm.js";
const Loading = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let sizeClasses;
  let textSizeClasses;
  let $_, $$unsubscribe__;
  $$unsubscribe__ = subscribe($format, (value) => $_ = value);
  let { text = "" } = $$props;
  let { size = "md" } = $$props;
  let { center = false } = $$props;
  if ($$props.text === void 0 && $$bindings.text && text !== void 0)
    $$bindings.text(text);
  if ($$props.size === void 0 && $$bindings.size && size !== void 0)
    $$bindings.size(size);
  if ($$props.center === void 0 && $$bindings.center && center !== void 0)
    $$bindings.center(center);
  sizeClasses = {
    sm: "w-4 h-4",
    md: "w-8 h-8",
    lg: "w-12 h-12"
  };
  textSizeClasses = {
    sm: "text-sm",
    md: "text-base",
    lg: "text-lg"
  };
  $$unsubscribe__();
  return `<div class="${"flex items-center space-x-3 " + escape(center ? "justify-center" : "", true)}"><div class="${"animate-spin rounded-full border-2 border-secondary-200 dark:border-secondary-700 border-t-primary-600 dark:border-t-primary-400 " + escape(sizeClasses[size], true)}"></div> ${text ? `<span class="${"text-secondary-600 dark:text-dark-500 " + escape(textSizeClasses[size], true)}">${escape(text)}</span>` : `<span class="${"text-secondary-600 dark:text-dark-500 " + escape(textSizeClasses[size], true)}">${escape($_("common.loading"))}</span>`}</div>`;
});
export {
  Loading as L
};
