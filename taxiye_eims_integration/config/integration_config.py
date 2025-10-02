"""
Configuration settings for Taxiye EIMS Integration
"""

# EIMS API Configuration
EIMS_CONFIG = {
    "base_url": "http://core.mor.gov.et",
    "api_version": "v1",
    "timeout": 30,
    "max_retries": 5,
    "retry_delay": 2,
    "rate_limit_delay": 10
}

# Tax Configuration
TAX_CONFIG = {
    "vat_rate": 0.15,  # 15% VAT
    "currency": "ETB"
}

# Commission Configuration
COMMISSION_CONFIG = {
    "default_rate": 0.15,  # 15% default commission
    "min_rate": 0.0,
    "max_rate": 1.0
}

# Validation Rules
VALIDATION_RULES = {
    "tin_length": {
        "min": 9,
        "max": 12
    },
    "phone_length": {
        "min": 10,
        "max": 15
    },
    "amount_precision": 2
}

# Status Options
STATUS_OPTIONS = {
    "trip_status": ["pending", "in_progress", "completed", "cancelled"],
    "invoice_status": ["Pending", "Sent to EIMS", "Completed", "Failed"],
    "receipt_status": ["Pending", "Created", "Acknowledged", "Failed"],
    "settlement_status": ["Pending", "Settled", "Failed"],
    "payment_status": ["Unpaid", "Paid"],
    "payment_method": ["Cash", "Bank"]
}

# Error Messages
ERROR_MESSAGES = {
    "INVALID_TIN": "Invalid TIN number format",
    "INVALID_PHONE": "Invalid phone number format",
    "INVALID_AMOUNT": "Invalid amount value",
    "INVALID_DATE": "Invalid date format",
    "INVALID_TIME": "Invalid time format",
    "MISSING_REQUIRED_FIELD": "Required field is missing",
    "EIMS_API_ERROR": "EIMS API error",
    "AUTHENTICATION_FAILED": "Authentication failed",
    "INVOICE_NOT_FOUND": "Invoice not found",
    "RECEIPT_NOT_FOUND": "Receipt not found",
    "SETTLEMENT_NOT_FOUND": "Settlement not found"
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "taxiye_eims_integration.log"
}

# Webhook Configuration
WEBHOOK_CONFIG = {
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 5
}

# Cache Configuration
CACHE_CONFIG = {
    "token_expiry_margin": 30,  # seconds
    "refresh_token_expiry": 7 * 24 * 60 * 60,  # 7 days in seconds
    "redis_keys": {
        "access_token": "eims:access_token",
        "refresh_token": "eims:refresh_token",
        "expires_in": "eims:expires_in"
    }
}
