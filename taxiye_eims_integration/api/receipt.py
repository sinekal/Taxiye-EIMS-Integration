# # import json
# import random
# import frappe
# import requests
# from taxiye_eims_integration.api.fetch_trips import (
#     get_rider_details,
#     get_tax_provider_details,
#     get_last_trip_invoice,
#     get_document_detail,
#     get_payment_detail,
#     get_reference_detail,
#     get_item_details,
#     get_driver_details,
#     clean_tin_no
# )
# from taxiye_eims_integration.utils.tasks import (
#     compute_commission,
#     compute_vat,
#     compute_total,
# )
# from taxiye_eims_integration.utils.auth import get_eims_headers_and_url
# from taxiye_eims_integration.utils.eims_receipt import save_eims_receipt
# from pydantic import BaseModel, Field, validator
# from typing import Optional


# class PaymentModel(BaseModel):
#     total_amount: float = Field(..., description="total passenger Payment amount")
#     vat_amount: float = Field(..., description="VAT amount")
#     commission_amount: float = Field(..., description="Commission amount")
#     date: datetime.date = Field(..., description="Payment date in YYYY-MM-DD format")
#     method: str = Field(..., description="Payment method")
#     transactionNumber: Optional[str] = Field(None, alias="transactionNumber", description="Transaction reference number")
#     accountNumber: Optional[str] = Field(None, alias="accountNumber", description="Account number")

# class ReceiptModel(BaseModel):
#     invoice_id: str = Field(..., description="Unique invoice ID")
#     irn: str = Field(..., description="Invoice Reference Number")
#     payment_status: str = Field("Paid", description="Payment status, always 'Paid'")
#     signer_qr: Optional[str] = Field(None, description="Signer QR code")

#     # Optional: validation to ensure payment_status is always 'Paid'
#     @validator("payment_status")
#     def validate_payment_status(cls, v):
#         if v != "Paid":
#             raise ValueError("payment_status must be 'Paid'")
#         return v



# @frappe.whitelist()  # type: ignore
# def create_receipt():
#     raw_data = frappe.request.get_data()  # type: ignore
#     if not raw_data:
#         frappe.throw(_("Empty request body"))  # type: ignore

#     data = json.loads(raw_data)

#     # Validate incoming payload
#     payload = ReceiptModel(**data)

#     driver_info = get_driver_details()

#     invoices = frappe.get_list(  # type: ignore
#         "Trip Invoice",
#         filters={"name": payload.invoice_id},
#         fields=["*"],
#     )
#     invoice = None

#     irn = None
#     total_amount = 0
#     tax_amount = 0
#     document_number = None
#     if invoices:
#         invoice = invoices[0]
#         irn = invoice.irn  # type: ignore
#         total_amount = invoice.compute_total  # type: ignore
#         document_number = invoice.document_number  # type: ignore
#         vat_amount = invoice.compute_vat  # type: ignore

#     seller_tin= clean_tin_no(driver_info["seller_tin"])

#     receipt_counter = str(random.randint(10000, 99999))
#     manual_receipt_number = str(random.randint(10000, 99999))

#     payment_method= get_payment_detail()

#     time_str = "00:00:00"

#     date_str = payload.payment.date  # e.g. "2025-09-01"
#     receipt_date_str = f"{date_str}T{time_str}+03:00"
#     # Format as ISO 8601 with +03:00 offset
#     receipt_date_str = f"{date_str}T{time_str}+03:00"

#     req_payload = {
#         "ReceiptNumber": payload.invoice_id,
#         "ReceiptType": "Sales Receipts",
#         "Reason": "Payment for taxi service",
#         "ReceiptDate": receipt_date_str,
#         "ReceiptCounter": str(receipt_counter),
#         "ManualReceiptNumber": str(manual_receipt_number),
#         "SourceSystemType": "POS",
#         "SourceSystemNumber": driver_info.get("systemnumber", ""),
#         "PaymentMode": payment_method["Cash"],
#         "ReceiptCurrency": "ETB",
#         "ExchangeRate": None,
#         "SellerTIN": seller_tin,
#         "Invoices": [
#             {
#                 "InvoiceIRN": irn,
#                 "PaymentCoverage": "FULL",
#                 "RemainingAmount": None,
#                 "TotalAmount": compute_total(base_fare, commission_amount, vat_amount),
#             }
#         ],
#         "TransactionDetails": {
#             "ModeOfPayment": payment_method["Cash"],
#             "ChequeNumber": None,
#             "CPONumber": None,
#             "DocumentNumber": document_number,
#             "PaymentServiceProvider": payload.payment.method or "Cash",
#             "AccountNumber": payload.payment.accountNumber or None,
#             "TransactionNumber": payload.payment.transactionNumber or None,
#         },
#     }

