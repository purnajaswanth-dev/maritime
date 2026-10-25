# Multi-stage Dockerfile for Where Is My Ferry? Full Stack (React + Spring Boot)
# Bundles the React frontend into the Spring Boot backend JAR so the entire website
# and REST API are served together from a single deployed URL.

# Stage 1: Build React 19 Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci || npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Build Spring Boot Backend with Built Frontend Assets
FROM maven:3.9.6-eclipse-temurin-17 AS backend-builder
WORKDIR /app
COPY backend/pom.xml .
RUN mvn dependency:resolve -B || true
COPY backend/src ./src
# Copy built frontend assets into Spring Boot's static directory
COPY --from=frontend-builder /app/frontend/dist/ ./src/main/resources/static/
RUN mvn clean package -DskipTests

# Stage 3: Runtime
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
RUN apk add --no-cache curl
COPY --from=backend-builder /app/target/*.jar app.jar

ENV PORT=8080
EXPOSE 8080
ENTRYPOINT ["java", "-XX:+UseContainerSupport", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]
