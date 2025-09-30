# Copyright (c) 2025, Mevinai and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document
# from taxiye_eims_integration.api.fetch_trips import EIMSClient

class TripReceipt(Document):
	pass
    # def on_submit(self):
    #     client = EIMSClient()
    #     try:
    #         response = client.send_receipt(self)
    #         self.receipt_status = "Created"
    #         self.signer_qr = response.get("signer_qr")
    #         frappe.msgprint("Receipt synced successfully to EIMS")
    #     except Exception as e:
    #         self.receipt_status = "Failed"
    #         frappe.log_error(frappe.get_traceback(), "Trip Receipt Sync Error")
    #         frappe.throw(f"Failed to send receipt: {str(e)}")
