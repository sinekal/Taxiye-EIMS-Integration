import frappe
from frappe.model.document import Document
from typing import Dict, Any


def calculate_settlement_amounts(base_fare: float, commission_rate: float) -> Dict[str, float]:
    """
    Calculate settlement amounts based on the business logic:
    - Commission Amount = base_fare * commission_rate
    - VAT Amount = (base_fare + commission_amount) * 0.15
    - Total Amount = base_fare + commission_amount + vat_amount
    """
    commission_amount = base_fare * commission_rate
    vat_amount = (base_fare + commission_amount) * 0.15
    total_amount = base_fare + commission_amount + vat_amount
    
    return {
        "base_fare": base_fare,
        "commission_amount": commission_amount,
        "vat_amount": vat_amount,
        "total_amount": total_amount
    }


def create_trip_settlement(invoice_id: str, base_fare: float, commission_rate: float) -> str:
    """
    Create a Trip Settlement record with calculated amounts
    """
    amounts = calculate_settlement_amounts(base_fare, commission_rate)
    
    settlement_doc = frappe.new_doc("Trip Settlement")
    settlement_doc.invoice_id = invoice_id
    settlement_doc.driver_earning = amounts["base_fare"]
    settlement_doc.taxiye_provider_earning = amounts["commission_amount"]
    settlement_doc.vat_paid = amounts["vat_amount"]
    
    settlement_doc.insert(ignore_permissions=True)
    frappe.db.commit()
    
    return settlement_doc.name


def get_settlement_summary(invoice_id: str) -> Dict[str, Any]:
    """
    Get settlement summary for an invoice
    """
    settlement = frappe.get_all(
        "Trip Settlement",
        filters={"invoice_id": invoice_id},
        fields=["*"]
    )
    
    if settlement:
        return settlement[0]
    return None


def update_invoice_settlement_status(invoice_id: str, status: str):
    """
    Update the settlement status of an invoice
    """
    invoice = frappe.get_doc("Trip Invoice", invoice_id)
    invoice.settlement_status = status
    invoice.save()
    frappe.db.commit()
