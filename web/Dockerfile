FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_API_BASE_URL=http://127.0.0.1:8001
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

EXPOSE 5174

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5174"]
