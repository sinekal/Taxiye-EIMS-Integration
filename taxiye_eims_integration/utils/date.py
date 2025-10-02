import frappe
from frappe.utils import formatdate
from datetime import datetime, timedelta


def safe_format_posting_date(posting_date, fmt="dd-mm-yyyy"):
    """
    Format posting_date with these rules using Ethiopian time (UTC+3):
    """
    try:
        if not posting_date:
            raise ValueError("posting_date is empty or None")

        # Convert posting_date to date object
        if isinstance(posting_date, str):
            posting_date = datetime.strptime(posting_date, "%Y-%m-%d").date()
        elif isinstance(posting_date, datetime):
            posting_date = posting_date.date()

        posting_date = posting_date - timedelta(days=1)
        return formatdate(posting_date, fmt)

    except Exception as e:
        frappe.log_error(f"Error formatting posting date: {str(e)}")
        return formatdate(datetime.now().date(), fmt)
