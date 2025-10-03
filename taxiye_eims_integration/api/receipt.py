import json
import random
import frappe
import requests
import datetime
from taxiye_eims_integration.api.fetch_trips import (
    get_payment_detail,
    get_driver_details,
    clean_tin_no
)
from taxiye_eims_integration.utils.auth import get_eims_headers_and_url
from taxiye_eims_integration.utils.eims_receipt import save_eims_receipt
from pydantic import BaseModel, Field, validator
from typing import Optional


class PaymentModel(BaseModel):
    total_payment: float = Field(..., description="total passenger Payment amount")
    amount: float = Field(..., description=" amount before tax")
    tax: float = Field(..., description="Tax amount")
    base_fare: float = Field(..., description="Base fare amount")
    commission_amount: float = Field(..., description="Commission amount")
    date: datetime.date = Field(..., description="Payment date in YYYY-MM-DD format")
    method: str = Field(..., description="Payment method")
    transactionNumber: Optional[str] = Field(None, alias="transactionNumber", description="Transaction reference number")
    accountNumber: Optional[str] = Field(None, alias="accountNumber", description="Account number")

class ReceiptModel(BaseModel):
    invoice_id: str = Field(..., description="Unique invoice ID")
    irn: str = Field(..., description="Invoice Reference Number")
    CollectorName: Optional[str] = Field(None, description="Collector Name")
    status: str 
    signer_qr: Optional[str] = Field(None, description="Signer QR code")
    payment: PaymentModel


@frappe.whitelist()  # type: ignore
def create_receipt():
    raw_data = frappe.request.get_data()  # type: ignore
    if not raw_data:
        frappe.throw(_("Empty request body"))  # type: ignore

    data = json.loads(raw_data)

    # Validate incoming payload
    payload = ReceiptModel(**data)

    driver_info = get_driver_details()

    invoices = frappe.get_list(  # type: ignore
        "Trip Invoice",
        filters={"name": payload.invoice_id},
        fields=["*"],
    )
    invoice = None

    irn = None
    total_amount = 0
    tax_amount = 0
    document_number = None
    if invoices:
        invoice = invoices[0]
        irn = invoice.irn  # type: ignore
        total_amount = invoice.total_payment  # type: ignore
        document_number = invoice.document_number  # type: ignore
        tax_amount = invoice.tax  # type: ignore
    collected_amount = payload.payment.amount + payload.payment.tax

    if collected_amount != total_amount:
        frappe.throw(  # type: ignore
            "CollectedAmount must be equal to TotalAmount (invoice's TotalValue)"
        )
    seller_tin= clean_tin_no(driver_info["seller_tin"])
    discount_amount = 0

    receipt_counter = str(random.randint(10000, 99999))
    manual_receipt_number = str(random.randint(10000, 99999))

    mode_of_payment = get_payment_detail()

    time_str = "00:00:00"

    date_str = payload.payment.date  # e.g. "2025-09-01"
    receipt_date_str = f"{date_str}T{time_str}+03:00"
    # Format as ISO 8601 with +03:00 offset
    receipt_date_str = f"{date_str}T{time_str}+03:00"

    req_payload = {
        "ReceiptNumber": payload.invoice_id,
        "ReceiptType": "Sales Receipts",
        "Reason": "Payment for taxi service",
        "ReceiptDate": receipt_date_str,
        "ReceiptCounter": str(receipt_counter),
        "ManualReceiptNumber": str(manual_receipt_number),
        "SourceSystemType": "POS",
        "SourceSystemNumber": driver_info.get("systemnumber", ""),
        "ReceiptCurrency": "ETB",
        "CollectedAmount": collected_amount,
        "ExchangeRate": None,
        "SellerTIN": seller_tin,
        "Invoices": [
            {
                "InvoiceIRN": irn,
                "PaymentCoverage": "FULL",
                "InvoicePaidAmount": collected_amount,
                "DiscountAmount": discount_amount,
                "RemainingAmount": None,
                "TotalAmount": total_amount,
            }
        ],
        "TransactionDetails": {
            "ModeOfPayment": mode_of_payment["Mode"],
            "ChequeNumber": None,
            "CPONumber": None,
            "DocumentNumber": document_number,
            "CollectorName": payload.CollectorName or None,
            "PaymentServiceProvider": payload.payment.method or "Bank",
            "AccountNumber": payload.payment.accountNumber or None,
            "TransactionNumber": payload.payment.transactionNumber or None,
        },
    }

    headers, url = get_eims_headers_and_url()
    submit_url = f"{url}/receipt/sales"
    res = requests.post(submit_url, json=req_payload, headers=headers)

    if res.status_code != 200:
        frappe.throw(f"EIMS Receipt Submission Failed: {res.text}")  # type: ignore

    response_data = res.json()
    body = response_data.get("body", {})
    status = body.get("status")
    rrn = body.get("rrn")
    qr = body.get("qr")

    # Calculate commission amount from invoice data
    commission_amount = invoice.commission_amount if invoice else 0
    base_fare = invoice.base_fare if invoice else 0
    
    save_eims_receipt(
        invoice_id=payload.invoice_id,  # Must be a valid Trip Invoice ID
        irn=irn,  # type: ignore
        rrn=rrn,
        payment_method=payload.payment.method,
        payment_date=str(date_str),
        total_payment=total_amount,
        tax=tax_amount,
        commission_amount=commission_amount,
        base_fare=base_fare,
        status="Acknowledged",
        signer_qr=qr,
    )

    result = {
        "status": "success",
        "message": "Receipt has been created successfully",
        "data": {
            "invoice_id": payload.invoice_id,
            "invoice_number": invoice.invoice_number if invoice else None,
            "taxi_provider_name": invoice.taxi_provider_name if invoice else None,
            "taxi_provider_tin": invoice.taxi_provider_tin if invoice else None,
            "taxi_provider_phone": invoice.taxi_provider_phone if invoice else None,
            "driver_name": invoice.taxi_provider_name if invoice else None,
            "driver_phone": invoice.taxi_provider_phone if invoice else None,
            "driver_tin": invoice.taxi_provider_tin if invoice else None,
            "rider_name": invoice.rider_name if invoice else None,
            "rider_phone": invoice.rider_phone if invoice else None,
            "time": invoice.time if invoice else None,
            "date": invoice.date if invoice else None,
            "description": invoice.description if invoice else None,
            "rrn": rrn,
            "qr": qr,
            "status": "Acknowledged",
            "payment": {
                "amount": total_amount,
                "tax": tax_amount,
                "commission_amount": commission_amount,
                "base_fare": base_fare,
                "date": date_str,
                "method": payload.payment.method,
            },
        },
    }

    return result
