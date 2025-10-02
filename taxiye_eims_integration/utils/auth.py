import json
import requests
import frappe
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from taxiye_eims_integration.api.fetch_trips import get_driver_details
from frappe.utils.password import encrypt, decrypt  # type: ignore
from frappe.utils import formatdate

# Redis keys
REDIS_KEY_ACCESS = "eims:access_token"
REDIS_KEY_REFRESH = "eims:refresh_token"
REDIS_KEY_EXPIRES = "eims:expires_in"


def set_token_in_redis(access_token, refresh_token, expires_sec):
    """Encrypt and store tokens in Redis with expiry."""
    r = frappe.cache()  # type: ignore # Redis cache
    eth_tz = timezone(timedelta(hours=3))
    expire_at = datetime.now(eth_tz) + timedelta(seconds=expires_sec)

    # Encrypt before storing
    if access_token:
        r.set_value(REDIS_KEY_ACCESS, encrypt(access_token), expires_sec)
    if refresh_token:
        # keep refresh token for 7 days
        r.set_value(REDIS_KEY_REFRESH, encrypt(refresh_token), 60 * 60 * 24 * 7)
    r.set_value(REDIS_KEY_EXPIRES, expire_at.isoformat(), expires_sec)


def get_token_from_redis():
    """Retrieve and decrypt tokens from Redis."""
    r = frappe.cache() # type: ignore
    enc_access = r.get_value(REDIS_KEY_ACCESS)
    enc_refresh = r.get_value(REDIS_KEY_REFRESH)
    expires_in_str = r.get_value(REDIS_KEY_EXPIRES)

    access_token, refresh_token, expires_in = None, None, None

    try:
        if enc_access:
            access_token = decrypt(enc_access)
    except Exception:
        frappe.log_error("Failed to decrypt access token") # type: ignore

    try:
        if enc_refresh:
            refresh_token = decrypt(enc_refresh)
    except Exception:
        frappe.log_error("Failed to decrypt refresh token") # type: ignore

    if expires_in_str:
        try:
            expires_in = datetime.fromisoformat(expires_in_str)
        except Exception:
            expires_in = None

    return access_token, refresh_token, expires_in


def refresh_eims_token(base_url, refresh_token):
    """Try to refresh access token using refresh token."""
    try:
        refresh_url = f"{base_url}/auth/refresh-token"
        response = requests.post(refresh_url, json={"refreshToken": refresh_token})
        response.raise_for_status()
        resp_data = response.json().get("data", {})

        access_token = resp_data.get("accessToken")
        refresh_token_new = resp_data.get("refreshToken")
        expires_sec = resp_data.get("expiresIn", 3600)

        if access_token:
            set_token_in_redis(access_token, refresh_token_new or refresh_token, expires_sec)
            return access_token
    except Exception as e:
        frappe.log_error(f"EIMS Refresh Failed: {str(e)}") # type: ignore
    return None


def login_eims(base_url, seller_info):
    """Perform login to get new tokens."""
    try:
        login_url = f"{base_url}/auth/login"
        response = requests.post(
            login_url,
            json={
                "clientId": seller_info.get("client_id"),
                "clientSecret": seller_info.get("client_secret"),
                "apikey": seller_info.get("api_key"),
                "tin": seller_info.get("tin"),
            },
        )
        response.raise_for_status()
        resp_data = response.json().get("data", {})

        access_token = resp_data.get("accessToken")
        refresh_token_new = resp_data.get("refreshToken")
        expires_sec = resp_data.get("expiresIn", 3600)

        if not access_token:
            frappe.throw(_("EIMS Login response missing accessToken")) # type: ignore

        set_token_in_redis(access_token, refresh_token_new or "", expires_sec)
        return access_token
    except requests.RequestException as e:
        frappe.throw(_("EIMS Login Failed: {0}").format(str(e))) # type: ignore
    except Exception as e:
        frappe.log_error(f"Unexpected EIMS login error: {str(e)}") # type: ignore
        frappe.throw(_("Failed to generate EIMS access token")) # type: ignore


def get_eims_access_token():
    """Fetch EIMS access token, auto-refresh if needed, or login."""
    eth_tz = timezone(timedelta(hours=3))
    current_time = datetime.now(eth_tz)

    seller_info = get_seller_information()
    base_url = seller_info.get("mor_base_url", "").rstrip("/")

    access_token, refresh_token, expires_in = get_token_from_redis()

    # Token is valid → return
    if access_token and expires_in and expires_in > current_time + timedelta(seconds=30):
        return access_token

    # Try refresh token first
    if refresh_token:
        token = refresh_eims_token(base_url, refresh_token)
        if token:
            return token

    # Otherwise login
    return login_eims(base_url, seller_info)








################
def get_seller_information():
    """Get seller information from EIMS Settings"""
    return get_driver_details()

def get_eims_headers_and_url():
    seller_info = get_driver_details()
    token = get_eims_access_token()

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }, f"{seller_info['mor_base_url']}/v1"


def extract_406_data(data):
    latest_document_number = None
    invoice_counter = None

    if "body" in data:
        for item in data["body"]:
            # ensure item is a dict and has "errorMessage"
            if isinstance(item, dict):
                messages = item.get("errorMessage", [])
            else:
                # if item is a string, treat it as a single-message list
                messages = [item]

            for msg in messages:
                if not isinstance(msg, str):
                    continue  # skip non-string messages

                if "Document number" in msg and "expected" in msg:
                    latest_document_number = msg.split("expected : ")[-1].strip()
                elif "Invoice counter" in msg and "expected" in msg:
                    invoice_counter = msg.split("expected : ")[-1].strip()

    return latest_document_number, invoice_counter

    #
    def parse_ack_date(ack_date_iso):
    if not ack_date_iso:
        return None
    # Remove anything after Z or + (timezone info)
    clean_str = ack_date_iso.split("Z")[0].split("+")[0]
    # Drop brackets if any
    clean_str = clean_str.split("[")[0]
    # Convert to datetime object
    dt = datetime.fromisoformat(clean_str)
    return dt.strftime("%Y-%m-%d %H:%M:%S")