#     headers, url = get_eims_headers_and_url()
#     submit_url = f"{url}/receipt/sales"
#     res = requests.post(submit_url, json=req_payload, headers=headers)

#     if res.status_code != 200:
#         frappe.throw(f"EIMS Receipt Submission Failed: {res.text}")  # type: ignore

#     response_data = res.json()
#     body = response_data.get("body", {})
#     status = body.get("status")
#     rrn = body.get("rrn")
#     qr = body.get("qr")

#     save_eims_receipt(
#         invoice_id=payload.invoice_id,  # Must be a valid USP Invoice ID
#         irn=irn,  # type: ignore
#         rrn=rrn,
#         payment_mode=payload.payment.mode,
#         payment_date=str(date_str),
#         total_amount=compute_total(base_fare, commission_amount, vat_amount),
#         vat_amount=compute_vat(base_fare, commission_amount),
#         commission_amount=compute_commission(base_fare, commission_rate),
#         status="Acknowledged",
#         signer_qr=signer_qr,
#     )

#     result = {
#         "status": "success",
#         "message": "Receipt has been created successfully",
#         "data": {
#             "invoice_id": payload.invoice_id,
#             "invoice_number": invoice.invoice_number if invoice else None,
#             "taxi_provider_name": invoice.taxi_provider_name if invoice else None,
#             "taxi_provider_tin": invoice.taxi_provider_tin if invoice else None,
#             "taxi_provider_phone": invoice.taxi_provider_phone if invoice else None,
#             "driver_name": invoice.driver_name if invoice else None,
#             "driver_phone": invoice.driver_phone if invoice else None,
#             "driver_tin": invoice.driver_tin if invoice else None,
#             "rider_name": invoice.rider_name if invoice else None,
#             "rider_phone": invoice.rider_phone if invoice else None,
#             "date": invoice.date if invoice else None,
#             "description": invoice.description if invoice else None,
#             "rrn": rrn,
#             "qr": qr,
#             "status": "Acknowledged",
#             "payment": {
#                 "total_amount": compute_total(base_fare, commission_amount, vat_amount),
#                 "vat_amount": compute_vat(base_fare, commission_amount),
#                 "commission_amount": compute_commission(base_fare, commission_rate),
#                 "date": date_str,
#                 "method": payload.payment.method,
#             },
#         },
#     }

#     return result



















# 
import json
import random
import datetime
import frappe
import requests
from frappe import _  # type: ignore
from taxiye_eims_integration.api.fetch_trips import (
    get_driver_details,
    clean_tin_no,
    get_payment_detail,
)
from taxiye_eims_integration.utils.tasks import (
    compute_commission,
    compute_vat,
    compute_total,
)
from taxiye_eims_integration.utils.auth import get_eims_headers_and_url
from taxiye_eims_integration.utils.eims_receipt import save_eims_receipt
from pydantic import BaseModel, Field, validator
from typing import Optional


class PaymentModel(BaseModel):
    total_amount: float = Field(..., description="Total passenger payment amount")
    vat_amount: float = Field(..., description="VAT amount")
    commission_amount: float = Field(..., description="Commission amount")
    date: datetime.date = Field(..., description="Payment date in YYYY-MM-DD format")
    method: str = Field(..., description="Payment method")
    transactionNumber: Optional[str] = None
    accountNumber: Optional[str] = None


class ReceiptModel(BaseModel):
    invoice_id: str = Field(..., description="Unique invoice ID")
    irn: str = Field(..., description="Invoice Reference Number")
    payment_status: str = Field("Paid", description="Payment status, always 'Paid'")
    signer_qr: Optional[str] = None
    payment: PaymentModel

    @validator("payment_status")
    def validate_payment_status(cls, v):
        if v != "Paid":
            raise ValueError("payment_status must be 'Paid'")
        return v


