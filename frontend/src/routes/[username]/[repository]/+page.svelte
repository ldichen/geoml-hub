<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import {
		Star,
		Download,
		Eye,
		GitFork,
		Calendar,
		Settings,
		Upload,
		FileText,
		ChevronRight,
		FolderOpen,
		ChevronDown,
		Edit2,
		Trash2,
		Tag,
		AlertCircle,
		X
	} from 'lucide-svelte';
	import { formatDistanceToNow } from 'date-fns';
	import { zhCN } from 'date-fns/locale';
	import { marked } from 'marked';
	import { _ } from 'svelte-i18n';
	import { api } from '$lib/utils/api';
	import { user as currentUser, isAuthenticated } from '$lib/stores/auth.js';
	import { isOwner, hasPermission } from '$lib/utils/auth.js';
	import UserAvatar from '$lib/components/UserAvatar.svelte';
	import SocialButton from '$lib/components/SocialButton.svelte';
	import Loading from '$lib/components/Loading.svelte';
	import ServiceList from '$lib/components/service/ServiceList.svelte';
	import ServiceCreateModal from '$lib/components/service/ServiceCreateModal.svelte';
	import ServiceMonitor from '$lib/components/service/ServiceMonitor.svelte';
	import ServiceLogs from '$lib/components/service/ServiceLogs.svelte';
	import ServiceSettings from '$lib/components/service/ServiceSettings.svelte';
	import ImageList from '$lib/components/image/ImageList.svelte';
	import ImageDetailModal from '$lib/components/image/ImageDetailModal.svelte';
	import ServiceFromImageModal from '$lib/components/image/ServiceFromImageModal.svelte';
	import ClassificationSelector from '$lib/components/ClassificationSelector.svelte';

	let repository = null;
	let files = [];
	let services = [];
	let availableImages = []; // 可用镜像列表，用于服务创建
	let loading = true;
	let error = null;
	let activeTab = 'model-card';
	let downloadingFiles = new Set();
	let uploadingFiles = new Set();
	let uploadProgress = {}; // 存储上传进度信息
	let folderInput; // 文件夹上传输入元素
	let fileInput;
	let newTagInput = '';
	let showDropZone = false; // 控制拖拽上传弹窗显示
	let isDragOver = false; // 控制拖拽状态
	let pendingFiles = []; // 待确认上传的文件
	let pendingFilesIsFolder = false; // 待上传文件是否为文件夹
	let showUploadConfirm = false; // 显示上传确认弹窗
	let showConfirmDialog = false;
	let confirmDialogData = null;

	// Service modals and views
	let showCreateServiceModal = false;
	let showServiceMonitor = false;
	let showServiceLogs = false;
	let showServiceSettings = false;
	let selectedService = null;
	let serviceModalLoading = false;

	// Image modals and views
	let showImageDetailModal = false;
	let showServiceFromImageModal = false;
	let selectedImage = null;

	// Classification management states
	let classifications = [];
	let taskClassifications = [];
	let selectedClassificationId: number | null = null;
	let selectedTaskClassificationIds: number[] = [];
	let originalClassificationId: number | null = null;
	let originalTaskClassificationIds: number[] = [];
	let loadingClassifications = false;
	let loadingTaskClassifications = false;
	let savingClassifications = false;
	let classificationSuccessMessage: string | null = null;
	let classificationError: string | null = null;

	// Settings form states
	let originalDescription: string = '';
	let originalVisibility: string = '';
	let originalLicense: string = '';
	let originalBaseModel: string = '';
	let originalTags: string[] = [];

	// Track if any changes have been made
	$: hasBasicChanges =
		repository &&
		(repository.description !== originalDescription ||
			repository.visibility !== originalVisibility ||
			repository.license !== originalLicense ||
			repository.base_model !== originalBaseModel ||
			JSON.stringify(repository.tags) !== JSON.stringify(originalTags));

	$: hasClassificationChanges =
		selectedClassificationId !== originalClassificationId ||
		JSON.stringify([...selectedTaskClassificationIds].sort()) !==
			JSON.stringify([...originalTaskClassificationIds].sort());

	$: username = $page.params.username;
	$: repoName = $page.params.repository;
	$: isRepoOwner =
		$currentUser && repository && isOwner(repository.owner?.username || repository.owner?.id);

	// 文件树状态
	let expandedFolders = new Set();
	let fileTree = [];

	// 构建文件树
	function buildFileTree(files) {
		const tree = {};
		const result = [];

		files.forEach((file) => {
			const filePath = file.file_path || file.filename;
			const pathParts = filePath.split('/');

			if (pathParts.length === 1) {
				// 根目录文件
				result.push({
					type: 'file',
					name: pathParts[0],
					path: filePath,
					data: file,
					level: 0
				});
			} else {
				// 文件夹中的文件
				const folderName = pathParts[0];
				if (!tree[folderName]) {
					tree[folderName] = {
						type: 'folder',
						name: folderName,
						path: folderName,
						files: [],
						level: 0
					};
				}
				tree[folderName].files.push({
					type: 'file',
					name: pathParts.slice(1).join('/'),
					path: filePath,
					data: file,
					level: 1
				});
			}
		});

		// 将文件夹添加到结果中
		Object.values(tree).forEach((folder) => {
			result.push(folder);
		});

		// 排序：文件夹在前，文件在后
		return result.sort((a, b) => {
			if (a.type === 'folder' && b.type === 'file') return -1;
			if (a.type === 'file' && b.type === 'folder') return 1;
			return a.name.localeCompare(b.name);
		});
	}

	// 响应式更新文件树
	$: fileTree = files ? buildFileTree(files) : [];

	// 切换文件夹展开状态
	function toggleFolder(folderPath) {
		if (expandedFolders.has(folderPath)) {
			expandedFolders.delete(folderPath);
		} else {
			expandedFolders.add(folderPath);
		}
		expandedFolders = expandedFolders;
	}

	onMount(async () => {
		await loadRepositoryData();
	});

	async function loadRepositoryData() {
		try {
			loading = true;
			error = null;

			const [repoResponse, filesResponse] = await Promise.all([
				api.getRepository(username, repoName),
				api.getRepositoryFiles(username, repoName)
			]);

			repository = repoResponse;
			files = filesResponse.items || filesResponse;

			// 增加浏览量统计
			try {
				await api.incrementRepositoryView(username, repoName);
			} catch (err) {
				// 浏览量统计失败不影响页面加载
				console.warn('Failed to increment repository view:', err);
			}

			// 加载服务并自动启动（如果是仓库所有者）
			const shouldAutoStart =
				$currentUser && repository && isOwner(repository.owner?.username || repository.owner?.id);
			const servicesResponse = await api
				.getRepositoryServices(username, repoName, {
					auto_start: shouldAutoStart
				})
				.catch(() => ({ items: [], services: [] }));

			services = servicesResponse.services || servicesResponse.items || servicesResponse || [];

			// 处理自动启动结果
			if (servicesResponse.auto_start_result) {
				handleAutoStartResult(servicesResponse.auto_start_result);
			}

			// 加载可用镜像列表（用于服务创建）
			try {
				console.log('Loading images for repository ID:', repository.id);
				const imagesResponse = await api.getRepositoryImages(repository.id);
				console.log('Images API response:', imagesResponse);

				if (imagesResponse && imagesResponse.success) {
					availableImages = (imagesResponse.data || []).filter((img) => img.status === 'ready');
				} else if (Array.isArray(imagesResponse)) {
					// 处理直接返回数组的情况
					availableImages = imagesResponse.filter((img) => img.status === 'ready');
				} else {
					availableImages = [];
				}

				console.log('Available images for service creation:', availableImages);
			} catch (err) {
				console.warn('Failed to load available images:', err);
				availableImages = [];
			}

			// 调试：查看数据结构
			console.log('Repository response:', repoResponse);
			console.log('Files response:', filesResponse);
			console.log('Services response:', servicesResponse);
			console.log('Services data:', services);

			// 调试：检查服务的镜像数据
			if (services && services.length > 0) {
				console.log('First service:', services[0]);
				console.log('First service image:', services[0].image);
				console.log('First service model_id:', services[0].model_id);
				console.log('First service image_id:', services[0].image_id);
			}

			// Load current user if authenticated
			const token = api.getToken();
			if (token) {
				// TODO: Implement current user loading
				// currentUser store is automatically managed by auth store
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load repository data';
			console.error('Error loading repository data:', err);
		} finally {
			loading = false;
		}
	}

	// 处理自动启动结果
	function handleAutoStartResult(autoStartResult) {
		if (!autoStartResult.auto_start_enabled) return;

		console.log('Auto-start result:', autoStartResult);

		// 显示自动启动状态通知
		const {
			services: startupResults,
			started_count,
			total_services,
			available_slots
		} = autoStartResult;

		if (started_count > 0) {
			// 有服务成功启动
			const message = `Successfully started ${started_count} of ${total_services} services`;
			showNotification(message, 'success');
		}

		// 检查永久失败的服务
		const permanentlyFailedServices = startupResults.filter(
			(s) => s.status === 'permanently_failed'
		);
		if (permanentlyFailedServices.length > 0) {
			const message = `${permanentlyFailedServices.length} services have permanent errors and cannot be retried`;
			showNotification(message, 'error');
		}

		// 检查重试次数耗尽的服务
		const retryExhaustedServices = startupResults.filter((s) => s.status === 'retry_exhausted');
		if (retryExhaustedServices.length > 0) {
			const message = `${retryExhaustedServices.length} services have reached maximum retry attempts`;
			showNotification(message, 'warning');
		}

		// 检查正在重试冷却的服务
		const retryPendingServices = startupResults.filter((s) => s.status === 'retry_pending');
		if (retryPendingServices.length > 0) {
			const message = `${retryPendingServices.length} services are in retry cooldown`;
			showNotification(message, 'info');
		}

		// 检查是否有其他启动失败的服务
		const failedServices = startupResults.filter(
			(s) => s.status === 'resource_error' || s.status === 'system_error'
		);

		if (failedServices.length > 0) {
			const message = `${failedServices.length} services failed to start (will retry automatically)`;
			showNotification(message, 'warning');
		}

		// 检查是否有资源不足导致的排队服务
		const queuedServices = startupResults.filter((s) => s.status === 'queued');
		if (queuedServices.length > 0) {
			const message = `${queuedServices.length} services queued due to resource limits`;
			showNotification(message, 'info');
		}
	}

	// 简单的通知函数（可以后续替换为更完善的通知系统）
	function showNotification(message, type = 'info') {
		console.log(`[${type.toUpperCase()}] ${message}`);
		// 这里可以集成toast通知或其他UI反馈
	}

	// 获取服务状态颜色样式
	function getServiceStatusColor(status) {
		switch (status) {
			case 'running':
				return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
			case 'starting':
				return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
			case 'stopping':
				return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
			case 'stopped':
				return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
			case 'error':
				return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
			case 'idle':
				return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
			// 新增重试相关状态
			case 'retry_pending':
				return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
			case 'permanently_failed':
				return 'bg-red-200 text-red-900 dark:bg-red-800 dark:text-red-100';
			case 'retry_exhausted':
				return 'bg-orange-200 text-orange-900 dark:bg-orange-800 dark:text-orange-100';
			default:
				return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
		}
	}

	// 获取服务状态显示文本
	function getServiceStatusText(status) {
		switch (status) {
			case 'running':
				return 'Running';
			case 'starting':
				return '启动中';
			case 'stopping':
				return '停止中';
			case 'stopped':
				return '已停止';
			case 'error':
				return '错误';
			case 'idle':
				return '空闲';
			case 'created':
				return '已创建';
			// 新增重试相关状态
			case 'retry_pending':
				return '等待重试';
			case 'permanently_failed':
				return '永久失败';
			case 'retry_exhausted':
				return '重试次数已耗尽';
			default:
				return '未知';
		}
	}

	// 获取服务卡片渐变背景
	function getServiceGradient(index) {
		const gradients = [
			'from-blue-500 via-cyan-500 to-teal-500', // Blue to teal gradient
			'from-purple-500 via-pink-500 to-rose-500', // Purple to rose gradient
			'from-orange-500 via-amber-500 to-yellow-500', // Orange to yellow gradient
			'from-emerald-500 via-green-500 to-lime-500', // Green gradient
			'from-indigo-500 via-purple-500 to-pink-500', // Indigo to pink gradient
			'from-red-500 via-pink-500 to-purple-500' // Red to purple gradient
		];
		return gradients[index % gradients.length];
	}

	// 跳转到服务demo页面
	function handleServiceClick(service) {
		if (service.status !== 'running') return;

		if (service.service_url) {
			// 如果有service_url，直接跳转
			window.open(service.service_url, '_blank');
		} else if (service.gradio_port) {
			// 如果有gradio_port，构建URL
			const demoUrl = `http://${service.model_ip}:${service.gradio_port}`;
			window.open(demoUrl, '_blank');
		} else {
			console.warn('Service has no accessible URL:', service);
		}
	}

	async function handleStar() {
		if (!repository || !$currentUser) return;

		try {
			if (repository.is_starred) {
				await api.unstarRepository(username, repoName);
				repository.is_starred = false;
				repository.stars_count -= 1;
			} else {
				await api.starRepository(username, repoName);
				repository.is_starred = true;
				repository.stars_count += 1;
			}
		} catch (err) {
			console.error('Error starring repository:', err);
		}
	}

	function formatFileSize(bytes: number) {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
	}

	function getRepoTypeLabel(type: string) {
		switch (type) {
			case 'model':
				return '模型';
			case 'dataset':
				return '数据集';
			case 'space':
				return '空间';
			default:
				return type;
		}
	}

	function getRepoTypeColor(type: string) {
		switch (type) {
			case 'model':
				return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
			case 'dataset':
				return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
			case 'space':
				return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
			default:
				return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
		}
	}

	$: readmeHtml = repository?.readme_content
		? processMarkdown(removeYamlFrontmatter(repository.readme_content))
		: '';

	function removeYamlFrontmatter(content) {
		// Remove YAML frontmatter (--- ... ---)
		return content.replace(/^---\s*\n[\s\S]*?\n---\s*\n/, '');
	}

	function processMarkdown(content) {
		let html = marked(content);

		// 为表格添加滚动容器
		html = html.replace(/<table>/g, '<div class="table-container"><table>');
		html = html.replace(/<\/table>/g, '</table></div>');

		// 处理相对路径的图片引用，转换为正确的API端点
		// 匹配相对路径图片：不以http://、https://、/开头的路径
		html = html.replace(
			/<img([^>]*?)src=["']((?!https?:\/\/)(?!\/)\.?\/?[^"']+)["']/gi,
			(match, attributes, imagePath) => {
				// 移除开头的 ./ 如果存在
				const cleanPath = imagePath.replace(/^\.\//, '');
				const newSrc = `/api/repositories/${username}/${repoName}/raw/${cleanPath}`;
				return `<img${attributes}src="${newSrc}"`;
			}
		);

		return html;
	}

	async function handleDownload(file) {
		try {
			// 防止重复下载
			if (downloadingFiles.has(file.id)) {
				return;
			}

			downloadingFiles.add(file.id);
			downloadingFiles = downloadingFiles; // 触发响应式更新

			const downloadData = await api.getDownloadUrl(username, repoName, file.file_path);

			// 使用fetch下载文件并强制下载
			try {
				const response = await fetch(downloadData.download_url);
				const blob = await response.blob();

				// 创建下载链接
				const url = window.URL.createObjectURL(blob);
				const link = document.createElement('a');
				link.href = url;
				link.download = file.filename;
				link.style.display = 'none';

				document.body.appendChild(link);
				link.click();
				document.body.removeChild(link);

				// 清理URL对象
				window.URL.revokeObjectURL(url);
			} catch (fetchError) {
				// 如果fetch失败，回退到直接链接方式
				console.warn('Fetch download failed, falling back to direct link:', fetchError);
				const link = document.createElement('a');
				link.href = downloadData.download_url;
				link.download = file.filename;
				link.style.display = 'none';
				document.body.appendChild(link);
				link.click();
				document.body.removeChild(link);
			}
		} catch (error) {
			console.error('Download failed:', error);
			// 可以在这里显示错误消息
			alert('下载失败，请重试');
		} finally {
			downloadingFiles.delete(file.id);
			downloadingFiles = downloadingFiles; // 触发响应式更新
		}
	}

	function handleUploadClick() {
		showDropZone = true;
	}

	function handleFolderUploadClick() {
		folderInput.click();
	}

	// 拖拽处理函数
	function handleDragEnter(e) {
		e.preventDefault();
		e.stopPropagation();
		isDragOver = true;
	}

	function handleDragLeave(e) {
		e.preventDefault();
		e.stopPropagation();
		// 检查是否真的离开了拖拽区域
		const rect = e.currentTarget.getBoundingClientRect();
		const x = e.clientX;
		const y = e.clientY;

		if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
			isDragOver = false;
		}
	}

	function handleDragOver(e) {
		e.preventDefault();
		e.stopPropagation();
	}

	function handleDrop(e) {
		e.preventDefault();
		e.stopPropagation();
		isDragOver = false;

		const files = [];
		const items = e.dataTransfer.items;

		if (items) {
			for (let i = 0; i < items.length; i++) {
				const item = items[i];
				if (item.kind === 'file') {
					const entry = item.webkitGetAsEntry();
					if (entry) {
						if (entry.isDirectory) {
							// 处理文件夹
							readDirectoryEntries(entry, files).then(() => {
								showUploadConfirmation(files, true);
							});
							return;
						} else {
							// 处理文件
							files.push(item.getAsFile());
						}
					}
				}
			}
		}

		if (files.length > 0) {
			showUploadConfirmation(files, false);
		}
	}

	// 文件输入处理
	function handleFileInputChange(e) {
		const target = e.target;
		const files = Array.from(target.files || []);
		const isFolder = files.some((file) => (file as any).webkitRelativePath);
		showUploadConfirmation(files, isFolder);
		target.value = ''; // 清空输入
	}

	// 递归读取文件夹
	async function readDirectoryEntries(directoryEntry, files) {
		const reader = directoryEntry.createReader();

		return new Promise((resolve) => {
			const readEntries = () => {
				reader.readEntries(async (entries) => {
					if (entries.length === 0) {
						resolve();
						return;
					}

					for (const entry of entries) {
						if (entry.isFile) {
							const file = await new Promise((fileResolve) => {
								entry.file((file) => {
									// 设置相对路径
									Object.defineProperty(file, 'webkitRelativePath', {
										value: entry.fullPath.substring(1), // 去掉开头的 /
										writable: false
									});
									fileResolve(file);
								});
							});
							files.push(file);
						} else if (entry.isDirectory) {
							await readDirectoryEntries(entry, files);
						}
					}

					readEntries(); // 递归读取更多条目
				});
			};

			readEntries();
		});
	}

	// 显示上传确认
	function showUploadConfirmation(files, isFolder) {
		pendingFiles = files;
		pendingFilesIsFolder = isFolder;
		showUploadConfirm = true;
	}

	// 确认上传
	async function confirmUpload() {
		showUploadConfirm = false;

		for (const file of pendingFiles) {
			const relativePath = (file as any).webkitRelativePath || null;
			await uploadFileWithProgress(file, relativePath);
		}

		pendingFiles = [];
	}

	// 取消上传
	function cancelUpload() {
		showUploadConfirm = false;
		pendingFiles = [];
	}

	async function handleFilesSelected(event) {
		const { files, isFolder } = event.detail;
		showDropZone = false;

		console.log(`选中了 ${files.length} 个文件进行上传，是文件夹: ${isFolder}`);

		for (const file of files) {
			const relativePath = isFolder ? (file as any).webkitRelativePath : null;
			await uploadFileWithProgress(file, relativePath);
		}
	}

	async function handleFileUpload(event) {
		const selectedFiles = Array.from(event.target.files);

		for (const file of selectedFiles) {
			await uploadFileWithProgress(file);
		}

		// 清空文件输入
		event.target.value = '';
	}

	async function handleFolderUpload(event) {
		const selectedFiles = Array.from(event.target.files);

		console.log(`选中了 ${selectedFiles.length} 个文件进行上传`);

		for (const file of selectedFiles) {
			await uploadFileWithProgress(file, (file as any).webkitRelativePath);
		}

		// 清空文件输入
		event.target.value = '';
	}

	async function uploadFile(file) {
		try {
			uploadingFiles.add(file.name);
			uploadingFiles = uploadingFiles; // 触发响应式更新

			// 使用带进度的上传流程（包含冲突检查）
			await uploadFileWithProgress(file);

			// 上传成功后重新加载文件列表
			await loadRepositoryData();
		} catch (error) {
			console.error('Upload failed:', error);
			alert(`上传文件 ${file.name} 失败：${error.message}`);
		} finally {
			uploadingFiles.delete(file.name);
			uploadingFiles = uploadingFiles; // 触发响应式更新
		}
	}

	// 处理用户确认替换
	async function handleConfirmReplace() {
		showConfirmDialog = false;
		const { file, relativePath } = confirmDialogData;

		try {
			// 直接调用上传函数，传入confirmed=true跳过冲突检查
			await uploadFileWithProgress(file, relativePath, true);
		} catch (error) {
			console.error('Upload failed:', error);
			alert(`上传文件 ${file.name} 失败：${error.message}`);
		}

		confirmDialogData = null;
	}

	// 处理用户取消替换
	function handleCancelReplace() {
		showConfirmDialog = false;
		const { file, relativePath } = confirmDialogData;
		const fileName = relativePath || file.name;

		// 清理进度状态
		if (uploadProgress[fileName]) {
			delete uploadProgress[fileName];
			uploadProgress = { ...uploadProgress };
		}

		// 从上传列表中移除文件
		uploadingFiles.delete(file.name);
		uploadingFiles = uploadingFiles;

		confirmDialogData = null;
	}

	async function uploadFileWithProgress(file, relativePath = null, confirmed = false) {
		const fileName = relativePath || file.name;

		try {
			// 如果未确认，先检查冲突
			if (!confirmed) {
				const conflictResult = await api.checkUploadConflict(username, repoName, fileName);

				// 如果有冲突，显示确认对话框
				if (conflictResult.has_conflict) {
					confirmDialogData = {
						file: file,
						relativePath: relativePath,
						conflictData: conflictResult
					};
					showConfirmDialog = true;
					return; // 等待用户确认，不继续上传
				}
			}

			// 初始化进度
			uploadProgress[fileName] = {
				loaded: 0,
				total: file.size,
				percentage: 0,
				status: 'uploading'
			};
			uploadProgress = { ...uploadProgress };

			// 使用XMLHttpRequest上传文件
			await uploadFileWithXHR(file, relativePath, confirmed);

			// 上传成功后重新加载文件列表
			await loadRepositoryData();
		} catch (error) {
			console.error('Upload failed:', error);

			// 更新进度状态为错误
			if (uploadProgress[fileName]) {
				uploadProgress[fileName] = {
					...uploadProgress[fileName],
					status: 'error'
				};
				uploadProgress = { ...uploadProgress };
			}
			alert(`上传文件 ${fileName} 失败：${error.message}`);
		}
	}

	// XMLHttpRequest上传实现
	async function uploadFileWithXHR(file, relativePath = null, confirmed = false) {
		const fileName = relativePath || file.name;
		const confirmParam = confirmed ? '&confirmed=true' : '';

		return new Promise((resolve, reject) => {
			// 创建FormData
			const formData = new FormData();
			formData.append('file', file);
			if (relativePath) {
				formData.append('filepath', relativePath);
			}

			// 创建XMLHttpRequest以支持进度回调
			const xhr = new XMLHttpRequest();

			// 监听上传进度
			xhr.upload.addEventListener('progress', (event) => {
				if (event.lengthComputable) {
					const percentage = Math.round((event.loaded / event.total) * 100);
					uploadProgress[fileName] = {
						loaded: event.loaded,
						total: event.total,
						percentage: percentage,
						status: 'uploading'
					};
					uploadProgress = { ...uploadProgress };
				}
			});

			// 监听上传完成
			xhr.addEventListener('load', () => {
				if (xhr.status === 200) {
					uploadProgress[fileName] = {
						...uploadProgress[fileName],
						percentage: 100,
						status: 'completed'
					};
					uploadProgress = { ...uploadProgress };

					// 2秒后清除进度条
					setTimeout(() => {
						delete uploadProgress[fileName];
						uploadProgress = { ...uploadProgress };
					}, 2000);

					resolve(JSON.parse(xhr.responseText));
				} else {
					uploadProgress[fileName] = {
						...uploadProgress[fileName],
						status: 'error'
					};
					uploadProgress = { ...uploadProgress };
					reject(new Error(`Upload failed with status ${xhr.status}`));
				}
			});

			// 监听错误
			xhr.addEventListener('error', () => {
				uploadProgress[fileName] = {
					...uploadProgress[fileName],
					status: 'error'
				};
				uploadProgress = { ...uploadProgress };
				reject(new Error('网络错误'));
			});

			// 发送请求
			const token = api.getToken();
			xhr.open(
				'POST',
				`/api/repositories/${username}/${repoName}/upload?file_path=${encodeURIComponent(
					fileName
				)}${confirmParam}`
			);
			if (token) {
				xhr.setRequestHeader('Authorization', `Bearer ${token}`);
			}
			xhr.send(formData);
		});
	}

	async function handleDeleteRepository() {
		if (!confirm('确定要删除这个仓库吗？此操作无法撤销！')) {
			return;
		}

		// 二次确认
		const repoName = repository.name;
		const userInput = prompt(`请输入仓库名称 "${repoName}" 以确认删除：`);

		if (userInput !== repoName) {
			alert('输入的仓库名称不匹配，删除操作已取消');
			return;
		}

		try {
			await api.deleteRepository(username, repoName);
			alert('仓库删除成功');
			// 重定向到用户页面
			window.location.href = `/${username}`;
		} catch (error) {
			console.error('Delete repository failed:', error);
			alert(`删除仓库失败：${error.message}`);
		}
	}

	function removeTag(tag) {
		if (repository.tags) {
			repository.tags = repository.tags.filter((t) => t !== tag);
		}
	}

	function addTag() {
		if (newTagInput.trim() && repository.tags && !repository.tags.includes(newTagInput.trim())) {
			repository.tags = [...repository.tags, newTagInput.trim()];
			newTagInput = '';
		} else if (newTagInput.trim() && !repository.tags) {
			repository.tags = [newTagInput.trim()];
			newTagInput = '';
		}
	}

	function handleTagKeydown(event) {
		if (event.key === 'Enter') {
			event.preventDefault();
			addTag();
		}
	}

	let savingSettings = false;
	let settingsSuccessMessage: string | null = null;
	let settingsError: string | null = null;

	async function handleSaveSettings() {
		try {
			savingSettings = true;
			settingsError = null;
			settingsSuccessMessage = null;

			await api.updateRepository(username, repoName, {
				description: repository.description,
				visibility: repository.visibility,
				license: repository.license,
				base_model: repository.base_model,
				tags: repository.tags
			});

			settingsSuccessMessage = '设置已成功保存';

			// 更新原始值
			originalDescription = repository.description || '';
			originalVisibility = repository.visibility || '';
			originalLicense = repository.license || '';
			originalBaseModel = repository.base_model || '';
			originalTags = repository.tags ? [...repository.tags] : [];

			// 3秒后清除成功消息
			setTimeout(() => {
				settingsSuccessMessage = null;
			}, 3000);
		} catch (error) {
			console.error('Save settings failed:', error);
			settingsError = error.message || '保存设置失败';
		} finally {
			savingSettings = false;
		}
	}

	// Service management functions
	let serviceCreationProgress = 0;

	async function handleCreateService(event) {
		try {
			serviceModalLoading = true;
			serviceCreationProgress = 0;

			const { type, data } = event.detail;

			let response;
			if (type === 'docker-upload') {
				// 为Docker tar包上传，使用专门的端点，支持进度条
				response = await api.createServiceWithDockerTar(username, repoName, data, (progress) => {
					serviceCreationProgress = progress;
				});
			} else if (type === 'existing-image') {
				// 基于已有镜像创建服务，使用标准API，支持进度条
				response = await api.createService(username, repoName, data, (progress) => {
					serviceCreationProgress = progress;
				});
			} else {
				throw new Error(`未知的服务创建类型: ${type}`);
			}

			serviceCreationProgress = 100;
			showCreateServiceModal = false;
			await loadRepositoryData(); // 重新加载数据
			showNotification('服务创建成功', 'success');
		} catch (error) {
			console.error('Create service failed:', error);
			showNotification(`创建服务失败：${error.message}`, 'error');
		} finally {
			serviceModalLoading = false;
		}
	}

	async function handleStartService(service) {
		try {
			await api.startService(service.id);

			// 立即更新本地状态以提供即时反馈
			const serviceIndex = services.findIndex((s) => s.id === service.id);
			if (serviceIndex !== -1) {
				services[serviceIndex] = { ...services[serviceIndex], status: 'starting' };
				services = [...services]; // 触发响应式更新
			}

			// 然后异步重新加载完整数据
			setTimeout(async () => {
				await loadRepositoryData();
			}, 1000);

			showNotification(`服务 "${service.service_name}" 正在启动`, 'success');
		} catch (error) {
			console.error('Start service failed:', error);
			showNotification(`启动服务失败：${error.message}`, 'error');
		}
	}

	async function handleStopService(service) {
		try {
			await api.stopService(service.id);

			// 立即更新本地状态以提供即时反馈
			const serviceIndex = services.findIndex((s) => s.id === service.id);
			if (serviceIndex !== -1) {
				services[serviceIndex] = { ...services[serviceIndex], status: 'stopping' };
				services = [...services]; // 触发响应式更新
			}

			// 然后异步重新加载完整数据
			setTimeout(async () => {
				await loadRepositoryData();
			}, 1000);

			showNotification(`服务 "${service.service_name}" 正在停止`, 'success');
		} catch (error) {
			console.error('Stop service failed:', error);
			showNotification(`停止服务失败：${error.message}`, 'error');
		}
	}

	async function handleRestartService(service) {
		try {
			await api.restartService(service.id);

			// 立即更新本地状态以提供即时反馈
			const serviceIndex = services.findIndex((s) => s.id === service.id);
			if (serviceIndex !== -1) {
				services[serviceIndex] = { ...services[serviceIndex], status: 'starting' };
				services = [...services]; // 触发响应式更新
			}

			// 然后异步重新加载完整数据
			setTimeout(async () => {
				await loadRepositoryData();
			}, 1000);

			showNotification(`服务 "${service.service_name}" 正在重启`, 'success');
		} catch (error) {
			console.error('Restart service failed:', error);
			showNotification(`重启服务失败：${error.message}`, 'error');
		}
	}

	async function handleDeleteService(service) {
		if (!confirm(`确定要删除服务 "${service.service_name}" 吗？此操作无法撤销！`)) {
			return;
		}

		try {
			await api.deleteService(service.id);

			// 立即从本地列表中移除该服务
			services = services.filter((s) => s.id !== service.id);

			// 然后异步重新加载完整数据（确保数据一致性）
			setTimeout(async () => {
				await loadRepositoryData();
			}, 500);

			showNotification(`服务 "${service.service_name}" 已删除`, 'success');
		} catch (error) {
			console.error('Delete service failed:', error);
			showNotification(`删除服务失败：${error.message}`, 'error');
			// 删除失败时重新加载数据
			await loadRepositoryData();
		}
	}

	// Service batch operations
	async function handleBatchStartServices(serviceIds) {
		try {
			await api.batchStartServices(username, repoName, serviceIds);

			// 立即更新本地状态
			services = services.map((service) =>
				serviceIds.includes(service.id) ? { ...service, status: 'starting' } : service
			);

			// 异步重新加载完整数据
			setTimeout(async () => {
				await loadRepositoryData();
			}, 1000);

			showNotification(`批量启动 ${serviceIds.length} 个服务`, 'success');
		} catch (error) {
			console.error('Batch start services failed:', error);
			showNotification(`批量启动失败：${error.message}`, 'error');
		}
	}

	async function handleBatchStopServices(serviceIds) {
		try {
			await api.batchStopServices(username, repoName, serviceIds);

			// 立即更新本地状态
			services = services.map((service) =>
				serviceIds.includes(service.id) ? { ...service, status: 'stopping' } : service
			);

			// 异步重新加载完整数据
			setTimeout(async () => {
				await loadRepositoryData();
			}, 1000);

			showNotification(`批量停止 ${serviceIds.length} 个服务`, 'success');
		} catch (error) {
			console.error('Batch stop services failed:', error);
			showNotification(`批量停止失败：${error.message}`, 'error');
		}
	}

	async function handleBatchDeleteServices(serviceIds) {
		if (!confirm(`确定要删除 ${serviceIds.length} 个服务吗？此操作无法撤销！`)) {
			return;
		}

		try {
			await api.batchDeleteServices(username, repoName, serviceIds);

			// 立即从本地列表中移除这些服务
			services = services.filter((service) => !serviceIds.includes(service.id));

			// 异步重新加载完整数据（确保数据一致性）
			setTimeout(async () => {
				await loadRepositoryData();
			}, 500);

			showNotification(`批量删除 ${serviceIds.length} 个服务`, 'success');
		} catch (error) {
			console.error('Batch delete services failed:', error);
			showNotification(`批量删除失败：${error.message}`, 'error');
			// 删除失败时重新加载数据
			await loadRepositoryData();
		}
	}

	// Service modal handlers
	function handleShowServiceMonitor(service) {
		selectedService = service;
		showServiceMonitor = true;
	}

	function handleShowServiceLogs(service) {
		selectedService = service;
		showServiceLogs = true;
	}

	function handleShowServiceSettings(service) {
		selectedService = service;
		showServiceSettings = true;
	}

	async function handleServiceUpdated(updatedData) {
		// Update the service in the services array
		const serviceIndex = services.findIndex((s) => s.id === selectedService.id);
		if (serviceIndex !== -1) {
			services[serviceIndex] = { ...services[serviceIndex], ...updatedData };
			services = services; // Trigger reactivity
		}
		showNotification('服务设置已更新', 'success');
	}

	function handleServiceTokenRegenerated(newToken) {
		showNotification('访问令牌已重新生成', 'success');
	}

	// Image related event handlers
	function handleImageViewDetail(event) {
		selectedImage = event.detail.image;
		showImageDetailModal = true;
	}

	function handleImageCreateService(event) {
		selectedImage = event.detail.image;
		showServiceFromImageModal = true;
	}

	function handleImageServiceCreated(event) {
		showServiceFromImageModal = false;
		showNotification(`服务 ${event.detail.service.service_name} 创建成功`, 'success');
		// 重新加载服务列表
		loadServices();
	}

	function handleImageDeleted(event) {
		showNotification(`镜像已删除`, 'success');
		// The ImageList component will handle reloading its own data
	}

	// 获取文件夹名称的辅助函数
	function getFolderName(file) {
		const relativePath = file?.webkitRelativePath;
		return relativePath ? relativePath.split('/')[0] : '文件夹';
	}

	// Classification management functions
	async function loadClassifications() {
		try {
			loadingClassifications = true;
			const response = await api.getClassificationTree();
			classifications = response;
		} catch (err) {
			console.error('Failed to load classifications:', err);
		} finally {
			loadingClassifications = false;
		}
	}

	async function loadTaskClassifications() {
		try {
			loadingTaskClassifications = true;
			const response = await fetch('/api/task-classifications/')
				.then((res) => res.json())
				.catch(() => ({ task_classifications: [] }));
			taskClassifications = response.task_classifications || [];
		} catch (err) {
			console.error('Failed to load task classifications:', err);
		} finally {
			loadingTaskClassifications = false;
		}
	}

	function handleClassificationSelect(event) {
		selectedClassificationId = event.detail.id;
	}

	function toggleTaskClassification(taskId: number) {
		const index = selectedTaskClassificationIds.indexOf(taskId);
		if (index > -1) {
			selectedTaskClassificationIds.splice(index, 1);
		} else {
			selectedTaskClassificationIds.push(taskId);
		}
		selectedTaskClassificationIds = selectedTaskClassificationIds;
	}

	async function saveClassifications() {
		try {
			savingClassifications = true;
			classificationError = null;
			classificationSuccessMessage = null;

			// 保存sphere分类
			if (selectedClassificationId) {
				// 先清除现有分类
				await api.repositories.removeClassifications(username, repoName);
				// 添加新分类
				await api.repositories.addClassification(username, repoName, selectedClassificationId);
			}

			// 保存任务分类
			// 获取当前的任务分类
			const currentTaskIds = repository.task_classifications_data
				? repository.task_classifications_data.map((tc) => tc.id)
				: [];

			// 找出需要删除的
			const toRemove = currentTaskIds.filter((id) => !selectedTaskClassificationIds.includes(id));
			// 找出需要添加的
			const toAdd = selectedTaskClassificationIds.filter((id) => !currentTaskIds.includes(id));

			// 删除不需要的任务分类
			for (const taskId of toRemove) {
				await api.repositories.removeTaskClassification(username, repoName, taskId);
			}

			// 添加新的任务分类
			for (const taskId of toAdd) {
				await api.repositories.addTaskClassification(username, repoName, taskId);
			}

			classificationSuccessMessage = '分类已成功更新';

			// 重新加载仓库数据
			await loadRepositoryData();

			// 更新原始值
			originalClassificationId = selectedClassificationId;
			originalTaskClassificationIds = [...selectedTaskClassificationIds];

			// 3秒后清除成功消息
			setTimeout(() => {
				classificationSuccessMessage = null;
			}, 3000);
		} catch (err) {
			classificationError = err.message || '保存失败';
		} finally {
			savingClassifications = false;
		}
	}

	// Load classifications when settings tab is opened and save original values
	$: if (activeTab === 'settings' && isRepoOwner && repository) {
		if (classifications.length === 0) {
			loadClassifications();
		}
		if (taskClassifications.length === 0) {
			loadTaskClassifications();
		}

		// 保存原始值（只在第一次加载时）
		if (originalDescription === '' && repository.description !== undefined) {
			originalDescription = repository.description || '';
			originalVisibility = repository.visibility || '';
			originalLicense = repository.license || '';
			originalBaseModel = repository.base_model || '';
			originalTags = repository.tags ? [...repository.tags] : [];
		}

		// 设置当前的任务分类
		if (repository.task_classifications_data) {
			const currentTaskIds = repository.task_classifications_data.map((tc) => tc.id);
			if (JSON.stringify(selectedTaskClassificationIds) !== JSON.stringify(currentTaskIds)) {
				selectedTaskClassificationIds = currentTaskIds;
				originalTaskClassificationIds = [...currentTaskIds];
			}
		}

		// 设置当前的sphere分类（从classification_path获取）
		// TODO: 需要实现从classification_path到classification_id的映射
	}
</script>

<svelte:head>
	<title>{username}/{repoName} - GeoML Hub</title>
	<meta name="description" content={repository?.description || `${username}/${repoName} 仓库`} />
</svelte:head>

<div class="bg-gray-50 dark:bg-gray-900">
	{#if loading}
		<div class="flex items-center justify-center py-12">
			<Loading size="lg" />
		</div>
	{:else if error}
		<div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
			<div
				class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6"
			>
				<div class="flex">
					<div class="flex-shrink-0">
						<svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
							<path
								fill-rule="evenodd"
								d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
								clip-rule="evenodd"
							/>
						</svg>
					</div>
					<div class="ml-3">
						<h3 class="text-sm font-medium text-red-800 dark:text-red-200">加载失败</h3>
						<p class="mt-1 text-sm text-red-700 dark:text-red-300">
							{error}
						</p>
					</div>
				</div>
			</div>
		</div>
	{:else if repository}
		<div class="flex flex-col min-h-full">
			<!-- Header -->
			<div
				class="bg-linear-to-t from-blue-500/8 dark:from-blue-500/20 to-white to-70% dark:to-gray-950 border-b border-gray-100 dark:border-gray-800 pt-6 sm:pt-9"
			>
				<div class="container">
					<!-- Repository Info -->
					<div>
						<div class="flex items-start justify-between">
							<div class="flex-1 min-w-0">
								<!-- Repository title with stats -->
								<div class="flex items-center justify-between mb-2">
									<div class="flex items-center">
										<div class="flex items-center">
											<UserAvatar user={repository.owner} size="sm" />
											<a
												href="/{repository.owner?.username}"
												class="text-gray-600 text-xl font-semibold font-mono ml-3 truncate dark:text-blue-300 hover:text-blue-700 dark:hover:text-blue-200"
											>
												{repository.owner?.username}
											</a>
											<span
												class="text-black text-xl font-mono font-semibold truncate dark:text-gray-400"
												>/</span
											>
											<h1
												class="text-xl font-mono truncate font-bold text-gray-900 dark:text-white"
											>
												{repository.name}
											</h1>
											{#if repository.visibility === 'private'}
												<span
													class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
												>
													私有
												</span>
											{/if}
										</div>

										<!-- Stats next to repository name with proper spacing -->
										<div
											class="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400 ml-6"
										>
											<div class="flex items-center space-x-1">
												<Star class="h-4 w-4" />
												<span>{repository.stars_count}</span>
											</div>
											<div class="flex items-center space-x-1">
												<Download class="h-4 w-4" />
												<span>{repository.downloads_count}</span>
											</div>
											<div class="flex items-center space-x-1">
												<Eye class="h-4 w-4" />
												<span>{repository.views_count}</span>
											</div>
											{#if repository.total_size > 0}
												<div class="flex items-center space-x-1">
													<span>{formatFileSize(repository.total_size)}</span>
												</div>
											{/if}
										</div>
									</div>

									<!-- Created time on the right -->
									<div class="flex items-center space-x-1 text-xs text-gray-500 dark:text-gray-400">
										<Calendar class="h-3 w-3" />
										<span>
											创建于 {formatDistanceToNow(new Date(repository.created_at), {
												addSuffix: true,
												locale: zhCN
											})}
										</span>
									</div>
								</div>

								<!-- Description -->
								{#if repository.description}
									<p class="text-gray-700 dark:text-gray-300 mb-4">
										{repository.description}
									</p>
								{/if}

								<!-- Tags Row (Apple-style) -->
								<div class="flex flex-wrap gap-2 mb-3">
									<!-- Task Classifications (紫色系，放在最前面) -->
									{#if repository.task_classifications_data && repository.task_classifications_data.length > 0}
										{#each repository.task_classifications_data as task}
											<span
												class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-purple-50 text-purple-700 hover:bg-purple-100 transition-colors duration-200 dark:bg-purple-950 dark:text-purple-300 dark:hover:bg-purple-900 shadow-sm border border-purple-100 dark:border-purple-900"
												title={task.description || task.name}
											>
												<!-- {#if task.icon}
													<span class="text-purple-600 dark:text-purple-400">{task.icon}</span>
												{/if} -->
												<span>{task.name}</span>
											</span>
										{/each}
									{/if}

									<!-- Regular Tags -->
									{#if repository.tags && repository.tags.length > 0}
										{#each repository.tags as tag}
											<span
												class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors duration-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 shadow-sm"
											>
												{tag}
											</span>
										{/each}
									{/if}

									<!-- License Badge -->
									{#if repository.license}
										<span
											class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-green-50 hover:bg-green-100 transition-colors duration-200 dark:bg-green-950 dark:hover:bg-green-900 shadow-sm border border-green-100 dark:border-green-900"
										>
											<svg
												class="w-3 h-3 text-gray-500 dark:text-gray-400"
												fill="currentColor"
												viewBox="0 0 16 16"
											>
												<path
													d="M8.75.75V2h.985c.304 0 .603.08.867.231l1.29.736c.038.022.08.033.124.033h2.234a.75.75 0 0 1 0 1.5h-.427l2.111 4.692a.75.75 0 0 1-.154.838l-.53-.53.529.531-.001.002-.002.002-.006.006-.006.005-.01.01-.045.04c-.21.176-.441.327-.686.45C14.556 10.78 13.88 11 13 11a4.498 4.498 0 0 1-2.023-.454 3.544 3.544 0 0 1-.686-.45l-.045-.04-.016-.015-.006-.006-.004-.004v-.001a.75.75 0 0 1-.154-.838L12.178 4.5h-.162c-.305 0-.604-.079-.868-.231l-1.29-.736a.245.245 0 0 0-.124-.033H8.75V13h2.5a.75.75 0 0 1 0 1.5h-6.5a.75.75 0 0 1 0-1.5h2.5V3.5h-.984a.245.245 0 0 0-.124.033l-1.289.737c-.265.15-.564.23-.869.23h-.162l2.112 4.692a.75.75 0 0 1-.154.838l-.53-.53.529.531-.001.002-.002.002-.006.006-.016.015-.045.04c-.21.176-.441.327-.686.45C4.556 10.78 3.88 11 3 11a4.498 4.498 0 0 1-2.023-.454 3.544 3.544 0 0 1-.686-.45l-.045-.04-.016-.015-.006-.006-.004-.004v-.001a.75.75 0 0 1-.154-.838L2.178 4.5H1.75a.75.75 0 0 1 0-1.5h2.234a.249.249 0 0 0 .125-.033l1.288-.737c.265-.15.564-.23.869-.23h.984V.75a.75.75 0 0 1 1.5 0Zm2.945 8.477c.285.135.718.273 1.305.273s1.02-.138 1.305-.273L13 6.327Zm-10 0c.285.135.718.273 1.305.273s1.02-.138 1.305-.273L3 6.327Z"
												/>
											</svg>
											<span class="text-gray-500 dark:text-gray-400">License:</span>
											<span class="text-green-700 dark:text-green-300">{repository.license}</span>
										</span>
									{/if}
								</div>

								<!-- Classification Path (Apple-style) -->
								{#if repository.classification_path && repository.classification_path.length > 0}
									<div class="flex items-center flex-wrap mb-3">
										{#each repository.classification_path as classification, index}
											<span
												class="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100 hover:bg-blue-100 transition-all duration-200 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-900 dark:hover:bg-blue-900 shadow-sm"
											>
												{classification}
											</span>
											{#if index < repository.classification_path.length - 1}
												<ChevronRight
													class="h-4 w-4 font-medium text-gray-900 dark:text-gray-500 mx-0.5"
												/>
											{/if}
										{/each}
									</div>
								{/if}
							</div>

							<!-- Actions -->
							<div class="flex items-center space-x-2 ml-6">
								{#if $currentUser && repository.owner?.username !== $currentUser.username}
									<SocialButton
										type="star"
										active={repository.is_starred}
										count={repository.stars_count}
										on:click={handleStar}
									/>
								{/if}
							</div>
						</div>
					</div>

					<!-- Navigation Tabs -->
					<div class="border-b border-gray-200 dark:border-gray-700">
						<nav class="flex space-x-8" aria-label="Tabs">
							<button
								class="py-2 px-1 border-b-2 font-medium text-sm {activeTab === 'model-card'
									? 'border-blue-500 text-blue-600 dark:text-blue-400'
									: 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
								on:click={() => (activeTab = 'model-card')}
							>
								<FileText class="h-4 w-4 inline mr-1" />
								Model Card
							</button>
							<button
								class="py-2 px-1 border-b-2 font-medium text-sm {activeTab === 'files'
									? 'border-blue-500 text-blue-600 dark:text-blue-400'
									: 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
								on:click={() => (activeTab = 'files')}
							>
								<FileText class="h-4 w-4 inline mr-1" />
								Files ({files.length})
							</button>
							<button
								class="py-2 px-1 border-b-2 font-medium text-sm {activeTab === 'services'
									? 'border-blue-500 text-blue-600 dark:text-blue-400'
									: 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
								on:click={() => (activeTab = 'services')}
							>
								<svg
									class="h-4 w-4 inline mr-1"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M13 10V3L4 14h7v7l9-11h-7z"
									/>
								</svg>
								Services ({services.length})
							</button>
							<button
								class="py-2 px-1 border-b-2 font-medium text-sm {activeTab === 'images'
									? 'border-blue-500 text-blue-600 dark:text-blue-400'
									: 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
								on:click={() => (activeTab = 'images')}
							>
								<svg
									class="h-4 w-4 inline mr-1"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2h4a1 1 0 011 1v1a1 1 0 01-1 1v9a2 2 0 01-2 2H5a2 2 0 01-2-2V7a1 1 0 01-1-1V5a1 1 0 011-1h4z"
									/>
								</svg>
								Images
							</button>
							{#if $currentUser && repository.owner?.username === $currentUser.username}
								<button
									class="py-2 px-1 border-b-2 font-medium text-sm {activeTab === 'settings'
										? 'border-blue-500 text-blue-600 dark:text-blue-400'
										: 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
									on:click={() => (activeTab = 'settings')}
								>
									<Settings class="h-4 w-4 inline mr-1" />
									Settings
								</button>
							{/if}
						</nav>
					</div>
				</div>
			</div>

			<!-- Content -->
			<div class="flex-1 bg-white dark:bg-gray-950">
				<div class="container">
					<div>
						{#if activeTab === 'model-card'}
							<div class="flex gap-6">
								<!-- Model Card Content (6/10) -->
								<div class="flex-[6.5] min-w-0">
									{#if readmeHtml}
										<div class="prose prose-gray dark:prose-invert max-w-none overflow-hidden">
											<div class="model-card-content">
												{@html readmeHtml}
											</div>
										</div>
									{:else}
										<div class="text-center py-12">
											<FileText class="h-12 w-12 text-gray-400 mx-auto mb-4" />
											<p class="text-gray-500 dark:text-gray-400">该仓库还没有 README 文件</p>
											{#if $currentUser && repository.owner?.username === $currentUser.username}
												<p class="text-sm text-gray-400 mt-2">README 文件会自动显示为 Model Card</p>
											{/if}
										</div>
									{/if}
								</div>

								<!-- Sidebar (4/10) -->
								<div
									class="flex-[3.5] py-6 border-l border-gray-200 dark:border-gray-700 pl-6 space-y-6"
								>
									<!-- Monthly Statistics -->
									<div
										class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6"
									>
										<!-- Downloads -->
										<div class="mb-6">
											<div class="flex items-center justify-between mb-2">
												<span class="text-sm text-gray-600 dark:text-gray-400"
													>Downloads last month</span
												>
											</div>
											<div class="flex items-end space-x-4">
												<div class="text-2xl font-bold text-gray-900 dark:text-white">3,383</div>
												<div class="flex-1 h-12 flex items-end">
													<!-- Smooth line chart representation -->
													<svg class="w-full h-full" viewBox="0 0 200 48" fill="none">
														<!-- Fill area under the curve -->
														<path
															d="M5 38 C15 42, 25 42, 35 30 C45 18, 55 25, 65 20 C75 15, 85 22, 95 12 C105 2, 115 8, 125 15 C135 22, 145 18, 155 25 C165 32, 175 20, 185 15 C190 12, 195 10, 200 8 L200 48 L5 48 Z"
															fill="url(#downloadFillGradient)"
														/>
														<!-- Line stroke -->
														<path
															d="M5 38 C15 42, 25 42, 35 30 C45 18, 55 25, 65 20 C75 15, 85 22, 95 12 C105 2, 115 8, 125 15 C135 22, 145 18, 155 25 C165 32, 175 20, 185 15 C190 12, 195 10, 200 8"
															stroke="#3b82f6"
															stroke-width="3"
															stroke-linecap="round"
															stroke-linejoin="round"
															fill="none"
														/>
														<defs>
															<linearGradient
																id="downloadFillGradient"
																x1="0%"
																y1="0%"
																x2="0%"
																y2="100%"
															>
																<stop offset="0%" style="stop-color:#3b82f6;stop-opacity:0.3" />
																<stop offset="100%" style="stop-color:#3b82f6;stop-opacity:0.05" />
															</linearGradient>
														</defs>
													</svg>
												</div>
											</div>
										</div>

										<!-- Views -->
										<div>
											<div class="flex items-center justify-between mb-2">
												<span class="text-sm text-gray-600 dark:text-gray-400"
													>Views last month</span
												>
											</div>
											<div class="flex items-end space-x-4">
												<div class="text-2xl font-bold text-gray-900 dark:text-white">
													{repository.views_count || 0}
												</div>
												<div class="flex-1 h-12 flex items-end">
													<!-- Smooth line chart representation -->
													<svg class="w-full h-full" viewBox="0 0 200 48" fill="none">
														<!-- Fill area under the curve -->
														<path
															d="M5 32 C15 35, 25 35, 35 22 C45 9, 55 16, 65 25 C75 34, 85 28, 95 22 C105 16, 115 25, 125 30 C135 35, 145 32, 155 25 C165 18, 175 22, 185 10 C190 6, 195 8, 200 12 L200 48 L5 48 Z"
															fill="url(#viewsFillGradient)"
														/>
														<!-- Line stroke -->
														<path
															d="M5 32 C15 35, 25 35, 35 22 C45 9, 55 16, 65 25 C75 34, 85 28, 95 22 C105 16, 115 25, 125 30 C135 35, 145 32, 155 25 C165 18, 175 22, 185 10 C190 6, 195 8, 200 12"
															stroke="#3b82f6"
															stroke-width="3"
															stroke-linecap="round"
															stroke-linejoin="round"
															fill="none"
														/>
														<defs>
															<linearGradient
																id="viewsFillGradient"
																x1="0%"
																y1="0%"
																x2="0%"
																y2="100%"
															>
																<stop offset="0%" style="stop-color:#3b82f6;stop-opacity:0.3" />
																<stop offset="100%" style="stop-color:#3b82f6;stop-opacity:0.05" />
															</linearGradient>
														</defs>
													</svg>
												</div>
											</div>
										</div>
									</div>

									<!-- Model Services Card - Compact view for sidebar -->
									<div
										class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6"
									>
										<div class="flex items-center justify-between mb-4">
											<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
												Model Services
											</h3>
											<button
												class="px-3 py-1.5 bg-blue-100 hover:bg-blue-200 dark:bg-blue-900 dark:hover:bg-blue-800 text-blue-700 dark:text-blue-300 text-sm font-medium rounded-md transition-colors"
												on:click={() => (activeTab = 'services')}
											>
												View All ({services.length})
											</button>
										</div>

										{#if services.length === 0}
											<div class="text-center py-8">
												<div
													class="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center mx-auto mb-3"
												>
													<svg
														class="w-6 h-6 text-gray-400"
														fill="none"
														stroke="currentColor"
														viewBox="0 0 24 24"
													>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															stroke-width="2"
															d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
														/>
													</svg>
												</div>
												<p class="text-sm text-gray-500 dark:text-gray-400">
													No model services yet
												</p>
												{#if isRepoOwner}
													<p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
														Create a service to deploy your model
													</p>
													<button
														class="mt-3 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md transition-colors"
														on:click={() => (showCreateServiceModal = true)}
													>
														Create Service
													</button>
												{/if}
											</div>
										{:else}
											<!-- Show first 3 running services -->
											<div class="space-y-3">
												{#each services
													.filter((service) => service.status === 'running')
													.slice(0, 3) as service, index}
													<div
														class="relative overflow-hidden rounded-xl p-2 bg-gradient-to-br {getServiceGradient(
															index
														)} shadow-sm hover:shadow-md transition-all duration-300 cursor-pointer transform hover:scale-[1.02]"
														on:click={() => handleServiceClick(service)}
													>
														<!-- Three-row flex layout -->
														<div class="relative flex flex-col h-full">
															<!-- Dark overlay for better text contrast -->

															<div class="relative z-10 flex flex-col justify-between h-full">
																<!-- Second row: Model information -->
																<div class="flex flex-col px-2 rounded-lg backdrop-blur-sm">
																	<div class="flex items-center space-x-3">
																		<div
																			class="flex-shrink-0 w-10 h-10 bg-white/90 backdrop-blur-sm rounded-lg shadow-sm flex items-center justify-center"
																		>
																			<svg
																				class="w-5 h-5 text-gray-700"
																				fill="none"
																				stroke="currentColor"
																				viewBox="0 0 24 24"
																			>
																				<path
																					stroke-linecap="round"
																					stroke-linejoin="round"
																					stroke-width="2"
																					d="M13 10V3L4 14h7v7l9-11h-7z"
																				/>
																			</svg>
																		</div>
																		<div class="flex-1">
																			<h4 class="text-lg font-bold text-white drop-shadow-md">
																				{service.service_name}
																			</h4>
																			<!-- Used model -->
																			<div class="flex items-center space-x-2">
																				<span class="text-white/80 text-sm font-medium">Model:</span
																				>
																				<div class="flex items-center space-x-2">
																					<span
																						class="text-white font-semibold text-sm drop-shadow-sm"
																					>
																						{service.image
																							? `${service.image.original_name}:${service.image.original_tag}`
																							: service.model_id || 'Unknown'}
																					</span>
																				</div>
																			</div>
																		</div>
																	</div>
																	<!-- Model description -->
																	<div class="flex items-start space-x-2">
																		<span class="text-white/95 text-sm drop-shadow-sm">
																			{service.description || 'Machine learning model service'}
																		</span>
																	</div>
																</div>
															</div>
														</div>
													</div>
												{/each}

												{#if services.filter((service) => service.status === 'running').length > 3}
													<div class="text-center pt-2">
														<button
															class="text-sm text-blue-600 dark:text-blue-400 hover:underline"
															on:click={() => (activeTab = 'services')}
														>
															View {services.filter((service) => service.status === 'running')
																.length - 3} more running services
														</button>
													</div>
												{/if}
											</div>
										{/if}
									</div>
								</div>
							</div>
						{:else if activeTab === 'files'}
							<!-- Upload Section -->
							{#if $currentUser && repository.owner?.username === $currentUser.username}
								<div class="mb-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
									<!-- 拖拽上传条 -->
									<div
										class="relative border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer group {isDragOver
											? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20'
											: 'border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 hover:border-gray-400 dark:hover:border-gray-500'}"
										on:click={() => document.getElementById('upload-input').click()}
										on:dragenter={handleDragEnter}
										on:dragleave={handleDragLeave}
										on:dragover={handleDragOver}
										on:drop={handleDrop}
									>
										<div class="flex flex-col items-center">
											<Upload class="h-8 w-8 text-gray-400 group-hover:text-gray-500 mb-2" />
											<p
												class="text-sm text-gray-600 dark:text-gray-300 group-hover:text-gray-700 dark:group-hover:text-gray-200"
											>
												{isDragOver ? '释放文件到此处' : '拖拽文件到此处或点击选择文件'}
											</p>
											<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
												支持文件和文件夹上传，单个文件最大 10GB
											</p>
										</div>

										<!-- 隐藏的文件输入 - 支持文件和文件夹 -->
										<input
											id="upload-input"
											type="file"
											multiple
											class="hidden"
											on:change={handleFileInputChange}
										/>
									</div>

									<!-- 上传进度显示 -->
									{#if uploadingFiles.size > 0 || Object.keys(uploadProgress).length > 0}
										<div class="mt-3 space-y-2">
											<h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">上传进度</h4>

											{#each Object.entries(uploadProgress) as [fileName, progress]}
												<div
													class="bg-white dark:bg-gray-700 rounded-lg p-3 border border-gray-200 dark:border-gray-600"
												>
													<div class="flex items-center justify-between mb-2">
														<span
															class="text-sm font-medium text-gray-700 dark:text-gray-300 truncate"
															>{fileName}</span
														>
														<span class="text-sm text-gray-500 dark:text-gray-400"
															>{progress.percentage}%</span
														>
													</div>
													<div class="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
														<div
															class="bg-blue-600 h-2 rounded-full transition-all duration-300"
															style="width: {progress.percentage}%"
														/>
													</div>
													<div
														class="flex items-center justify-between mt-1 text-xs text-gray-500 dark:text-gray-400"
													>
														<span
															>{formatFileSize(progress.loaded)} / {formatFileSize(
																progress.total
															)}</span
														>
														{#if progress.status === 'error'}
															<span class="text-red-500">上传失败</span>
														{:else if progress.status === 'completed'}
															<span class="text-green-500">上传完成</span>
														{:else if progress.status === 'uploading'}
															<span class="text-blue-500">上传中...</span>
														{/if}
													</div>
												</div>
											{/each}

											<!-- 显示传统上传状态 -->
											{#if uploadingFiles.size > 0}
												<div class="text-sm text-gray-600 dark:text-gray-400">
													正在上传: {Array.from(uploadingFiles).join(', ')}
												</div>
											{/if}
										</div>
									{/if}
								</div>
							{/if}

							{#if fileTree.length > 0}
								<div class="space-y-1">
									{#each fileTree as item}
										{#if item.type === 'folder'}
											<!-- 文件夹 -->
											<div class="space-y-1">
												<div
													class="flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg cursor-pointer"
													on:click={() => toggleFolder(item.path)}
												>
													<div class="flex items-center space-x-3">
														{#if expandedFolders.has(item.path)}
															<ChevronDown class="h-4 w-4 text-gray-400" />
														{:else}
															<ChevronRight class="h-4 w-4 text-gray-400" />
														{/if}
														<FolderOpen class="h-5 w-5 text-blue-500" />
														<div>
															<div class="text-sm font-medium text-gray-900 dark:text-white">
																{item.name}
															</div>
															<div class="text-xs text-gray-500 dark:text-gray-400">
																{item.files.length} 个文件
															</div>
														</div>
													</div>
												</div>

												<!-- 展开的文件列表 -->
												{#if expandedFolders.has(item.path)}
													<div class="ml-6 space-y-1">
														{#each item.files as file}
															<div
																class="flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg"
															>
																<div class="flex flex-[4.5] items-center space-x-3">
																	<FileText class="h-5 w-5 text-gray-400" />
																	<div class="flex items-center space-x-3">
																		<a
																			href="/{username}/{repoName}/blob/{file.path}"
																			class="text-sm font-medium text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400"
																		>
																			{file.name}
																		</a>
																	</div>
																</div>
																<div class="flex flex-[1.5] items-center justify-end space-x-2">
																	<span class="text-xs text-gray-500 dark:text-gray-400">
																		{formatFileSize(file.data.file_size)}
																	</span>
																	<span class="text-xs text-gray-500 dark:text-gray-400">
																		{formatDistanceToNow(new Date(file.data.created_at), {
																			addSuffix: true,
																			locale: zhCN
																		})}
																	</span>
																</div>
																<div class="flex flex-[4] items-center justify-end space-x-2">
																	<a
																		href="/{username}/{repoName}/blob/{file.path}"
																		class="text-blue-600 dark:text-blue-400 hover:underline text-sm"
																	>
																		查看
																	</a>
																	{#if $currentUser && repository.owner?.username === $currentUser.username}
																		<a
																			href="/{username}/{repoName}/edit/{file.path}"
																			class="text-green-600 dark:text-green-400 hover:underline text-sm"
																		>
																			编辑
																		</a>
																	{/if}
																	<button
																		class="text-gray-600 dark:text-gray-400 hover:underline text-sm disabled:opacity-50 disabled:cursor-not-allowed"
																		on:click={() => handleDownload(file.data)}
																		disabled={downloadingFiles.has(file.data.id)}
																	>
																		{downloadingFiles.has(file.data.id) ? '下载中...' : '下载'}
																	</button>
																</div>
															</div>
														{/each}
													</div>
												{/if}
											</div>
										{:else}
											<!-- 根目录文件 -->
											<div
												class="flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg"
											>
												<div class="flex flex-[4] items-center space-x-3">
													<FileText class="h-5 w-5 text-gray-400" />
													<div class="flex items-center space-x-3">
														<a
															href="/{username}/{repoName}/blob/{item.path}"
															class="text-sm font-medium text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400"
														>
															{item.name}
														</a>
													</div>
												</div>
												<div class="flex flex-[1.5] items-center justify-end space-x-2">
													<span class="text-xs text-gray-500 dark:text-gray-400">
														{formatFileSize(item.data.file_size)}
													</span>
													<span class="text-xs text-gray-500 dark:text-gray-400">
														{formatDistanceToNow(new Date(item.data.created_at), {
															addSuffix: true,
															locale: zhCN
														})}
													</span>
												</div>
												<div class="flex flex-[4.5] items-center justify-end space-x-2">
													<a
														href="/{username}/{repoName}/blob/{item.path}"
														class="text-blue-600 dark:text-blue-400 hover:underline text-sm"
													>
														查看
													</a>
													{#if $currentUser && repository.owner?.username === $currentUser.username}
														<a
															href="/{username}/{repoName}/edit/{item.path}"
															class="text-green-600 dark:text-green-400 hover:underline text-sm"
														>
															编辑
														</a>
													{/if}
													<button
														class="text-gray-600 dark:text-gray-400 hover:underline text-sm disabled:opacity-50 disabled:cursor-not-allowed"
														on:click={() => handleDownload(item.data)}
														disabled={downloadingFiles.has(item.data.id)}
													>
														{downloadingFiles.has(item.data.id) ? '下载中...' : '下载'}
													</button>
												</div>
											</div>
										{/if}
									{/each}
								</div>
							{:else}
								<div class="text-center py-12">
									<FileText class="h-12 w-12 text-gray-400 mx-auto mb-4" />
									<p class="text-gray-500 dark:text-gray-400">该仓库还没有文件</p>
									{#if $currentUser && repository.owner?.username === $currentUser.username}
										<button
											class="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
											on:click={handleUploadClick}
										>
											<Upload class="h-4 w-4 mr-2" />
											上传文件
										</button>
										<input
											type="file"
											bind:this={fileInput}
											on:change={handleFileUpload}
											multiple
											class="hidden"
										/>
									{/if}
								</div>
							{/if}
						{:else if activeTab === 'services'}
							<!-- Services Tab -->
							<div class="py-6">
								<ServiceList
									{services}
									{loading}
									isOwner={isRepoOwner}
									on:createService={() => (showCreateServiceModal = true)}
									on:start={(e) => handleStartService(e.detail)}
									on:stop={(e) => handleStopService(e.detail)}
									on:restart={(e) => handleRestartService(e.detail)}
									on:delete={(e) => handleDeleteService(e.detail)}
									on:viewLogs={(e) => handleShowServiceLogs(e.detail)}
									on:settings={(e) => handleShowServiceSettings(e.detail)}
									on:monitor={(e) => handleShowServiceMonitor(e.detail)}
									on:batchStart={(e) => handleBatchStartServices(e.detail)}
									on:batchStop={(e) => handleBatchStopServices(e.detail)}
									on:batchDelete={(e) => handleBatchDeleteServices(e.detail)}
								/>
							</div>
						{:else if activeTab === 'images'}
							<!-- Images Tab -->
							<div class="py-6">
								<ImageList
									repositoryId={repository.id}
									canManage={isRepoOwner}
									on:viewDetail={handleImageViewDetail}
									on:createService={handleImageCreateService}
									on:delete={handleImageDeleted}
								/>
							</div>
						{:else if activeTab === 'settings'}
							{#if $currentUser && repository.owner?.username === $currentUser.username}
								<!-- Repository Settings - HuggingFace Style -->
								<section class="pt-8 col-span-12 space-y-6 pb-16">
									<!-- Success/Error Messages -->
									{#if settingsSuccessMessage || classificationSuccessMessage}
										<div
											class="mb-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-xl p-4 animate-in fade-in duration-200"
										>
											<p class="text-sm font-medium text-green-800 dark:text-green-200">
												{settingsSuccessMessage || classificationSuccessMessage}
											</p>
										</div>
									{/if}

									{#if settingsError || classificationError}
										<div
											class="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-xl p-4"
										>
											<p class="text-sm font-medium text-red-800 dark:text-red-200">
												{settingsError || classificationError}
											</p>
										</div>
									{/if}

									<!-- Settings Container -->
									<div
										class="relative divide-y divide-gray-200 dark:divide-gray-700 overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700"
									>
										<!-- Repository Name Section -->
										<section
											class="group relative items-start justify-between px-6 py-8 dark:bg-gray-800/30 lg:flex"
										>
											<div class="flex-1">
												<div class="mb-4 flex items-start text-lg font-semibold">
													<div class="w-7 flex-none pt-1.5 sm:w-9">
														<svg
															class="text-gray-400 text-base group-hover:text-gray-500 dark:group-hover:text-gray-300"
															xmlns="http://www.w3.org/2000/svg"
															viewBox="0 0 12 12"
															fill="currentColor"
															width="1em"
															height="1em"
														>
															<path
																d="M1.5 3.75h9a.75.75 0 0 1 0 1.5h-9a.75.75 0 0 1 0-1.5zm0 3h6a.75.75 0 0 1 0 1.5h-6a.75.75 0 0 1 0-1.5z"
															/>
														</svg>
													</div>
													<h2 class="flex items-center gap-2 text-gray-900 dark:text-white">
														仓库名称
													</h2>
												</div>
												<div
													class="max-w-3xl xl:max-w-4xl pl-7 sm:pl-9 text-gray-600 dark:text-gray-400"
												>
													<p class="mb-3">
														当前仓库名称：
														<strong
															class="mx-0.5 rounded-lg border px-1.5 text-gray-800 dark:text-gray-200 shadow-sm dark:border-gray-600 dark:bg-gray-700"
															>{repository.name}</strong
														>
													</p>
													<p class="text-sm">
														重命名仓库后，所有指向旧URL的链接将自动重定向到新位置，包括git操作。
													</p>
												</div>
											</div>
										</section>

										<!-- Visibility Section -->
										<section
											class="group relative items-start justify-between px-6 py-8 dark:bg-gray-800/30 lg:flex"
										>
											<div class="flex-1">
												<div class="mb-4 flex items-start text-lg font-semibold">
													<div class="w-7 flex-none pt-1.5 sm:w-9">
														<svg
															class="text-gray-400 text-base group-hover:text-gray-500 dark:group-hover:text-gray-300"
															xmlns="http://www.w3.org/2000/svg"
															viewBox="0 0 12 12"
															fill="currentColor"
															width="1em"
															height="1em"
														>
															<path
																d="M6 9.75828C4.86056 9.75828 3.81948 9.45144 2.87678 8.83776C1.93407 8.22373 1.22089 7.39474 0.737243 6.35077C0.712651 6.30901 0.696256 6.25673 0.688059 6.19393C0.679861 6.13146 0.675763 6.06681 0.675763 6C0.675763 5.93319 0.679861 5.86838 0.688059 5.80557C0.696256 5.7431 0.712651 5.69098 0.737243 5.64923C1.22089 4.60526 1.93407 3.77643 2.87678 3.16274C3.81948 2.54872 4.86056 2.24171 6 2.24171C7.13944 2.24171 8.18052 2.54872 9.12323 3.16274C10.0659 3.77643 10.7791 4.60526 11.2628 5.64923C11.2873 5.69098 11.3037 5.7431 11.3119 5.80557C11.3201 5.86838 11.3242 5.93319 11.3242 6C11.3242 6.06681 11.3201 6.13146 11.3119 6.19393C11.3037 6.25673 11.2873 6.30901 11.2628 6.35077C10.7791 7.39474 10.0659 8.22373 9.12323 8.83776C8.18052 9.45144 7.13944 9.75828 6 9.75828ZM6 8.75608C6.92631 8.75608 7.77688 8.50753 8.5517 8.01043C9.32619 7.51367 9.91838 6.84353 10.3282 6C9.91838 5.15647 9.32619 4.48616 8.5517 3.98907C7.77688 3.4923 6.92631 3.24392 6 3.24392C5.07369 3.24392 4.22312 3.4923 3.4483 3.98907C2.67381 4.48616 2.08162 5.15647 1.67175 6C2.08162 6.84353 2.67381 7.51367 3.4483 8.01043C4.22312 8.50753 5.07369 8.75608 6 8.75608Z"
															/>
															<path
																d="M7.80933 5.92992C7.80933 6.51092 7.53544 7.02796 7.10973 7.35894C6.80337 7.59714 6.41838 6.98403 6.00027 6.98403C5.58215 6.98403 5.19716 7.59714 4.8908 7.35894C4.46509 7.02796 4.1912 6.51092 4.1912 5.92992C4.1912 4.9308 5.00115 4.12086 6.00027 4.12086C6.99939 4.12086 7.80933 4.9308 7.80933 5.92992Z"
															/>
														</svg>
													</div>
													<h2 class="flex items-center gap-2 text-gray-900 dark:text-white">
														更改仓库可见性
													</h2>
												</div>
												<div
													class="max-w-3xl xl:max-w-4xl pl-7 sm:pl-9 text-gray-600 dark:text-gray-400"
												>
													<p>
														此仓库当前为
														<strong
															class="mx-0.5 rounded-lg border px-1.5 text-gray-800 dark:text-gray-200 shadow-sm dark:border-gray-600 dark:bg-gray-700"
														>
															{repository.visibility === 'public' ? '公开' : '私有'}
														</strong>。
														{#if repository.visibility === 'public'}
															互联网上的任何人都可以看到此仓库。只有您（个人仓库）或组织成员（组织仓库）可以提交。
														{:else}
															只有您可以看到和访问此仓库。
														{/if}
													</p>
												</div>
											</div>
											<div class="ml-8 mt-4 flex-none sm:ml-9 lg:ml-16 lg:mt-0">
												<button
													type="button"
													class="btn text-sm hover:text-blue-600 dark:hover:text-blue-400"
													on:click={() => {
														repository.visibility =
															repository.visibility === 'public' ? 'private' : 'public';
													}}
												>
													{repository.visibility === 'public' ? '设为私有' : '设为公开'}
												</button>
											</div>
										</section>

										<!-- Delete Repository Section -->
										<section
											class="group relative items-start justify-between px-6 py-8 dark:bg-gray-800/30 lg:flex"
										>
											<div class="flex-1">
												<div class="mb-4 flex items-start text-lg font-semibold">
													<div class="w-7 flex-none pt-1.5 sm:w-9">
														<svg
															class="text-gray-400 text-base group-hover:text-gray-500 dark:group-hover:text-gray-300"
															xmlns="http://www.w3.org/2000/svg"
															viewBox="0 0 32 32"
															fill="currentColor"
															width="1em"
															height="1em"
														>
															<path d="M12 12h2v12h-2z" />
															<path d="M18 12h2v12h-2z" />
															<path
																d="M4 6v2h2v20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8h2V6zm4 22V8h16v20z"
															/>
															<path d="M12 2h8v2h-8z" />
														</svg>
													</div>
													<h2 class="flex items-center gap-2 text-gray-900 dark:text-white">
														删除此仓库
													</h2>
												</div>
												<div
													class="max-w-3xl xl:max-w-4xl pl-7 sm:pl-9 text-gray-600 dark:text-gray-400"
												>
													<p>
														此操作<strong>无法撤销</strong>。这将永久删除
														<strong>{username}/{repository.name}</strong>
														仓库及其所有文件，包括权重、服务、历史记录和数据。
													</p>
													<form
														class="mt-4 flex flex-col gap-y-5"
														on:submit|preventDefault={handleDeleteRepository}
													>
														<label class="text-sm">
															请输入 <strong>{username}/{repository.name}</strong> 以确认删除。
															<input
																autocomplete="off"
																class="form-input mt-2 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm dark:bg-gray-700 dark:text-white"
																type="text"
																required
															/>
														</label>
														<div>
															<button
																class="btn text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 text-sm"
																type="submit"
															>
																我明白了，删除此仓库
															</button>
														</div>
													</form>
												</div>
											</div>
										</section>
									</div>
								</section>
							{:else}
								<div class="text-center py-12">
									<Settings class="h-12 w-12 text-gray-400 mx-auto mb-4" />
									<p class="text-gray-500 dark:text-gray-400">只有仓库所有者才能访问设置</p>
								</div>
							{/if}
						{/if}
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>

<!-- Service Create Modal -->
<ServiceCreateModal
	isOpen={showCreateServiceModal}
	loading={serviceModalLoading}
	progress={serviceCreationProgress}
	{availableImages}
	on:create={handleCreateService}
	on:close={() => (showCreateServiceModal = false)}
/>

<!-- Service Monitor Modal -->
{#if showServiceMonitor && selectedService}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
		<div
			class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto"
		>
			<div
				class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700"
			>
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white">Service Monitor</h3>
				<button
					class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
					on:click={() => (showServiceMonitor = false)}
				>
					<X class="w-5 h-5" />
				</button>
			</div>
			<div class="p-6">
				<ServiceMonitor service={selectedService} />
			</div>
		</div>
	</div>
{/if}

<!-- Service Logs Modal -->
{#if showServiceLogs && selectedService}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
		<div
			class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto"
		>
			<div
				class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700"
			>
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white">Service Logs</h3>
				<button
					class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
					on:click={() => (showServiceLogs = false)}
				>
					<X class="w-5 h-5" />
				</button>
			</div>
			<div class="p-6">
				<ServiceLogs service={selectedService} autoRefresh={true} />
			</div>
		</div>
	</div>
{/if}

<!-- Service Settings Modal -->
{#if showServiceSettings && selectedService}
	<ServiceSettings
		service={selectedService}
		isOpen={showServiceSettings}
		loading={serviceModalLoading}
		on:close={() => (showServiceSettings = false)}
		on:updated={handleServiceUpdated}
		on:tokenRegenerated={handleServiceTokenRegenerated}
		on:delete={handleDeleteService}
	/>
{/if}

<!-- 上传确认弹窗 -->
{#if showUploadConfirm}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4">
			<div class="p-6">
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">确认上传文件</h3>

				<div class="mb-4">
					{#if pendingFilesIsFolder}
						<p class="text-sm text-gray-600 dark:text-gray-300 mb-2">
							将要上传文件夹及其内容（共 {pendingFiles.length} 个文件）：
						</p>

						<div class="bg-gray-50 dark:bg-gray-700 rounded border p-3">
							<div class="flex items-center">
								<FolderOpen class="h-5 w-5 text-blue-600 mr-2" />
								<div>
									<div class="text-sm font-medium text-gray-900 dark:text-white">
										{getFolderName(pendingFiles[0])}
									</div>
									<div class="text-xs text-gray-500 dark:text-gray-400">
										包含 {pendingFiles.length} 个文件
									</div>
								</div>
							</div>
						</div>
					{:else}
						<p class="text-sm text-gray-600 dark:text-gray-300 mb-2">
							将要上传 {pendingFiles.length} 个文件：
						</p>

						<div class="max-h-32 overflow-y-auto bg-gray-50 dark:bg-gray-700 rounded border p-2">
							{#each pendingFiles.slice(0, 5) as file}
								<div class="text-xs text-gray-700 dark:text-gray-300 truncate">
									{file.name} ({formatFileSize(file.size)})
								</div>
							{/each}
							{#if pendingFiles.length > 5}
								<div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
									...还有 {pendingFiles.length - 5} 个文件
								</div>
							{/if}
						</div>
					{/if}
				</div>

				<div class="flex justify-end space-x-3">
					<button
						class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-600 hover:bg-gray-200 dark:hover:bg-gray-500 rounded-md"
						on:click={cancelUpload}
					>
						取消
					</button>
					<button
						class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
						on:click={confirmUpload}
					>
						确认上传
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}

<!-- Image Detail Modal -->
{#if showImageDetailModal && selectedImage}
	<ImageDetailModal
		image={selectedImage}
		canManage={isRepoOwner}
		on:close={() => (showImageDetailModal = false)}
		on:delete={handleImageDeleted}
		on:serviceCreated={handleImageServiceCreated}
	/>
{/if}

<!-- Service From Image Modal -->
{#if showServiceFromImageModal && selectedImage}
	<ServiceFromImageModal
		image={selectedImage}
		owner={username}
		repository={repoName}
		on:created={handleImageServiceCreated}
		on:close={() => (showServiceFromImageModal = false)}
	/>
{/if}

<!-- 确认替换对话框 -->
{#if showConfirmDialog && confirmDialogData}
	<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
		<div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
			<div class="flex items-center mb-4">
				<AlertCircle class="w-6 h-6 text-orange-500 mr-3" />
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white">确认替换文件</h3>
			</div>

			<div class="mb-6">
				<p class="text-gray-600 dark:text-gray-300 mb-3">
					{#if confirmDialogData.conflictData.is_special_file}
						检测到特殊文件冲突。此文件将会替换现有的同名文件，是否继续？
					{:else}
						检测到文件冲突，是否继续上传？
					{/if}
				</p>

				<div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
					<p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">现有文件：</p>
					<ul class="list-disc list-inside text-sm text-gray-600 dark:text-gray-400 mb-3">
						{#each confirmDialogData.conflictData.existing_files as existingFile}
							<li>
								{existingFile.file_path}
								<span class="text-xs text-gray-500">
									({Math.round(existingFile.file_size / 1024)}KB,
									{new Date(existingFile.updated_at).toLocaleString()})
								</span>
							</li>
						{/each}
					</ul>

					<p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">新文件：</p>
					<p class="text-sm text-gray-600 dark:text-gray-400">
						{confirmDialogData.conflictData.file_path}
					</p>
				</div>
			</div>

			<div class="flex justify-end space-x-3">
				<button
					on:click={handleCancelReplace}
					class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
				>
					取消
				</button>
				<button
					on:click={handleConfirmReplace}
					class="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors"
				>
					确认替换
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.prose {
		max-width: none;
	}

	.prose :global(h1) {
		font-size: 1.875rem;
		line-height: 2.25rem;
		font-weight: 700;
		margin-top: 2rem;
		margin-bottom: 1rem;
	}

	.prose :global(h2) {
		font-size: 1.5rem;
		line-height: 2rem;
		font-weight: 600;
		margin-top: 1.5rem;
		margin-bottom: 0.75rem;
	}

	.prose :global(h3) {
		font-size: 1.25rem;
		line-height: 1.75rem;
		font-weight: 600;
		margin-top: 1.25rem;
		margin-bottom: 0.5rem;
	}

	.prose :global(p) {
		margin-bottom: 1rem;
		line-height: 1.75;
	}

	.prose :global(ul) {
		margin-bottom: 1rem;
		padding-left: 1.5rem;
	}

	.prose :global(li) {
		margin-bottom: 0.5rem;
	}

	.prose :global(code) {
		color: #1e293b;
		font-size: 0.875rem;
		font-family: 'Fira Code', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
	}

	.dark .prose :global(code) {
		color: #f1f5f9;
	}

	.prose :global(pre) {
		background-color: #f1f5f9;
		color: #1e293b;
		padding: 1.25rem;
		border-radius: 0.5rem;
		overflow-x: auto;
		margin-bottom: 1.5rem;
		border: 1px solid #e2e8f0;
		font-family: 'Fira Code', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
		line-height: 1.5;
	}

	.dark .prose :global(pre) {
		background-color: #374151;
		color: #f9fafb;
		border-color: #4b5563;
	}

	/* Model Card Content Styles */
	.model-card-content {
		min-height: 60vh; /* 设置最小高度为视口高度的60% */
		width: 100%;
		overflow-wrap: break-word;
		word-wrap: break-word;
		padding-bottom: 2rem; /* 底部留出间距 */
	}

	/* 表格滚动样式 */
	.model-card-content :global(table) {
		display: table;
		width: max-content;
		min-width: 100%;
		border-collapse: collapse;
		margin-bottom: 1rem;
		white-space: nowrap;
	}

	.model-card-content :global(.table-container) {
		overflow-x: auto;
		margin-bottom: 1rem;
		border: 1px solid #e5e7eb;
		border-radius: 0.375rem;
		scrollbar-width: thin;
		scrollbar-color: #64748b #f1f5f9;
	}

	.dark .model-card-content :global(.table-container) {
		border-color: #374151;
		scrollbar-color: #64748b #1f2937;
	}

	.model-card-content :global(.table-container)::-webkit-scrollbar {
		height: 8px;
	}

	.model-card-content :global(.table-container)::-webkit-scrollbar-track {
		background: #f1f5f9;
		border-radius: 4px;
	}

	.dark .model-card-content :global(.table-container)::-webkit-scrollbar-track {
		background: #1f2937;
	}

	.model-card-content :global(.table-container)::-webkit-scrollbar-thumb {
		background: #64748b;
		border-radius: 4px;
	}

	.model-card-content :global(.table-container)::-webkit-scrollbar-thumb:hover {
		background: #94a3b8;
	}

	.model-card-content :global(table th),
	.model-card-content :global(table td) {
		border: 1px solid #e5e7eb;
		padding: 0.75rem;
		text-align: left;
		white-space: nowrap;
		min-width: 120px;
	}

	.dark .model-card-content :global(table th),
	.dark .model-card-content :global(table td) {
		border-color: #374151;
	}

	.model-card-content :global(table th) {
		background-color: #f8fafc;
		font-weight: 600;
	}

	.dark .model-card-content :global(table th) {
		background-color: #1e293b;
	}

	/* 图片响应式 */
	.model-card-content :global(img) {
		max-width: 100%;
		height: auto;
	}

	/* 长文本换行 */
	.model-card-content :global(p),
	.model-card-content :global(div),
	.model-card-content :global(span) {
		word-wrap: break-word;
		overflow-wrap: break-word;
	}
</style>
