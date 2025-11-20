"""
Kafka consumer for feature engineering and prediction
"""
import os
import json
import logging
import signal
import sys
from typing import List, Dict, Any
from collections import deque
from kafka import KafkaConsumer
from kafka.errors import KafkaError

from ..features.feature_engineering import FeatureEngine

logger = logging.getLogger(__name__)


class FeatureService:
    """Consumes Kafka messages and performs feature engineering"""
    
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.input_topic = os.getenv("KAFKA_TOPIC", "coinbase-trades")
        self.output_topic = os.getenv("KAFKA_PREDICTION_TOPIC", "predictions")
        self.window_size = int(os.getenv("WINDOW_SIZE", "50"))
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Initialize feature engine
        self.feature_engine = FeatureEngine(window_size=self.window_size)
        
        # Initialize Kafka consumer and producer
        self.consumer = None
        self.producer = None
        self._init_kafka()
    
    def _init_kafka(self, retries=5, backoff=1.0):
        """Initialize Kafka consumer and producer with retry logic"""
        for attempt in range(retries):
            try:
                # Consumer
                self.consumer = KafkaConsumer(
                    self.input_topic,
                    bootstrap_servers=self.bootstrap_servers.split(','),
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    key_deserializer=lambda k: k.decode('utf-8') if k else None,
                    auto_offset_reset='earliest',
                    enable_auto_commit=True,
                    group_id='feature-service-group',
                    consumer_timeout_ms=1000
                )
                
                # Producer for predictions
                from kafka import KafkaProducer
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers.split(','),
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    acks='all',
                    retries=3
                )
                
                logger.info(f"Kafka consumer/producer initialized: {self.bootstrap_servers}")
                return
            except Exception as e:
                if attempt < retries - 1:
                    wait_time = backoff * (2 ** attempt)
                    logger.warning(f"Failed to connect to Kafka (attempt {attempt + 1}/{retries}): {e}")
                    logger.info(f"Retrying in {wait_time} seconds...")
                    import time
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to initialize Kafka after {retries} attempts")
                    raise
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def _reconnect_if_needed(self):
        """Check and reconnect if needed"""
        try:
            # Check consumer
            self.consumer.list_consumer_groups(timeout=1)
        except Exception as e:
            logger.warning(f"Kafka connection lost: {e}, reconnecting...")
            self._init_kafka()
    
    def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single message and extract features
        
        Returns:
            Feature dict with ret_mean, ret_std, n, or None if window not ready
        """
        try:
            # Extract price/return information
            # Assuming message has 'price' or 'return' field
            price = message.get('price') or message.get('close') or message.get('value')
            
            if price is None:
                logger.warning("Message missing price information")
                return None
            
            # Update feature engine
            features = self.feature_engine.update(price)
            
            if features is None:
                # Window not ready yet
                return None
            
            return features
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return None
    
    def run(self):
        """Main consumption loop"""
        logger.info(f"Starting feature service, consuming from {self.input_topic}")
        message_count = 0
        
        try:
            while self.running:
                try:
                    # Poll for messages
                    message_pack = self.consumer.poll(timeout_ms=1000)
                    
                    if not message_pack:
                        continue
                    
                    for topic_partition, messages in message_pack.items():
                        for message in messages:
                            message_count += 1
                            
                            # Process message
                            features = self.process_message(message.value)
                            
                            if features is not None:
                                # Send to prediction topic
                                try:
                                    self.producer.send(
                                        self.output_topic,
                                        value=features
                                    )
                                    
                                    if message_count % 100 == 0:
                                        logger.info(f"Processed {message_count} messages, latest features: {features}")
                                
                                except Exception as e:
                                    logger.error(f"Failed to send prediction: {e}")
                    
                    # Commit offsets
                    self.consumer.commit()
                
                except KafkaError as e:
                    logger.error(f"Kafka error: {e}")
                    self._reconnect_if_needed()
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    continue
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down feature service...")
        if self.consumer:
            self.consumer.close()
        if self.producer:
            self.producer.flush()
            self.producer.close()
        logger.info("Feature service shut down")


def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    service = FeatureService()
    service.run()


if __name__ == "__main__":
    main()