@frappe.whitelist()  # type: ignore
def create_receipt():
    raw_data = frappe.request.get_data(as_text=True)  # type: ignore
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

    invoice = invoices[0] if invoices else None
    irn = invoice.irn if invoice else payload.irn
    document_number = invoice.document_number if invoice else None

    # Extract amounts
    base_fare = payload.payment.total_amount - payload.payment.vat_amount - payload.payment.commission_amount
    commission_amount = payload.payment.commission_amount
    vat_amount = payload.payment.vat_amount
    commission_rate = 0.15  # or pull dynamically from invoice if available

    seller_tin = clean_tin_no(driver_info["seller_tin"])
    receipt_counter = str(random.randint(10000, 99999))
    manual_receipt_number = str(random.randint(10000, 99999))

    payment_method = get_payment_detail()

    time_str = "00:00:00"
    date_str = str(payload.payment.date)  # e.g. "2025-09-01"
    receipt_date_str = f"{date_str}T{time_str}+03:00"

    # Request body for EIMS
    req_payload = {
        "ReceiptNumber": payload.invoice_id,
        "ReceiptType": "Sales Receipts",
        "Reason": "Payment for taxi service",
        "ReceiptDate": receipt_date_str,
        "ReceiptCounter": receipt_counter,
        "ManualReceiptNumber": manual_receipt_number,
        "SourceSystemType": "POS",
        "SourceSystemNumber": driver_info.get("systemnumber", ""),
        "PaymentMode": payment_method.get("Cash", "CASH"),
        "ReceiptCurrency": "ETB",
        "SellerTIN": seller_tin,
        "Invoices": [
            {
                "InvoiceIRN": irn,
                "PaymentCoverage": "FULL",
                "RemainingAmount": None,
                "TotalAmount": compute_total(base_fare, commission_amount, vat_amount),
            }
        ],
        "TransactionDetails": {
            "ModeOfPayment": payload.payment.method,
            "DocumentNumber": document_number,
            "PaymentServiceProvider": payload.payment.method,
            "AccountNumber": payload.payment.accountNumber,
            "TransactionNumber": payload.payment.transactionNumber,
        },
    }

    # Submit to EIMS
    headers, url = get_eims_headers_and_url()
    submit_url = f"{url}/receipt/sales"
    res = requests.post(submit_url, json=req_payload, headers=headers)

    if res.status_code != 200:
        frappe.throw(f"EIMS Receipt Submission Failed: {res.text}")  # type: ignore

    response_data = res.json()
    body = response_data.get("body", {})
    rrn = body.get("rrn")
    qr = body.get("qr")

    # Save receipt locally
    save_eims_receipt(
        invoice_id=payload.invoice_id,
        irn=irn,
        rrn=rrn,
        payment_mode=payload.payment.method,
        payment_date=str(date_str),
        total_amount=compute_total(base_fare, commission_amount, vat_amount),
        vat_amount=compute_vat(base_fare, commission_amount),
        commission_amount=compute_commission(base_fare, commission_rate),
        status="Acknowledged",
        signer_qr=payload.signer_qr,
    )

    return {
        "status": "success",
        "message": "Receipt has been created successfully",
        "data": {
            "invoice_id": payload.invoice_id,
            "invoice_number": getattr(invoice, "invoice_number", None),
            "taxi_provider_name": getattr(invoice, "taxi_provider_name", None),
            "taxi_provider_tin": getattr(invoice, "taxi_provider_tin", None),
            "driver_name": getattr(invoice, "driver_name", None),
            "rider_name": getattr(invoice, "rider_name", None),
            "date": getattr(invoice, "date", date_str),
            "rrn": rrn,
            "qr": qr,
            "status": "Acknowledged",
            "payment": {
                "total_amount": compute_total(base_fare, commission_amount, vat_amount),
                "vat_amount": compute_vat(base_fare, commission_amount),
                "commission_amount": compute_commission(base_fare, commission_rate),
                "date": date_str,
                "method": payload.payment.method,
            },
        },
    }