###
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












# # Cache key used in frappe.cache() (Redis)
# REDIS_KEY = "eims_tokens"

# # In-memory fallback for fast access (kept in sync with cache)
# _TOKEN_CACHE: Dict[str, Any] = {}

# ETH_TZ = timezone(timedelta(hours=3))


# def _now() -> datetime:
#     return datetime.now(ETH_TZ)


# def _expires_at_from_seconds(expires_in: int) -> str:
#     """Return ISO timestamp for expiry (stored as string)."""
#     return (_now() + timedelta(seconds=expires_in)).isoformat()


# def save_tokens(access_token: str, refresh_token: Optional[str], expires_in: int) -> None:
#     """Persist tokens into cache and in-memory store."""
#     payload = {
#         "access_token": access_token,
#         "refresh_token": refresh_token,
#         "expires_at": _expires_at_from_seconds(expires_in),
#         "expires_in": expires_in,
#     }
#     try:
#         frappe.cache().set_value(REDIS_KEY, json.dumps(payload))
#         # Optionally set Redis key TTL so it auto-expires
#         try:
#             frappe.cache().expire(REDIS_KEY, int(expires_in))
#         except Exception:
#             # Not all cache backends implement expire in same way; ignore if absent
#             pass
#     except Exception as e:
#         frappe.log_error(f"Failed to save EIMS tokens to cache: {str(e)}", "EIMS Integration")
#     # update in-memory
#     _TOKEN_CACHE.update(payload)


# def load_tokens() -> Optional[Dict[str, Any]]:
#     """Load tokens from in-memory cache first, fallback to persistent cache."""
#     # prefer in-memory if present
#     if _TOKEN_CACHE.get("access_token"):
#         return dict(_TOKEN_CACHE)

#     try:
#         raw = frappe.cache().get_value(REDIS_KEY)
#         if not raw:
#             return None
#         data = json.loads(raw)
#         # normalize into in-memory cache for subsequent fast reads
#         _TOKEN_CACHE.update(data)
#         return data
#     except Exception as e:
#         frappe.log_error(f"Failed to load EIMS tokens from cache: {str(e)}", "EIMS Integration")
#         return None


# def _is_token_valid(data: Dict[str, Any], margin_seconds: int = 30) -> bool:
#     """Return True if access token exists and isn't expired (with margin)."""
#     if not data:
#         return False
#     expires_at = data.get("expires_at")
#     if not expires_at:
#         return False
#     try:
#         expires_dt = datetime.fromisoformat(expires_at)
#         return expires_dt > (_now() + timedelta(seconds=margin_seconds))
#     except Exception:
#         return False


# def login_eims(base_url: str) -> str:
#     """
#     Login to EIMS and return access token.
#     Raises a frappe.ValidationError on failure.
#     """
#     creds = get_auth_credentials()
#     login_url = f"{base_url.rstrip('/')}/auth/login"
#     try:
#         resp = requests.post(login_url, json=creds, timeout=30)
#         resp.raise_for_status()
#         data = resp.json().get("data", {}) or {}
#     except requests.RequestException as e:
#         frappe.log_error(f"EIMS login request failed: {str(e)}", "EIMS Integration")
#         frappe.throw("EIMS login failed")
#     access_token = data.get("accessToken")
#     refresh_token = data.get("refreshToken")
#     expires_in = int(data.get("expiresIn", 3600))

#     if not access_token:
#         frappe.log_error(f"EIMS login response missing accessToken: {resp.text if 'resp' in locals() else ''}", "EIMS Integration")
#         frappe.throw("Login failed: no access token returned from EIMS")

#     save_tokens(access_token, refresh_token, expires_in)
#     return access_token


# def refresh_eims_token(base_url: str) -> Optional[str]:
#     """
#     Use refresh token to obtain a new access token. Returns the new token or None.
#     """
#     tokens = load_tokens()
#     refresh_token = tokens.get("refresh_token") if tokens else None
#     if not refresh_token:
#         return None

#     refresh_url = f"{base_url.rstrip('/')}/auth/refresh-token"
#     try:
#         resp = requests.post(refresh_url, json={"refreshToken": refresh_token}, timeout=30)
#         resp.raise_for_status()
#         data = resp.json().get("data", {}) or {}
#     except requests.RequestException as e:
#         frappe.log_error(f"EIMS token refresh failed: {str(e)}", "EIMS Integration")
#         return None

#     access_token = data.get("accessToken")
#     refresh_token_new = data.get("refreshToken") or refresh_token
#     expires_in = int(data.get("expiresIn", 3600))

#     if access_token:
#         save_tokens(access_token, refresh_token_new, expires_in)
#         return access_token

#     return None


# def get_eims_access_token(base_url: str) -> str:
#     """
#     Return a valid access token. Attempt to use cached token, then refresh, then login.
#     """
#     tokens = load_tokens()
#     if tokens and _is_token_valid(tokens):
#         return tokens["access_token"]

#     # try refresh flow
#     new_token = refresh_eims_token(base_url)
#     if new_token:
#         return new_token

#     # fallback to login
#     return login_eims(base_url)


#endpoint and headers
