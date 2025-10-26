/**
 * Bundle Analyzer Utility
 * Helps analyze and optimize bundle sizes
 */

import { PERFORMANCE_CONFIG } from '../../config/performance.config';

class BundleAnalyzer {
  constructor() {
    this.chunks = new Map();
    this.warnings = [];
  }

  /**
   * Analyze loaded chunks
   */
  analyzeChunks() {
    const resources = performance.getEntriesByType('resource');
    const scripts = resources.filter((r) => r.initiatorType === 'script');

    scripts.forEach((script) => {
      const size = script.transferSize || script.decodedBodySize || 0;
      const name = this.extractChunkName(script.name);

      this.chunks.set(name, {
        name,
        url: script.name,
        size,
        compressed: script.transferSize,
        uncompressed: script.decodedBodySize,
        duration: script.duration,
        cached: script.transferSize === 0,
      });

      // Check against thresholds
      if (size > PERFORMANCE_CONFIG.bundle.chunkSizeWarning) {
        this.warnings.push({
          type: 'large-chunk',
          chunk: name,
          size,
          threshold: PERFORMANCE_CONFIG.bundle.chunkSizeWarning,
        });
      }
    });

    return this.getAnalysis();
  }

  /**
   * Extract chunk name from URL
   */
  extractChunkName(url) {
    const match = url.match(/\/static\/js\/(.+?)\.chunk\.js/);
    return match ? match[1] : 'main';
  }

  /**
   * Get bundle analysis
   */
  getAnalysis() {
    const chunks = Array.from(this.chunks.values());
    const totalSize = chunks.reduce((sum, chunk) => sum + chunk.size, 0);
    const totalUncompressed = chunks.reduce((sum, chunk) => sum + chunk.uncompressed, 0);

    return {
      chunks,
      totalSize,
      totalUncompressed,
      compressionRatio: totalUncompressed > 0 ? totalSize / totalUncompressed : 1,
      warnings: this.warnings,
      recommendations: this.getRecommendations(),
    };
  }

  /**
   * Get optimization recommendations
   */
  getRecommendations() {
    const recommendations = [];
    const analysis = this.getAnalysis();

    // Check total bundle size
    if (analysis.totalSize > PERFORMANCE_CONFIG.budgets.resources.totalSize) {
      recommendations.push({
        priority: 'high',
        type: 'bundle-size',
        message: `Total bundle size (${this.formatBytes(analysis.totalSize)}) exceeds budget`,
        suggestion: 'Consider code splitting, lazy loading, or removing unused dependencies',
      });
    }

    // Check compression
    if (analysis.compressionRatio > 0.5) {
      recommendations.push({
        priority: 'medium',
        type: 'compression',
        message: 'Compression ratio could be improved',
        suggestion: 'Enable gzip or brotli compression on your server',
      });
    }

    // Check for large chunks
    this.warnings.forEach((warning) => {
      if (warning.type === 'large-chunk') {
        recommendations.push({
          priority: 'medium',
          type: 'large-chunk',
          message: `Chunk "${warning.chunk}" is large (${this.formatBytes(warning.size)})`,
          suggestion: 'Split this chunk into smaller pieces or lazy load it',
        });
      }
    });

    return recommendations;
  }

  /**
   * Format bytes to human readable
   */
  formatBytes(bytes) {
    if (bytes === 0) {
      return '0 Bytes';
    }
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Generate report
   */
  generateReport() {
    const analysis = this.analyzeChunks();

    if (process.env.NODE_ENV === 'development') {
      /* eslint-disable no-console */
      console.group('📦 Bundle Analysis Report');
      console.log(`Total Size: ${this.formatBytes(analysis.totalSize)}`);
      console.log(`Total Uncompressed: ${this.formatBytes(analysis.totalUncompressed)}`);
      console.log(`Compression Ratio: ${(analysis.compressionRatio * 100).toFixed(2)}%`);
      console.log(`Chunks: ${analysis.chunks.length}`);

      if (analysis.warnings.length > 0) {
        console.group('⚠️ Warnings');
        analysis.warnings.forEach((warning) => {
          console.warn(warning);
        });
        console.groupEnd();
      }

      if (analysis.recommendations.length > 0) {
        console.group('💡 Recommendations');
        analysis.recommendations.forEach((rec) => {
          console.log(`[${rec.priority.toUpperCase()}] ${rec.message}`);
          console.log(`  → ${rec.suggestion}`);
        });
        console.groupEnd();
      }

      console.groupEnd();
      /* eslint-enable no-console */
    }

    return analysis;
  }
}

// Create singleton instance
export const bundleAnalyzer = new BundleAnalyzer();

// Auto-analyze in development after page load
if (process.env.NODE_ENV === 'development') {
  window.addEventListener('load', () => {
    setTimeout(() => {
      bundleAnalyzer.generateReport();
    }, 1000);
  });
}

export default bundleAnalyzer;
