from taxiye_eims_integration.utils.tasks import (
    compute_commission,
    compute_vat,
    compute_total,
)
import frappe
from frappe import _  # type: ignore
from frappe.utils import now_datetime  # type: ignore
import json
import re
from frappe.utils.password import get_decrypted_password # type: ignore

#clean TIN Number
def clean_tin_no(tin):
    """Clean and format the provided tax identification number."""
    if not tin:
        return ""

    tinClean = tin.strip().replace("-", "").replace(" ", "")
    if len(tinClean) < 9 or len(tinClean) > 12:
        return ""

    return tinClean
#GET passenger(rider) information
def get_rider_details(payload) -> dict:
    """Extract rider details"""
    rider_tin = clean_tin_no(payload.rider_tin)
    rider_details = {
        "City": payload.taxi_provider_address,
        "Phone": payload.rider_phone,
        "Tin": rider_tin or None,
        "Legal Name": payload.rider_name,
        "Email": payload.rider_email,
        "Region": None,
        "city": None,
        "Wereda": None,
    }
    return rider_details
#item details
def get_item_details(payload): 
    """Extract item and value details for Trip Invoice"""

    item = {
            "ItemCode": payload.reference,
            "ProductDescription": payload.description,
            "Quantity": payload.quantity,
            "LineNumber": payload.line_number or 1,
            "VatAmount": vat_amount,
            "TotalLineAmount": total_amount,
            "Unit": "PCs",
            "UnitPrice": commission_rate,
            "NatureOfSupplies": "services",
        }

    item_list = [item]

    value_details = {
        "vat_amount": payload.compute_vat,
        "total_amount": payload.compute_total,
        "commission_amount": payload.compute_commission,
        "currency": "ETB",
    }

    return item_list, value_details

#get taxi provider information
def get_tax_provider_details(payload):
    """Extract taxi provider details"""
    settings = frappe.get_single("EIMS Settings")  
    tax_provider_details = {
        "City": settings.city or None,  
        "Email": settings.email,  
        "LegalName": settings.legalname,  
        "Locality": settings.locality,  
        "Phone": "+251" + re.sub(r'\D', '', settings.phone), # remove non-numeric characters and prefex with +251. 
        "Region": settings.region,  
        "SubCity": settings.subcity, 
        "Wereda": settings.woreda,
        "Tin": clean_tin_no(get_decrypted_password("EIMS Settings", "EIMS Settings", "tin")),
        "VatNumber": get_decrypted_password("EIMS Settings", "EIMS Settings", "vatnumber") or None, 
    }

    return tax_provider_details

#get driver information
def get_driver_details():
    settings = frappe.get_single("EIMS Settings")
    """Extract driver details"""
    driver_details = {
        "city": settings.city,  
        "email": settings.email,  
        "housenumber": settings.housenumber,  
        "legalname": settings.legalname,  
        "locality": settings.locality,  
        "phone": clean_phone(settings.phone), 
        "region": settings.region,  
        "subcity": settings.subcity,
        "woreda": settings.woreda,
        "systemtype": settings.systemtype,
        "tin": clean_tin_no(get_decrypted_password("EIMS Settings", "EIMS Settings", "tin")) or "0079140416",
        "seller_tin": clean_tin_no(get_decrypted_password("EIMS Settings", "EIMS Settings", "seller_tin")) or "0079140416",
        "vatnumber": get_decrypted_password("EIMS Settings", "EIMS Settings", "vatnumber") or None,
        "systemnumber": get_decrypted_password("EIMS Settings", "EIMS Settings", "systemnumber") or None,
        "client_id": get_decrypted_password("EIMS Settings", "EIMS Settings", "client_id"),
        "client_secret": get_decrypted_password("EIMS Settings", "EIMS Settings", "client_secret"),
        "api_key": get_decrypted_password("EIMS Settings", "EIMS Settings", "api_key"),
        "mor_base_url": settings.mor_base_url or "http://core.mor.gov.et",
    
    }
    return driver_details
    
#last trip invoice
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

def get_transaction_type(transaction_type):
    return transaction_type


#
def get_source_system_detail(payload, invoice_counter):

    return {
        "driver_name": payload.driver_name,
        "InvoiceCounter": invoice_counter,
        "SystemNumber": get_decrypted_password(
            "EIMS Settings", "EIMS Settings", "systemnumber"
        )
        or None,  # type: ignore
        "SystemType": "POS",
    }