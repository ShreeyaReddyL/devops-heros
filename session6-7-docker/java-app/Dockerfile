FROM eclipse-temurin:17-jdk-alpine AS build
WORKDIR /app
COPY HelloServer.java .
RUN javac HelloServer.java

FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=build /app/HelloServer.class .
EXPOSE 8080
CMD ["java", "HelloServer"]
