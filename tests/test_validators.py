"""
Tests for Brunswick data validators
"""
import pytest
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.validators.brunswick_enhanced_validator import BrunswickEnhancedValidator
from .sample_data import SAMPLE_BUSINESSES, SAMPLE_PROPERTIES, SAMPLE_LICENSES

@pytest.fixture
def validator():
    return BrunswickEnhancedValidator()

class TestBusinessValidation:
    def test_valid_business(self, validator):
        """Test validation of valid business data"""
        business = SAMPLE_BUSINESSES[0].copy()  # Brunswick Cafe
        results = validator.validate_business(business)
        assert all(r.is_valid for r in results), "Valid business should pass validation"
        
    def test_invalid_business_name(self, validator):
        """Test validation of invalid business name"""
        business = SAMPLE_BUSINESSES[0].copy()
        business['name'] = "A"  # Too short
        results = validator.validate_business(business)
        name_results = [r for r in results if r.field == 'name']
        assert any(not r.is_valid for r in name_results)
        assert any("too short" in r.message.lower() for r in name_results)
        
    def test_invalid_business_type(self, validator):
        """Test validation of invalid business type"""
        business = SAMPLE_BUSINESSES[0].copy()
        business['type'] = "INVALID_TYPE"
        results = validator.validate_business(business)
        type_results = [r for r in results if r.field == 'type']
        assert any(not r.is_valid for r in type_results)
        assert any("invalid business type" in r.message.lower() for r in type_results)
        
    def test_missing_required_permits(self, validator):
        """Test validation of missing required permits"""
        business = SAMPLE_BUSINESSES[0].copy()
        business['health_inspection'] = False
        results = validator.validate_business(business)
        permit_results = [r for r in results if r.field == 'health_inspection']
        assert any(not r.is_valid for r in permit_results)
        assert any("required permit missing" in r.message.lower() for r in permit_results)
        
    def test_invalid_address(self, validator):
        """Test validation of invalid address"""
        business = SAMPLE_BUSINESSES[0].copy()
        business['address'] = "123 Invalid St, Wrong City, ME 12345"
        results = validator.validate_business(business)
        address_results = [r for r in results if r.field == 'address']
        assert any(not r.is_valid for r in address_results)
        assert any("invalid address format" in r.message.lower() for r in address_results)

class TestPropertyValidation:
    def test_valid_property(self, validator):
        """Test validation of valid property data"""
        property = SAMPLE_PROPERTIES[0].copy()
        results = validator.validate_property(property)
        assert all(r.is_valid for r in results), "Valid property should pass validation"
        
    def test_invalid_map_lot(self, validator):
        """Test validation of invalid map-lot format"""
        property = SAMPLE_PROPERTIES[0].copy()
        property['map_lot'] = "123-45"  # Invalid format
        results = validator.validate_property(property)
        map_lot_results = [r for r in results if r.field == 'map_lot']
        assert any(not r.is_valid for r in map_lot_results)
        assert any("invalid map-lot format" in r.message.lower() for r in map_lot_results)
        
    def test_invalid_assessment(self, validator):
        """Test validation of invalid assessment value"""
        property = SAMPLE_PROPERTIES[0].copy()
        property['assessment'] = 100  # Too low
        results = validator.validate_property(property)
        assessment_results = [r for r in results if r.field == 'assessment']
        assert any(not r.is_valid for r in assessment_results)
        assert any("too low" in r.message.lower() for r in assessment_results)
        
    def test_invalid_zoning(self, validator):
        """Test validation of invalid zoning code"""
        property = SAMPLE_PROPERTIES[0].copy()
        property['zoning'] = "INVALID"
        results = validator.validate_property(property)
        zoning_results = [r for r in results if r.field == 'zoning']
        assert any(not r.is_valid for r in zoning_results)
        assert any("invalid zoning code" in r.message.lower() for r in zoning_results)

class TestLicenseValidation:
    def test_valid_license(self, validator):
        """Test validation of valid license data"""
        license = SAMPLE_LICENSES[0].copy()
        results = validator.validate_license(license)
        assert all(r.is_valid for r in results), "Valid license should pass validation"
        
    def test_invalid_license_number(self, validator):
        """Test validation of invalid license number"""
        license = SAMPLE_LICENSES[0].copy()
        license['license_number'] = "INVALID123"
        results = validator.validate_license(license)
        number_results = [r for r in results if r.field == 'license_number']
        assert any(not r.is_valid for r in number_results)
        assert any("invalid license number format" in r.message.lower() for r in number_results)
        
    def test_invalid_dates(self, validator):
        """Test validation of invalid dates"""
        license = SAMPLE_LICENSES[0].copy()
        future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        license['issue_date'] = future_date
        results = validator.validate_license(license)
        date_results = [r for r in results if r.field == 'issue_date']
        assert any(not r.is_valid for r in date_results)
        assert any("cannot be in the future" in r.message.lower() for r in date_results)
        
    def test_invalid_status(self, validator):
        """Test validation of invalid status"""
        license = SAMPLE_LICENSES[0].copy()
        license['status'] = "INVALID_STATUS"
        results = validator.validate_license(license)
        status_results = [r for r in results if r.field == 'status']
        assert any(not r.is_valid for r in status_results)
        assert any("invalid status" in r.message.lower() for r in status_results)
