/**
 * Tests for UI constants
 * @module __tests__/constants/ui.test
 */

import {
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
} from '../../constants/ui';

describe('UI Constants', () => {
  describe('ANIMATION', () => {
    it('should have valid timing constants', () => {
      expect(ANIMATION.NOTIFICATION_TIMEOUT).toBe(3000);
      expect(ANIMATION.DURATION).toBe(200);
      expect(ANIMATION.DURATION_FAST).toBe(100);
      expect(ANIMATION.DURATION_SLOW).toBe(500);
      expect(ANIMATION.DEBOUNCE_DELAY).toBe(300);
      expect(ANIMATION.THROTTLE_DELAY).toBe(100);
      expect(ANIMATION.TOOLTIP_DELAY).toBe(500);
    });

    it('should have all values as positive numbers', () => {
      Object.values(ANIMATION).forEach((value) => {
        expect(typeof value).toBe('number');
        expect(value).toBeGreaterThan(0);
      });
    });
  });

  describe('SEARCH', () => {
    it('should have valid search constants', () => {
      expect(SEARCH.MIN_LENGTH).toBe(2);
      expect(SEARCH.MAX_RESULTS).toBe(10);
      expect(SEARCH.DEBOUNCE).toBe(300);
    });

    it('should have MIN_LENGTH less than MAX_RESULTS', () => {
      expect(SEARCH.MIN_LENGTH).toBeLessThan(SEARCH.MAX_RESULTS);
    });
  });

  describe('PAGINATION', () => {
    it('should have valid pagination constants', () => {
      expect(PAGINATION.DEFAULT_PAGE_SIZE).toBe(20);
      expect(Array.isArray(PAGINATION.PAGE_SIZE_OPTIONS)).toBe(true);
      expect(PAGINATION.MAX_VISIBLE_PAGES).toBe(5);
    });

    it('should have DEFAULT_PAGE_SIZE in PAGE_SIZE_OPTIONS', () => {
      expect(PAGINATION.PAGE_SIZE_OPTIONS).toContain(PAGINATION.DEFAULT_PAGE_SIZE);
    });

    it('should have sorted PAGE_SIZE_OPTIONS', () => {
      const sorted = [...PAGINATION.PAGE_SIZE_OPTIONS].sort((a, b) => a - b);
      expect(PAGINATION.PAGE_SIZE_OPTIONS).toEqual(sorted);
    });
  });

  describe('MODAL', () => {
    it('should have valid modal constants', () => {
      expect(MODAL.ANIMATION_DURATION).toBe(200);
      expect(MODAL.MAX_WIDTH).toBe(800);
      expect(MODAL.Z_INDEX).toBe(1000);
      expect(MODAL.BACKDROP_Z_INDEX).toBe(999);
    });

    it('should have BACKDROP_Z_INDEX less than Z_INDEX', () => {
      expect(MODAL.BACKDROP_Z_INDEX).toBeLessThan(MODAL.Z_INDEX);
    });
  });

  describe('TOAST', () => {
    it('should have valid toast constants', () => {
      expect(TOAST.DURATION).toBe(3000);
      expect(TOAST.ERROR_DURATION).toBe(5000);
      expect(TOAST.SUCCESS_DURATION).toBe(2000);
      expect(TOAST.MAX_VISIBLE).toBe(3);
      expect(TOAST.POSITION).toBe('top-right');
    });

    it('should have ERROR_DURATION longer than SUCCESS_DURATION', () => {
      expect(TOAST.ERROR_DURATION).toBeGreaterThan(TOAST.SUCCESS_DURATION);
    });
  });

  describe('VALIDATION', () => {
    it('should have valid validation constants', () => {
      expect(VALIDATION.MIN_USERNAME_LENGTH).toBe(3);
      expect(VALIDATION.MAX_USERNAME_LENGTH).toBe(50);
      expect(VALIDATION.MIN_PASSWORD_LENGTH).toBe(8);
      expect(VALIDATION.MAX_PASSWORD_LENGTH).toBe(128);
    });

    it('should have regex patterns', () => {
      expect(VALIDATION.EMAIL_PATTERN).toBeInstanceOf(RegExp);
      expect(VALIDATION.PHONE_PATTERN).toBeInstanceOf(RegExp);
    });

    it('should validate email with EMAIL_PATTERN', () => {
      expect(VALIDATION.EMAIL_PATTERN.test('test@example.com')).toBe(true);
      expect(VALIDATION.EMAIL_PATTERN.test('invalid-email')).toBe(false);
    });

    it('should have MIN less than MAX for lengths', () => {
      expect(VALIDATION.MIN_USERNAME_LENGTH).toBeLessThan(VALIDATION.MAX_USERNAME_LENGTH);
      expect(VALIDATION.MIN_PASSWORD_LENGTH).toBeLessThan(VALIDATION.MAX_PASSWORD_LENGTH);
    });
  });

  describe('BREAKPOINTS', () => {
    it('should have valid breakpoint constants', () => {
      expect(BREAKPOINTS.SM).toBe(640);
      expect(BREAKPOINTS.MD).toBe(768);
      expect(BREAKPOINTS.LG).toBe(1024);
      expect(BREAKPOINTS.XL).toBe(1280);
      expect(BREAKPOINTS['2XL']).toBe(1536);
    });

    it('should have breakpoints in ascending order', () => {
      expect(BREAKPOINTS.SM).toBeLessThan(BREAKPOINTS.MD);
      expect(BREAKPOINTS.MD).toBeLessThan(BREAKPOINTS.LG);
      expect(BREAKPOINTS.LG).toBeLessThan(BREAKPOINTS.XL);
      expect(BREAKPOINTS.XL).toBeLessThan(BREAKPOINTS['2XL']);
    });
  });

  describe('Z_INDEX', () => {
    it('should have valid z-index constants', () => {
      expect(Z_INDEX.BASE).toBe(0);
      expect(Z_INDEX.DROPDOWN).toBe(100);
      expect(Z_INDEX.STICKY).toBe(200);
      expect(Z_INDEX.MODAL_BACKDROP).toBe(999);
      expect(Z_INDEX.MODAL).toBe(1000);
      expect(Z_INDEX.TOOLTIP).toBe(1100);
      expect(Z_INDEX.TOAST).toBe(1200);
      expect(Z_INDEX.LOADING).toBe(1300);
    });

    it('should have z-index values in proper hierarchy', () => {
      expect(Z_INDEX.BASE).toBeLessThan(Z_INDEX.DROPDOWN);
      expect(Z_INDEX.DROPDOWN).toBeLessThan(Z_INDEX.STICKY);
      expect(Z_INDEX.MODAL_BACKDROP).toBeLessThan(Z_INDEX.MODAL);
      expect(Z_INDEX.MODAL).toBeLessThan(Z_INDEX.TOOLTIP);
      expect(Z_INDEX.TOOLTIP).toBeLessThan(Z_INDEX.TOAST);
      expect(Z_INDEX.TOAST).toBeLessThan(Z_INDEX.LOADING);
    });
  });

  describe('LOADING', () => {
    it('should have valid loading constants', () => {
      expect(LOADING.MIN_DISPLAY_TIME).toBe(500);
      expect(LOADING.TIMEOUT).toBe(30000);
      expect(LOADING.SKELETON_DURATION).toBe(1500);
    });

    it('should have all positive values', () => {
      Object.values(LOADING).forEach((value) => {
        expect(value).toBeGreaterThan(0);
      });
    });
  });

  describe('A11Y', () => {
    it('should have valid accessibility constants', () => {
      expect(A11Y.FOCUS_RING_WIDTH).toBe(2);
      expect(A11Y.MIN_TOUCH_TARGET).toBe(44);
      expect(A11Y.SKIP_LINK_TARGET).toBe('main-content');
    });

    it('should have MIN_TOUCH_TARGET meeting WCAG standards', () => {
      expect(A11Y.MIN_TOUCH_TARGET).toBeGreaterThanOrEqual(44);
    });
  });

  describe('UPLOAD', () => {
    it('should have valid upload constants', () => {
      expect(UPLOAD.MAX_FILE_SIZE).toBe(10 * 1024 * 1024);
      expect(Array.isArray(UPLOAD.IMAGE_FORMATS)).toBe(true);
      expect(Array.isArray(UPLOAD.DOCUMENT_FORMATS)).toBe(true);
      expect(UPLOAD.MAX_CONCURRENT).toBe(3);
    });

    it('should have common image formats', () => {
      expect(UPLOAD.IMAGE_FORMATS).toContain('image/jpeg');
      expect(UPLOAD.IMAGE_FORMATS).toContain('image/png');
    });

    it('should have common document formats', () => {
      expect(UPLOAD.DOCUMENT_FORMATS).toContain('application/pdf');
    });
  });

  describe('THEME', () => {
    it('should have valid theme constants', () => {
      expect(THEME.DEFAULT).toBe('light');
      expect(Array.isArray(THEME.THEMES)).toBe(true);
      expect(THEME.STORAGE_KEY).toBe('theme-preference');
    });

    it('should have DEFAULT in THEMES', () => {
      expect(THEME.THEMES).toContain(THEME.DEFAULT);
    });

    it('should have common themes', () => {
      expect(THEME.THEMES).toContain('light');
      expect(THEME.THEMES).toContain('dark');
    });
  });

  describe('UI_TEXT', () => {
    it('should have valid text constants', () => {
      expect(typeof UI_TEXT.LOADING).toBe('string');
      expect(typeof UI_TEXT.NO_DATA).toBe('string');
      expect(typeof UI_TEXT.ERROR).toBe('string');
      expect(typeof UI_TEXT.SUCCESS).toBe('string');
      expect(typeof UI_TEXT.CONFIRM).toBe('string');
    });

    it('should have button text', () => {
      expect(UI_TEXT.CANCEL).toBe('Cancel');
      expect(UI_TEXT.OK).toBe('OK');
      expect(UI_TEXT.SAVE).toBe('Save');
      expect(UI_TEXT.DELETE).toBe('Delete');
    });

    it('should have non-empty strings', () => {
      Object.values(UI_TEXT).forEach((text) => {
        expect(text.length).toBeGreaterThan(0);
      });
    });
  });
});
