// Initialize OpenTelemetry BEFORE any other imports
// require('./otel-setup');

const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

function calculateSipValue(monthlySip, annualRate, years, annualStepUpPercent = 0) {
  const monthlyRate = annualRate / 100 / 12;
  const totalMonths = years * 12;

  let futureValue = 0;
  let totalInvested = 0;

  for (let month = 1; month <= totalMonths; month += 1) {
    const yearIndex = Math.floor((month - 1) / 12);
    const sipAmount = monthlySip * Math.pow(1 + annualStepUpPercent / 100, yearIndex);

    totalInvested += sipAmount;
    futureValue = futureValue * (1 + monthlyRate) + sipAmount;
  }

  return {
    futureValue,
    totalInvested,
    estimatedGains: futureValue - totalInvested,
  };
}

app.get('/api/health', (req, res) => {
  res.json({ ok: true, service: 'sip-calculator-api' });
});

app.get('/api/sip', (req, res) => {
  const monthlyInvestment = Number(req.query.monthlyInvestment);
  const expectedReturn = Number(req.query.expectedReturn);
  const years = Number(req.query.years);
  const annualStepUp = Number(req.query.annualStepUp || 0);

  if (!Number.isFinite(monthlyInvestment) || monthlyInvestment <= 0) {
    return res.status(400).json({ error: 'monthlyInvestment must be a positive number' });
  }

  if (!Number.isFinite(expectedReturn) || expectedReturn < 0) {
    return res.status(400).json({ error: 'expectedReturn must be zero or greater' });
  }

  if (!Number.isFinite(years) || years <= 0) {
    return res.status(400).json({ error: 'years must be a positive number' });
  }

  if (!Number.isFinite(annualStepUp) || annualStepUp < 0) {
    return res.status(400).json({ error: 'annualStepUp must be zero or greater' });
  }

  const result = calculateSipValue(monthlyInvestment, expectedReturn, years, annualStepUp);

  return res.json({
    monthlyInvestment,
    expectedReturn,
    years,
    annualStepUp,
    ...result,
  });
});

app.use(express.static(path.join(__dirname)));

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`SIP calculator server running on http://localhost:${PORT}`);
  });
}

module.exports = {
  app,
  calculateSipValue,
};
