package com.whereismyferry.backend.security;

import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

@Component
public class AuthRateLimiter {

    private static final int MAX_REQUESTS_PER_MINUTE = 100;
    private final Map<String, RequestBucket> buckets = new ConcurrentHashMap<>();

    public void reset() {
        buckets.clear();
    }

    public boolean allowRequest(String clientIp) {
        if (clientIp == null || clientIp.isBlank()) {
            return true;
        }

        long currentWindow = Instant.now().getEpochSecond() / 60;
        RequestBucket bucket = buckets.compute(clientIp, (key, existing) -> {
            if (existing == null || existing.window != currentWindow) {
                return new RequestBucket(currentWindow, new AtomicInteger(1));
            }
            existing.count.incrementAndGet();
            return existing;
        });

        return bucket.count.get() <= MAX_REQUESTS_PER_MINUTE;
    }

    private static class RequestBucket {
        final long window;
        final AtomicInteger count;

        RequestBucket(long window, AtomicInteger count) {
            this.window = window;
            this.count = count;
        }
    }
}
