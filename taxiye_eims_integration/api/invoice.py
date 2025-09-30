import time
import requests
import frappe
from frappe import _  # type: ignore
import json
from taxiye_eims_integration.api.fetch_trips import (
    get_rider_details,
    get_tax_provider_details,
    get_last_trip_invoice,
    get_document_detail,
    get_payment_detail,
    get_reference_detail,
    get_item_details,
    get_driver_details,compute_commission, compute_vat, compute_total
)
from taxiye_eims_integration.utils.tasks import (
    compute_commission,
    compute_vat,
    compute_total,
)
from taxiye_eims_integration.utils.eims_invoice import save_eims_invoice,
from pydantic import BaseModel, Field, validator
from typing import Optional

# Maximum retries for API submission
max_retries = 5

class InvoicePayload(BaseModel):
    place_identifier: str
    invoice_number: str
    taxi_provider_name: str
    taxi_provider_tin: str
    taxi_provider_address: str
    taxi_provider_phone: str
    rider_phone: Optional[str] = None
    rider_name: Optional[str] = None
    rider_tin: Optional[str] = None
    date: str = Field(..., description="Invoice date in YYYY-MM-DD format")
    description: str
    commission_amount: float
    vat_amount: float
    total_amount: float
    base_fare:float

    # Validate email format manually
    @field_validator("payer_email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Invalid email format")
        return v

    # Date validation
    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("date must be in YYYY-MM-DD format")
        return v

   

def get_items_information(payload):
    """Prepare item and value details for invoice"""
    return get_item_details(
        payload,
        unit_price=payload.commission_rate,
        Quantity=payload.base_fare,
        commission_amount=payload.compute_commission,
        vat_amount=payload.compute_vat,
        total_amount=payload.compute_total,
    )


def prepare_invoice_request_body(payload, last_doc):
    """Prepare payload for EIMS API submission"""

    if last_doc:
        document_number = int(last_doc.document_number) + 1
        invoice_counter = int(last_doc.invoice_counter) + 1
        previous_irn = last_doc.irn
    else:
        document_number = 1
        invoice_counter = 1
        previous_irn = None

    item_list, value_details = get_items_information(payload)
    tax_provider = get_tax_provider_details(payload)
    rider = get_rider_details(payload)
    driver = get_driver_details(payload)
    payment_info = get_payment_detail()

    payload_data = {
        "RiderDetails": rider,
        "DocumentDetails": get_document_detail(payload, document_number),
        "ItemList": item_list,
        "PaymentDetails": payment_info,
        "ReferenceDetails": get_reference_detail(previous_irn),
        "DriverDetails": driver,
        "TaxProviderDetails": tax_provider,
        "ValueDetails": value_details,
        "Version": "1",
    }

    return payload_data


def extract_doc_no_and_invoice_count(data):
    """Extract last document number and invoice counter from 406/417 response"""
    latest_doc_number, latest_invoice_counter = extract_406_data(data)
    if latest_doc_number and latest_invoice_counter:
        try:
            latest_doc_number_int = int(latest_doc_number)
            latest_invoice_counter_int = int(latest_invoice_counter)
        except ValueError:
            raise frappe.throw(
                f"406 Error: Non-numeric values for document number ({latest_doc_number}) "
                f"or invoice counter ({latest_invoice_counter})."
            )
        return latest_doc_number_int - 1, latest_invoice_counter_int - 1
    else:
        raise frappe.ValidationError(f"406 Error: {data}")


def save_invoice_for_internal_reference(last_doc, data, payload):
    """Save EIMS invoice response into Trip Invoice DocType"""

    body = data.get("body", {})
    irn = body.get("irn")
    signed_qr = body.get("signedQR")
    acknowledged_date = body.get("acknowledged_date")
    signed_invoice = body.get("signedInvoice")

    if last_doc:
        document_number = int(last_doc.document_number) + 1
        invoice_counter = int(last_doc.invoice_counter) + 1
        previous_irn = last_doc.irn
    else:
        document_number = 1
        invoice_counter = 1
        previous_irn = None

    invoice_number = getattr(payload, "trip_id", 1)

    invoice = save_eims_invoice(
        document_number=document_number,
        invoice_counter=invoice_counter,
        irn=irn,
        previous_irn=previous_irn,
        vat_amount=payload.vat_amount,
        total_amount=payload.total_amount,
        status="Completed",
        signed_qr=signed_qr,
        acknowledged_date=acknowledged_date,
        signed_invoice=signed_invoice,
        taxi_provider_name=payload.taxi_provider_name,
        taxi_provider_tin=payload.taxi_provider_tin,
        taxi_provider_phone=payload.taxi_provider_phone,
        taxi_provider_email=payload.taxi_provider_email,
        date=payload.date,
        base_fare=payload.base_fare,
        commission_amount=payload.commission_amount,
        invoice_number=invoice_number,
        description=payload.description,
        rider_name=payload.rider_name,
        rider_phone=getattr(payload, "rider__phone", None),
        rider_tin=payload.rider_tin,
    )

    return {
        "status": "success",
        "message": "Invoice has been created successfully",
        "data": {
            "invoice_id": invoice.name,
            "invoice_number": invoice_number,
            "taxi_provider_name": payload.taxi_provider_name,
            "taxi_provider_tin": payload.taxi_provider_tin,
            "taxi_provider_phone": payload.taxi_provider_phone,
            "rider_name": payload.rider_name,
            "rider_phone": getattr(payload, "rider__phone", None),
            "rider_tin": payload.rider_tin,
            "date": payload.date,
            "description": payload.description,
            "total_amount": payload.total_amount,
            "vat_amount": payload.vat_amount,
            "commission_amount": payload.commission_amount,
            "previous_irn": previous_irn,
            "irn": irn,
            "signed_qr": signed_qr,
            "signed_invoice": signed_invoice,
            "acknowledged_date": acknowledged_date,
            "document_number": document_number,
            "invoice_counter": invoice_counter,
            "status": "Succeed",
        },
    }


@frappe.whitelist()
def create_invoice():
    """Main function to create invoice and push to EIMS"""

    headers, url = get_eims_headers_and_url()
    submit_url = f"{url}/register"

    last_doc = get_last_eims_invoice()

    raw_data = frappe.request.get_data(as_text=True)
    if not raw_data:
        frappe.throw(_("Empty request body"))

    data = json.loads(raw_data)
    validated_data = InvoicePayload(**data)

    payload = prepare_invoice_request_body(validated_data, last_doc)

    for attempt in range(1, max_retries + 1):
        response = requests.post(submit_url, json=payload, headers=headers)
        data = response.json()

        if data.get("statusCode") in (406, 417):
            latest_doc_number, latest_invoice_counter = extract_doc_no_and_invoice_count(data)
            last_doc = get_last_eims_invoice()
            payload = prepare_invoice_request_body(validated_data, last_doc)
            continue

        elif data.get("message") == "Too many requests!":
            delay = min(2**attempt, 10)
            frappe.logger().info(f"Rate limited. Retrying in {delay} seconds...")
            time.sleep(delay)
            continue

        else:
            last_doc = get_last_eims_invoice()
            result = save_invoice_for_internal_reference(last_doc, data, validated_data)
            return result

    raise Exception("Failed to submit invoice: Too many requests repeatedly.")
