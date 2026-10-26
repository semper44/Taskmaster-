FROM node:22-slim AS builder

WORKDIR /app
    
COPY package*.json ./
RUN npm ci

COPY . .

RUN npm run build

FROM nginx:alpine

# Removing default nginx HTML files
RUN rm -rf /usr/share/nginx/html/*



# Copying home.html as my index.html (so accessing / works) and home.html. 
# Nginx always looks for "index.html" when someone opens the root URL: e.g., http://localhost/ or http://mywebsite.com/
# Without this, visiting "/" gives a 403 Forbidden error!
COPY --from=builder /app/home.html /usr/share/nginx/html/index.html
# copy home.html as "home.html": If a button, link, or user types the full URL in their browser:
# e.g., http://localhost/home.html. Nginx looks for the exact file "home.html".
COPY --from=builder /app/home.html /usr/share/nginx/html/home.html

# Copy static assets and scripts
COPY --from=builder /app/styles /usr/share/nginx/html/styles
COPY --from=builder /app/js /usr/share/nginx/html/js
COPY --from=builder /app/images /usr/share/nginx/html/images
COPY --from=builder /app/config.js /usr/share/nginx/html/config.js
COPY --from=builder /app/icons.js /usr/share/nginx/html/icons.js

EXPOSE 80

# just for formality sake
CMD ["nginx", "-g", "daemon off;"]
