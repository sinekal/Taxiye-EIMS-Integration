# from datetime import datetime, timedelta, timezone
import frappe
# from frappe import _  # type: ignore

def compute_commission(base_fare: float, commission_rate: float) -> float:
    # commission_amount = base_fare * commission_rate
    return float(base_fare) * float(commission_rate)

def compute_vat(base_fare: float, commission_amount: float, vat_rate: float = 0.15) -> float:
    # vat_amount = (base_fare + commission_amount) * 0.15
    return (float(base_fare) + float(commission_amount)) * float(vat_rate)

def compute_total(base_fare: float, commission_amount: float, vat_amount: float) -> float:
    return float(base_fare) + float(commission_amount) + float(vat_amount)


