import frappe

def save_eims_receipt(
    invoice_id: str,
    irn: str,
    rrn: str,
    payment_method: str,
    payment_date: str,
    payment_amount: float,
    vat_amount: float,
    base_fare: float,
    commission_amount: float,
    status: str,
    signer_qr: str
):
    """Save a new Trip Receipt with all required fields"""

    # Create a new Document instance of doctype 'Trip Receipt'
    receipt_doc = frappe.new_doc("Trip Receipt")  # type: ignore

    # Map fields from parameters to doctype
    receipt_doc.invoice_id = invoice_id                           # Invoice ID (Link to USP Invoice)
    receipt_doc.irn = irn                                         # ERCA Invoice Reference Number
    receipt_doc.rrn = rrn                                         # Receipt Reference Number
    receipt_doc.payment_method = payment_method                   # Payment Method
    receipt_doc.payment_date = payment_date                       # Payment Date (YYYY-MM-DD)
    receipt_doc.payment_amount = payment_amount                   # Payment Amount
    receipt_doc.vat_amount = vat_amount                             # VAT Amount
    receipt_doc.status = status                                   # Receipt Status (Draft/Created/Acknowledged/Failed)
    receipt_doc.signer_qr = signer_qr                             # Signer QR

    # Save the document
    receipt_doc.insert(ignore_permissions=True)
    frappe.db.commit()  # type: ignore

    return receipt_doc
 