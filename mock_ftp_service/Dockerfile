FROM node:latest

WORKDIR /mock_ftp_service
COPY FileSystem/ ./FileSystem
COPY index.js ./
COPY package.json ./

RUN npm install
CMD ["npm", "start"]