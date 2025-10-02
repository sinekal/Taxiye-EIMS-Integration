# Taxiye EIMS Integration API Documentation

## Overview

This document describes the API endpoints for the Taxiye EIMS Integration app, which facilitates automated invoice reporting and tax compliance between MevinaiERP and Ethiopia's Electronic Invoice Management System (EIMS).

## Base URL

All API endpoints are relative to your Frappe site URL:

```
https://your-site.com/api/method/taxiye_eims_integration.api.[endpoint_name]
```

## Authentication

Most endpoints require authentication. Include the API key in the request headers:

```
Authorization: token [api_key]:[api_secret]
```

## Endpoints

### 1. Receive Completed Trip (Webhook)

**Endpoint:** `/api/method/taxiye_eims_integration.api.taxiye_webhook.receive_completed_trip`

**Method:** POST

**Description:** Receives completed trip data from Taxiye and initiates the invoice creation process.

**Request Body:**

```json
{
  "trip_id": "TRIP-001",
  "driver_id": "DRV-001",
  "driver_name": "John Doe",
  "driver_phone": "912345678",
  "driver_tin": "1234567890",
  "rider_name": "Jane Smith",
  "rider_phone": "987654321",
  "rider_tin": "0987654321",
  "base_fare": 100.0,
  "commission_rate": 0.15,
  "pickup_location": "Bole Airport",
  "dropoff_location": "Meskel Square",
  "trip_date": "2025-01-15",
  "trip_time": "14:30:00",
  "payment_method": "Cash",
  "status": "completed"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Trip processed successfully",
  "trip_id": "TRIP-001",
  "invoice_id": "INV-001",
  "settlement_id": "SET-001",
  "amounts": {
    "base_fare": 100.0,
    "commission_amount": 15.0,
    "vat_amount": 17.25,
    "total_amount": 132.25
  }
}
```

### 2. Create Invoice

**Endpoint:** `/api/method/taxiye_eims_integration.api.invoice.create_invoice`

**Method:** POST

**Description:** Creates an invoice in EIMS and stores it in MevinaiERP.

**Request Body:**

```json
{
  "trip_id": "TRIP-001",
  "invoice_number": "INV-001",
  "taxi_provider_name": "John Doe",
  "taxi_provider_tin": "1234567890",
  "taxi_provider_address": "Addis Ababa",
  "taxi_provider_phone": "912345678",
  "rider_name": "Jane Smith",
  "rider_phone": "987654321",
  "rider_tin": "0987654321",
  "date": "2025-01-15",
  "time": "14:30:00",
  "description": "Taxi service from Bole Airport to Meskel Square",
  "reference": "TRIP-001",
  "base_fare": 100.0,
  "commission_amount": 15.0,
  "tax": 17.25,
  "amount": 115.0,
  "total_payment": 132.25
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Invoice has been created successfully",
  "data": {
    "invoice_id": "INV-001",
    "invoice_number": "INV-001",
    "irn": "IRN-123456789",
    "signed_qr": "QR_CODE_DATA",
    "signed_invoice": "SIGNED_INVOICE_DATA",
    "acknowledged_date": "2025-01-15 14:30:00",
    "document_number": 1,
    "invoice_counter": 1,
    "status": "Succeed"
  }
}
```

### 3. Process Payment

**Endpoint:** `/api/method/taxiye_eims_integration.api.taxiye_webhook.process_payment`

**Method:** POST

**Description:** Processes payment for a completed trip and creates a receipt.

**Request Body:**

```json
{
  "invoice_id": "INV-001",
  "payment_method": "Cash",
  "payment_date": "2025-01-15"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Payment processed successfully",
  "invoice_id": "INV-001",
  "receipt_data": {
    "rrn": "RRN-123456789",
    "qr": "RECEIPT_QR_CODE",
    "status": "Acknowledged"
  }
}
```

### 4. Create Receipt

**Endpoint:** `/api/method/taxiye_eims_integration.api.receipt.create_receipt`

**Method:** POST

**Description:** Creates a receipt in EIMS for a paid invoice.

**Request Body:**

```json
{
  "invoice_id": "INV-001",
  "irn": "IRN-123456789",
  "status": "Created",
  "signer_qr": null,
  "payment": {
    "total_amount": 132.25,
    "vat_amount": 17.25,
    "commission_amount": 15.0,
    "date": "2025-01-15",
    "method": "Cash",
    "transactionNumber": null,
    "accountNumber": null
  }
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Receipt has been created successfully",
  "data": {
    "invoice_id": "INV-001",
    "rrn": "RRN-123456789",
    "qr": "RECEIPT_QR_CODE",
    "status": "Acknowledged"
  }
}
```

