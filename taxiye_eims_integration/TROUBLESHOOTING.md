# Troubleshooting Guide - Taxiye EIMS Integration

## Common Issues and Solutions

### 1. 406 Sequence Error (Document Number/Invoice Counter)

**Error Message:**

```json
{
  "statusCode": 406,
  "message": "RULE VALIDATION ERROR",
  "body": [
    {
      "portion": "DocumentDetails",
      "errorMessage": [
        "7001: (id) Document number error. : Document number is not in correct sequence expected : 19"
      ]
    },
    {
      "portion": "SourceSystem",
      "errorMessage": [
        "7015: (id) Invoice Counter is not correct. : Invoice counter is not correct expected : 19"
      ]
    }
  ]
}
```

**Cause:** Your local system's sequence numbers are out of sync with EIMS.

**Solution:**

#### Step 1: Check Current Sequence

```bash
# Call this endpoint to see your current sequence
POST /api/method/taxiye_eims_integration.api.sequence_sync.get_current_sequence
```

#### Step 2: Sync with EIMS Expected Values

```bash
# Use the values from the error message (19, 19 in your case)
POST /api/method/taxiye_eims_integration.api.sequence_sync.sync_sequence_with_eims
{
  "document_number": 19,
  "invoice_counter": 19
}
```

#### Step 3: Test with Correct Sequence

```bash
# Test your invoice with the correct sequence
POST /api/method/taxiye_eims_integration.api.debug_invoice.test_invoice_with_sequence
{
  "document_number": 19,
  "invoice_counter": 19,
  "trip_id": "TRIP-001",
  "invoice_number": "INV-001",
  "taxi_provider_name": "Test Driver",
  "taxi_provider_tin": "1234567890",
  "taxi_provider_address": "Addis Ababa",
  "taxi_provider_phone": "912345678",
  "date": "2025-01-15",
  "time": "14:30:00",
  "description": "Test trip",
  "reference": "TRIP-001",
  "base_fare": 100.0,
  "commission_amount": 15.0,
  "tax": 17.25,
  "amount": 115.0,
  "total_payment": 132.25
}
```

### 2. Authentication Errors

**Error Message:**

```json
{
  "statusCode": 401,
  "message": "Unauthorized"
}
```

**Solution:**

1. Check your EIMS Settings configuration
2. Verify your credentials (Client ID, Client Secret, API Key, TIN)
3. Test connection:

```bash
POST /api/method/taxiye_eims_integration.api.sequence_sync.test_eims_connection
```

### 3. Invalid Payload Format

**Error Message:**

```json
{
  "statusCode": 400,
  "message": "Invalid request format"
}
```

**Solution:**

1. Use the debug endpoint to validate your payload:

```bash
POST /api/method/taxiye_eims_integration.api.debug_invoice.debug_invoice_payload
```

2. Check the generated payload against EIMS requirements

### 4. Rate Limiting

**Error Message:**

```json
{
  "message": "Too many requests!"
}
```

**Solution:**

- The app automatically handles rate limiting with exponential backoff
- Wait a few minutes before retrying
- Consider implementing request queuing for high-volume scenarios

## Debug Endpoints

### 1. Get Current Sequence

```bash
POST /api/method/taxiye_eims_integration.api.sequence_sync.get_current_sequence
```

### 2. Test EIMS Connection

```bash
POST /api/method/taxiye_eims_integration.api.sequence_sync.test_eims_connection
```

### 3. Debug Invoice Payload

```bash
POST /api/method/taxiye_eims_integration.api.debug_invoice.debug_invoice_payload
{
  "trip_id": "TRIP-001",
  "invoice_number": "INV-001",
  "taxi_provider_name": "Test Driver",
  "taxi_provider_tin": "1234567890",
  "taxi_provider_address": "Addis Ababa",
  "taxi_provider_phone": "912345678",
  "date": "2025-01-15",
  "time": "14:30:00",
  "description": "Test trip",
  "reference": "TRIP-001",
  "base_fare": 100.0,
  "commission_amount": 15.0,
  "tax": 17.25,
  "amount": 115.0,
  "total_payment": 132.25
}
```

### 4. Test with Specific Sequence

```bash
POST /api/method/taxiye_eims_integration.api.debug_invoice.test_invoice_with_sequence
{
  "document_number": 19,
  "invoice_counter": 19,
  "trip_id": "TRIP-001",
  "invoice_number": "INV-001",
  "taxi_provider_name": "Test Driver",
  "taxi_provider_tin": "1234567890",
  "taxi_provider_address": "Addis Ababa",
  "taxi_provider_phone": "912345678",
  "date": "2025-01-15",
  "time": "14:30:00",
  "description": "Test trip",
  "reference": "TRIP-001",
  "base_fare": 100.0,
  "commission_amount": 15.0,
  "tax": 17.25,
  "amount": 115.0,
  "total_payment": 132.25
}
```

## Manual Sequence Sync

If you need to manually sync your sequence with EIMS:

### Option 1: Using the API

