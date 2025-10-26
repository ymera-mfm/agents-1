/**
 * CRACO Configuration Override
 * Optimize build output and code splitting
 */

const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
const CompressionPlugin = require('compression-webpack-plugin');

module.exports = {
  webpack: {
    configure: (webpackConfig, { env, paths }) => {
      // Production optimizations
      if (env === 'production') {
        // Optimize chunk splitting
        webpackConfig.optimization = {
          ...webpackConfig.optimization,
          splitChunks: {
            chunks: 'all',
            cacheGroups: {
              // Vendor chunks
              vendor: {
                test: /[\\/]node_modules[\\/]/,
                name(module) {
                  // Get the name of the package
                  const packageName = module.context.match(/[\\/]node_modules[\\/](.*?)([\\/]|$)/)[1];
                  // npm package names are URL-safe, but some servers don't like @ symbols
                  return `vendor.${packageName.replace('@', '')}`;
                },
                priority: 10,
              },
              // React and core libraries
              react: {
                test: /[\\/]node_modules[\\/](react|react-dom|react-router-dom)[\\/]/,
                name: 'react-vendor',
                priority: 20,
              },
              // Redux
              redux: {
                test: /[\\/]node_modules[\\/](@reduxjs|react-redux|redux)[\\/]/,
                name: 'redux-vendor',
                priority: 15,
              },
              // UI libraries (heavy)
              ui: {
                test: /[\\/]node_modules[\\/](framer-motion|@headlessui|@heroicons)[\\/]/,
                name: 'ui-vendor',
                priority: 15,
              },
              // 3D libraries (very heavy - should be lazy loaded)
              three: {
                test: /[\\/]node_modules[\\/](three|@react-three)[\\/]/,
                name: 'three-vendor',
                priority: 15,
              },
              // Firebase
              firebase: {
                test: /[\\/]node_modules[\\/](firebase)[\\/]/,
                name: 'firebase-vendor',
                priority: 15,
              },
              // Common chunks
              common: {
                minChunks: 2,
                priority: 5,
                reuseExistingChunk: true,
              },
            },
          },
          // Runtime chunk
          runtimeChunk: {
            name: 'runtime',
          },
        };

        // Add compression plugin
        webpackConfig.plugins.push(
          new CompressionPlugin({
            filename: '[path][base].gz',
            algorithm: 'gzip',
            test: /\.(js|css|html|svg)$/,
            threshold: 8192,
            minRatio: 0.8,
          })
        );

        // Add bundle analyzer in analyze mode
        if (process.env.ANALYZE) {
          webpackConfig.plugins.push(
            new BundleAnalyzerPlugin({
              analyzerMode: 'static',
              reportFilename: 'bundle-report.html',
              openAnalyzer: false,
            })
          );
        }

        // Minimize source maps in production
        webpackConfig.devtool = false;
      }

      return webpackConfig;
    },
  },
  
  babel: {
    plugins: [
      // Remove PropTypes from production build
      process.env.NODE_ENV === 'production' && ['babel-plugin-transform-react-remove-prop-types', { removeImport: true }],
    ].filter(Boolean),
  },
};
