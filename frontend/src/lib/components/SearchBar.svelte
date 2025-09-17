<script>
	import { _ } from 'svelte-i18n';
	import { Search, X } from 'lucide-svelte';
	import { createEventDispatcher } from 'svelte';

	export let value = '';
	export let placeholder = '';

	const dispatch = createEventDispatcher();

	function handleSubmit() {
		dispatch('search', value);
	}

	function handleClear() {
		value = '';
		dispatch('search', '');
	}

	function handleKeydown(event) {
		if (event.key === 'Enter') {
			handleSubmit();
		}
	}
</script>

<div class="relative">
	<div class="relative">
		<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
			<Search class="h-5 w-5 text-gray-400" />
		</div>

		<input
			bind:value
			type="text"
			class="block w-full pl-10 pr-20 py-3 text-gray-900 dark:text-white bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
			placeholder={placeholder || $_('search.placeholder')}
			on:keydown={handleKeydown}
		/>

		{#if value}
			<div class="absolute inset-y-0 right-16 pr-3 flex items-center">
				<button
					type="button"
					class="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
					on:click={handleClear}
				>
					<X class="h-4 w-4 text-gray-400" />
				</button>
			</div>
		{/if}
	</div>

	<div class="absolute right-2 top-1/2 transform -translate-y-1/2">
		<button
			type="button"
			class="px-4 py-2 bg-blue-500 hover:bg-blue-700 text-white font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
			on:click={handleSubmit}
		>
			Search
		</button>
	</div>
</div>