```bash
POST /api/method/taxiye_eims_integration.api.sequence_sync.sync_sequence_with_eims
{
  "document_number": 19,
  "invoice_counter": 19
}
```

### Option 2: Direct Database Update (Advanced)

```sql
-- Check current sequence
SELECT document_number, invoice_counter FROM `tabTrip Invoice` ORDER BY creation DESC LIMIT 1;

-- Update sequence (be careful with this)
UPDATE `tabTrip Invoice`
SET document_number = 19, invoice_counter = 19
WHERE name = 'YOUR_LAST_INVOICE_NAME';
```

## Testing Your Integration

### 1. Test with Postman

Use this exact payload structure:

```json
{
  "BuyerDetails": {
    "City": null,
    "Email": null,
    "HouseNumber": null,
    "IdNumber": null,
    "IdType": "KID",
    "Tin": null,
    "LegalName": "Lidia Keralem",
    "Phone": null,
    "Region": "1",
    "Country": "70",
    "Zone": null,
    "Kebele": null,
    "VatNumber": null,
    "Wereda": null
  },
  "DocumentDetails": {
    "DocumentNumber": "19",
    "Date": "30-09-2025T00:00:00",
    "Type": "INV"
  },
  "ItemList": [
    {
      "Discount": 0,
      "ExciseTaxValue": 0,
      "HarmonizationCode": null,
      "NatureOfSupplies": "goods",
      "ItemCode": "trip1",
      "ProductDescription": "Taxi Service",
      "PreTaxValue": 10000,
      "Quantity": 1,
      "LineNumber": 1,
      "TaxAmount": 1500,
      "TaxCode": "VAT15",
      "TotalLineAmount": 11500.0,
      "Unit": "PCS",
      "UnitPrice": 10000
    }
  ],
  "PaymentDetails": {
    "Mode": "CASH",
    "PaymentTerm": "IMMIDIATE"
  },
  "ReferenceDetails": {
    "PreviousIrn": null,
    "RelatedDocument": null
  },
  "SellerDetails": {
    "City": null,
    "Email": "your-email@example.com",
    "HouseNumber": null,
    "LegalName": "Your Company Name",
    "Locality": null,
    "Phone": "+251912345678",
    "Region": "1",
    "SubCity": null,
    "Tin": "1234567890",
    "VatNumber": "1234567890",
    "Wereda": "1"
  },
  "SourceSystem": {
    "CashierName": null,
    "InvoiceCounter": 19,
    "SalesPersonName": null,
    "SystemNumber": "12345",
    "SystemType": "POS"
  },
  "TransactionType": "B2C",
  "ValueDetails": {
    "Discount": 0,
    "ExciseValue": 0,
    "IncomeWithholdValue": 0,
    "TaxValue": 1500.0,
    "TotalValue": 11500.0,
    "TransactionWithholdValue": 0,
    "InvoiceCurrency": "ETB"
  },
  "Version": "1"
}
```

### 2. Key Points for Testing

1. **Document Number**: Must match EIMS expected value (19 in your case)
2. **Invoice Counter**: Must match EIMS expected value (19 in your case)
3. **Date Format**: Use "DD-MM-YYYYTHH:MM:SS" format
4. **Payment Term**: Should be "IMMIDIATE" (note the typo in EIMS API)
5. **Tax Code**: Use "VAT15" for 15% VAT
6. **Transaction Type**: Use "B2C" for business-to-consumer

## Logs and Monitoring

### Check Frappe Logs

```bash
# Check error logs
tail -f logs/error.log

# Check access logs
tail -f logs/access.log
```

### Check EIMS Integration Logs

```bash
# Check specific EIMS logs
grep "EIMS" logs/error.log
```

## Common Configuration Issues

### 1. EIMS Settings Not Configured

- Navigate to EIMS Settings in your Frappe site
- Fill in all required fields
- Save the settings

### 2. Invalid Credentials

- Double-check your TIN, Client ID, Client Secret, API Key
- Ensure they match your EIMS account

### 3. Network Issues

- Check if your server can reach the EIMS API
- Verify firewall settings
- Test with curl:

```bash
curl -X GET "http://core.mor.gov.et/v1/test" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Getting Help

If you're still experiencing issues:

1. **Check the logs** for detailed error messages
2. **Use the debug endpoints** to validate your payload
3. **Test the sequence sync** to ensure proper numbering
4. **Contact support** with:
   - Error messages
   - Log files
   - Your payload structure
   - EIMS response details

## Quick Fix for Your Current Issue

Based on your error message, here's the quick fix:

1. **Sync your sequence to 19, 19:**

```bash
POST /api/method/taxiye_eims_integration.api.sequence_sync.sync_sequence_with_eims
{
  "document_number": 19,
  "invoice_counter": 19
}
```

2. **Test with the correct sequence:**

```bash
POST /api/method/taxiye_eims_integration.api.debug_invoice.test_invoice_with_sequence
{
  "document_number": 19,
  "invoice_counter": 19,
  // ... rest of your payload
}
```

3. **Use the generated payload** in your Postman test

This should resolve your 406 sequence error!
