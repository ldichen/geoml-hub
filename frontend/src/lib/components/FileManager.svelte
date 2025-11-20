<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import {
		File,
		Folder,
		Download,
		Trash2,
		Calendar,
		Search,
		Grid,
		List,
		ChevronRight,
		ArrowLeft
	} from 'lucide-svelte';
	import { formatDistanceToNow } from 'date-fns';
	import zhCN from 'date-fns/locale/zh-CN/index.js';
	import type { RepositoryFile } from '$lib/types';
	import { api } from '$lib/utils/api';

	const dispatch = createEventDispatcher<{
		download: { file: RepositoryFile };
		delete: { file: RepositoryFile };
		select: { file: Partial<RepositoryFile> | { file_path: string } };
	}>();

	export let files: RepositoryFile[] = [];
	export let currentPath: string = '';
	export let editable: boolean = false;
	export let viewMode: 'grid' | 'list' = 'list';
	export let searchQuery: string = '';

	let selectedFiles: Set<number> = new Set();
	let sortBy: 'name' | 'size' | 'created_at' = 'name';
	let sortOrder: 'asc' | 'desc' = 'asc';

	// Filter and sort files
	$: filteredFiles = files
		.filter((file) => {
			if (searchQuery) {
				return file.filename.toLowerCase().includes(searchQuery.toLowerCase());
			}
			return true;
		})
		.sort((a, b) => {
			let aValue: string | number;
			let bValue: string | number;

			switch (sortBy) {
				case 'name':
					aValue = a.filename.toLowerCase();
					bValue = b.filename.toLowerCase();
					break;
				case 'size':
					aValue = a.file_size;
					bValue = b.file_size;
					break;
				case 'created_at':
					aValue = new Date(a.created_at).getTime();
					bValue = new Date(b.created_at).getTime();
					break;
				default:
					aValue = a.filename.toLowerCase();
					bValue = b.filename.toLowerCase();
			}

			if (sortOrder === 'asc') {
				return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
			} else {
				return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
			}
		});

	// Get file/folder structure
	$: fileStructure = buildFileStructure(filteredFiles, currentPath);

	function buildFileStructure(files: RepositoryFile[], path: string) {
		const pathParts = path ? path.split('/') : [];
		const folders: Set<string> = new Set();
		const currentFiles: RepositoryFile[] = [];

		files.forEach((file) => {
			const fileParts = file.file_path.split('/');

			// Check if file is in current path
			if (fileParts.length > pathParts.length + 1) {
				// File is in a subfolder
				const folderName = fileParts[pathParts.length];
				if (fileParts.slice(0, pathParts.length).join('/') === path) {
					folders.add(folderName);
				}
			} else if (fileParts.length === pathParts.length + 1) {
				// File is directly in current path
				if (fileParts.slice(0, pathParts.length).join('/') === path) {
					currentFiles.push(file);
				}
			}
		});

		return {
			folders: Array.from(folders).sort(),
			files: currentFiles
		};
	}

	function formatFileSize(bytes: number): string {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
	}

	function getFileIcon(filename: string) {
		const extension = filename.split('.').pop()?.toLowerCase();

		// Define icon classes based on file types
		const iconClasses = {
			// Images
			jpg: 'text-green-500',
			jpeg: 'text-green-500',
			png: 'text-green-500',
			gif: 'text-green-500',
			webp: 'text-green-500',
			svg: 'text-green-500',

			// Documents
			pdf: 'text-red-500',
			doc: 'text-blue-500',
			docx: 'text-blue-500',
			txt: 'text-gray-500',
			md: 'text-gray-500',
			readme: 'text-gray-500',

			// Code
			js: 'text-yellow-500',
			ts: 'text-blue-500',
			py: 'text-yellow-500',
			java: 'text-orange-500',
			cpp: 'text-blue-500',
			c: 'text-blue-500',
			html: 'text-orange-500',
			css: 'text-blue-500',
			json: 'text-green-500',
			xml: 'text-green-500',
			yml: 'text-green-500',
			yaml: 'text-green-500',

			// Archives
			zip: 'text-purple-500',
			rar: 'text-purple-500',
			'7z': 'text-purple-500',
			tar: 'text-purple-500',
			gz: 'text-purple-500',

			// Machine Learning
			pkl: 'text-indigo-500',
			h5: 'text-indigo-500',
			pt: 'text-indigo-500',
			pth: 'text-indigo-500',
			onnx: 'text-indigo-500',
			pb: 'text-indigo-500',
			tflite: 'text-indigo-500',
			joblib: 'text-indigo-500',

			// Data
			csv: 'text-green-500',
			xlsx: 'text-green-500',
			xls: 'text-green-500',
			parquet: 'text-green-500',
			hdf5: 'text-green-500',
			nc: 'text-green-500',

			// Default
			default: 'text-gray-400'
		};

		return iconClasses[extension || 'default'] || iconClasses.default;
	}

	function navigateToFolder(folderName: string) {
		const newPath = currentPath ? `${currentPath}/${folderName}` : folderName;
		dispatch('select', { file: { file_path: newPath } });
	}

	function navigateUp() {
		const pathParts = currentPath.split('/');
		pathParts.pop();
		const newPath = pathParts.join('/');
		dispatch('select', { file: { file_path: newPath } });
	}

	function toggleFileSelection(fileId: number) {
		if (selectedFiles.has(fileId)) {
			selectedFiles.delete(fileId);
		} else {
			selectedFiles.add(fileId);
		}
		selectedFiles = new Set(selectedFiles);
	}

	function selectAllFiles() {
		selectedFiles = new Set(fileStructure.files.map((f) => f.id));
	}

	function clearSelection() {
		selectedFiles = new Set();
	}

	async function downloadFile(file: RepositoryFile) {
		dispatch('download', { file });
	}

	async function deleteFile(file: RepositoryFile) {
		dispatch('delete', { file });
	}

	function handleSort(field: typeof sortBy) {
		if (sortBy === field) {
			sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
		} else {
			sortBy = field;
			sortOrder = 'asc';
		}
	}
