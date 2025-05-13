FROM docker.io/node:22.14-bookworm-slim

WORKDIR /app

# Copy the Corporate CA certificate to the image
COPY ./cdhb.crt /usr/local/share/ca-certificates/corporate.crt

RUN apt-get update && apt-get install -y ca-certificates \
 && update-ca-certificates \
 && rm -rf /var/lib/apt/lists/*

ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/corporate.crt


COPY ./package.json /app

RUN npm install && npm cache clean --force

ENV PATH=./node_modules/.bin/:$PATH
