"""
Real-time processing system for property data
"""
from typing import Dict, List, Optional, Callable, Any
import asyncio
from datetime import datetime
import logging
from kafka import KafkaProducer, KafkaConsumer
from redis import Redis
import json
import websockets
import threading
from queue import Queue
from dataclasses import dataclass

@dataclass
class Event:
    type: str
    data: Dict
    timestamp: datetime = datetime.utcnow()

class RealTimeProcessor:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.subscribers = {}
        self.event_queue = Queue()
        self._init_connections()
        
    def _init_connections(self):
        """Initialize connections to message brokers"""
        try:
            # Initialize Kafka producer
            self.producer = KafkaProducer(
                bootstrap_servers=self.config['kafka']['servers'],
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            
            # Initialize Redis for pub/sub
            self.redis = Redis(
                host=self.config['redis']['host'],
                port=self.config['redis']['port']
            )
            
            # Start event processing
            self._start_event_processing()
            
        except Exception as e:
            self.logger.error(f"Error initializing connections: {str(e)}")
            raise
            
    def _start_event_processing(self):
        """Start event processing thread"""
        def process_events():
            while True:
                try:
                    event = self.event_queue.get()
                    self._process_event(event)
                except Exception as e:
                    self.logger.error(f"Error processing event: {str(e)}")
                    
        thread = threading.Thread(target=process_events, daemon=True)
        thread.start()
        
    async def start_kafka_consumer(self, topics: List[str]):
        """Start Kafka consumer"""
        try:
            consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=self.config['kafka']['servers'],
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            
            for message in consumer:
                event = Event(
                    type=message.topic,
                    data=message.value
                )
                self.event_queue.put(event)
                
        except Exception as e:
            self.logger.error(f"Error in Kafka consumer: {str(e)}")
            raise
            
    async def start_websocket_server(self):
        """Start WebSocket server"""
        async def handler(websocket, path):
            try:
                # Register client
                client_id = str(id(websocket))
                self.subscribers[client_id] = websocket
                
                try:
                    async for message in websocket:
                        # Process incoming messages
                        data = json.loads(message)
                        event = Event(
                            type=data['type'],
                            data=data['data']
                        )
                        self.event_queue.put(event)
                        
                finally:
                    # Unregister client
                    del self.subscribers[client_id]
                    
            except Exception as e:
                self.logger.error(f"Error in WebSocket handler: {str(e)}")
                
        server = await websockets.serve(
            handler,
            self.config['websocket']['host'],
            self.config['websocket']['port']
        )
        
        await server.wait_closed()
        
    async def publish_event(self, event_type: str, data: Dict):
        """Publish event to all channels"""
        try:
            event = Event(type=event_type, data=data)
            
            # Add to processing queue
            self.event_queue.put(event)
            
            # Publish to Kafka
            await self._publish_to_kafka(event)
            
            # Publish to Redis
            await self._publish_to_redis(event)
            
            # Broadcast to WebSocket clients
            await self._broadcast_to_websocket(event)
            
        except Exception as e:
            self.logger.error(f"Error publishing event: {str(e)}")
            raise
            
    async def _publish_to_kafka(self, event: Event):
        """Publish event to Kafka"""
        try:
            self.producer.send(
                event.type,
                value={
                    'data': event.data,
                    'timestamp': event.timestamp.isoformat()
                }
            )
        except Exception as e:
            self.logger.error(f"Error publishing to Kafka: {str(e)}")
            raise
            
    async def _publish_to_redis(self, event: Event):
        """Publish event to Redis"""
        try:
            self.redis.publish(
                event.type,
                json.dumps({
                    'data': event.data,
                    'timestamp': event.timestamp.isoformat()
                })
            )
        except Exception as e:
            self.logger.error(f"Error publishing to Redis: {str(e)}")
            raise
            
    async def _broadcast_to_websocket(self, event: Event):
        """Broadcast event to WebSocket clients"""
        message = json.dumps({
            'type': event.type,
            'data': event.data,
            'timestamp': event.timestamp.isoformat()
        })
        
        # Broadcast to all connected clients
        for websocket in self.subscribers.values():
            try:
                await websocket.send(message)
            except Exception as e:
                self.logger.error(f"Error broadcasting to WebSocket: {str(e)}")
                
    def _process_event(self, event: Event):
        """Process event based on type"""
        try:
            # Property update events
            if event.type == 'property_update':
                self._handle_property_update(event.data)
                
            # Analysis events
            elif event.type == 'analysis_complete':
                self._handle_analysis_complete(event.data)
                
            # Validation events
            elif event.type == 'validation_complete':
                self._handle_validation_complete(event.data)
                
            # Market events
            elif event.type == 'market_update':
                self._handle_market_update(event.data)
                
        except Exception as e:
            self.logger.error(f"Error processing event: {str(e)}")
            
    def _handle_property_update(self, data: Dict):
        """Handle property update event"""
        try:
            # Update cache
            self.redis.set(
                f"property:{data['id']}",
                json.dumps(data),
                ex=3600  # 1 hour expiry
            )
            
            # Trigger notifications
            self._send_notifications('property_update', data)
            
        except Exception as e:
            self.logger.error(f"Error handling property update: {str(e)}")
            
    def _handle_analysis_complete(self, data: Dict):
        """Handle analysis complete event"""
        try:
            # Cache analysis results
            self.redis.set(
                f"analysis:{data['property_id']}:{data['type']}",
                json.dumps(data),
                ex=3600
            )
            
            # Trigger notifications
            self._send_notifications('analysis_complete', data)
            
        except Exception as e:
            self.logger.error(f"Error handling analysis complete: {str(e)}")
            
    def _handle_validation_complete(self, data: Dict):
        """Handle validation complete event"""
        try:
            # Cache validation results
            self.redis.set(
                f"validation:{data['property_id']}:{data['type']}",
                json.dumps(data),
                ex=3600
            )
            
            # Trigger notifications
            self._send_notifications('validation_complete', data)
            
        except Exception as e:
            self.logger.error(f"Error handling validation complete: {str(e)}")
            
    def _handle_market_update(self, data: Dict):
        """Handle market update event"""
        try:
            # Update market data cache
            self.redis.set(
                f"market:{data['region']}",
                json.dumps(data),
                ex=3600
            )
            
            # Trigger notifications
            self._send_notifications('market_update', data)
            
        except Exception as e:
            self.logger.error(f"Error handling market update: {str(e)}")
            
    def _send_notifications(self, event_type: str, data: Dict):
        """Send notifications for event"""
        try:
            # Add notification to queue
            notification = {
                'type': event_type,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.redis.rpush('notifications', json.dumps(notification))
            
        except Exception as e:
            self.logger.error(f"Error sending notifications: {str(e)}")
            
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Close Kafka producer
            self.producer.close()
            
            # Close Redis connection
            self.redis.close()
            
            # Close WebSocket connections
            for websocket in self.subscribers.values():
                await websocket.close()
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            raise
