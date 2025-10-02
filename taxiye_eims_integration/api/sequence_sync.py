import frappe
from frappe import _
import requests
from taxiye_eims_integration.utils.auth import get_eims_headers_and_url
from taxiye_eims_integration.utils.eims_invoice import temporary_eims_invoice


@frappe.whitelist()
def sync_sequence_with_eims(document_number=None, invoice_counter=None):
    """
    Manually sync sequence numbers with EIMS system.
    This function helps resolve 406 sequence errors by creating temporary invoices
    to bring your local sequence in sync with EIMS.
    
    Args:
        document_number (int): The document number EIMS expects
        invoice_counter (int): The invoice counter EIMS expects
    """
    try:
        if not document_number or not invoice_counter:
            frappe.throw(_("Both document_number and invoice_counter are required"))
        
        # Convert to integers
        try:
            doc_num = int(document_number)
            inv_counter = int(invoice_counter)
        except ValueError:
            frappe.throw(_("Document number and invoice counter must be valid integers"))
        
        # Get current last invoice
        last_invoice = frappe.get_all(
            "Trip Invoice",
            fields=["document_number", "invoice_counter"],
            order_by="creation desc",
            limit=1
        )
        
        current_doc_num = int(last_invoice[0].document_number) if last_invoice else 0
        current_inv_counter = int(last_invoice[0].invoice_counter) if last_invoice else 0
        
        frappe.msgprint(f"Current local sequence: Document {current_doc_num}, Counter {current_inv_counter}")
        frappe.msgprint(f"EIMS expects: Document {doc_num}, Counter {inv_counter}")
        
        # Calculate how many temporary invoices we need to create
        doc_diff = doc_num - current_doc_num
        counter_diff = inv_counter - current_inv_counter
        
        if doc_diff <= 0 and counter_diff <= 0:
            frappe.msgprint(_("Local sequence is already in sync or ahead of EIMS"))
            return {
                "status": "success",
                "message": "No sync needed",
                "current_document_number": current_doc_num,
                "current_invoice_counter": current_inv_counter,
                "eims_document_number": doc_num,
                "eims_invoice_counter": inv_counter
            }
        
        # Create temporary invoices to sync
        created_invoices = []
        for i in range(max(doc_diff, counter_diff)):
            temp_doc_num = current_doc_num + i + 1
            temp_inv_counter = current_inv_counter + i + 1
            
            # Create temporary invoice
            temp_invoice = temporary_eims_invoice(temp_doc_num, temp_inv_counter)
            created_invoices.append({
                "name": temp_invoice.name,
                "document_number": temp_doc_num,
                "invoice_counter": temp_inv_counter
            })
        
        frappe.msgprint(f"Created {len(created_invoices)} temporary invoices to sync sequence")
        
        return {
            "status": "success",
            "message": f"Successfully synced sequence with EIMS",
            "created_invoices": created_invoices,
            "final_document_number": doc_num,
            "final_invoice_counter": inv_counter
        }
        
    except Exception as e:
        frappe.log_error(f"Error syncing sequence with EIMS: {str(e)}")
        frappe.throw(_("Error syncing sequence: {0}").format(str(e)))


@frappe.whitelist()
def get_current_sequence():
    """
    Get current sequence numbers from local system
    """
    try:
        last_invoice = frappe.get_all(
            "Trip Invoice",
            fields=["name", "document_number", "invoice_counter", "creation"],
            order_by="creation desc",
            limit=1
        )
        
        if last_invoice:
            return {
                "status": "success",
                "last_invoice": last_invoice[0],
                "document_number": int(last_invoice[0].document_number),
                "invoice_counter": int(last_invoice[0].invoice_counter)
            }
        else:
            return {
                "status": "success",
                "message": "No invoices found",
                "document_number": 0,
                "invoice_counter": 0
            }
            
    except Exception as e:
        frappe.log_error(f"Error getting current sequence: {str(e)}")
        frappe.throw(_("Error getting current sequence: {0}").format(str(e)))


@frappe.whitelist()
def test_eims_connection():
    """
    Test connection to EIMS API
    """
    try:
        headers, url = get_eims_headers_and_url()
        
        # Try to make a simple request to test connection
        test_url = f"{url}/test"  # Adjust this endpoint as needed
        
        response = requests.get(test_url, headers=headers, timeout=10)
        
        return {
            "status": "success",
            "message": "EIMS connection successful",
            "status_code": response.status_code,
            "response": response.text[:500] if response.text else "No response body"
        }
        
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "EIMS connection timeout",
            "error": "Connection timed out after 10 seconds"
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "message": "EIMS connection failed",
            "error": "Could not connect to EIMS server"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "EIMS connection error",
            "error": str(e)
        }


@frappe.whitelist()
def reset_sequence_to_eims_expected(document_number, invoice_counter):
    """
    Reset local sequence to match EIMS expected values.
    WARNING: This will create temporary invoices to sync the sequence.
    """
    try:
        # Validate inputs
        try:
            doc_num = int(document_number)
            inv_counter = int(invoice_counter)
        except ValueError:
            frappe.throw(_("Document number and invoice counter must be valid integers"))
        
        # Get confirmation
        frappe.msgprint(
            f"This will sync your local sequence to match EIMS expectations:\n"
            f"Document Number: {doc_num}\n"
            f"Invoice Counter: {inv_counter}\n\n"
            f"This may create temporary invoices. Continue?",
            title="Confirm Sequence Reset"
        )
        
        # Call the sync function
        result = sync_sequence_with_eims(doc_num, inv_counter)
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error resetting sequence: {str(e)}")
        frappe.throw(_("Error resetting sequence: {0}").format(str(e)))
