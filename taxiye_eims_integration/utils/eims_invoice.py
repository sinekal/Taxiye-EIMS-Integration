import frappe
from frappe.utils import now_datetime # type: ignore


def get_last_eims_invoice():
    last_txn = frappe.get_list(  # type: ignore
        "Trip Invoice", order_by="creation desc", limit=1
    )
    if last_txn:
        return frappe.get_doc("Trip Invoice", last_txn[0].name)  # type: ignore
    return None


def save_eims_invoice(
    document_number: int,
    invoice_counter: int,
    irn: str,
    invoice_number: str,
    previous_irn: str | None,
    base_fare: float,
    commission_amount: float,
    vat_amount: float,
    total_amount: float,
    status: str,
    signed_qr: str,
    acknowledged_date,
    signed_invoice: str,
    taxi_provider_name: str,
    taxi_provider_tin: str,
    taxi_provider_phone: str | None,
    taxi_provider_email: str | None,
    date,
    description: str = "",
    # New fields
    rider_name: str | None = None,
    rider_phone: str | None = None,
):
    """Save a Trip Invoice with extended rider and plate information"""

    transaction_doc = frappe.new_doc("Trip Invoice")  # type: ignore

    # Mandatory fields
    transaction_doc.taxi_provider_name = taxi_provider_name
    transaction_doc.taxi_provider_tin = taxi_provider_tin
    transaction_doc.invoice_number = invoice_number
    transaction_doc.date = date
    

    # Optional rider information
    transaction_doc.rider_name = rider_name
    transaction_doc.rider_phone = rider_phone

    # Other fields
    transaction_doc.document_number = document_number
    transaction_doc.invoice_counter = invoice_counter
    transaction_doc.irn = irn
    transaction_doc.previous_irn = previous_irn
    transaction_doc.vat_amount = vat_amount
    transaction_doc.commission_amount = commission_amount
    transaction_doc.base_fare = base_fare
    transaction_doc.total_amount = total_amount
    transaction_doc.status = status
    transaction_doc.signed_qr = signed_qr
    transaction_doc.signed_invoice = signed_invoice
    transaction_doc.acknowledged_date = acknowledged_date
    transaction_doc.description = description

    transaction_doc.insert(ignore_permissions=True)
    frappe.db.commit()  # type: ignore

    return transaction_doc

#create temporary invoice 
def temporary_eims_invoice(document_number, invoice_counter):
    # Create a new Document instance of doctype 'USP Invoice'
    transaction_doc = frappe.new_doc("Trip Invoice")  # type: ignore

    # --- Required fields from schema ---
    transaction_doc.invoice_number = f"TEMP-{invoice_counter}"
    transaction_doc.taxi_provider_name = "TEMP PROVIDER"
    transaction_doc.taxi_provider_tin = "000000000"
    transaction_doc.date = now_datetime().date()
    transaction_doc.reference = f"REF-{invoice_counter}"
    transaction_doc.amount = 0
    transaction_doc.total_amount = 0
    transaction_doc.status = "Pending"  # must be one of: pending, sent to EIMS, acknowledged, completed, failed

    # --- Optional / placeholder fields ---
    transaction_doc.tax = 0
    transaction_doc.previous_irn = ""
    transaction_doc.irn = ""
    transaction_doc.signed_qr = ""
    transaction_doc.signed_invoice = ""
    transaction_doc.acknowledged_date = now_datetime()
    transaction_doc.document_number = document_number
    transaction_doc.invoice_counter = invoice_counter
    transaction_doc.description = "Temporary invoice created for synchronization."

    # Save
    transaction_doc.insert(ignore_permissions=True)
    frappe.db.commit()  # type: ignore

    return transaction_doc