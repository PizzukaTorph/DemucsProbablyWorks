FROM node:20-slim

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Use official registry and upgrade npm; then install deps (prefer npm ci if lockfile present)
RUN npm config set registry https://registry.npmjs.org/ \
 && npm install -g npm@11.7.0 \
 && if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi

# Copy app sources
COPY . .

EXPOSE 3000

CMD ["node", "server.js"]