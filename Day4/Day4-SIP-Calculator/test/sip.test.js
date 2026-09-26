const test = require('node:test');
const assert = require('node:assert/strict');
const { calculateSipValue } = require('../server.js');

test('calculateSipValue returns expected growth for a standard SIP', () => {
  const result = calculateSipValue(5000, 12, 10, 0);

  assert.ok(result.futureValue > result.totalInvested, 'future value should exceed invested amount');
  assert.equal(Math.round(result.totalInvested), 600000);
  assert.ok(result.estimatedGains > 0, 'gains should be positive');
});

test('calculateSipValue supports annual step-up contributions', () => {
  const result = calculateSipValue(5000, 12, 10, 5);

  assert.ok(result.futureValue > 0, 'future value should be positive');
  assert.ok(result.totalInvested > 600000, 'yearly step-up should increase total invested amount');
  assert.ok(result.estimatedGains > 0, 'step-up gains should remain positive');
});
