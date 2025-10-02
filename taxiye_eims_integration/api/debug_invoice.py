import frappe
from frappe import _
import json
from taxiye_eims_integration.api.fetch_trips import (
    get_rider_details,
    get_document_detail,
    get_payment_detail,
    get_reference_detail,
    get_item_details,
    get_driver_details,
    get_transaction_type,
    get_source_system_detail
)
from taxiye_eims_integration.utils.auth import get_eims_headers_and_url
from pydantic import BaseModel, Field
from typing import Optional


class DebugInvoicePayload(BaseModel):
    """Debug invoice payload model"""
    trip_id: str
    invoice_number: str
    taxi_provider_name: str
    taxi_provider_tin: str
    taxi_provider_address: str
    taxi_provider_phone: str
    rider_name: Optional[str] = None
    rider_phone: Optional[str] = None
    rider_tin: Optional[str] = None
    date: str
    time: str
    description: str
    reference: str
    base_fare: float
    commission_amount: float
    tax: float
    amount: float
    total_payment: float
    document_number: Optional[int] = None
    invoice_counter: Optional[int] = None


@frappe.whitelist()
def debug_invoice_payload():
    """
    Debug endpoint to help troubleshoot invoice payload issues.
    This endpoint will show you exactly what payload is being sent to EIMS.
    """
    try:
        # Get request data
        raw_data = frappe.request.get_data(as_text=True)
        if not raw_data:
            frappe.throw(_("Empty request body"))
        
        # Parse JSON
        data = json.loads(raw_data)
        
        # Validate incoming payload
        validated_data = DebugInvoicePayload(**data)
        
        # Get last invoice to determine sequence
        last_doc = frappe.get_all(
            "Trip Invoice",
            fields=["document_number", "invoice_counter", "irn"],
            order_by="creation desc",
            limit=1
        )
        
        if last_doc:
            document_number = int(last_doc[0].document_number) + 1
            invoice_counter = int(last_doc[0].invoice_counter) + 1
            previous_irn = last_doc[0].irn
        else:
            document_number = 1
            invoice_counter = 1
            previous_irn = None
        
        # Override with provided values if available
        if validated_data.document_number:
            document_number = validated_data.document_number
        if validated_data.invoice_counter:
            invoice_counter = validated_data.invoice_counter
        
        # Prepare the payload that will be sent to EIMS
        item_list, value_details = get_item_details(validated_data)
        rider = get_rider_details(validated_data)
        driver = get_driver_details()
        payment_info = get_payment_detail()
        
        payload_data = {
            "BuyerDetails": rider,
            "DocumentDetails": get_document_detail(validated_data, document_number),
            "ItemList": item_list,
            "PaymentDetails": payment_info,
            "ReferenceDetails": get_reference_detail(previous_irn),
            "SellerDetails": driver,
            "SourceSystem": get_source_system_detail(validated_data, invoice_counter),
            "ValueDetails": value_details,
            "TransactionType": get_transaction_type("B2C"),
            "Version": "1",
        }
        
        # Get EIMS headers and URL
        headers, url = get_eims_headers_and_url()
        
        return {
            "status": "success",
            "message": "Debug payload prepared",
            "debug_info": {
                "current_sequence": {
                    "document_number": document_number,
                    "invoice_counter": invoice_counter,
                    "previous_irn": previous_irn
                },
                "eims_endpoint": f"{url}/register",
                "headers": {
                    "Authorization": headers.get("Authorization", "Not set"),
                    "Content-Type": headers.get("Content-Type", "Not set")
                },
                "payload": payload_data,
                "payload_size": len(json.dumps(payload_data))
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in debug invoice payload: {str(e)}")
        return {
            "status": "error",
            "message": f"Error preparing debug payload: {str(e)}",
            "error": str(e)
        }


@frappe.whitelist()
def test_invoice_with_sequence(document_number, invoice_counter):
    """
    Test invoice creation with specific sequence numbers
    """
    try:
        # Validate inputs
        try:
            doc_num = int(document_number)
            inv_counter = int(invoice_counter)
        except ValueError:
            frappe.throw(_("Document number and invoice counter must be valid integers"))
        
        # Get request data
        raw_data = frappe.request.get_data(as_text=True)
        if not raw_data:
            frappe.throw(_("Empty request body"))
        
        # Parse JSON
        data = json.loads(raw_data)
        
        # Validate incoming payload
        validated_data = DebugInvoicePayload(**data)
        
        # Use provided sequence numbers
        validated_data.document_number = doc_num
        validated_data.invoice_counter = inv_counter
        
        # Prepare the payload
        item_list, value_details = get_item_details(validated_data)
        rider = get_rider_details(validated_data)
        driver = get_driver_details()
        payment_info = get_payment_detail()
        
        # Get last invoice for previous IRN
        last_doc = frappe.get_all(
            "Trip Invoice",
            fields=["irn"],
            order_by="creation desc",
            limit=1
        )
        previous_irn = last_doc[0].irn if last_doc else None
        
        payload_data = {
            "BuyerDetails": rider,
            "DocumentDetails": get_document_detail(validated_data, doc_num),
            "ItemList": item_list,
            "PaymentDetails": payment_info,
            "ReferenceDetails": get_reference_detail(previous_irn),
            "SellerDetails": driver,
            "SourceSystem": get_source_system_detail(validated_data, inv_counter),
            "ValueDetails": value_details,
            "TransactionType": get_transaction_type("B2C"),
            "Version": "1",
        }
        
        # Get EIMS headers and URL
        headers, url = get_eims_headers_and_url()
        
        return {
            "status": "success",
            "message": f"Test payload prepared with sequence: Document {doc_num}, Counter {inv_counter}",
            "test_info": {
                "sequence": {
                    "document_number": doc_num,
                    "invoice_counter": inv_counter,
                    "previous_irn": previous_irn
                },
                "eims_endpoint": f"{url}/register",
                "payload": payload_data
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error in test invoice with sequence: {str(e)}")
        return {
            "status": "error",
            "message": f"Error preparing test payload: {str(e)}",
            "error": str(e)
        }