</script>

<div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
	<!-- Header -->
	<div class="p-4 border-b border-gray-200 dark:border-gray-700">
		<div class="flex items-center justify-between mb-4">
			<h3 class="text-lg font-semibold text-gray-900 dark:text-white">文件管理</h3>

			<div class="flex items-center space-x-2">
				<!-- View Mode Toggle -->
				<div class="flex items-center space-x-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
					<button
						class="p-1 rounded {viewMode === 'list' ? 'bg-white dark:bg-gray-600 shadow-sm' : ''}"
						on:click={() => (viewMode = 'list')}
					>
						<List class="h-4 w-4" />
					</button>
					<button
						class="p-1 rounded {viewMode === 'grid' ? 'bg-white dark:bg-gray-600 shadow-sm' : ''}"
						on:click={() => (viewMode = 'grid')}
					>
						<Grid class="h-4 w-4" />
					</button>
				</div>

				<!-- Search -->
				<div class="relative">
					<Search
						class="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
					/>
					<input
						type="text"
						placeholder="搜索文件..."
						bind:value={searchQuery}
						class="pl-9 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
					/>
				</div>
			</div>
		</div>

		<!-- Breadcrumb -->
		{#if currentPath}
			<div class="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
				<button
					class="hover:text-blue-600 dark:hover:text-blue-400"
					on:click={() => dispatch('select', { file: { file_path: '' } })}
				>
					根目录
				</button>
				{#each currentPath.split('/') as part, index}
					<ChevronRight class="h-4 w-4" />
					<button
						class="hover:text-blue-600 dark:hover:text-blue-400"
						on:click={() => {
							const pathParts = currentPath.split('/').slice(0, index + 1);
							dispatch('select', { file: { file_path: pathParts.join('/') } });
						}}
					>
						{part}
					</button>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Content -->
	<div class="p-4">
		{#if viewMode === 'list'}
			<!-- List View -->
			<div class="space-y-1">
				<!-- Header -->
				<div
					class="flex items-center px-3 py-2 text-sm font-medium text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700"
				>
					<div class="flex-1">
						<button
							class="flex items-center space-x-1 hover:text-gray-700 dark:hover:text-gray-200"
							on:click={() => handleSort('name')}
						>
							<span>名称</span>
							{#if sortBy === 'name'}
								<span class="text-xs">
									{sortOrder === 'asc' ? '↑' : '↓'}
								</span>
							{/if}
						</button>
					</div>
					<div class="w-20">
						<button
							class="flex items-center space-x-1 hover:text-gray-700 dark:hover:text-gray-200"
							on:click={() => handleSort('size')}
						>
							<span>大小</span>
							{#if sortBy === 'size'}
								<span class="text-xs">
									{sortOrder === 'asc' ? '↑' : '↓'}
								</span>
							{/if}
						</button>
					</div>
					<div class="w-32">
						<button
							class="flex items-center space-x-1 hover:text-gray-700 dark:hover:text-gray-200"
							on:click={() => handleSort('created_at')}
						>
							<span>创建时间</span>
							{#if sortBy === 'created_at'}
								<span class="text-xs">
									{sortOrder === 'asc' ? '↑' : '↓'}
								</span>
							{/if}
						</button>
					</div>
					<div class="w-20">操作</div>
				</div>

				<!-- Back Button -->
				{#if currentPath}
					<button
						class="flex items-center px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-md cursor-pointer w-full text-left"
						on:click={navigateUp}
					>
						<ArrowLeft class="h-4 w-4 mr-3 text-gray-400" />
						<span class="text-sm text-gray-600 dark:text-gray-400">返回上级</span>
					</button>
				{/if}

				<!-- Folders -->
				{#each fileStructure.folders as folder}
					<button
						class="flex items-center px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-md cursor-pointer w-full text-left"
						on:click={() => navigateToFolder(folder)}
					>
						<Folder class="h-4 w-4 mr-3 text-blue-500" />
						<div class="flex-1 min-w-0">
							<p class="text-sm font-medium text-gray-900 dark:text-white truncate">
								{folder}
							</p>
						</div>
						<div class="w-20 text-sm text-gray-500 dark:text-gray-400">-</div>
						<div class="w-32 text-sm text-gray-500 dark:text-gray-400">-</div>
						<div class="w-20" />
					</button>
				{/each}

				<!-- Files -->
				{#each fileStructure.files as file}
					<div
						class="flex items-center px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-md"
					>
						<File class="h-4 w-4 mr-3 {getFileIcon(file.filename)}" />
						<div class="flex-1 min-w-0">
							<p class="text-sm font-medium text-gray-900 dark:text-white truncate">
								{file.filename}
							</p>
						</div>
						<div class="w-20 text-sm text-gray-500 dark:text-gray-400">
							{formatFileSize(file.file_size)}
						</div>
						<div class="w-32 text-sm text-gray-500 dark:text-gray-400">
							{formatDistanceToNow(new Date(file.created_at), { addSuffix: true, locale: zhCN })}
						</div>
						<div class="w-20 flex items-center space-x-1">
							<button
								class="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
								on:click={() => downloadFile(file)}
								title="下载"
							>
								<Download class="h-4 w-4" />
							</button>
							{#if editable}
								<button
									class="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
									on:click={() => deleteFile(file)}
									title="删除"
								>
									<Trash2 class="h-4 w-4" />
								</button>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		{:else}
			<!-- Grid View -->
			<div
				class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4"
			>
				<!-- Back Button -->
				{#if currentPath}
					<button
						class="flex flex-col items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
						on:click={navigateUp}
					>
						<ArrowLeft class="h-8 w-8 text-gray-400 mb-2" />
						<span class="text-xs text-gray-600 dark:text-gray-400 text-center">返回上级</span>
					</button>
				{/if}

				<!-- Folders -->
				{#each fileStructure.folders as folder}
					<button
						class="flex flex-col items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
						on:click={() => navigateToFolder(folder)}
					>
						<Folder class="h-8 w-8 text-blue-500 mb-2" />
						<span
							class="text-xs text-gray-900 dark:text-white text-center truncate w-full"
							title={folder}
						>
							{folder}
						</span>
					</button>
				{/each}

				<!-- Files -->
				{#each fileStructure.files as file}
					<div
						class="flex flex-col items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 group"
					>
						<File class="h-8 w-8 mb-2 {getFileIcon(file.filename)}" />
						<span
							class="text-xs text-gray-900 dark:text-white text-center truncate w-full"
							title={file.filename}
						>
							{file.filename}
						</span>
						<span class="text-xs text-gray-500 dark:text-gray-400 mt-1">
							{formatFileSize(file.file_size)}
						</span>
						<div
							class="flex items-center space-x-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity"
						>
							<button
								class="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
								on:click={() => downloadFile(file)}
								title="下载"
							>
								<Download class="h-4 w-4" />
							</button>
							{#if editable}
								<button
									class="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
									on:click={() => deleteFile(file)}
									title="删除"
								>
									<Trash2 class="h-4 w-4" />
								</button>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		{/if}

		<!-- Empty State -->
		{#if fileStructure.folders.length === 0 && fileStructure.files.length === 0}
			<div class="text-center py-12">
				<File class="h-12 w-12 text-gray-400 mx-auto mb-4" />
				<p class="text-gray-500 dark:text-gray-400">
					{searchQuery ? '没有找到匹配的文件' : '该目录为空'}
				</p>
			</div>
		{/if}
	</div>
</div>
