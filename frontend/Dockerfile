# --- Stage 1: Build the React + Vite Application ---
FROM node:20-alpine AS builder
WORKDIR /app

# Copy ONLY package files first to speed up future builds via caching
COPY package*.json ./
RUN npm install

# Copy all other source files listed in your directory
COPY index.html vite.config.js ./
COPY public/ ./public/
COPY src/ ./src/

# Build the production-ready static files (creates the 'dist' folder)
RUN npm run build

# --- Stage 2: Serve the application with Nginx ---
FROM nginx:alpine

# Vite outputs to 'dist'. We copy it directly into Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
