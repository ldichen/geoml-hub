import "../../chunks/index2.js";
const prerender = true;
async function load({ fetch }) {
  return {
    meta: {
      title: "GeoML-Hub - 地理科学机器学习模型仓库",
      description: "首个专注于地理科学的机器学习模型中心"
    }
  };
}
export {
  load,
  prerender
};
