<script>
  import { 
    Button, Card, Badge, Alert, Input, FormField, Modal, Dropdown, Tabs, Pagination
  } from './ui/index.js';
  import { toast } from '$lib/utils/toast.js';

  let showModal = false;
  let inputValue = '';
  let dropdownValue = null;
  let activeTab = 'colors';
  let currentPage = 1;

  const dropdownItems = [
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2' },
    { value: 'option3', label: 'Option 3' }
  ];

  const tabs = [
    { id: 'colors', label: 'Colors' },
    { id: 'typography', label: 'Typography' },
    { id: 'components', label: 'Components' },
    { id: 'utilities', label: 'Utilities' }
  ];

  function showToast(variant) {
    toast[variant](`This is a ${variant} toast notification!`);
  }
</script>

<div class="max-w-6xl mx-auto p-6 space-y-8">
  <div class="text-center">
    <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4">
      GeoML-Hub Design System
    </h1>
    <p class="text-lg text-gray-600 dark:text-gray-400">
      A comprehensive UI component library and design system
    </p>
  </div>

  <Tabs {tabs} bind:activeTab>
    <div slot="panel" let:tab let:active>
      {#if tab.id === 'colors'}
        <div class="space-y-6">
          <h2 class="text-2xl font-semibold mb-4">Color Palette</h2>
          
          <!-- Primary Colors -->
          <div>
            <h3 class="text-lg font-medium mb-3">Primary Colors</h3>
            <div class="grid grid-cols-5 gap-4">
              {#each [50, 100, 200, 300, 400, 500, 600, 700, 800, 900] as shade}
                <div class="text-center">
                  <div class="h-16 w-full bg-primary-{shade} rounded-lg mb-2"></div>
                  <p class="text-sm text-gray-600 dark:text-gray-400">primary-{shade}</p>
                </div>
              {/each}
            </div>
          </div>

          <!-- Status Colors -->
          <div>
            <h3 class="text-lg font-medium mb-3">Status Colors</h3>
            <div class="grid grid-cols-4 gap-4">
              <div class="text-center">
                <div class="h-16 w-full bg-green-500 rounded-lg mb-2"></div>
                <p class="text-sm text-gray-600 dark:text-gray-400">Success</p>
              </div>
              <div class="text-center">
                <div class="h-16 w-full bg-yellow-500 rounded-lg mb-2"></div>
                <p class="text-sm text-gray-600 dark:text-gray-400">Warning</p>
              </div>
              <div class="text-center">
                <div class="h-16 w-full bg-red-500 rounded-lg mb-2"></div>
                <p class="text-sm text-gray-600 dark:text-gray-400">Error</p>
              </div>
              <div class="text-center">
                <div class="h-16 w-full bg-blue-500 rounded-lg mb-2"></div>
                <p class="text-sm text-gray-600 dark:text-gray-400">Info</p>
              </div>
            </div>
          </div>
        </div>

      {:else if tab.id === 'typography'}
        <div class="space-y-6">
          <h2 class="text-2xl font-semibold mb-4">Typography</h2>
          
          <!-- Display Text -->
          <div>
            <h3 class="text-lg font-medium mb-3">Display Text</h3>
            <div class="space-y-4">
              <div>
                <h1 class="text-display-2xl">Display 2XL</h1>
                <p class="text-sm text-gray-500">text-display-2xl</p>
              </div>
              <div>
                <h2 class="text-display-xl">Display XL</h2>
                <p class="text-sm text-gray-500">text-display-xl</p>
              </div>
              <div>
                <h3 class="text-display-lg">Display LG</h3>
                <p class="text-sm text-gray-500">text-display-lg</p>
              </div>
            </div>
          </div>

          <!-- Body Text -->
          <div>
            <h3 class="text-lg font-medium mb-3">Body Text</h3>
            <div class="space-y-2">
              <p class="text-lg">Large text - text-lg</p>
              <p class="text-base">Base text - text-base</p>
              <p class="text-sm">Small text - text-sm</p>
              <p class="text-xs">Extra small text - text-xs</p>
            </div>
          </div>
        </div>

      {:else if tab.id === 'components'}
        <div class="space-y-8">
          <h2 class="text-2xl font-semibold mb-4">Components</h2>
          
          <!-- Buttons -->
          <div>
            <h3 class="text-lg font-medium mb-4">Buttons</h3>
            <div class="space-y-4">
              <div class="flex flex-wrap gap-3">
                <Button variant="primary">Primary</Button>
                <Button variant="secondary">Secondary</Button>
                <Button variant="danger">Danger</Button>
                <Button variant="ghost">Ghost</Button>
                <Button variant="outline">Outline</Button>
              </div>
              
              <div class="flex flex-wrap gap-3">
                <Button size="xs">Extra Small</Button>
                <Button size="sm">Small</Button>
                <Button size="md">Medium</Button>
                <Button size="lg">Large</Button>
                <Button size="xl">Extra Large</Button>
              </div>
              
              <div class="flex flex-wrap gap-3">
                <Button loading>Loading</Button>
                <Button disabled>Disabled</Button>
              </div>
            </div>
          </div>

          <!-- Cards -->
          <div>
            <h3 class="text-lg font-medium mb-4">Cards</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <div slot="header">
                  <h4 class="font-medium">Default Card</h4>
                </div>
                <p>This is a default card with header and footer.</p>
                <div slot="footer">
                  <Button size="sm">Action</Button>
                </div>
              </Card>
              
              <Card variant="outline" hover>
                <h4 class="font-medium mb-2">Outline Card</h4>
                <p>This card has an outline variant with hover effect.</p>
              </Card>
              
              <Card variant="elevated" clickable>
                <h4 class="font-medium mb-2">Elevated Card</h4>
                <p>This is an elevated card that's clickable.</p>
              </Card>
            </div>
          </div>

          <!-- Badges -->
          <div>
            <h3 class="text-lg font-medium mb-4">Badges</h3>
            <div class="space-y-3">
              <div class="flex flex-wrap gap-2">
                <Badge variant="default">Default</Badge>
                <Badge variant="primary">Primary</Badge>
                <Badge variant="secondary">Secondary</Badge>
                <Badge variant="success">Success</Badge>
                <Badge variant="warning">Warning</Badge>
                <Badge variant="danger">Danger</Badge>
              </div>
              
              <div class="flex flex-wrap gap-2">
                <Badge variant="primary" outline>Outline Primary</Badge>
                <Badge variant="success" outline>Outline Success</Badge>
                <Badge variant="warning" outline>Outline Warning</Badge>
              </div>
              
              <div class="flex flex-wrap gap-2">
                <Badge size="sm">Small</Badge>
                <Badge size="md">Medium</Badge>
                <Badge size="lg">Large</Badge>
              </div>
            </div>
          </div>

          <!-- Alerts -->
          <div>
            <h3 class="text-lg font-medium mb-4">Alerts</h3>
            <div class="space-y-4">
              <Alert variant="info" title="Information">
                This is an info alert with a title.
              </Alert>
              
              <Alert variant="success" dismissible>
                This is a success alert that can be dismissed.
              </Alert>
              
              <Alert variant="warning" title="Warning">
                This is a warning alert.
              </Alert>
              
              <Alert variant="danger" title="Error" dismissible>
                This is an error alert that can be dismissed.
              </Alert>
            </div>
          </div>

          <!-- Form Elements -->
          <div>
            <h3 class="text-lg font-medium mb-4">Form Elements</h3>
            <div class="space-y-4 max-w-md">
              <Input placeholder="Basic input" />
              
              <FormField
                label="Email Address"
                type="email"
                placeholder="Enter your email"
                hint="We'll never share your email"
                required
                bind:value={inputValue}
              />
              
              <Dropdown
                items={dropdownItems}
                placeholder="Select an option"
                bind:value={dropdownValue}
              />
            </div>
          </div>

          <!-- Modal -->
          <div>
            <h3 class="text-lg font-medium mb-4">Modal</h3>
            <Button on:click={() => showModal = true}>Show Modal</Button>
            
            <Modal bind:show={showModal} title="Example Modal">
              <p>This is an example modal with header and footer.</p>
              
              <div slot="footer">
                <Button variant="ghost" on:click={() => showModal = false}>Cancel</Button>
                <Button variant="primary" on:click={() => showModal = false}>Confirm</Button>
              </div>
            </Modal>
          </div>

          <!-- Toast Notifications -->
          <div>
            <h3 class="text-lg font-medium mb-4">Toast Notifications</h3>
            <div class="flex flex-wrap gap-3">
              <Button variant="ghost" on:click={() => showToast('info')}>Info Toast</Button>
              <Button variant="ghost" on:click={() => showToast('success')}>Success Toast</Button>
              <Button variant="ghost" on:click={() => showToast('warning')}>Warning Toast</Button>
              <Button variant="ghost" on:click={() => showToast('error')}>Error Toast</Button>
            </div>
          </div>

          <!-- Pagination -->
          <div>
            <h3 class="text-lg font-medium mb-4">Pagination</h3>
            <Pagination
              bind:currentPage
              totalPages={10}
              on:change={(e) => currentPage = e.detail.page}
            />
          </div>
        </div>

      {:else if tab.id === 'utilities'}
        <div class="space-y-6">
          <h2 class="text-2xl font-semibold mb-4">Utility Classes</h2>
          
          <!-- Spacing -->
          <div>
            <h3 class="text-lg font-medium mb-3">Spacing</h3>
            <div class="space-y-2">
              <div class="p-2 bg-gray-100 dark:bg-gray-800">p-2 (padding: 0.5rem)</div>
              <div class="p-4 bg-gray-100 dark:bg-gray-800">p-4 (padding: 1rem)</div>
              <div class="p-6 bg-gray-100 dark:bg-gray-800">p-6 (padding: 1.5rem)</div>
            </div>
          </div>

          <!-- Shadows -->
          <div>
            <h3 class="text-lg font-medium mb-3">Shadows</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="p-4 bg-white dark:bg-gray-800 shadow-sm rounded">shadow-sm</div>
              <div class="p-4 bg-white dark:bg-gray-800 shadow rounded">shadow</div>
              <div class="p-4 bg-white dark:bg-gray-800 shadow-md rounded">shadow-md</div>
              <div class="p-4 bg-white dark:bg-gray-800 shadow-lg rounded">shadow-lg</div>
            </div>
          </div>

          <!-- Border Radius -->
          <div>
            <h3 class="text-lg font-medium mb-3">Border Radius</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="p-4 bg-primary-100 dark:bg-primary-900/30 rounded-none">rounded-none</div>
              <div class="p-4 bg-primary-100 dark:bg-primary-900/30 rounded">rounded</div>
              <div class="p-4 bg-primary-100 dark:bg-primary-900/30 rounded-lg">rounded-lg</div>
              <div class="p-4 bg-primary-100 dark:bg-primary-900/30 rounded-full">rounded-full</div>
            </div>
          </div>
        </div>
      {/if}
    </div>
  </Tabs>
</div>