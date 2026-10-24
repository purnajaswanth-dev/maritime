package com.whereismyferry.backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class BackendApplication {

    public static void main(String[] args) {
        try {
            SpringApplication.run(BackendApplication.class, args);
        } catch (Throwable t) {
            System.err.println("=================================================");
            System.err.println("FATAL APPLICATION STARTUP ERROR:");
            System.err.println(t.getMessage());
            System.err.println("=================================================");
            t.printStackTrace(System.err);
            throw t;
        }
    }
}
