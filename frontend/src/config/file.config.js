// File Management Configuration
// Comprehensive configuration for file storage, uploads, downloads, and processing

import env from './env';

export const fileConfig = {
  // Storage Configuration
  storage: {
    provider: env.isProduction ? 's3' : 'local', // 's3', 'local', 'azure', 'gcs'
    
    local: {
      enabled: !env.isProduction,
      basePath: '/uploads',
      maxSize: 1073741824, // 1GB
      tempDir: '/tmp/uploads',
      cleanupInterval: 3600000, // 1 hour
    },

    s3: {
      enabled: env.isProduction,
      bucket: process.env.REACT_APP_S3_BUCKET || 'agentflow-files',
      region: process.env.REACT_APP_S3_REGION || 'us-east-1',
      accessKeyId: process.env.REACT_APP_S3_ACCESS_KEY,
      secretAccessKey: process.env.REACT_APP_S3_SECRET_KEY,
      acl: 'private',
      encryption: 'AES256',
      versioning: true,
    },

    azure: {
      enabled: false,
      account: process.env.REACT_APP_AZURE_ACCOUNT,
      key: process.env.REACT_APP_AZURE_KEY,
      container: 'agentflow-files',
    },

    gcs: {
      enabled: false,
      bucket: process.env.REACT_APP_GCS_BUCKET,
      projectId: process.env.REACT_APP_GCS_PROJECT_ID,
      keyFilename: process.env.REACT_APP_GCS_KEY_FILE,
    },

    cdn: {
      enabled: env.isProduction,
      url: process.env.REACT_APP_CDN_URL || '',
      caching: true,
      cacheDuration: 31536000, // 1 year
    },
  },

  // Upload Configuration
  upload: {
    enabled: true,
    
    limits: {
      maxFileSize: 52428800, // 50MB
      maxTotalSize: 524288000, // 500MB per upload session
      maxFiles: 10, // per upload
      maxConcurrent: 3, // concurrent uploads
    },

    allowedTypes: {
      images: {
        enabled: true,
        types: ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'],
        maxSize: 10485760, // 10MB
      },
      documents: {
        enabled: true,
        types: [
          'application/pdf',
          'application/msword',
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          'application/vnd.ms-excel',
          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          'application/vnd.ms-powerpoint',
          'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        ],
        maxSize: 52428800, // 50MB
      },
      code: {
        enabled: true,
        types: [
          'text/plain',
          'text/javascript',
          'text/typescript',
          'text/python',
          'text/html',
          'text/css',
          'text/markdown',
          'application/json',
          'application/xml',
        ],
        maxSize: 10485760, // 10MB
      },
      archives: {
        enabled: true,
        types: [
          'application/zip',
          'application/x-tar',
          'application/gzip',
          'application/x-7z-compressed',
        ],
        maxSize: 104857600, // 100MB
      },
      media: {
        enabled: true,
        types: [
          'audio/mpeg',
          'audio/wav',
          'audio/ogg',
          'video/mp4',
          'video/webm',
          'video/ogg',
        ],
        maxSize: 104857600, // 100MB
      },
    },

    validation: {
      enabled: true,
      checkMimeType: true,
      checkExtension: true,
      checkMagicBytes: env.isProduction,
      scanVirus: env.isProduction,
    },

    chunking: {
      enabled: true,
      chunkSize: 5242880, // 5MB
      parallel: true,
      maxRetries: 3,
    },

    resumable: {
      enabled: true,
      expiry: 86400000, // 24 hours
      cleanup: true,
    },

    metadata: {
      extract: true,
      store: true,
      fields: [
        'filename',
        'size',
        'mimeType',
        'extension',
        'uploadedBy',
        'uploadedAt',
        'checksum',
      ],
    },

    security: {
      sanitizeFilename: true,
      checksum: 'sha256',
      encryption: env.httpsOnly,
      virusScanning: env.isProduction,
    },

    notifications: {
      enabled: true,
      onProgress: true,
      onComplete: true,
      onError: true,
    },
  },

  // Download Configuration
  download: {
    enabled: true,
    
    streaming: {
      enabled: true,
      bufferSize: 1048576, // 1MB
    },

    caching: {
      enabled: true,
      ttl: 3600000, // 1 hour
      maxSize: 104857600, // 100MB
    },

    rateLimit: {
      enabled: env.isProduction,
      maxDownloads: 100,
      windowMs: 3600000, // 1 hour
      maxBandwidth: 104857600, // 100MB per hour
    },

    authorization: {
      required: true,
      checkOwnership: true,
      checkPermissions: true,
    },

    tracking: {
      enabled: env.analyticsEnabled,
      metrics: ['download_count', 'bandwidth_used', 'response_time'],
    },

    urls: {
      expiry: 3600000, // 1 hour
      signed: env.isProduction,
    },
  },

  // Processing Configuration
  processing: {
    enabled: true,

    images: {
      enabled: true,
      
      resize: {
        enabled: true,
        sizes: [
          { name: 'thumbnail', width: 150, height: 150 },
          { name: 'small', width: 400, height: 400 },
          { name: 'medium', width: 800, height: 800 },
          { name: 'large', width: 1600, height: 1600 },
        ],
        quality: 85,
        format: 'webp',
      },

      optimization: {
        enabled: env.isProduction,
        quality: 85,
        progressive: true,
        stripMetadata: true,
      },

      watermark: {
        enabled: false,
        text: 'AgentFlow',
        position: 'bottom-right',
        opacity: 0.5,
      },
    },

    documents: {
      enabled: true,
      
      preview: {
        enabled: true,
        generateThumbnail: true,
        extractText: true,
        maxPages: 10,
      },

      conversion: {
        enabled: false,
        formats: ['pdf', 'html'],
      },
    },

    video: {
      enabled: false,
      
      thumbnails: {
        enabled: true,
        count: 3,
        width: 640,
        height: 360,
      },

      transcoding: {
        enabled: false,
        formats: ['mp4', 'webm'],
        quality: 'medium',
      },
    },

    async: {
      enabled: true,
      queue: 'file-processing',
      priority: 'low',
      timeout: 300000, // 5 minutes
    },
  },

  // Organization
  organization: {
    folders: {
      enabled: true,
      maxDepth: 5,
      defaults: [
        { name: 'Uploads', path: '/uploads', shared: false },
        { name: 'Projects', path: '/projects', shared: true },
        { name: 'Agents', path: '/agents', shared: false },
        { name: 'Documents', path: '/documents', shared: false },
        { name: 'Media', path: '/media', shared: false },
      ],
    },

    tagging: {
      enabled: true,
      maxTags: 10,
      autoTag: true,
    },

    search: {
      enabled: true,
      indexing: true,
      fuzzySearch: true,
      filters: ['name', 'type', 'size', 'date', 'tags', 'owner'],
    },

    sorting: {
      defaultBy: 'uploadedAt',
      defaultOrder: 'desc',
      options: ['name', 'size', 'type', 'uploadedAt', 'updatedAt'],
    },
  },

  // Sharing & Permissions
  sharing: {
    enabled: true,
    
    links: {
      enabled: true,
      expiry: true,
      defaultExpiry: 604800000, // 7 days
      maxExpiry: 2592000000, // 30 days
      password: true,
      downloadLimit: true,
    },

    permissions: {
      levels: ['view', 'download', 'edit', 'delete', 'share'],
      defaultLevel: 'view',
      inheritance: true,
    },

    collaboration: {
      enabled: env.enableRealTimeCollaboration,
      simultaneousEditors: 10,
      lockOnEdit: false,
      versionHistory: true,
    },
  },

  // Versioning
  versioning: {
    enabled: true,
    maxVersions: 10,
    autoVersion: true,
    compression: true,
    retention: 2592000000, // 30 days
  },

  // Backup & Recovery
  backup: {
    enabled: env.isProduction,
    frequency: 'daily', // 'hourly', 'daily', 'weekly'
    retention: 30, // days
    encryption: true,
    verification: true,
  },

  // Cleanup & Maintenance
  cleanup: {
    enabled: true,
    
    orphanedFiles: {
      enabled: true,
      checkInterval: 86400000, // 24 hours
      gracePeriod: 604800000, // 7 days
    },

    tempFiles: {
      enabled: true,
      maxAge: 3600000, // 1 hour
      checkInterval: 1800000, // 30 minutes
    },

    deletedFiles: {
      enabled: true,
      softDelete: true,
      retention: 2592000000, // 30 days
      permanentDeleteAfter: true,
    },

    oldVersions: {
      enabled: true,
      keepRecent: 5,
      deleteOlderThan: 5184000000, // 60 days
    },
  },

  // Monitoring & Analytics
  monitoring: {
    enabled: true,
    
    metrics: [
      'total_files',
      'total_size',
      'upload_count',
      'download_count',
      'storage_used',
      'bandwidth_used',
      'processing_time',
    ],

    alerts: {
      storageLimit: {
        threshold: 0.9, // 90%
        action: 'notify_admin',
      },
      uploadFailureRate: {
        threshold: 0.1, // 10%
        action: 'investigate',
      },
      slowProcessing: {
        threshold: 60000, // 1 minute
        action: 'scale_workers',
      },
    },

    logging: {
      enabled: true,
      level: env.logLevel,
      includeMetadata: true,
    },
  },

  // Integration
  integration: {
    agents: {
      enabled: true,
      allowUpload: true,
      allowDownload: true,
      maxSize: 52428800, // 50MB
    },

    projects: {
      enabled: true,
      autoAttach: true,
      maxFilesPerProject: 100,
    },

    chat: {
      enabled: env.enableRealTimeCollaboration,
      inlinePreview: true,
      maxSizeInline: 10485760, // 10MB
    },

    api: {
      enabled: true,
      endpoints: {
        upload: '/api/v1/files/upload',
        download: '/api/v1/files/:id/download',
        list: '/api/v1/files',
        metadata: '/api/v1/files/:id/metadata',
        delete: '/api/v1/files/:id',
        share: '/api/v1/files/:id/share',
      },
    },
  },

  // UI Configuration
  ui: {
    dragAndDrop: {
      enabled: true,
      overlay: true,
      multipleFiles: true,
    },

    preview: {
      enabled: true,
      types: ['image', 'pdf', 'text', 'video', 'audio'],
      modal: true,
    },

    uploader: {
      showProgress: true,
      showSpeed: true,
      showETA: true,
      allowCancel: true,
      allowRetry: true,
    },

    browser: {
      layout: 'grid', // 'grid', 'list'
      showThumbnails: true,
      showDetails: true,
      compactMode: false,
    },
  },

  // Development & Testing
  development: {
    mockUploads: env.mockApi,
    verboseLogging: env.debugMode,
    simulateProgress: false,
    simulateErrors: false,
    bypassValidation: false,
  },
};

// Helper functions
export const isFileTypeAllowed = (mimeType) => {
  const allTypes = Object.values(fileConfig.upload.allowedTypes)
    .filter(category => category.enabled)
    .flatMap(category => category.types);
  
  return allTypes.includes(mimeType);
};

export const getMaxFileSizeForType = (mimeType) => {
  for (const category of Object.values(fileConfig.upload.allowedTypes)) {
    if (category.enabled && category.types.includes(mimeType)) {
      return category.maxSize;
    }
  }
  return fileConfig.upload.limits.maxFileSize;
};

export const canUploadFile = (file) => {
  return (
    isFileTypeAllowed(file.type) &&
    file.size <= getMaxFileSizeForType(file.type)
  );
};

export default fileConfig;
