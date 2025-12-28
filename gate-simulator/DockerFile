FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install

# Копируем код эмулятора
COPY . .

EXPOSE 9999

# Проверка работоспособности
HEALTHCHECK CMD curl -f http://localhost:9999/health || exit 1

CMD ["npm", "start"]
