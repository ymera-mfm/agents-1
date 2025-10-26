#!/usr/bin/env node

/**
 * PWA Initialization Script
 * Sets up Progressive Web App functionality
 */

const fs = require('fs');
const path = require('path');

console.log('🌐 Initializing PWA...\n');

// Check if service worker exists
const swPath = path.join(__dirname, '..', 'public', 'service-worker.js');
if (!fs.existsSync(swPath)) {
  console.error('❌ Error: service-worker.js not found in public directory');
  process.exit(1);
}

// Check if manifest exists
const manifestPath = path.join(__dirname, '..', 'public', 'manifest.json');
if (!fs.existsSync(manifestPath)) {
  console.error('❌ Error: manifest.json not found in public directory');
  process.exit(1);
}

// Create service worker registration code
const registrationCode = `
// Service Worker Registration
if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/service-worker.js')
      .then((registration) => {
        console.log('✅ Service Worker registered successfully:', registration.scope);
        
        // Check for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New service worker available
              if (window.confirm('New version available! Reload to update?')) {
                window.location.reload();
              }
            }
          });
        });
      })
      .catch((error) => {
        console.error('❌ Service Worker registration failed:', error);
      });
  });
}
`;

console.log('✅ Service Worker found');
console.log('✅ Manifest found');
console.log('\n📝 Service Worker Registration Code:');
console.log('-----------------------------------');
console.log(registrationCode);
console.log('\n💡 To enable PWA:');
console.log('   Add the above code to src/index.js');
console.log('\n✨ PWA initialization complete!\n');
