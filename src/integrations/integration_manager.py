"""
Integration manager for external systems and services
"""
from typing import Dict, List, Optional, Any
import requests
import json
import boto3
from datetime import datetime
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from sqlalchemy import create_engine
from elasticsearch import Elasticsearch

class IntegrationManager:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize connections
        self._init_connections()
        
    def _init_connections(self):
        """Initialize connections to external services"""
        try:
            # Initialize document storage
            if 's3' in self.config:
                self.s3 = boto3.client('s3',
                    aws_access_key_id=self.config['s3']['access_key'],
                    aws_secret_access_key=self.config['s3']['secret_key']
                )
            
            # Initialize search
            if 'elasticsearch' in self.config:
                self.es = Elasticsearch([self.config['elasticsearch']['host']])
                
            # Initialize database
            if 'database' in self.config:
                self.db_engine = create_engine(self.config['database']['url'])
                
        except Exception as e:
            self.logger.error(f"Error initializing connections: {str(e)}")
            
    def connect_tax_assessor(self, property_id: str) -> Dict:
        """Connect to tax assessor API"""
        try:
            response = requests.get(
                f"{self.config['tax_assessor']['url']}/property/{property_id}",
                headers={'Authorization': f"Bearer {self.config['tax_assessor']['api_key']}"}
            )
            return response.json()
        except Exception as e:
            self.logger.error(f"Error connecting to tax assessor: {str(e)}")
            return {}
            
    def connect_gis(self, lat: float, lon: float) -> Dict:
        """Connect to GIS system"""
        try:
            response = requests.get(
                f"{self.config['gis']['url']}/query",
                params={'lat': lat, 'lon': lon},
                headers={'Authorization': f"Bearer {self.config['gis']['api_key']}"}
            )
            return response.json()
        except Exception as e:
            self.logger.error(f"Error connecting to GIS: {str(e)}")
            return {}
            
    def store_document(self, document: Dict, metadata: Dict) -> str:
        """Store document in document management system"""
        try:
            # Create document key
            doc_key = f"properties/{metadata['type']}/{metadata['id']}/{datetime.now().isoformat()}"
            
            # Store in S3
            self.s3.put_object(
                Bucket=self.config['s3']['bucket'],
                Key=doc_key,
                Body=json.dumps(document),
                Metadata=metadata
            )
            
            return doc_key
        except Exception as e:
            self.logger.error(f"Error storing document: {str(e)}")
            return ""
            
    def process_workflow(self, property_data: Dict, workflow_type: str) -> Dict:
        """Process workflow for property data"""
        try:
            # Create workflow instance
            workflow = {
                'type': workflow_type,
                'property_id': property_data['id'],
                'status': 'pending',
                'steps': self._get_workflow_steps(workflow_type),
                'created_at': datetime.now().isoformat()
            }
            
            # Store workflow
            workflow_id = self._store_workflow(workflow)
            
            return {'workflow_id': workflow_id, 'status': 'pending'}
        except Exception as e:
            self.logger.error(f"Error processing workflow: {str(e)}")
            return {'error': str(e)}
            
    def send_notification(self, notification_type: str, data: Dict):
        """Send notification via email/SMS"""
        try:
            if notification_type == 'email':
                self._send_email(data)
            elif notification_type == 'sms':
                self._send_sms(data)
        except Exception as e:
            self.logger.error(f"Error sending notification: {str(e)}")
            
    def export_data(self, data: List[Dict], format: str) -> bytes:
        """Export data in specified format"""
        try:
            if format == 'csv':
                df = pd.DataFrame(data)
                return df.to_csv(index=False).encode()
            elif format == 'json':
                return json.dumps(data, indent=2).encode()
            elif format == 'excel':
                df = pd.DataFrame(data)
                excel_buffer = io.BytesIO()
                df.to_excel(excel_buffer, index=False)
                return excel_buffer.getvalue()
        except Exception as e:
            self.logger.error(f"Error exporting data: {str(e)}")
            return b""
            
    def import_data(self, data: bytes, format: str) -> List[Dict]:
        """Import data from specified format"""
        try:
            if format == 'csv':
                df = pd.read_csv(io.BytesIO(data))
                return df.to_dict('records')
            elif format == 'json':
                return json.loads(data)
            elif format == 'excel':
                df = pd.read_excel(io.BytesIO(data))
                return df.to_dict('records')
        except Exception as e:
            self.logger.error(f"Error importing data: {str(e)}")
            return []
            
    def audit_action(self, action: str, user: str, data: Dict):
        """Record audit entry"""
        try:
            audit_entry = {
                'action': action,
                'user': user,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            # Store in database
            with self.db_engine.connect() as conn:
                conn.execute(
                    "INSERT INTO audit_log (action, user_id, timestamp, data) VALUES (%s, %s, %s, %s)",
                    (action, user, audit_entry['timestamp'], json.dumps(data))
                )
                
        except Exception as e:
            self.logger.error(f"Error recording audit: {str(e)}")
            
    def generate_report(self, report_type: str, parameters: Dict) -> bytes:
        """Generate custom report"""
        try:
            # Get report template
            template = self._get_report_template(report_type)
            
            # Generate report
            if report_type == 'property_summary':
                return self._generate_property_summary(template, parameters)
            elif report_type == 'validation_report':
                return self._generate_validation_report(template, parameters)
            elif report_type == 'audit_report':
                return self._generate_audit_report(template, parameters)
                
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            return b""
            
    def search_properties(self, query: Dict) -> List[Dict]:
        """Search properties using Elasticsearch"""
        try:
            response = self.es.search(
                index="properties",
                body=query
            )
            
            return [hit['_source'] for hit in response['hits']['hits']]
        except Exception as e:
            self.logger.error(f"Error searching properties: {str(e)}")
            return []
            
    def manage_user(self, action: str, user_data: Dict) -> Dict:
        """Manage user accounts"""
        try:
            if action == 'create':
                return self._create_user(user_data)
            elif action == 'update':
                return self._update_user(user_data)
            elif action == 'delete':
                return self._delete_user(user_data['id'])
            elif action == 'get_permissions':
                return self._get_user_permissions(user_data['id'])
        except Exception as e:
            self.logger.error(f"Error managing user: {str(e)}")
            return {'error': str(e)}
            
    def _send_email(self, data: Dict):
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['email']['from']
            msg['To'] = data['to']
            msg['Subject'] = data['subject']
            
            msg.attach(MIMEText(data['body'], 'html'))
            
            with smtplib.SMTP(self.config['email']['host']) as server:
                server.starttls()
                server.login(
                    self.config['email']['username'],
                    self.config['email']['password']
                )
                server.send_message(msg)
                
        except Exception as e:
            self.logger.error(f"Error sending email: {str(e)}")
            
    def _send_sms(self, data: Dict):
        """Send SMS notification"""
        try:
            # Using AWS SNS for SMS
            sns = boto3.client('sns',
                aws_access_key_id=self.config['aws']['access_key'],
                aws_secret_access_key=self.config['aws']['secret_key']
            )
            
            sns.publish(
                PhoneNumber=data['phone'],
                Message=data['message']
            )
            
        except Exception as e:
            self.logger.error(f"Error sending SMS: {str(e)}")
            
    def _store_workflow(self, workflow: Dict) -> str:
        """Store workflow in database"""
        try:
            with self.db_engine.connect() as conn:
                result = conn.execute(
                    "INSERT INTO workflows (type, property_id, status, steps, created_at) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (workflow['type'], workflow['property_id'], workflow['status'],
                     json.dumps(workflow['steps']), workflow['created_at'])
                )
                return str(result.fetchone()[0])
        except Exception as e:
            self.logger.error(f"Error storing workflow: {str(e)}")
            return ""
            
    def _get_workflow_steps(self, workflow_type: str) -> List[Dict]:
        """Get steps for workflow type"""
        return {
            'property_review': [
                {'name': 'initial_review', 'status': 'pending'},
                {'name': 'validation', 'status': 'pending'},
                {'name': 'approval', 'status': 'pending'}
            ],
            'assessment': [
                {'name': 'data_collection', 'status': 'pending'},
                {'name': 'valuation', 'status': 'pending'},
                {'name': 'review', 'status': 'pending'}
            ]
        }.get(workflow_type, [])
