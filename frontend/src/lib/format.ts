const LOCALE = "es-ES";

export function formatCompactNumber(value: number) {
  return new Intl.NumberFormat(LOCALE, {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

export function formatCurrency(value: number, currency = "EUR") {
  return new Intl.NumberFormat(LOCALE, {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(value);
}

/** Como formatCurrency, pero con más decimales para importes de céntimos. */
export function formatCost(value: number, currency = "EUR") {
  return new Intl.NumberFormat(LOCALE, {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: value < 0.01 ? 4 : 2,
  }).format(value);
}

export function formatTime(date: Date) {
  return new Intl.DateTimeFormat(LOCALE, { hour: "2-digit", minute: "2-digit" }).format(date);
}

export function formatPercent(value: number, { signed = false } = {}) {
  return new Intl.NumberFormat(LOCALE, {
    style: "percent",
    maximumFractionDigits: 1,
    signDisplay: signed ? "exceptZero" : "auto",
  }).format(value / 100);
}
