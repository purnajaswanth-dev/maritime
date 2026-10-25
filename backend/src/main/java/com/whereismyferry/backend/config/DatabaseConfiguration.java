package com.whereismyferry.backend.config;

import com.zaxxer.hikari.HikariDataSource;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.BeansException;
import org.springframework.beans.factory.config.BeanPostProcessor;
import org.springframework.boot.autoconfigure.jdbc.DataSourceProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.env.Environment;

/**
 * Ensures DataSourceProperties and HikariDataSource are configured with valid JDBC URLs
 * even if cloud providers pass postgresql:// or postgres:// connection strings via DATABASE_URL.
 */
@Configuration(proxyBeanMethods = false)
public class DatabaseConfiguration {

    private static final Logger log = LoggerFactory.getLogger(DatabaseConfiguration.class);

    @Bean
    public static BeanPostProcessor databasePropertiesPostProcessor(Environment environment) {
        return new BeanPostProcessor() {
            @Override
            public Object postProcessBeforeInitialization(Object bean, String beanName) throws BeansException {
                if (bean instanceof DataSourceProperties props) {
                    configureDataSourceProperties(props, environment);
                } else if (bean instanceof HikariDataSource hikari) {
                    configureHikariDataSource(hikari, environment);
                }
                return bean;
            }
        };
    }

    private static void configureDataSourceProperties(DataSourceProperties props, Environment env) {
        String dbUrl = env.getProperty("DATABASE_URL");
        String currentUrl = props.getUrl();

        // 1. If DATABASE_URL is present, or current URL contains user credentials or raw protocol
        String candidateUrl = (dbUrl != null && !dbUrl.isBlank()) ? dbUrl : currentUrl;
        if (candidateUrl != null && (candidateUrl.contains("@")
                || candidateUrl.startsWith("postgres://")
                || (candidateUrl.startsWith("postgresql://") && !candidateUrl.startsWith("jdbc:postgresql://")))) {

            DatabaseUrlParser.ParsedDbConfig parsed = DatabaseUrlParser.parse(candidateUrl);
            if (parsed != null && parsed.jdbcUrl() != null) {
                log.info("DatabaseConfiguration: Sanitized datasource URL to JDBC format: {}",
                        parsed.jdbcUrl().replaceAll(":[^/@]+@", ":***@"));

                props.setUrl(parsed.jdbcUrl());
                if (parsed.username() != null && !parsed.username().isBlank()) {
                    props.setUsername(parsed.username());
                }
                if (parsed.password() != null && !parsed.password().isBlank()) {
                    props.setPassword(parsed.password());
                }
                props.setDriverClassName("org.postgresql.Driver");
            }
        }
    }

    private static void configureHikariDataSource(HikariDataSource hikari, Environment env) {
        String currentJdbcUrl = hikari.getJdbcUrl();
        if (currentJdbcUrl != null && (currentJdbcUrl.contains("@")
                || currentJdbcUrl.startsWith("postgres://")
                || (currentJdbcUrl.startsWith("postgresql://") && !currentJdbcUrl.startsWith("jdbc:postgresql://")))) {

            DatabaseUrlParser.ParsedDbConfig parsed = DatabaseUrlParser.parse(currentJdbcUrl);
            if (parsed != null && parsed.jdbcUrl() != null) {
                log.info("DatabaseConfiguration: Corrected HikariDataSource URL to: {}",
                        parsed.jdbcUrl().replaceAll(":[^/@]+@", ":***@"));

                hikari.setJdbcUrl(parsed.jdbcUrl());
                if (parsed.username() != null && !parsed.username().isBlank()) {
                    hikari.setUsername(parsed.username());
                }
                if (parsed.password() != null && !parsed.password().isBlank()) {
                    hikari.setPassword(parsed.password());
                }
            }
        }
    }
}
