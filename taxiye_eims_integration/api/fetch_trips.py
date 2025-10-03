import frappe
from frappe import _  # type: ignore
from frappe.utils import now_datetime  # type: ignore
import json
import re
from taxiye_eims_integration.utils.date import safe_format_posting_date
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

#clean phone number
def clean_phone(phone):
    """Clean and format phone number with Ethiopian country code."""
    if not phone:
        return ""
    
    # Remove all non-numeric characters
    cleaned = re.sub(r'\D', '', phone)
    
    # Add Ethiopian country code if missing
    if not cleaned.startswith('251'):
        cleaned = '251' + cleaned
    
    return '+' + cleaned
#GET passenger(rider) information
def get_rider_details(payload) -> dict:
    """Extract rider details"""
    rider_tin = clean_tin_no(payload.rider_tin)
    rider_details = {
        "City": payload.rider_city or None,
        "Phone": payload.rider_phone or None,
        "Email": payload.rider_email or None,
        "Housenumber": payload.housenumber or None,
        "IdType": "PST",  # Assuming passport as default
        "IdNumber": payload.id_number or None,
        "Tin": rider_tin or None,
        "LegalName": payload.rider_name,
        "Region": None,
        "City": None,
        "Wereda": None,
    }
    return rider_details
#item details
def get_item_details(payload): 
    """Extract item and value details for Trip Invoice"""
    commission_amount=float(payload.base_fare*payload.commission_rate)
    amount=float(payload.base_fare+commission_amount)
    tax=float((payload.base_fare+commission_amount)*0.15)
    total_payment=float(payload.base_fare+commission_amount+tax)

    item = {
            "ItemCode": payload.reference,
            "ProductDescription": payload.description,
            "PreTaxValue": amount,
            "Quantity": payload.quantity,
            "LineNumber": payload.line_number or 1,
            "TaxAmount": tax,
            "TaxCode": "VAT15" or None,
            "TotalLineAmount": total_payment,
            "Unit": "PCs",
            "Discount": 0,
            "UnitPrice": float(payload.commission_rate),
            "NatureOfSupplies": "goods",
        }

    item_list = [item]

    value_details = {
        "TaxValue": tax,
        "TotalValue": total_payment,
        "InvoiceCurrency": "ETB",
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
    """Extract driver details"""
    try:
        settings = frappe.get_single("EIMS Settings")
    except frappe.DoesNotExistError:
        frappe.throw(
            _("EIMS Settings are not configured. Please go to 'EIMS Settings' and save your credentials before submitting an invoice."),
            title="Configuration Missing"
        )
    driver_details = {
        "city": settings.city,  
        "email": settings.email,  
        "housenumber": settings.housenumber,  
        "legalname": settings.legalname,  
        "locality": settings.locality,  
        "phone": clean_phone(settings.phone), 
        "region": settings.region,  
        "woreda": settings.woreda,
        "subcity": settings.subcity,
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
    date = payload.date
    time = payload.time

    date_str = safe_format_posting_date(date)
    time_str = str(time) if time else "00:00:00"

    return {
        "DocumentNumber": document_number,
        "Date": f"{date_str}T{time_str}",
        "Type": "INV",
    }


def get_payment_detail():
    return {
        "Mode": "CASH",
        "PaymentTerm": "IMMEDIATE",
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
        # "CashierName": payload.taxi_provider_name,
        "InvoiceCounter": invoice_counter,
        "SystemNumber": get_decrypted_password(
            "EIMS Settings", "EIMS Settings", "systemnumber"
        )
        or None,  # type: ignore
        "SystemType": "POS",
    }