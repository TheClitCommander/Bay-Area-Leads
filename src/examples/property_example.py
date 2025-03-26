"""
Example showing how all our models work together
"""
import logging
from datetime import datetime
from typing import Dict, List
from sqlalchemy.orm import Session
from ..models.property_models import (
    Property, Owner, Transaction, Permit, 
    Violation, PropertyScore, UtilityRecord
)
from ..models.system_models import (
    DataSource, CollectionRun, DataValidation,
    SystemConfig, ProcessingJob, APIUsage
)

class PropertyExample:
    """Shows how everything works together with a real example"""
    
    def __init__(self, session: Session):
        self.session = session
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_example_property(self):
        """Creates an example property with all related data"""
        try:
            # 1. Create the owner (The People Folder 👥)
            owner = Owner(
                name="Jane Smith",
                mailing_address="123 Main St, Brunswick, ME",
                owner_type="individual",
                phone="207-555-0123",
                email="jane@email.com"
            )
            self.session.add(owner)
            self.session.flush()  # This gets us the owner.id

            # 2. Create the property (The Main Folder 📁)
            property = Property(
                parcel_id="BRU123456",
                address="456 Pine St",
                city="Brunswick",
                state="ME",
                zipcode="04011",
                property_type="residential",
                year_built=1985,
                square_feet=2000,
                bedrooms=3,
                bathrooms=2,
                land_value=100000,
                building_value=200000,
                total_value=300000,
                owner_id=owner.id
            )
            self.session.add(property)
            self.session.flush()  # This gets us the property.id

            # 3. Add a transaction (The Money Folder 💰)
            transaction = Transaction(
                property_id=property.id,
                transaction_type="sale",
                date=datetime(2023, 6, 15),
                price=290000,
                seller="Previous Owner",
                buyer="Jane Smith",
                document_type="warranty_deed",
                document_number="2023-12345"
            )
            self.session.add(transaction)

            # 4. Add a permit (The Permission Folder 📋)
            permit = Permit(
                property_id=property.id,
                permit_type="renovation",
                permit_number="BRU-2023-789",
                description="Kitchen remodel",
                status="completed",
                issue_date=datetime(2023, 8, 1),
                completed_date=datetime(2023, 10, 15),
                estimated_cost=25000
            )
            self.session.add(permit)

            # 5. Add property score (The Report Card 📊)
            score = PropertyScore(
                property_id=property.id,
                total_score=0.85,
                occupation_type="landlord",
                confidence_score=0.9,
                value_score=0.8,
                location_score=0.9,
                condition_score=0.85,
                potential_score=0.87,
                risk_score=0.15
            )
            self.session.add(score)

            # 6. Add utility record (The Bills Folder 💡)
            utility = UtilityRecord(
                property_id=property.id,
                utility_type="water",
                account_number="W123456",
                service_status="active",
                usage=5000,
                units="gallons",
                reading_date=datetime(2024, 1, 15)
            )
            self.session.add(utility)

            # 7. Record the collection (The Diary 📔)
            source = DataSource(
                name="Brunswick Tax Records",
                source_type="assessor",
                url="https://brunswickme.gov/assessor",
                auth_type="none"
            )
            self.session.add(source)
            self.session.flush()

            collection = CollectionRun(
                source_id=source.id,
                start_time=datetime.now(),
                end_time=datetime.now(),
                status="completed",
                total_records=1,
                new_records=1
            )
            self.session.add(collection)

            # 8. Validate the data (The Check List ✅)
            validation = DataValidation(
                collection_run_id=collection.id,
                validation_type="completeness",
                field_name="total_value",
                expected_format="number",
                passed=True
            )
            self.session.add(validation)

            # 9. Track the processing (The To-Do List 📝)
            job = ProcessingJob(
                job_type="collect",
                parameters={"parcel_id": "BRU123456"},
                status="completed",
                result_summary={"success": True}
            )
            self.session.add(job)

            # 10. Record API usage (The Traffic Log 🚦)
            api_log = APIUsage(
                endpoint="/api/properties/BRU123456",
                method="GET",
                timestamp=datetime.now(),
                response_time=0.15,
                status_code=200
            )
            self.session.add(api_log)

            # Save everything
            self.session.commit()

            return {
                "success": True,
                "property_id": property.id,
                "message": "Created example property with all related data"
            }

        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error creating example: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def show_property_details(self, property_id: int) -> Dict:
        """Shows all the information we have about a property"""
        try:
            # Get the property and all related data
            property = self.session.query(Property).get(property_id)
            
            if not property:
                return {"error": "Property not found"}

            return {
                "property": {
                    "address": property.address,
                    "value": property.total_value,
                    "type": property.property_type
                },
                "owner": {
                    "name": property.owner.name,
                    "contact": property.owner.phone
                },
                "transactions": [{
                    "date": t.date,
                    "price": t.price,
                    "type": t.transaction_type
                } for t in property.transactions],
                "permits": [{
                    "type": p.permit_type,
                    "status": p.status,
                    "cost": p.estimated_cost
                } for p in property.permits],
                "scores": [{
                    "total": s.total_score,
                    "confidence": s.confidence_score,
                    "type": s.occupation_type
                } for s in property.scores],
                "utilities": [{
                    "type": u.utility_type,
                    "usage": u.usage,
                    "status": u.service_status
                } for u in property.utilities]
            }

        except Exception as e:
            self.logger.error(f"Error showing property details: {str(e)}")
            return {"error": str(e)}
