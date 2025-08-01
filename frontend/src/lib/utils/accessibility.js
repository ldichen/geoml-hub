/**
 * Accessibility utilities for better a11y support
 */

/**
 * Generate unique IDs for form elements
 */
let idCounter = 0;
export function generateId(prefix = 'element') {
  return `${prefix}-${++idCounter}`;
}

/**
 * Trap focus within a container element
 * @param {HTMLElement} container - Container element to trap focus within
 * @returns {Function} cleanup function
 */
export function trapFocus(container) {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  function handleTabKey(event) {
    if (event.key !== 'Tab') return;

    if (event.shiftKey) {
      // Shift + Tab
      if (document.activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      }
    } else {
      // Tab
      if (document.activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    }
  }

  container.addEventListener('keydown', handleTabKey);

  // Focus first element
  if (firstElement) {
    firstElement.focus();
  }

  // Return cleanup function
  return () => {
    container.removeEventListener('keydown', handleTabKey);
  };
}

/**
 * Manage ARIA live regions for screen readers
 */
class LiveRegionManager {
  constructor() {
    this.regions = new Map();
    this.createRegions();
  }

  createRegions() {
    const politeness = ['polite', 'assertive'];
    
    politeness.forEach(level => {
      const region = document.createElement('div');
      region.setAttribute('aria-live', level);
      region.setAttribute('aria-atomic', 'true');
      region.className = 'sr-only';
      document.body.appendChild(region);
      this.regions.set(level, region);
    });
  }

  announce(message, priority = 'polite') {
    const region = this.regions.get(priority);
    if (region) {
      region.textContent = '';
      // Small delay to ensure screen reader picks up the change
      setTimeout(() => {
        region.textContent = message;
      }, 100);
    }
  }

  clear(priority = 'polite') {
    const region = this.regions.get(priority);
    if (region) {
      region.textContent = '';
    }
  }
}

export const liveRegion = new LiveRegionManager();

/**
 * Check if user prefers reduced motion
 */
export function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Check if user prefers high contrast
 */
export function prefersHighContrast() {
  return window.matchMedia('(prefers-contrast: high)').matches;
}

/**
 * Keyboard navigation utilities
 */
export const Keys = {
  ENTER: 'Enter',
  SPACE: ' ',
  TAB: 'Tab',
  ESCAPE: 'Escape',
  ARROW_UP: 'ArrowUp',
  ARROW_DOWN: 'ArrowDown',
  ARROW_LEFT: 'ArrowLeft',
  ARROW_RIGHT: 'ArrowRight',
  HOME: 'Home',
  END: 'End'
};

/**
 * Handle arrow key navigation for lists
 * @param {Event} event - Keyboard event
 * @param {NodeList} items - List of focusable items
 * @param {number} currentIndex - Current focused item index
 * @param {boolean} circular - Whether navigation should wrap around
 * @returns {number} new index
 */
export function handleArrowNavigation(event, items, currentIndex, circular = true) {
  const { key } = event;
  let newIndex = currentIndex;

  switch (key) {
    case Keys.ARROW_UP:
    case Keys.ARROW_LEFT:
      event.preventDefault();
      newIndex = currentIndex > 0 ? currentIndex - 1 : (circular ? items.length - 1 : 0);
      break;
    
    case Keys.ARROW_DOWN:
    case Keys.ARROW_RIGHT:
      event.preventDefault();
      newIndex = currentIndex < items.length - 1 ? currentIndex + 1 : (circular ? 0 : items.length - 1);
      break;
    
    case Keys.HOME:
      event.preventDefault();
      newIndex = 0;
      break;
    
    case Keys.END:
      event.preventDefault();
      newIndex = items.length - 1;
      break;
  }

  if (newIndex !== currentIndex && items[newIndex]) {
    items[newIndex].focus();
  }

  return newIndex;
}

/**
 * Create skip link for keyboard navigation
 */
export function createSkipLink(targetId, text = 'Skip to main content') {
  const skipLink = document.createElement('a');
  skipLink.href = `#${targetId}`;
  skipLink.textContent = text;
  skipLink.className = 'sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-primary-600 text-white px-4 py-2 rounded-md z-50';
  
  document.body.insertBefore(skipLink, document.body.firstChild);
  
  return skipLink;
}

/**
 * Screen reader only class utility
 */
export const srOnly = 'absolute w-px h-px p-0 -m-px overflow-hidden whitespace-nowrap border-0';

/**
 * Focus management for modals and overlays
 */
export class FocusManager {
  constructor() {
    this.previousFocus = null;
    this.trapCleanup = null;
  }

  save() {
    this.previousFocus = document.activeElement;
  }

  restore() {
    if (this.previousFocus && this.previousFocus.focus) {
      this.previousFocus.focus();
    }
    this.previousFocus = null;
  }

  trap(container) {
    this.release();
    this.trapCleanup = trapFocus(container);
  }

  release() {
    if (this.trapCleanup) {
      this.trapCleanup();
      this.trapCleanup = null;
    }
  }
}

/**
 * ARIA attributes helpers
 */
export const aria = {
  expanded: (expanded) => ({ 'aria-expanded': expanded }),
  selected: (selected) => ({ 'aria-selected': selected }),
  checked: (checked) => ({ 'aria-checked': checked }),
  disabled: (disabled) => ({ 'aria-disabled': disabled }),
  hidden: (hidden) => ({ 'aria-hidden': hidden }),
  label: (label) => ({ 'aria-label': label }),
  labelledby: (id) => ({ 'aria-labelledby': id }),
  describedby: (id) => ({ 'aria-describedby': id }),
  controls: (id) => ({ 'aria-controls': id }),
  owns: (id) => ({ 'aria-owns': id }),
  live: (politeness) => ({ 'aria-live': politeness }),
  atomic: (atomic) => ({ 'aria-atomic': atomic })
};