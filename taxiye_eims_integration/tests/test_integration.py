import frappe
import unittest
from frappe.tests import IntegrationTestCase
from taxiye_eims_integration.utils.settlement import calculate_settlement_amounts, create_trip_settlement
from taxiye_eims_integration.api.fetch_trips import clean_tin_no, clean_phone


class TestTaxiyeEIMSIntegration(IntegrationTestCase):
    """Integration tests for Taxiye EIMS Integration"""
    
    def setUp(self):
        """Set up test data"""
        self.test_base_fare = 100.0
        self.test_commission_rate = 0.15  # 15%
        
    def test_settlement_calculation(self):
        """Test settlement amount calculations"""
        amounts = calculate_settlement_amounts(self.test_base_fare, self.test_commission_rate)
        
        # Verify calculations
        expected_commission = 100.0 * 0.15  # 15.0
        expected_vat = (100.0 + 15.0) * 0.15  # 17.25
        expected_total = 100.0 + 15.0 + 17.25  # 132.25
        
        self.assertEqual(amounts["base_fare"], 100.0)
        self.assertEqual(amounts["commission_amount"], expected_commission)
        self.assertEqual(amounts["vat_amount"], expected_vat)
        self.assertEqual(amounts["total_amount"], expected_total)
    
    def test_tin_cleaning(self):
        """Test TIN number cleaning"""
        # Test valid TIN
        clean_tin = clean_tin_no("1234567890")
        self.assertEqual(clean_tin, "1234567890")
        
        # Test TIN with dashes and spaces
        clean_tin = clean_tin_no("123-456-7890")
        self.assertEqual(clean_tin, "1234567890")
        
        # Test invalid TIN (too short)
        clean_tin = clean_tin_no("123")
        self.assertEqual(clean_tin, "")
        
        # Test empty TIN
        clean_tin = clean_tin_no("")
        self.assertEqual(clean_tin, "")
    
    def test_phone_cleaning(self):
        """Test phone number cleaning"""
        # Test phone with country code
        clean_phone_num = clean_phone("+251912345678")
        self.assertEqual(clean_phone_num, "+251912345678")
        
        # Test phone without country code
        clean_phone_num = clean_phone("912345678")
        self.assertEqual(clean_phone_num, "+251912345678")
        
        # Test phone with spaces and dashes
        clean_phone_num = clean_phone("+251 912 345 678")
        self.assertEqual(clean_phone_num, "+251912345678")
        
        # Test empty phone
        clean_phone_num = clean_phone("")
        self.assertEqual(clean_phone_num, "")
    
    def test_eims_settings_creation(self):
        """Test EIMS Settings creation"""
        # Create test EIMS Settings
        settings = frappe.new_doc("EIMS Settings")
        settings.legalname = "Test Company"
        settings.email = "test@example.com"
        settings.phone = "912345678"
        settings.region = "Addis Ababa"
        settings.city = "Addis Ababa"
        settings.woreda = "Test Woreda"
        settings.tin = "1234567890"
        settings.client_id = "test_client_id"
        settings.client_secret = "test_client_secret"
        settings.api_key = "test_api_key"
        settings.mor_base_url = "http://test.mor.gov.et"
        settings.seller_tin = "1234567890"
        settings.systemnumber = "12345"
        settings.systemtype = "POS"
        
        settings.insert()
        
        # Verify creation
        self.assertTrue(settings.name)
        self.assertEqual(settings.legalname, "Test Company")
        
        # Clean up
        settings.delete()
    
    def test_trip_invoice_creation(self):
        """Test Trip Invoice creation"""
        # Create test invoice
        invoice = frappe.new_doc("Trip Invoice")
        invoice.trip_id = "TEST-TRIP-001"
        invoice.taxi_provider_name = "Test Driver"
        invoice.taxi_provider_tin = "1234567890"
        invoice.taxi_provider_phone = "912345678"
        invoice.date = "2025-01-01"
        invoice.time = "10:00:00"
        invoice.reference = "TEST-REF-001"
        invoice.base_fare = 100.0
        invoice.commission_rate = 0.15
        invoice.commission_amount = 15.0
        invoice.tax = 17.25
        invoice.amount = 115.0
        invoice.total_payment = 132.25
        invoice.status = "Pending"
        invoice.settlement_status = "Pending"
        
        invoice.insert()
        
        # Verify creation
        self.assertTrue(invoice.name)
        self.assertEqual(invoice.trip_id, "TEST-TRIP-001")
        self.assertEqual(invoice.base_fare, 100.0)
        
        # Clean up
        invoice.delete()
    
    def test_trip_receipt_creation(self):
        """Test Trip Receipt creation"""
        # First create an invoice
        invoice = frappe.new_doc("Trip Invoice")
        invoice.trip_id = "TEST-TRIP-002"
        invoice.taxi_provider_name = "Test Driver"
        invoice.taxi_provider_tin = "1234567890"
        invoice.date = "2025-01-01"
        invoice.reference = "TEST-REF-002"
        invoice.base_fare = 100.0
        invoice.commission_rate = 0.15
        invoice.commission_amount = 15.0
        invoice.tax = 17.25
        invoice.amount = 115.0
        invoice.total_payment = 132.25
        invoice.status = "Completed"
        invoice.irn = "TEST-IRN-002"
        invoice.insert()
        
        # Create receipt
        receipt = frappe.new_doc("Trip Receipt")
        receipt.invoice_id = invoice.name
        receipt.irn = "TEST-IRN-002"
        receipt.rrn = "TEST-RRN-002"
        receipt.payment_date = "2025-01-01"
        receipt.payment_method = "Cash"
        receipt.base_fare = 100.0
        receipt.commission_amount = 15.0
        receipt.tax = 17.25
        receipt.amount = 115.0
        receipt.total_payment = 132.25
        receipt.status = "Created"
        
        receipt.insert()
        
        # Verify creation
        self.assertTrue(receipt.name)
        self.assertEqual(receipt.invoice_id, invoice.name)
        self.assertEqual(receipt.irn, "TEST-IRN-002")
        
        # Clean up
        receipt.delete()
        invoice.delete()
    
    def test_trip_settlement_creation(self):
        """Test Trip Settlement creation"""
        # First create an invoice
        invoice = frappe.new_doc("Trip Invoice")
        invoice.trip_id = "TEST-TRIP-003"
        invoice.taxi_provider_name = "Test Driver"
        invoice.taxi_provider_tin = "1234567890"
        invoice.date = "2025-01-01"
        invoice.reference = "TEST-REF-003"
        invoice.base_fare = 100.0
        invoice.commission_rate = 0.15
        invoice.commission_amount = 15.0
        invoice.tax = 17.25
        invoice.amount = 115.0
        invoice.total_payment = 132.25
        invoice.status = "Completed"
        invoice.insert()
        
        # Create settlement
        settlement = frappe.new_doc("Trip Settlement")
        settlement.invoice_id = invoice.name
        settlement.driver_earning = 100.0
        settlement.taxiye_provider_earning = 15.0
        settlement.vat_paid = 17.25
        
        settlement.insert()
        
        # Verify creation
        self.assertTrue(settlement.name)
        self.assertEqual(settlement.invoice_id, invoice.name)
        self.assertEqual(settlement.driver_earning, 100.0)
        self.assertEqual(settlement.taxiye_provider_earning, 15.0)
        self.assertEqual(settlement.vat_paid, 17.25)
        
        # Clean up
        settlement.delete()
        invoice.delete()


if __name__ == "__main__":
    unittest.main()
