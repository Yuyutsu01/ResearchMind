# Use Node 22 Alpine to support modern Vite 8+ requirements (e.g. CustomEvent API)
FROM node:22-alpine

WORKDIR /app

# Copy package.json and lock file
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the project
COPY . .

# Build the Vite project (optional if we just want to run dev server, 
# but best practice for production is to build and serve)
RUN npm run build

# Install a simple static file server to serve the built files
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Serve the 'dist' directory
CMD ["serve", "-s", "dist", "-l", "3000"]
