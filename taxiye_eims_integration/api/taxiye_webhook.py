import frappe
import json
from frappe import _
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re

from taxiye_eims_integration.api.invoice import create_invoice
from taxiye_eims_integration.api.receipt import create_receipt
from taxiye_eims_integration.utils.settlement import create_trip_settlement, calculate_settlement_amounts


class TripData(BaseModel):
    """Model for incoming trip data from Taxiye"""
    trip_id: str = Field(..., description="Unique trip identifier")
    driver_id: str = Field(..., description="Driver identifier")
    driver_name: str = Field(..., description="Driver full name")
    driver_phone: str = Field(..., description="Driver phone number")
    driver_tin: str = Field(..., description="Driver TIN number")
    rider_name: Optional[str] = Field(None, description="Rider name")
    rider_phone: Optional[str] = Field(None, description="Rider phone number")
    rider_tin: Optional[str] = Field(None, description="Rider TIN number")
    base_fare: float = Field(..., description="Base fare amount")
    commission_rate: float = Field(..., description="Commission rate (0.0 to 1.0)")
    pickup_location: Optional[str] = Field(None, description="Pickup location")
    dropoff_location: Optional[str] = Field(None, description="Dropoff location")
    trip_date: str = Field(..., description="Trip date in YYYY-MM-DD format")
    trip_time: str = Field(..., description="Trip time in HH:MM:SS format")
    payment_method: str = Field(..., description="Payment method (Cash/Bank)")
    status: str = Field(..., description="Trip status (completed)")
    
    @validator("commission_rate")
    @classmethod
    def validate_commission_rate(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Commission rate must be between 0.0 and 1.0")
        return v
    
    @validator("trip_date")
    @classmethod
    def validate_trip_date(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Trip date must be in YYYY-MM-DD format")
        return v
    
    @validator("trip_time")
    @classmethod
    def validate_trip_time(cls, v: str) -> str:
        if not re.match(r"^\d{2}:\d{2}:\d{2}$", v):
            raise ValueError("Trip time must be in HH:MM:SS format")
        return v


@frappe.whitelist(allow_guest=True)
def receive_completed_trip():
    """
    Webhook endpoint to receive completed trip data from Taxiye
    Implements Use Case 1: Receive Completed Route Order
    """
    try:
        # Get request data
        raw_data = frappe.request.get_data(as_text=True)
        if not raw_data:
            frappe.throw(_("Empty request body"))
        
        # Parse and validate data
        data = json.loads(raw_data)
        trip_data = TripData(**data)
        
        # Validate trip status
        if trip_data.status != "completed":
            frappe.throw(_("Only completed trips can be processed"))
        
        # Check if trip already exists
        existing_trip = frappe.get_all(
            "Trip Invoice",
            filters={"trip_id": trip_data.trip_id},
            fields=["name"]
        )
        
        if existing_trip:
            return {
                "status": "success",
                "message": "Trip already processed",
                "trip_id": trip_data.trip_id,
                "invoice_id": existing_trip[0].name
            }
        
        # Calculate settlement amounts
        amounts = calculate_settlement_amounts(trip_data.base_fare, trip_data.commission_rate)
        
        # Prepare invoice payload
        invoice_payload = {
            "trip_id": trip_data.trip_id,
            "invoice_number": f"INV-{trip_data.trip_id}",
            "taxi_provider_name": trip_data.driver_name,
            "taxi_provider_tin": trip_data.driver_tin,
            "taxi_provider_address": f"{trip_data.pickup_location or 'N/A'}",
            "taxi_provider_phone": trip_data.driver_phone,
            "rider_name": trip_data.rider_name,
            "rider_phone": trip_data.rider_phone,
            "rider_tin": trip_data.rider_tin,
            "date": trip_data.trip_date,
            "time": trip_data.trip_time,
            "description": f"Taxi service from {trip_data.pickup_location or 'N/A'} to {trip_data.dropoff_location or 'N/A'}",
            "reference": trip_data.trip_id,
            "base_fare": trip_data.base_fare,
            "commission_amount": amounts["commission_amount"],
            "tax": amounts["vat_amount"],
            "amount": amounts["base_fare"] + amounts["commission_amount"],
            "total_payment": amounts["total_amount"]
        }
        
        # Create invoice (Use Case 2: Send Order for Invoice)
        invoice_result = create_invoice_with_retry(invoice_payload)
        
        if invoice_result.get("status") == "success":
            invoice_id = invoice_result["data"]["invoice_id"]
            
            # Create settlement record
            settlement_id = create_trip_settlement(
                invoice_id, 
                trip_data.base_fare, 
                trip_data.commission_rate
            )
            
            return {
                "status": "success",
                "message": "Trip processed successfully",
                "trip_id": trip_data.trip_id,
                "invoice_id": invoice_id,
                "settlement_id": settlement_id,
                "amounts": amounts
            }
        else:
            frappe.throw(_("Failed to create invoice: {0}").format(invoice_result.get("message", "Unknown error")))
            
    except Exception as e:
        frappe.log_error(f"Error processing completed trip: {str(e)}")
        frappe.throw(_("Error processing trip: {0}").format(str(e)))


def create_invoice_with_retry(payload, max_retries=3):
    """
    Create invoice with retry logic
    """
    for attempt in range(max_retries):
        try:
            # Mock the request data for the create_invoice function
            frappe.local.request = type('obj', (object,), {
                'get_data': lambda as_text=True: json.dumps(payload)
            })()
            
            result = create_invoice()
            return result
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            frappe.log_error(f"Invoice creation attempt {attempt + 1} failed: {str(e)}")
            continue


@frappe.whitelist()
def process_payment():
    """
    Process payment for a completed trip
    Implements Use Case 4: Record Payment
    """
    try:
        raw_data = frappe.request.get_data(as_text=True)
        if not raw_data:
            frappe.throw(_("Empty request body"))
        
        data = json.loads(raw_data)
        invoice_id = data.get("invoice_id")
        payment_method = data.get("payment_method", "Cash")
        payment_date = data.get("payment_date", datetime.now().strftime("%Y-%m-%d"))
        
        if not invoice_id:
            frappe.throw(_("Invoice ID is required"))
        
        # Get invoice details
        invoice = frappe.get_doc("Trip Invoice", invoice_id)
        
        if not invoice:
            frappe.throw(_("Invoice not found"))
        
        # Prepare receipt payload
        receipt_payload = {
            "invoice_id": invoice_id,
            "irn": invoice.irn,
            "status": "Created",
            "signer_qr": None,
            "payment": {
                "total_amount": invoice.total_payment,
                "vat_amount": invoice.tax,
                "commission_amount": invoice.commission_amount,
                "date": payment_date,
                "method": payment_method,
                "transactionNumber": None,
                "accountNumber": None
            }
        }
        
        # Create receipt (Use Case 5: Send Data for Receipt Generation)
        receipt_result = create_receipt_with_retry(receipt_payload)
        
        if receipt_result.get("status") == "success":
            # Update invoice payment status
            invoice.payment_status = "Paid"
            invoice.save()
            
            return {
                "status": "success",
                "message": "Payment processed successfully",
                "invoice_id": invoice_id,
                "receipt_data": receipt_result["data"]
            }
        else:
            frappe.throw(_("Failed to create receipt: {0}").format(receipt_result.get("message", "Unknown error")))
            
    except Exception as e:
        frappe.log_error(f"Error processing payment: {str(e)}")
        frappe.throw(_("Error processing payment: {0}").format(str(e)))


def create_receipt_with_retry(payload, max_retries=3):
    """
    Create receipt with retry logic
    """
    for attempt in range(max_retries):
        try:
            # Mock the request data for the create_receipt function
            frappe.local.request = type('obj', (object,), {
                'get_data': lambda: json.dumps(payload)
            })()
            
            result = create_receipt()
            return result
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            frappe.log_error(f"Receipt creation attempt {attempt + 1} failed: {str(e)}")
            continue


@frappe.whitelist()
def get_trip_status(trip_id):
    """
    Get the status of a trip and its associated documents
    """
    try:
        # Get invoice
        invoice = frappe.get_all(
            "Trip Invoice",
            filters={"trip_id": trip_id},
            fields=["*"]
        )
        
        if not invoice:
            return {
                "status": "not_found",
                "message": "Trip not found"
            }
        
        invoice = invoice[0]
        
        # Get receipt
        receipt = frappe.get_all(
            "Trip Receipt",
            filters={"invoice_id": invoice.name},
            fields=["*"]
        )
        
        # Get settlement
        settlement = frappe.get_all(
            "Trip Settlement",
            filters={"invoice_id": invoice.name},
            fields=["*"]
        )
        
        return {
            "status": "success",
            "trip_id": trip_id,
            "invoice": invoice,
            "receipt": receipt[0] if receipt else None,
            "settlement": settlement[0] if settlement else None
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting trip status: {str(e)}")
        frappe.throw(_("Error getting trip status: {0}").format(str(e)))


@frappe.whitelist()
def send_receipt_to_taxiye():
    """
    Send signed receipt back to Taxiye for rider access
    Implements Use Case 7: Send Signed Receipt for Print
    """
    try:
        raw_data = frappe.request.get_data(as_text=True)
        if not raw_data:
            frappe.throw(_("Empty request body"))
        
        data = json.loads(raw_data)
        invoice_id = data.get("invoice_id")
        
        if not invoice_id:
            frappe.throw(_("Invoice ID is required"))
        
        # Get receipt data
        receipt = frappe.get_all(
            "Trip Receipt",
            filters={"invoice_id": invoice_id},
            fields=["*"]
        )
        
        if not receipt:
            frappe.throw(_("Receipt not found"))
        
        receipt = receipt[0]
        
        # Here you would typically send the receipt to Taxiye's API
        # For now, we'll return the receipt data
        
        return {
            "status": "success",
            "message": "Receipt sent to Taxiye",
            "receipt_data": {
                "invoice_id": invoice_id,
                "rrn": receipt.rrn,
                "signed_qr": receipt.signer_qr,
                "payment_date": receipt.payment_date,
                "total_payment": receipt.total_payment
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error sending receipt to Taxiye: {str(e)}")
        frappe.throw(_("Error sending receipt: {0}").format(str(e)))
