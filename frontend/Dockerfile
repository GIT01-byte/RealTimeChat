FROM node:alpine as build

ARG VITE_GW_URL
ARG VITE_WS_URL
ENV VITE_GW_URL=$VITE_GW_URL
ENV VITE_WS_URL=$VITE_WS_URL

COPY package.json package.json
RUN npm install
COPY . .
RUN npm run build

FROM nginx:stable-alpine

COPY --from=build /dist /usr/share/nginx/html
COPY --from=build nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD [ "nginx", "-g", "daemon off;" ]