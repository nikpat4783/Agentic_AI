const form = document.getElementById('sip-form');
const resetBtn = document.getElementById('reset-btn');

const monthlyInvestmentInput = document.getElementById('monthly-investment');
const expectedReturnInput = document.getElementById('expected-return');
const investmentYearsInput = document.getElementById('investment-years');
const annualStepUpInput = document.getElementById('annual-step-up');

const maturityAmountEl = document.getElementById('maturity-amount');
const totalInvestedEl = document.getElementById('total-invested');
const estimatedGainsEl = document.getElementById('estimated-gains');
const monthlySipDisplayEl = document.getElementById('monthly-sip-display');
const returnRateDisplayEl = document.getElementById('return-rate-display');
const summaryChipEl = document.getElementById('summary-chip');

const currencyFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
});

function formatCurrency(value) {
  return currencyFormatter.format(value || 0);
}

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

function updateSummary(years) {
  summaryChipEl.textContent = `${years}-year outlook`;
}

function renderResults(data, monthlySip, annualRate, years) {
  maturityAmountEl.textContent = formatCurrency(data.futureValue);
  totalInvestedEl.textContent = formatCurrency(data.totalInvested);
  estimatedGainsEl.textContent = formatCurrency(data.estimatedGains);
  monthlySipDisplayEl.textContent = formatCurrency(monthlySip);
  returnRateDisplayEl.textContent = `${Number(annualRate).toFixed(1)}% p.a.`;
  updateSummary(years);
}

async function loadSipResults(monthlySip, annualRate, years, annualStepUp) {
  const params = new URLSearchParams({
    monthlyInvestment: monthlySip,
    expectedReturn: annualRate,
    years: years,
    annualStepUp: annualStepUp,
  });

  try {
    const response = await fetch(`/api/sip?${params.toString()}`);
    if (!response.ok) {
      throw new Error('API request failed');
    }

    const data = await response.json();
    renderResults(
      {
        futureValue: data.futureValue,
        totalInvested: data.totalInvested,
        estimatedGains: data.estimatedGains,
      },
      monthlySip,
      annualRate,
      years
    );
    return;
  } catch (error) {
    const fallback = calculateSipValue(monthlySip, annualRate, years, annualStepUp);
    renderResults(fallback, monthlySip, annualRate, years);
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const monthlySip = Number(monthlyInvestmentInput.value);
  const annualRate = Number(expectedReturnInput.value);
  const years = Number(investmentYearsInput.value);
  const annualStepUp = Number(annualStepUpInput.value || 0);

  if (!monthlySip || monthlySip <= 0 || !annualRate || annualRate < 0 || !years || years <= 0) {
    return;
  }

  await loadSipResults(monthlySip, annualRate, years, annualStepUp);
});

resetBtn.addEventListener('click', () => {
  form.reset();
  monthlyInvestmentInput.value = 5000;
  expectedReturnInput.value = 12;
  investmentYearsInput.value = 10;
  annualStepUpInput.value = 5;

  const initial = calculateSipValue(5000, 12, 10, 5);
  renderResults(initial, 5000, 12, 10);
});

const initial = calculateSipValue(5000, 12, 10, 5);
renderResults(initial, 5000, 12, 10);
