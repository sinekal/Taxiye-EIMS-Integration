from datetime import datetime, timedelta, timezone
import frappe
from frappe import _  # type: ignore

def compute_commission(base_fare: float, commission_rate: float) -> float:
    # commission_amount = base_fare * commission_rate
    return float(base_fare) * float(commission_rate)

def compute_vat(base_fare: float, commission_amount: float, vat_rate: float = 0.15) -> float:
    # vat_amount = (base_fare + commission_amount) * 0.15
    return (float(base_fare) + float(commission_amount)) * float(vat_rate)

def compute_total(base_fare: float, commission_amount: float, vat_amount: float) -> float:
    return float(base_fare) + float(commission_amount) + float(vat_amount)




# Redis keys
REDIS_KEY_ACCESS = "access_token"
REDIS_KEY_REFRESH = "refresh_token"
REDIS_KEY_EXPIRES = "expires_in"


def set_token_in_redis(access_token, refresh_token, expires_sec):
    """Encrypt and store tokens in Redis with expiry."""
    r = frappe.cache()  # type: ignore # Redis cache
    eth_tz = timezone(timedelta(hours=3))
    expire_at = datetime.now(eth_tz) + timedelta(seconds=expires_sec)

    # Encrypt before storing
    if access_token:
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        encrypted_access_token = cipher_suite.encrypt(access_token.encode())
        r.set_value(REDIS_KEY_ACCESS, encrypted_access_token, expires_sec)
    if refresh_token:
        # keep refresh token for 7 days
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        encrypted_refresh_token = cipher_suite.encrypt(refresh_token.encode())
        r.set_value(REDIS_KEY_REFRESH, encrypted_refresh_token, 60 * 60 * 24 * 7)
    r.set_value(REDIS_KEY_EXPIRES, expire_at.isoformat(), expires_sec)


def get_token_from_redis():
    """Retrieve and decrypt tokens from Redis."""
    r = frappe.cache() # type: ignore
    encrypted_access = r.get_value(REDIS_KEY_ACCESS)
    encrypted_refresh = r.get_value(REDIS_KEY_REFRESH)
    expires_in_str = r.get_value(REDIS_KEY_EXPIRES)

    access_token, refresh_token, expires_in = None, None, None

    if encrypted_access:
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        try:
            decrypted_access = cipher_suite.decrypt(encrypted_access).decode()
            access_token = decrypted_access
        except Exception:
            frappe.log_error("Failed to decrypt access token") # type: ignore

    if encrypted_refresh:
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)
        try:
            decrypted_refresh = cipher_suite.decrypt(encrypted_refresh).decode()
            refresh_token = decrypted_refresh
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


import requests

base_url = "http://core.mor.gov.et"
client_id = "my_client_id"
client_secret = "my_client_secret"
api_key = "my_api_key"
tin = "my_tin"

access_token = login_eims(base_url, client_id, client_secret, api_key, tin)
def login_to_eims(base_url, client_id, client_secret, api_key, tin_number):
    """Perform login to obtain new access and refresh tokens."""
    login_url = f"{base_url}/auth/login"

    try:
        response = requests.post(
            login_url,
            json={
                "clientId": client_id,
                "clientSecret": client_secret,
                "apiKey": api_key,
                "tin": tin_number,
            },
        )
        response.raise_for_status()

        data = response.json().get("data", {})
        access_token = data.get("accessToken")
        refresh_token = data.get("refreshToken")
        expires_in_seconds = data.get("expiresIn", 3600)

        if not access_token:
            raise ValueError("EIMS login response missing accessToken")

        return access_token, refresh_token, expires_in_seconds

    except requests.RequestException as e:
        raise ValueError(f"EIMS login failed: {e}")
    except Exception as e:
        raise ValueError(f"Unexpected EIMS login error: {e}")


