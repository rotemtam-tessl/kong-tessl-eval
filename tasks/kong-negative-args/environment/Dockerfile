FROM golang:1.23-alpine

WORKDIR /workspace

# Install git for go mod download
RUN apk add --no-cache git bash

# Copy go module files first for caching
COPY go.mod go.sum ./
RUN go mod download

# Copy source files
COPY main.go main_test.go ./

# Verify the setup compiles
RUN go build -o /dev/null . || true

