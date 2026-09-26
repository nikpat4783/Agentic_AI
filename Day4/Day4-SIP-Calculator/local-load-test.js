import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const duration = new Trend('duration');
const requestCount = new Counter('requests');

// Export configuration
export const options = {
  thresholds: {
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],
    'http_req_failed': ['rate<0.01'],
    'errors': ['rate<0.01'],
  },
  stages: [
    { duration: '10s', target: 5 },   // Ramp-up
    { duration: '30s', target: 10 },  // Sustained load
    { duration: '15s', target: 5 },   // Ramp-down
    { duration: '5s', target: 0 },    // Cooldown
  ],
};

export default function () {
  group('SIP Calculator Tests', () => {
    const params = {
      headers: {
        'Content-Type': 'application/json',
      },
    };

    // Test 1: Valid SIP calculation request
    group('Valid SIP Calculation', () => {
      const res = http.get(
        'http://10.160.2.228:5000/api/sip?monthlyInvestment=5000&expectedReturn=12&years=10&annualStepUp=5',
        params
      );

      requestCount.add(1);
      duration.add(res.timings.duration);

      const success = check(res, {
        'status is 200': (r) => r.status === 200,
        'response time < 500ms': (r) => r.timings.duration < 500,
        'has futureValue': (r) => r.body.includes('futureValue'),
        'has totalInvested': (r) => r.body.includes('totalInvested'),
        'has estimatedGains': (r) => r.body.includes('estimatedGains'),
      });

      if (!success) {
        errorRate.add(1);
      }
    });

    sleep(1);

    // Test 2: Health check endpoint
    group('Health Check', () => {
      const res = http.get('http://10.160.2.228:5000/api/health', params);

      requestCount.add(1);
      duration.add(res.timings.duration);

      const success = check(res, {
        'status is 200': (r) => r.status === 200,
        'response time < 100ms': (r) => r.timings.duration < 100,
        'service is healthy': (r) => r.body.includes('ok'),
      });

      if (!success) {
        errorRate.add(1);
      }
    });

    sleep(1);

    // Test 3: Invalid parameters (should handle gracefully)
    group('Error Handling', () => {
      const res = http.get(
        'http://10.160.2.228:5000/api/sip?monthlyInvestment=-1000&expectedReturn=12&years=10',
        params
      );

      requestCount.add(1);
      duration.add(res.timings.duration);

      const success = check(res, {
        'status is 400 for invalid input': (r) => r.status === 400,
        'response time < 200ms': (r) => r.timings.duration < 200,
        'error message present': (r) => r.body.includes('error'),
      });

      if (res.status >= 400) {
        // Expected errors don't count against error rate
      } else if (!success) {
        errorRate.add(1);
      }
    });

    sleep(2);
  });
}
