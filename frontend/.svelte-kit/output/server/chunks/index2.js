import { r as registerLocaleLoader, i as init, g as getLocaleFromNavigator } from "./runtime.js";
registerLocaleLoader("en-US", () => import("./en-US.js"));
registerLocaleLoader("zh-CN", () => import("./zh-CN.js"));
function getInitialLocale() {
  return getLocaleFromNavigator() || "zh-CN";
}
init({
  fallbackLocale: "zh-CN",
  initialLocale: getInitialLocale()
});
