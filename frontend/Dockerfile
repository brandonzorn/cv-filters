FROM node:26-alpine AS build-stage

COPY . .

ARG VITE_API_BASE
ENV VITE_API_BASE=$VITE_API_BASE

RUN npm install
RUN npm run build

FROM nginx:alpine AS production-stage

COPY --from=build-stage /dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]