### 5. Get Trip Status

**Endpoint:** `/api/method/taxiye_eims_integration.api.taxiye_webhook.get_trip_status`

**Method:** POST

**Description:** Retrieves the status of a trip and its associated documents.

**Request Body:**

```json
{
  "trip_id": "TRIP-001"
}
```

**Response:**

```json
{
  "status": "success",
  "trip_id": "TRIP-001",
  "invoice": {
    "name": "INV-001",
    "trip_id": "TRIP-001",
    "status": "Completed",
    "settlement_status": "Settled",
    "irn": "IRN-123456789",
    "total_payment": 132.25
  },
  "receipt": {
    "name": "REC-001",
    "rrn": "RRN-123456789",
    "status": "Acknowledged",
    "payment_date": "2025-01-15"
  },
  "settlement": {
    "name": "SET-001",
    "driver_earning": 100.0,
    "taxiye_provider_earning": 15.0,
    "vat_paid": 17.25
  }
}
```

### 6. Send Receipt to Taxiye

**Endpoint:** `/api/method/taxiye_eims_integration.api.taxiye_webhook.send_receipt_to_taxiye`

**Method:** POST

**Description:** Sends the signed receipt back to Taxiye for rider access.

**Request Body:**

```json
{
  "invoice_id": "INV-001"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Receipt sent to Taxiye",
  "receipt_data": {
    "invoice_id": "INV-001",
    "rrn": "RRN-123456789",
    "signed_qr": "RECEIPT_QR_CODE",
    "payment_date": "2025-01-15",
    "total_payment": 132.25
  }
}
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "status": "error",
  "message": "Error description",
  "error_code": "ERROR_CODE"
}
```

### Common Error Codes

- `INVALID_DATA`: Invalid or missing required data
- `INVOICE_NOT_FOUND`: Invoice not found
- `EIMS_API_ERROR`: Error from EIMS API
- `AUTHENTICATION_FAILED`: Authentication failed
- `VALIDATION_ERROR`: Data validation failed

## Data Models

### Trip Data Model

```json
{
  "trip_id": "string (required)",
  "driver_id": "string (required)",
  "driver_name": "string (required)",
  "driver_phone": "string (required)",
  "driver_tin": "string (required)",
  "rider_name": "string (optional)",
  "rider_phone": "string (optional)",
  "rider_tin": "string (optional)",
  "base_fare": "number (required)",
  "commission_rate": "number (required, 0.0-1.0)",
  "pickup_location": "string (optional)",
  "dropoff_location": "string (optional)",
  "trip_date": "string (required, YYYY-MM-DD)",
  "trip_time": "string (required, HH:MM:SS)",
  "payment_method": "string (required, Cash/Bank)",
  "status": "string (required, completed)"
}
```

### Settlement Calculation

The settlement amounts are calculated as follows:

```javascript
commission_amount = base_fare * commission_rate;
vat_amount = (base_fare + commission_amount) * 0.15;
total_amount = base_fare + commission_amount + vat_amount;
```

### Settlement Allocation

- **Driver**: Receives the base fare
- **Hailing Provider**: Receives the commission amount
- **Revenue Authority**: Receives the VAT amount

## Integration Flow

1. **Receive Completed Trip**: Taxiye sends completed trip data
2. **Create Invoice**: MevinaiERP creates invoice in EIMS
3. **Receive IRN**: EIMS returns Invoice Reference Number
4. **Process Payment**: Payment is recorded and settlement calculated
5. **Create Receipt**: Receipt is generated in EIMS
6. **Send Receipt**: Signed receipt is sent back to Taxiye

## Rate Limiting

The API implements rate limiting for EIMS requests:

- Maximum 5 retries for failed requests
- Exponential backoff for rate limit errors
- Automatic retry for sequence errors (406/417)

## Security

- All sensitive data is encrypted
- API keys are required for authentication
- Input validation is performed on all endpoints
- Audit logging is implemented for all transactions

## Testing

Use the provided test suite to validate the integration:

```bash
cd apps/taxiye_eims_integration
python -m pytest tests/test_integration.py
```

## Support

For technical support or questions, contact:

- Email: sintayehu@mevinai.com
- Documentation: [Link to documentation]
- Issues: [Link to issue tracker]
