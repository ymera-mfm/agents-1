# Multi-stage Docker build for AgentFlow

# Stage 1: Build the application
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production --silent

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Production server
FROM nginx:alpine AS production

# Install security updates
RUN apk update && apk upgrade && apk add --no-cache \
    curl \
    && rm -rf /var/cache/apk/*

# Copy built application
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY --from=builder /app/build/nginx.conf /etc/nginx/conf.d/default.conf

# Copy custom nginx config for SPA
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    # Security headers \
    add_header X-Content-Type-Options nosniff; \
    add_header X-Frame-Options DENY; \
    add_header X-XSS-Protection "1; mode=block"; \
    add_header Referrer-Policy "strict-origin-when-cross-origin"; \
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()"; \
    \
    # Compression \
    gzip on; \
    gzip_vary on; \
    gzip_min_length 1024; \
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json; \
    \
    # Cache control \
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ { \
        expires 1y; \
        add_header Cache-Control "public, immutable"; \
    } \
    \
    # SPA routing \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    \
    # Health check endpoint \
    location /health { \
        access_log off; \
        return 200 "healthy\\n"; \
        add_header Content-Type text/plain; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S agentflow -u 1001

# Set ownership
RUN chown -R agentflow:nodejs /usr/share/nginx/html && \
    chown -R agentflow:nodejs /var/cache/nginx && \
    chown -R agentflow:nodejs /var/log/nginx && \
    chown -R agentflow:nodejs /etc/nginx/conf.d

# Switch to non-root user
USER agentflow

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
