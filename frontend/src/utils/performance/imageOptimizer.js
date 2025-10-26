/**
 * Image Optimizer Utility
 * Provides utilities for optimizing image loading and performance
 */

import { PERFORMANCE_CONFIG } from '../../config/performance.config';

class ImageOptimizer {
  constructor() {
    this.observers = new Map();
    this.imageCache = new Map();
    this.lazyLoadEnabled = PERFORMANCE_CONFIG.images.lazyLoad;
  }

  /**
   * Create optimized image URL with size and format
   */
  getOptimizedUrl(url, options = {}) {
    const {
      size = 'medium',
      format = 'webp',
      quality = PERFORMANCE_CONFIG.images.quality,
    } = options;

    // If URL is already optimized or external, return as-is
    if (!url || url.startsWith('http')) {
      return url;
    }

    // Add optimization parameters
    const sizeParam = PERFORMANCE_CONFIG.images.sizes[size];
    return `${url}?w=${sizeParam}&q=${quality}&f=${format}`;
  }

  /**
   * Generate responsive srcSet for an image
   */
  generateSrcSet(url, sizes = ['small', 'medium', 'large']) {
    return sizes
      .map((size) => {
        const width = PERFORMANCE_CONFIG.images.sizes[size];
        const optimizedUrl = this.getOptimizedUrl(url, { size });
        return `${optimizedUrl} ${width}w`;
      })
      .join(', ');
  }

  /**
   * Lazy load images using Intersection Observer
   */
  lazyLoad(element, options = {}) {
    if (!this.lazyLoadEnabled || !('IntersectionObserver' in window)) {
      // Fallback: load immediately
      this.loadImage(element);
      return;
    }

    const { rootMargin = '50px', threshold = 0.01 } = options;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            this.loadImage(entry.target);
            observer.unobserve(entry.target);
          }
        });
      },
      { rootMargin, threshold }
    );

    observer.observe(element);
    this.observers.set(element, observer);
  }

  /**
   * Load an image
   */
  loadImage(element) {
    const src = element.dataset.src;
    const srcSet = element.dataset.srcset;

    if (!src) {
      return;
    }

    // Check cache
    if (this.imageCache.has(src)) {
      this.applyImage(element, src, srcSet);
      return;
    }

    // Create new image to preload
    const img = new Image();

    img.onload = () => {
      this.imageCache.set(src, true);
      this.applyImage(element, src, srcSet);
    };

    img.onerror = () => {
      console.warn(`Failed to load image: ${src}`);
      element.classList.add('image-load-error');
    };

    if (srcSet) {
      img.srcset = srcSet;
    }
    img.src = src;
  }

  /**
   * Apply loaded image to element
   */
  applyImage(element, src, srcSet) {
    if (element.tagName === 'IMG') {
      element.src = src;
      if (srcSet) {
        element.srcset = srcSet;
      }
    } else {
      element.style.backgroundImage = `url(${src})`;
    }

    element.classList.remove('lazy-loading');
    element.classList.add('lazy-loaded');
  }

  /**
   * Preload critical images
   */
  preloadImage(url) {
    if (this.imageCache.has(url)) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        this.imageCache.set(url, true);
        resolve();
      };
      img.onerror = reject;
      img.src = url;
    });
  }

  /**
   * Batch preload multiple images
   */
  async preloadImages(urls) {
    return Promise.all(urls.map((url) => this.preloadImage(url)));
  }

  /**
   * Check if image format is supported
   */
  async checkFormatSupport(format) {
    if (format === 'webp') {
      return this.checkWebPSupport();
    }
    return true;
  }

  /**
   * Check WebP support
   */
  checkWebPSupport() {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => resolve(img.width === 1);
      img.onerror = () => resolve(false);
      img.src =
        'data:image/webp;base64,UklGRiQAAABXRUJQVlA4IBgAAAAwAQCdASoBAAEAAwA0JaQAA3AA/vuUAAA=';
    });
  }

  /**
   * Get placeholder for image
   */
  getPlaceholder(type = 'blur') {
    const placeholders = {
      blur: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Cfilter id="b"%3E%3CfeGaussianBlur stdDeviation="10"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" fill="%23ddd" filter="url(%23b)"/%3E%3C/svg%3E',
      solid:
        'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect width="100%25" height="100%25" fill="%23ddd"/%3E%3C/svg%3E',
      transparent: 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',
    };

    return placeholders[type] || placeholders.blur;
  }

  /**
   * Optimize all images on the page
   */
  optimizeAllImages() {
    const images = document.querySelectorAll('img[data-src], [data-bg-src]');
    images.forEach((img) => this.lazyLoad(img));
  }

  /**
   * Calculate image dimensions while maintaining aspect ratio
   */
  calculateDimensions(originalWidth, originalHeight, maxWidth, maxHeight) {
    let width = originalWidth;
    let height = originalHeight;

    if (width > maxWidth) {
      height = (maxWidth / width) * height;
      width = maxWidth;
    }

    if (height > maxHeight) {
      width = (maxHeight / height) * width;
      height = maxHeight;
    }

    return {
      width: Math.round(width),
      height: Math.round(height),
    };
  }

  /**
   * Clean up observers
   */
  cleanup() {
    this.observers.forEach((observer) => observer.disconnect());
    this.observers.clear();
  }
}

// Create singleton instance
export const imageOptimizer = new ImageOptimizer();

// Auto-optimize images when DOM is ready
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      imageOptimizer.optimizeAllImages();
    });
  } else {
    imageOptimizer.optimizeAllImages();
  }
}

export default imageOptimizer;
