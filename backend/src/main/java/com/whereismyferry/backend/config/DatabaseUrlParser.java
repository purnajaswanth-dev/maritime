package com.whereismyferry.backend.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Robust database URL parser supporting cloud deployment formats (Render, Neon, Supabase, Heroku, Railway).
 * Converts postgres:// or postgresql:// URIs into valid JDBC URLs (jdbc:postgresql://...) and extracts
 * embedded username/password credentials.
 */
public final class DatabaseUrlParser {

    private static final Logger log = LoggerFactory.getLogger(DatabaseUrlParser.class);

    // Regex fallback: [protocol://][user[:pass]@]host[:port][/path][?query]
    private static final Pattern URL_PATTERN = Pattern.compile(
            "^(?:(?:jdbc:)?(?:postgresql|postgres)://)?(?:([^:@/]+)(?::([^@/]*))?@)?([^:/?#]+)(?::(\\d+))?(?:/([^?#]*))?(?:\\?(.*))?$"
    );

    public record ParsedDbConfig(String jdbcUrl, String username, String password, String host, int port) {
    }

    private DatabaseUrlParser() {
    }

    /**
     * Parses any database connection string or JDBC URL into a clean JDBC URL and credentials.
     *
     * @param rawUrl The raw URL (e.g. from DATABASE_URL or SPRING_DATASOURCE_URL)
     * @return ParsedDbConfig with clean JDBC URL and credentials
     */
    public static ParsedDbConfig parse(String rawUrl) {
        if (rawUrl == null || rawUrl.isBlank()) {
            return null;
        }

        String input = rawUrl.trim();

        // 1. Try URI parsing first
        try {
            String uriStr = input;
            if (uriStr.startsWith("jdbc:postgresql://")) {
                uriStr = "postgresql://" + uriStr.substring("jdbc:postgresql://".length());
            } else if (uriStr.startsWith("postgres://")) {
                uriStr = "postgresql://" + uriStr.substring("postgres://".length());
            } else if (!uriStr.startsWith("postgresql://")) {
                uriStr = "postgresql://" + uriStr;
            }

            URI uri = new URI(uriStr);
            String host = uri.getHost();
            if (host != null && !host.isBlank()) {
                String userInfo = uri.getUserInfo();
                String username = null;
                String password = null;

                if (userInfo != null && !userInfo.isBlank()) {
                    int colonIdx = userInfo.indexOf(':');
                    if (colonIdx >= 0) {
                        username = decode(userInfo.substring(0, colonIdx));
                        password = decode(userInfo.substring(colonIdx + 1));
                    } else {
                        username = decode(userInfo);
                    }
                }

                int port = uri.getPort() == -1 ? 5432 : uri.getPort();
                String path = uri.getPath();
                if (path == null || path.isBlank()) {
                    path = "";
                }
                String query = uri.getQuery();

                String cleanJdbcUrl = buildJdbcUrl(host, port, path, query);
                return new ParsedDbConfig(cleanJdbcUrl, username, password, host, port);
            }
        } catch (Exception e) {
            log.debug("Standard URI parser failed for URL, falling back to regex: {}", e.getMessage());
        }

        // 2. Fallback to Regex Parser
        Matcher matcher = URL_PATTERN.matcher(input);
        if (matcher.matches()) {
            String username = matcher.group(1) != null ? decode(matcher.group(1)) : null;
            String password = matcher.group(2) != null ? decode(matcher.group(2)) : null;
            String host = matcher.group(3);
            String portStr = matcher.group(4);
            int port = (portStr != null && !portStr.isBlank()) ? Integer.parseInt(portStr) : 5432;
            String path = matcher.group(5) != null ? "/" + matcher.group(5) : "";
            String query = matcher.group(6);

            if (host != null && !host.isBlank()) {
                String cleanJdbcUrl = buildJdbcUrl(host, port, path, query);
                return new ParsedDbConfig(cleanJdbcUrl, username, password, host, port);
            }
        }

        // 3. If already starts with jdbc:postgresql:// and has no credentials embedded, return as is
        if (input.startsWith("jdbc:postgresql://") && !input.contains("@")) {
            return new ParsedDbConfig(input, null, null, null, 5432);
        }

        // Default safety prefix
        String fallback = input.startsWith("jdbc:") ? input : "jdbc:" + input;
        return new ParsedDbConfig(fallback, null, null, null, 5432);
    }

    private static String buildJdbcUrl(String host, int port, String path, String query) {
        StringBuilder sb = new StringBuilder("jdbc:postgresql://")
                .append(host)
                .append(":")
                .append(port)
                .append(path.startsWith("/") ? path : "/" + path);

        if (query != null && !query.isBlank()) {
            sb.append("?").append(query);
        } else if (!isLocalOrInternal(host)) {
            sb.append("?sslmode=require");
        }

        return sb.toString();
    }

    private static boolean isLocalOrInternal(String host) {
        if (host == null) return true;
        String lower = host.toLowerCase();
        return lower.equals("localhost")
                || lower.equals("127.0.0.1")
                || lower.equals("postgres")
                || lower.startsWith("dpg-")
                || lower.endsWith(".internal");
    }

    private static String decode(String val) {
        if (val == null) return null;
        try {
            return URLDecoder.decode(val, StandardCharsets.UTF_8);
        } catch (Exception e) {
            return val;
        }
    }
}
