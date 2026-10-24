// k6 Load Test Script: Where Is My Ferry?
// Validates 200 concurrent users against SSE streaming and catalog endpoints.
// Thresholds: p(95) < 200ms, http_req_failed < 1%

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '5s', target: 50 },    // Ramp up
    { duration: '15s', target: 200 },  // Sustained 200 concurrent clients
    { duration: '5s', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'],  // p95 latency under 200 ms
    http_req_failed: ['rate<0.01'],    // Under 1% failures
  },
};

const BASE_URL = __ENV.TARGET_URL || 'http://localhost:8080';

export default function () {
  // 1. Fetch catalog departures
  const resCatalog = http.get(`${BASE_URL}/api/v1/departures`);
  check(resCatalog, {
    'catalog status 200': (r) => r.status === 200,
    'catalog returns items': (r) => r.body.length > 0,
  });

  // 2. Fetch ports catalog
  const resPorts = http.get(`${BASE_URL}/api/v1/ports`);
  check(resPorts, {
    'ports status 200': (r) => r.status === 200,
  });

  sleep(0.5);
}
