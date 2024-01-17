FROM node:latest

WORKDIR /MockFTPService
COPY FileSystem/ ./FileSystem
COPY index.js ./
COPY package.json ./

RUN npm install
CMD ["npm", "start"]