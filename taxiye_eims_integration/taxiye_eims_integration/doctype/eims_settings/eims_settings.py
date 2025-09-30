# Copyright (c) 2025, Mevinai and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EIMSSettings(Document):
	pass

@frappe.whitelist()
def get_settings():
    return frappe.get_doc("EIMS Settings")
