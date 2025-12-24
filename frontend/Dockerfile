FROM node:20-slim

WORKDIR /app

# Install build dependencies for native modules
RUN apt-get update && apt-get install -y \
    python3 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first for better caching
COPY package*.json ./
RUN npm install

# Rebuild native modules for this platform
RUN npm rebuild lightningcss || true

COPY . .

# Expose port 3000
EXPOSE 3000

# Run in development mode, binding to all interfaces
CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0"]
