import calendar
from datetime import date


def add_months(start: date, months: int) -> date:
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def warranty_summary(purchase_date: date, duration_months: int, today: date | None = None) -> dict:
    expiry = add_months(purchase_date, duration_months)
    current = today or date.today()
    remaining = (expiry - current).days
    status = "expired" if remaining < 0 else "expiring" if remaining <= 30 else "active"
    return {
        "expiryDate": expiry,
        "warrantyDaysRemaining": remaining,
        "warrantyStatus": status,
    }
