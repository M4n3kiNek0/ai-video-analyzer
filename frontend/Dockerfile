FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Expose port 3000
EXPOSE 3000

# Run in development mode, binding to all interfaces
CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0"]
