import time
import requests
import frappe
from frappe import _  # type: ignore
import json
import re
from taxiye_eims_integration.api.fetch_trips import (
    get_rider_details,
    get_document_detail,
    get_payment_detail,
    get_reference_detail,
    get_item_details,
    get_driver_details,
    get_transaction_type,   
)

from taxiye_eims_integration.utils.auth import (
    extract_406_data, 
    get_eims_headers_and_url, 
    parse_ack_date,
    get_source_system_detail,
)
from taxiye_eims_integration.utils.eims_invoice import (
    save_eims_invoice, 
    temporary_eims_invoice, 
    get_last_eims_invoice, 
    )
from pydantic import BaseModel, Field, field_validator
from typing import Optional

# Maximum retries for API submission
max_retries = 5

class InvoicePayload(BaseModel):
    """Invoice payload model"""
    trip_id: str
    invoice_number: str
    taxi_provider_name: str
    taxi_provider_tin: str
    taxi_provider_address: str
    taxi_provider_phone: str
    rider_phone: Optional[str] = None
    rider_name: Optional[str] = None
    rider_tin: Optional[str] = None
    date: str = Field(..., description="Invoice date in YYYY-MM-DD format")
    time: str = Field(..., description="Invoice time in HH:MM:SS format")
    description: str
    reference: str
    base_fare: float
    commission_amount: float
    tax: float
    amount: float
    total_payment: float
    
    # Date validation
    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("date must be in YYYY-MM-DD format")
        return v
    #validate date
     @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("date must be in YYYY-MM-DD format")
        return v

    # Time validation
    @field_validator("time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        if not re.match(r"^\d{2}:\d{2}:\d{2}$", v):
            raise ValueError("time must be in HH:MM:SS format")
        return v


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

    item_list, value_details = get_item_details(payload)
    rider = get_rider_details(payload)
    driver = get_driver_details(payload)
    payment_info = get_payment_detail()

    payload_data = {
        "BuyerDetails": rider,
        "DocumentDetails": get_document_detail(payload, document_number),
        "ItemList": item_list,
        "PaymentDetails": payment_info,
        "ReferenceDetails": get_reference_detail(previous_irn),
        "SellerDetails": driver,
        "SourceSystem": get_source_system_detail(payload, invoice_counter),  
        "ValueDetails": value_details,
        "TransactionType": get_transaction_type("B2C"),
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

    ackDate_clean = parse_ack_date(acknowledged_date)
    invoice = save_eims_invoice(
        document_number=document_number,
        invoice_counter=invoice_counter,
        irn=irn,
        previous_irn=previous_irn,
        tax=payload.tax,
        amount=payload.amount,
        total_payment=payload.total_payment,
        status="Completed",
        signed_qr=signed_qr,
        acknowledged_date=ackDate_clean,
        signed_invoice=signed_invoice,
        taxi_provider_name=payload.taxi_provider_name,
        taxi_provider_tin=payload.taxi_provider_tin,
        taxi_provider_phone=payload.taxi_provider_phone,
        date=payload.date,
        time=payload.time,
        reference=payload.reference,
        description=payload.description,
        base_fare=payload.base_fare,
        commission_amount=payload.commission_amount,
        invoice_number=payload.invoice_number,
        rider_name=payload.rider_name,
        rider_phone=payload.rider_phone,
        rider_tin=payload.rider_tin,
        trip_id = payload.trip_id,
    )

    return {
        "status": "success",
        "message": "Invoice has been created successfully",
        "data": {
            "invoice_id": invoice.name,
            "invoice_number": payload.invoice_number,
            "taxi_provider_name": payload.taxi_provider_name,
            "taxi_provider_tin": payload.taxi_provider_tin,
            "taxi_provider_phone": payload.taxi_provider_phone,
            "rider_name": payload.rider_name,
            "rider_phone": payload.rider_phone,
            "rider_tin": payload.rider_tin,
            "date": payload.date,
            "time": payload.time,
            "reference": payload.reference,
            "description": payload.description,
            "total_payment": payload.total_payment,
            "tax": payload.tax,
            "base_fare": payload.base_fare,
            "commission_amount": payload.commission_amount,
            "previous_irn": previous_irn,
            "irn": irn,
            "signed_qr": signed_qr,
            "signed_invoice": signed_invoice,
            "acknowledged_date": ackDate_clean,
            "document_number": document_number,
            "invoice_counter": invoice_counter,
            "status": "Succeed",
        },
    }


@frappe.whitelist()
def create_invoice(max_retries=5):

    headers, url = get_eims_headers_and_url()
    submit_url = f"{url}/register"

    # Fetch last invoice
    last_doc = get_last_eims_invoice()

    raw_data = frappe.request.get_data(as_text=True)  # type: ignore
    if not raw_data:
        frappe.throw(_("Empty request body"))  # type: ignore

    # Parse JSON
    data = json.loads(raw_data)

    # Validate incoming payload
    validated_data = InvoicePayload(**data)

    payload = prepare_invoice_request_body(validated_data, last_doc)

    for attempt in range(1, max_retries + 1):
        response = requests.post(submit_url, json=payload, headers=headers)
        data = response.json()

        if data.get("statusCode") in (406, 417):
            # Sequence error: create temporary invoice and retry
            latest_doc_number, latest_invoice_counter = (
                extract_doc_no_and_invoice_count(data)
            )
            temporary_eims_invoice(latest_doc_number, latest_invoice_counter)
            last_doc = get_last_eims_invoice()
            payload = prepare_invoice_request_body(validated_data, last_doc)  # type: ignore
            # prevalidate_invoice_payload(payload)
            continue

        elif data.get("message") == "Too many requests!":
            # Rate limit: exponential backoff
            delay = min(2**attempt, 10)  # max 10 seconds
            print(f"Rate limited. Retrying in {delay} seconds...")  # type: ignore
            time.sleep(delay)
            continue

        else:
            # Success
            last_doc = get_last_eims_invoice()
            result = save_invoice_for_internal_reference(last_doc, data, validated_data)
            return result
            # break
    else:
        raise Exception("Failed to submit invoice: Too many requests repeatedly.")
