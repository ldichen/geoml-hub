const prerender = false;
const ssr = false;
async function load({ params, fetch }) {
  try {
    const response = await fetch(`/api/repositories/${params.username}/${params.repository}`);
    if (!response.ok) {
      return {
        repository: null,
        error: "Repository not found"
      };
    }
    const repository = await response.json();
    return {
      repository,
      meta: {
        title: `${params.username}/${params.repository} - GeoML-Hub`,
        description: repository.description || `${params.username}/${params.repository} 模型仓库`,
        keywords: `${params.repository},模型仓库,${params.username},机器学习模型`
      }
    };
  } catch (error) {
    return {
      repository: null,
      error: error.message
    };
  }
}
export {
  load,
  prerender,
  ssr
};
