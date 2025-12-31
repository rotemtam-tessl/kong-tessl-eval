FROM golang:1.23-alpine

WORKDIR /workspace

# Install dependencies
RUN apk add --no-cache git bash nodejs npm

# Install Tessl CLI globally (for agent to use tessl commands if needed)
RUN npm install -g @tessl/cli

# Copy everything (tessl tiles, go files, configs)
COPY . .

# Download go modules
RUN go mod download
