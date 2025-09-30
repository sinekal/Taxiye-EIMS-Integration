# Copyright (c) 2025, Mevinai and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TripInvoice(Document):
	pass

# from taxiye_eims_integration.api.invoice import send_invoice_to_eims

# def create_invoice_record(trip_data):
#     settings = frappe.get_doc("EIMS Settings")
#     commission_rate = settings.default_commission_rate / 100
#     vat_rate = settings.vat_rate / 100

#     commission_amount = trip_data["base_fare"] * commission_rate
#     vat_amount = (trip_data["base_fare"] + commission_amount) * vat_rate
#     total_amount = trip_data["base_fare"] + commission_amount + vat_amount

#     doc = frappe.get_doc({
#         "doctype": "Trip Invoice",
# 		"date":trip_data["date"],
#         "trip_id": trip_data["trip_id"],
#         "driver_name": trip_data["driver_name"],
#         "rider_name": trip_data["rider_name"],
#         "base_fare": trip_data["base_fare"],
#         "commission": commission_amount,
#         "vat": vat_amount,
#         "total_amount": total_amount,
#         "status": "Pending"
#     }).insert(ignore_permissions=True)

#     # Send invoice to EIMS
#     irn = send_invoice_to_eims(doc)
#     if irn:
#         doc.irn = irn
#         doc.status = "Sent"
#         doc.save()
#     return doc
