/**
 * UI-related constants
 * Centralizes magic numbers and strings for UI components
 * @module constants/ui
 */

/**
 * Animation and timing constants
 */
export const ANIMATION = {
  /** Duration for notification fade animation (ms) */
  NOTIFICATION_TIMEOUT: 3000,

  /** Standard animation duration (ms) */
  DURATION: 200,

  /** Fast animation duration (ms) */
  DURATION_FAST: 100,

  /** Slow animation duration (ms) */
  DURATION_SLOW: 500,

  /** Debounce delay for input events (ms) */
  DEBOUNCE_DELAY: 300,

  /** Throttle delay for scroll events (ms) */
  THROTTLE_DELAY: 100,

  /** Tooltip show delay (ms) */
  TOOLTIP_DELAY: 500,
};

/**
 * Search and filter constants
 */
export const SEARCH = {
  /** Minimum characters required to trigger search */
  MIN_LENGTH: 2,

  /** Maximum search results to display */
  MAX_RESULTS: 10,

  /** Search debounce delay (ms) */
  DEBOUNCE: 300,
};

/**
 * Pagination constants
 */
export const PAGINATION = {
  /** Default items per page */
  DEFAULT_PAGE_SIZE: 20,

  /** Items per page options */
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],

  /** Maximum pages to show in pagination controls */
  MAX_VISIBLE_PAGES: 5,
};

/**
 * Modal and overlay constants
 */
export const MODAL = {
  /** Modal animation duration (ms) */
  ANIMATION_DURATION: 200,

  /** Maximum modal width (px) */
  MAX_WIDTH: 800,

  /** Z-index for modals */
  Z_INDEX: 1000,

  /** Z-index for modal backdrop */
  BACKDROP_Z_INDEX: 999,
};

/**
 * Toast notification constants
 */
export const TOAST = {
  /** Default toast duration (ms) */
  DURATION: 3000,

  /** Error toast duration (ms) */
  ERROR_DURATION: 5000,

  /** Success toast duration (ms) */
  SUCCESS_DURATION: 2000,

  /** Maximum number of visible toasts */
  MAX_VISIBLE: 3,

  /** Toast position */
  POSITION: 'top-right',
};

/**
 * Form validation constants
 */
export const VALIDATION = {
  /** Minimum username length */
  MIN_USERNAME_LENGTH: 3,

  /** Maximum username length */
  MAX_USERNAME_LENGTH: 50,

  /** Minimum password length */
  MIN_PASSWORD_LENGTH: 8,

  /** Maximum password length */
  MAX_PASSWORD_LENGTH: 128,

  /** Email regex pattern */
  EMAIL_PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,

  /** Phone regex pattern (basic) */
  PHONE_PATTERN: /^\+?[\d\s-()]+$/,
};

/**
 * Breakpoint constants (matches Tailwind defaults)
 */
export const BREAKPOINTS = {
  /** Small screen breakpoint (px) */
  SM: 640,

  /** Medium screen breakpoint (px) */
  MD: 768,

  /** Large screen breakpoint (px) */
  LG: 1024,

  /** Extra large screen breakpoint (px) */
  XL: 1280,

  /** 2X large screen breakpoint (px) */
  '2XL': 1536,
};

/**
 * Z-index scale
 */
export const Z_INDEX = {
  /** Base content */
  BASE: 0,

  /** Dropdown menus */
  DROPDOWN: 100,

  /** Sticky headers */
  STICKY: 200,

  /** Modals backdrop */
  MODAL_BACKDROP: 999,

  /** Modals */
  MODAL: 1000,

  /** Tooltips */
  TOOLTIP: 1100,

  /** Toast notifications */
  TOAST: 1200,

  /** Loading overlays */
  LOADING: 1300,
};

/**
 * Loading state constants
 */
export const LOADING = {
  /** Minimum loading spinner display time (ms) */
  MIN_DISPLAY_TIME: 500,

  /** Loading timeout before showing error (ms) */
  TIMEOUT: 30000,

  /** Skeleton animation duration (ms) */
  SKELETON_DURATION: 1500,
};

/**
 * Accessibility constants
 */
export const A11Y = {
  /** Focus ring width (px) */
  FOCUS_RING_WIDTH: 2,

  /** Minimum touch target size (px) */
  MIN_TOUCH_TARGET: 44,

  /** Skip link target ID */
  SKIP_LINK_TARGET: 'main-content',
};

/**
 * File upload constants
 */
export const UPLOAD = {
  /** Maximum file size (bytes) - 10MB */
  MAX_FILE_SIZE: 10 * 1024 * 1024,

  /** Allowed image formats */
  IMAGE_FORMATS: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],

  /** Allowed document formats */
  DOCUMENT_FORMATS: [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  ],

  /** Maximum number of simultaneous uploads */
  MAX_CONCURRENT: 3,
};

/**
 * Color theme constants
 */
export const THEME = {
  /** Default theme */
  DEFAULT: 'light',

  /** Available themes */
  THEMES: ['light', 'dark', 'auto'],

  /** Theme storage key */
  STORAGE_KEY: 'theme-preference',
};

/**
 * Default UI text
 */
export const UI_TEXT = {
  /** Loading text */
  LOADING: 'Loading...',

  /** No data text */
  NO_DATA: 'No data available',

  /** Error text */
  ERROR: 'An error occurred',

  /** Success text */
  SUCCESS: 'Success!',

  /** Confirm text */
  CONFIRM: 'Are you sure?',

  /** Cancel button */
  CANCEL: 'Cancel',

  /** OK button */
  OK: 'OK',

  /** Save button */
  SAVE: 'Save',

  /** Delete button */
  DELETE: 'Delete',
};

const UI_CONSTANTS = {
  ANIMATION,
  SEARCH,
  PAGINATION,
  MODAL,
  TOAST,
  VALIDATION,
  BREAKPOINTS,
  Z_INDEX,
  LOADING,
  A11Y,
  UPLOAD,
  THEME,
  UI_TEXT,
};

export default UI_CONSTANTS;
