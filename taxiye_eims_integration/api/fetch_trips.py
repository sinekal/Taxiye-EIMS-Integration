from taxiye_eims_integration.utils.tasks import (
    compute_commission,
    compute_vat,
    compute_total,
)
import frappe
from frappe import _  # type: ignore
from frappe.utils import now_datetime  # type: ignore
import json
def get_rider_details(payload) -> dict:
    """Extract rider details"""

rider_tin = payload.get("rider_tin")
    rider_details = {
        "City": payload.get("taxi_provider_address"),
        "Phone": payload.get("rider_phone"),
        "Tin": rider_tin if rider_tin and rider_tin != "0" else None,
        "Rider Name": payload.get("rider_name"),
        "Region": None,
        "city_sub": None,
        "Wereda": None,
    }

    return rider_details
def get_tax_provider_details(payload) -> dict:
    """Extract taxi provider details"""

    tax_provider_details = {
        "Name": payload.taxi_provider_name,
        "Tin": payload.taxi_provider_tin,
        "Phone": payload.taxi_provider_phone,
        "Email": payload.taxi_provider_email,
        "City": getattr(payload, "taxi_provider_address", None),
        "Region": None,
        "city_sub": None,
        "Wereda": None,
    }

    return tax_provider_details
def get_driver_details(payload) -> dict:
    """Extract driver details"""

    driver_tin = payload.get("driver_tin")

    driver_details = {
        "Name": payload.get("driver_name"),
        "Tin": driver_tin if driver_tin and driver_tin != "0" else None,
        "Phone": payload.get("driver_phone"),
        "Email": payload.get("driver_email"),
        "City": payload.get("driver_address"),
        "Region": None,
        "city_sub": None,
        "Wereda": None,
    }

    return driver_details
def get_last_trip_invoice(taxi_provider_tin: str):
    """Fetch the last Trip Invoice for a given taxi provider TIN"""
    last_txn = frappe.get_all(  # type: ignore
        "Trip Invoice",
        filters={"taxi_provider_tin": taxi_provider_tin},
        fields=["name"],               # ✅ important
        order_by="creation desc",
        limit_page_length=1,
    )
    if last_txn:
        return frappe.get_doc("Trip Invoice", last_txn[0]["name"])  # ✅ dict access
    return None

def get_document_detail(payload, document_number):
    date_obj = getattr(payload, "date", None)
    date_str = date_obj.strftime("%Y-%m-%d") if date_obj else None
    
    document_detail = {
        "document_number": document_number,
        "date": date_str,
        "document_type": "INV",
    }
    return document_detail


def get_payment_detail():
    return {
        "Mode": "CASH",
    }


def get_reference_detail(previous_irn):
    return {
        "PreviousIrn": previous_irn,
        "RelatedDocument": None,  # replace with actual doc ref if required
    }
def get_item_details(
    payload: dict, unit_price: float, tax_amount: float, total_amount: float
) -> tuple[list[dict], dict]:
    """Extract item and value details for Trip Invoice"""

    item = {
        "item_code": payload.get("reference"),
        "product_description": payload.get("description"),
        "item_type": "service",
        "quantity": 1,
        "line_number": 1,
        "tax_amount": tax_amount,
        "tax_code": "VAT15",
        "total_line_amount": total_amount,
        "unit": "PCS",
        "unit_price": unit_price,
    }

    item_list = [item]

    value_details = {
        "vat_amount": compute_vat(item["unit_price"], item["tax_amount"]),
        "total_amount": compute_total(
            item["unit_price"], item["tax_amount"], item["tax_amount"]
        ),
        "commission_amount": compute_commission(item["unit_price"], payload.commission_rate),
        "currency": "ETB",
    }

    return item_list, value_details
