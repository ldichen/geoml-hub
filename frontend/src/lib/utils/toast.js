import { writable } from 'svelte/store';

// Toast store for global toast management
export const toasts = writable([]);

let toastId = 0;

/**
 * Add a toast notification
 * @param {Object} toast - Toast configuration
 * @param {string} toast.variant - Toast variant ('info', 'success', 'warning', 'error')
 * @param {string} toast.title - Toast title (optional)
 * @param {string} toast.message - Toast message
 * @param {number} toast.duration - Auto-dismiss duration in ms (default: 5000, 0 for no auto-dismiss)
 * @param {boolean} toast.dismissible - Whether the toast can be manually dismissed (default: true)
 * @param {string} toast.position - Toast position (default: 'top-right')
 */
export function addToast(toast) {
  const id = ++toastId;
  const newToast = {
    id,
    variant: 'info',
    title: '',
    message: '',
    duration: 5000,
    dismissible: true,
    position: 'top-right',
    ...toast
  };

  toasts.update(current => [...current, newToast]);

  // Auto-dismiss if duration is set
  if (newToast.duration > 0) {
    setTimeout(() => {
      removeToast(id);
    }, newToast.duration);
  }

  return id;
}

/**
 * Remove a toast by ID
 * @param {number} id - Toast ID
 */
export function removeToast(id) {
  toasts.update(current => current.filter(toast => toast.id !== id));
}

/**
 * Clear all toasts
 */
export function clearToasts() {
  toasts.set([]);
}

// Convenience methods for different toast types
export const toast = {
  info: (message, options = {}) => addToast({ variant: 'info', message, ...options }),
  success: (message, options = {}) => addToast({ variant: 'success', message, ...options }),
  warning: (message, options = {}) => addToast({ variant: 'warning', message, ...options }),
  error: (message, options = {}) => addToast({ variant: 'error', message, ...options })
};

// Usage examples:
// toast.success('File uploaded successfully!');
// toast.error('Failed to save changes', { duration: 0 }); // No auto-dismiss
// toast.info('Processing...', { title: 'Please wait', position: 'top-center' });