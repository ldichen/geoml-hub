import { c as create_ssr_component, b as add_attribute, e as escape } from "./ssr.js";
function getVariantClasses(variant) {
  const baseClasses = "inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed";
  switch (variant) {
    case "primary":
      return `${baseClasses} bg-primary-600 hover:bg-primary-700 text-white shadow-sm focus:ring-primary-500`;
    case "secondary":
      return `${baseClasses} bg-gray-100 hover:bg-gray-200 text-gray-900 focus:ring-gray-500 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-100`;
    case "danger":
      return `${baseClasses} bg-red-600 hover:bg-red-700 text-white shadow-sm focus:ring-red-500`;
    case "ghost":
      return `${baseClasses} text-gray-600 hover:bg-gray-100 focus:ring-gray-500 dark:text-gray-400 dark:hover:bg-gray-800`;
    case "outline":
      return `${baseClasses} border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-gray-300`;
    default:
      return `${baseClasses} bg-primary-600 hover:bg-primary-700 text-white shadow-sm focus:ring-primary-500`;
  }
}
function getSizeClasses(size) {
  switch (size) {
    case "xs":
      return "px-2 py-1 text-xs";
    case "sm":
      return "px-3 py-1.5 text-sm";
    case "md":
      return "px-4 py-2 text-sm";
    case "lg":
      return "px-6 py-3 text-base";
    case "xl":
      return "px-8 py-4 text-lg";
    default:
      return "px-4 py-2 text-sm";
  }
}
function getIconSize(size) {
  switch (size) {
    case "xs":
      return "h-3 w-3";
    case "sm":
      return "h-4 w-4";
    case "md":
      return "h-4 w-4";
    case "lg":
      return "h-5 w-5";
    case "xl":
      return "h-6 w-6";
    default:
      return "h-4 w-4";
  }
}
const Button = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let buttonClasses;
  let iconClasses;
  let { variant = "primary" } = $$props;
  let { size = "md" } = $$props;
  let { disabled = false } = $$props;
  let { loading = false } = $$props;
  let { href = null } = $$props;
  let { type = "button" } = $$props;
  let { fullWidth = false } = $$props;
  if ($$props.variant === void 0 && $$bindings.variant && variant !== void 0)
    $$bindings.variant(variant);
  if ($$props.size === void 0 && $$bindings.size && size !== void 0)
    $$bindings.size(size);
  if ($$props.disabled === void 0 && $$bindings.disabled && disabled !== void 0)
    $$bindings.disabled(disabled);
  if ($$props.loading === void 0 && $$bindings.loading && loading !== void 0)
    $$bindings.loading(loading);
  if ($$props.href === void 0 && $$bindings.href && href !== void 0)
    $$bindings.href(href);
  if ($$props.type === void 0 && $$bindings.type && type !== void 0)
    $$bindings.type(type);
  if ($$props.fullWidth === void 0 && $$bindings.fullWidth && fullWidth !== void 0)
    $$bindings.fullWidth(fullWidth);
  buttonClasses = `${getVariantClasses(variant)} ${getSizeClasses(size)} ${fullWidth ? "w-full" : ""}`;
  iconClasses = getIconSize(size);
  return `${href ? `<a${add_attribute("href", href, 0)} class="${[
    escape(buttonClasses, true),
    (disabled ? "opacity-50" : "") + " " + (disabled ? "pointer-events-none" : "")
  ].join(" ").trim()}">${loading ? `<div class="${"animate-spin rounded-full border-2 border-current border-t-transparent " + escape(iconClasses, true) + " mr-2"}"></div>` : ``} ${slots.default ? slots.default({}) : ``}</a>` : `<button${add_attribute("type", type, 0)}${add_attribute("class", buttonClasses, 0)} ${disabled ? "disabled" : ""}>${loading ? `<div class="${"animate-spin rounded-full border-2 border-current border-t-transparent " + escape(iconClasses, true) + " mr-2"}"></div>` : ``} ${slots.default ? slots.default({}) : ``}</button>`}`;
});
export {
  Button as B
};
