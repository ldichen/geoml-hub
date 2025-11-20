<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import UserProfile from '$lib/components/UserProfile.svelte';
	import type { User } from '$lib/types';
	import { api } from '$lib/utils/api';
	import { user } from '$lib/stores/auth';

	let currentUser: User | null = null;
	let username: string;

	$: username = $page.params.username;
	$: currentUser = $user;

	onMount(async () => {
		// User is loaded from auth store
		// No need to manually fetch current user here
	});
</script>

<svelte:head>
	<title>@{username} - GeoML Hub</title>
	<meta name="description" content="查看 @{username} 在 GeoML Hub 上的个人资料和仓库" />
</svelte:head>

<UserProfile {username} {currentUser} />
