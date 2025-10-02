# Taxiye EIMS Integration

A comprehensive Frappe-based integration app that enables seamless communication between MevinaiERP and Ethiopia's Electronic Invoice Management System (EIMS) for taxi services, automating invoice reporting and tax compliance.

## 🚀 Features

- **Complete Integration Flow**: End-to-end automation from trip completion to receipt generation
- **EIMS API Integration**: Seamless communication with Ethiopia's tax authority system
- **Automated Settlement**: Accurate calculation and allocation of earnings between drivers, providers, and tax authorities
- **Webhook Support**: Real-time data processing from Taxiye dispatching system
- **Comprehensive Error Handling**: Robust retry mechanisms and error recovery
- **Tax Compliance**: Automated VAT calculation and reporting (15% VAT)
- **Audit Trail**: Complete logging and tracking of all transactions

## 📋 Integration Flow

The app implements a complete 7-step integration process:

1. **Receive Completed Trip** - Taxiye sends completed trip data
2. **Create Invoice** - MevinaiERP creates invoice in EIMS
3. **Receive IRN** - EIMS returns Invoice Reference Number
4. **Process Payment** - Payment recording and settlement calculation
5. **Create Receipt** - Receipt generation in EIMS
6. **Receive Signed Receipt** - Digital receipt from EIMS
7. **Send Receipt to Taxiye** - Receipt delivery to rider

## 🏗️ Architecture

```
Taxiye → MevinaiERP → EIMS
   ↑         ↓         ↓
   ←─────────←─────────←
```

### Core Components

- **DocTypes**: EIMS Settings, Trip Invoice, Trip Receipt, Trip Settlement
- **API Layer**: Invoice creation, receipt processing, webhook handling
- **Utils**: Authentication, settlement calculations, data formatting
- **Configuration**: Settings management and validation rules

## 💰 Settlement Logic

### Commission Calculation

```python
commission_amount = base_fare * commission_rate
vat_amount = (base_fare + commission_amount) * 0.15
total_amount = base_fare + commission_amount + vat_amount
```

### Settlement Allocation

- **Driver**: Receives base fare (100% of base fare)
- **Hailing Provider**: Receives commission amount
- **Revenue Authority**: Receives VAT amount (15% of total revenue)

## 🛠️ Installation

### Prerequisites

- Frappe Framework (v15+)
- Python 3.10+
- Redis (for token caching)
- Valid EIMS credentials

### Installation Steps

1. **Clone the repository**:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/your-repo/taxiye_eims_integration --branch main
```

2. **Install the app**:

```bash
bench install-app taxiye_eims_integration
```

3. **Configure EIMS Settings**:

   - Navigate to EIMS Settings in your Frappe site
   - Enter your EIMS credentials (TIN, Client ID, Client Secret, API Key)
   - Configure your business information (legal name, address, etc.)

4. **Set up webhooks** (optional):
   - Configure Taxiye to send completed trips to the webhook endpoint
   - Set up receipt delivery webhook to Taxiye

## 🔧 Configuration

### EIMS Settings

Configure the following in EIMS Settings:

**Authentication**:

- TIN (Tax Identification Number)
- Client ID
- Client Secret
- API Key
- MoR Base URL

**Business Information**:

- Legal Name
- Email
- Phone Number
- Region, City, Subcity, Woreda
- House Number, Locality
- VAT Number
- System Number
- System Type (POS)

### API Endpoints

The app provides the following API endpoints:

- `POST /api/method/taxiye_eims_integration.api.taxiye_webhook.receive_completed_trip`
- `POST /api/method/taxiye_eims_integration.api.taxiye_webhook.process_payment`
- `POST /api/method/taxiye_eims_integration.api.taxiye_webhook.get_trip_status`
- `POST /api/method/taxiye_eims_integration.api.taxiye_webhook.send_receipt_to_taxiye`
- `POST /api/method/taxiye_eims_integration.api.invoice.create_invoice`
- `POST /api/method/taxiye_eims_integration.api.receipt.create_receipt`

## 📖 Usage

### 1. Receiving Completed Trips

Send a POST request to the webhook endpoint with trip data:

```json
{
  "trip_id": "TRIP-001",
  "driver_name": "John Doe",
  "driver_tin": "1234567890",
  "base_fare": 100.0,
  "commission_rate": 0.15,
  "trip_date": "2025-01-15",
  "trip_time": "14:30:00",
  "status": "completed"
}
```

### 2. Processing Payments

After invoice creation, process payment:

```json
{
  "invoice_id": "INV-001",
  "payment_method": "Cash",
  "payment_date": "2025-01-15"
}
```

### 3. Checking Trip Status

Query the status of any trip:

```json
{
  "trip_id": "TRIP-001"
}
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
cd apps/taxiye_eims_integration
python -m pytest tests/test_integration.py -v
```

The test suite covers:

- Settlement calculations
- Data validation
- DocType creation
- API endpoint functionality
- Error handling

## 📊 Monitoring

### Logs

- All API calls are logged with timestamps
- Error logs include detailed stack traces
- EIMS API responses are logged for debugging

### Audit Trail

- All invoice and receipt transactions are tracked
- Settlement records maintain complete audit history
- Status changes are logged with timestamps

## 🔒 Security

- **Encryption**: All sensitive data is encrypted using Frappe's encryption
- **Authentication**: API key authentication for all endpoints
- **Input Validation**: Comprehensive validation using Pydantic models
- **Rate Limiting**: Built-in rate limiting for EIMS API calls
- **Token Management**: Secure token storage and automatic refresh

## 🚨 Error Handling

The app implements comprehensive error handling:

- **Retry Logic**: Automatic retry for failed API calls (max 5 attempts)
- **Sequence Errors**: Handles EIMS sequence errors (406/417) with temporary invoice creation
- **Rate Limiting**: Exponential backoff for rate limit errors
- **Validation Errors**: Detailed error messages for invalid data
- **Network Errors**: Timeout handling and connection error recovery

## 📈 Performance

- **Connection Pooling**: Efficient HTTP connection management
- **Token Caching**: Redis-based token caching with automatic refresh
- **Batch Processing**: Support for batch invoice processing
- **Async Operations**: Non-blocking API calls where possible

## 🔄 Maintenance

### Regular Tasks

- Monitor EIMS API status and response times
- Review error logs for failed transactions
- Update EIMS credentials when they expire
- Backup settlement and invoice data

### Troubleshooting

**Common Issues**:

1. **Authentication Errors**: Check EIMS credentials in settings
2. **Sequence Errors**: App automatically handles with retry logic
3. **Rate Limiting**: App implements exponential backoff
4. **Network Timeouts**: Check network connectivity to EIMS

## 📞 Support

For technical support or questions:

- **Email**: sintayehu@mevinai.com
- **Documentation**: See `API_DOCUMENTATION.md`
- **Issues**: Create an issue in the repository

## 📄 License

This project is licensed under the MIT License - see the `license.txt` file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 Changelog

### Version 1.0.0

- Initial release
- Complete integration flow implementation
- EIMS API integration
- Settlement calculation logic
- Webhook support
- Comprehensive test suite
- API documentation

## 🎯 Roadmap

- [ ] Batch processing for multiple trips
- [ ] Advanced reporting and analytics
- [ ] Mobile app integration
- [ ] Multi-currency support
- [ ] Advanced settlement rules
- [ ] Real-time notifications
- [ ] Performance monitoring dashboard

---

**Built with ❤️ by Mevinai Team**
