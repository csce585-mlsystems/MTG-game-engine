# Use Node.js 18 Alpine image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Set build-time environment variable
ARG REACT_APP_API_URL=http://localhost:8000
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Build the application
RUN npm run build

# Install serve to run the production build
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Command to serve the production build
CMD ["sh", "-c", "echo 'MTG Game Engine Frontend starting...' && echo 'Frontend available at: http://localhost:3000' && echo 'Backend API: http://localhost:8000' && echo 'Starting React application...' && serve -s build -l 3000"]
