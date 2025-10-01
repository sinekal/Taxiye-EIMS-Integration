# import frappe
# from frappe.utils.password import get_decrypted_password


# def get_secret(doctype: str, name: str, fieldname: str) -> str | None:
#     """Fetch and decrypt a Password field from a DocType."""
#     try:
#         return get_decrypted_password(doctype, name, fieldname)
#     except Exception:
#         frappe.log_error(f"Failed to decrypt field '{fieldname}' in {doctype}")
#         return None


# def get_auth_credentials() -> dict:
#     """
#     Get the required authentication variables for EIMS API login.
#     Raises an error if any are missing.
#     """
#     doctype = "EIMS Settings"
#     name = "EIMS Settings"  # singleton

#     client_id = get_secret(doctype, name, "client_id")
#     client_secret = get_secret(doctype, name, "client_secret")
#     api_key = get_secret(doctype, name, "api_key")
#     seller_tin = get_secret(doctype, name, "seller_tin")

#     creds = {
#         "clientId": client_id,
#         "clientSecret": client_secret,
#         "apikey": api_key,
#         "tin": seller_tin,
#     }

#     missing = [k for k, v in creds.items() if not v]
#     if missing:
#         frappe.throw(f"Missing required authentication variables: {', '.join(missing)}")

#     return creds
