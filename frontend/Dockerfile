FROM node:18-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

# Next.js telemetry disable
ENV NEXT_TELEMETRY_DISABLED 1

# Note: We build Next.js output.
RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]
