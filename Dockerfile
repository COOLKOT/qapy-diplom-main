FROM eclipse-temurin:21-jdk-jammy

WORKDIR /app

COPY aqa-shop.jar /app/aqa-shop.jar
COPY application.properties /app/application.properties

EXPOSE 8080

CMD ["java", "-Duser.timezone=Europe/Moscow", "-jar", "/app/aqa-shop.jar"]