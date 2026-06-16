FROM node:26-alpine AS build-stage

COPY . .

RUN npm install
RUN npm run build

FROM nginx:alpine AS production-stage

COPY --from=build-stage /dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]