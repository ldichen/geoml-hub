const prerender = false;
const ssr = false;
async function load({ params, fetch }) {
  try {
    const response = await fetch(`/api/users/${params.username}`);
    if (!response.ok) {
      return {
        user: null,
        error: "User not found"
      };
    }
    const user = await response.json();
    return {
      user,
      meta: {
        title: `${user.username} - GeoML-Hub`,
        description: user.bio || `${user.username} 的模型仓库`,
        keywords: `${user.username},用户主页,模型仓库`
      }
    };
  } catch (error) {
    return {
      user: null,
      error: error.message
    };
  }
}
export {
  load,
  prerender,
  ssr
};
