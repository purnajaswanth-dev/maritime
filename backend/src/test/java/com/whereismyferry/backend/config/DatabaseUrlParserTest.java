package com.whereismyferry.backend.config;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class DatabaseUrlParserTest {

    @Test
    void testNeonCloudDatabaseUrl() {
        String neonUrl = "postgresql://neondb_owner:npg_eBcd4ZArnJE2@ep-small-hall-b341yhmj-pooler.c-4.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require";
        DatabaseUrlParser.ParsedDbConfig parsed = DatabaseUrlParser.parse(neonUrl);

        assertNotNull(parsed);
        assertEquals("neondb_owner", parsed.username());
        assertEquals("npg_eBcd4ZArnJE2", parsed.password());
        assertEquals("ep-small-hall-b341yhmj-pooler.c-4.ap-southeast-1.aws.neon.tech", parsed.host());
        assertEquals(5432, parsed.port());
        assertTrue(parsed.jdbcUrl().startsWith("jdbc:postgresql://ep-small-hall-b341yhmj-pooler.c-4.ap-southeast-1.aws.neon.tech:5432/neondb"));
        assertTrue(parsed.jdbcUrl().contains("sslmode=require"));
        assertTrue(parsed.jdbcUrl().contains("channel_binding=require"));
        assertFalse(parsed.jdbcUrl().contains("neondb_owner"));
        assertFalse(parsed.jdbcUrl().contains("npg_eBcd4ZArnJE2"));
    }

    @Test
    void testRenderInternalDatabaseUrl() {
        String renderUrl = "postgres://ferry_user:ferry_pass@dpg-abcdef123456:5432/where_is_my_ferry";
        DatabaseUrlParser.ParsedDbConfig parsed = DatabaseUrlParser.parse(renderUrl);

        assertNotNull(parsed);
        assertEquals("ferry_user", parsed.username());
        assertEquals("ferry_pass", parsed.password());
        assertEquals("dpg-abcdef123456", parsed.host());
        assertEquals(5432, parsed.port());
        assertEquals("jdbc:postgresql://dpg-abcdef123456:5432/where_is_my_ferry", parsed.jdbcUrl());
    }

    @Test
    void testStandardJdbcUrlRemainsClean() {
        String jdbcUrl = "jdbc:postgresql://localhost:5432/where_is_my_ferry";
        DatabaseUrlParser.ParsedDbConfig parsed = DatabaseUrlParser.parse(jdbcUrl);

        assertNotNull(parsed);
        assertEquals("jdbc:postgresql://localhost:5432/where_is_my_ferry", parsed.jdbcUrl());
    }

    @Test
    void testEncodedCredentials() {
        String url = "postgresql://my%40user:p%23ss%24word@ep-test.aws.neon.tech/neondb";
        DatabaseUrlParser.ParsedDbConfig parsed = DatabaseUrlParser.parse(url);

        assertNotNull(parsed);
        assertEquals("my@user", parsed.username());
        assertEquals("p#ss$word", parsed.password());
        assertEquals("ep-test.aws.neon.tech", parsed.host());
        assertTrue(parsed.jdbcUrl().endsWith("?sslmode=require"));
    }

    @Test
    void testNullAndEmptyInput() {
        assertNull(DatabaseUrlParser.parse(null));
        assertNull(DatabaseUrlParser.parse("   "));
    }
}
