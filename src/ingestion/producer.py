"""
Kafka producer for Coinbase data replay
"""
import os
import json
import time
import signal
import sys
import logging
from typing import Optional
import pandas as pd
from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class CoinbaseIngestor:
    """Ingests Coinbase data and publishes to Kafka"""
    
    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.topic = os.getenv("KAFKA_TOPIC", "coinbase-trades")
        # Use absolute path in Docker, relative path for local development
        default_data_file = os.getenv("DATA_FILE", "data/replay_10min.csv")
        # If running in Docker (/app) or locally, handle both cases
        if os.path.exists("/app/data/replay_10min.csv"):
            self.data_file = "/app/data/replay_10min.csv"
        elif os.path.exists(default_data_file):
            self.data_file = default_data_file
        else:
            # Try relative to script location
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            potential_path = os.path.join(script_dir, "data", "replay_10min.csv")
            self.data_file = potential_path if os.path.exists(potential_path) else default_data_file
        self.replay_speed = float(os.getenv("REPLAY_SPEED", "1.0"))
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Initialize Kafka producer with retry configuration
        self.producer = None
        self._init_producer()
    
    def _init_producer(self, retries=5, backoff=1.0):
        """Initialize Kafka producer with retry logic"""
        for attempt in range(retries):
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers.split(','),
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None,
                    acks='all',
                    retries=3,
                    max_in_flight_requests_per_connection=1,
                    enable_idempotence=True
                )
                logger.info(f"Kafka producer initialized: {self.bootstrap_servers}")
                return
            except Exception as e:
                if attempt < retries - 1:
                    wait_time = backoff * (2 ** attempt)
                    logger.warning(f"Failed to connect to Kafka (attempt {attempt + 1}/{retries}): {e}")
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to initialize Kafka producer after {retries} attempts")
                    raise
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def _reconnect_if_needed(self):
        """Check and reconnect if producer is disconnected"""
        try:
            # Simple check - try to get metadata
            self.producer.list_topics(timeout=1)
        except Exception as e:
            logger.warning(f"Producer disconnected: {e}, reconnecting...")
            self._init_producer()
    
    def load_data(self) -> pd.DataFrame:
        """Load Coinbase data from CSV"""
        try:
            # Check if file exists
            if not os.path.exists(self.data_file):
                raise FileNotFoundError(f"Data file not found: {self.data_file}")
            
            df = pd.read_csv(self.data_file)
            logger.info(f"Loaded {len(df)} records from {self.data_file}")
            return df
        except FileNotFoundError:
            logger.error(f"Data file not found: {self.data_file}")
            logger.info("Please ensure data/replay_10min.csv exists or set DATA_FILE environment variable")
            raise
        except Exception as e:
            logger.error(f"Failed to load data file: {e}")
            raise
    
    def replay_data(self, df: pd.DataFrame):
        """Replay data to Kafka with configurable speed"""
        if len(df) == 0:
            logger.warning("No data to replay")
            return
        
        # Calculate time intervals
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            time_diffs = df['timestamp'].diff().fillna(pd.Timedelta(seconds=0))
        else:
            # If no timestamp, assume uniform distribution over 10 minutes
            total_time = 10 * 60  # 10 minutes in seconds
            interval = total_time / len(df)
            time_diffs = pd.Series([pd.Timedelta(seconds=interval)] * len(df))
        
        logger.info(f"Starting replay at {self.replay_speed}x speed...")
        
        for idx, row in df.iterrows():
            if not self.running:
                break
            
            # Convert row to dict and prepare message
            message = row.to_dict()
            # Convert any non-serializable types
            for key, value in message.items():
                if pd.isna(value):
                    message[key] = None
                elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
                    message[key] = str(value)
            
            # Send to Kafka
            try:
                self._reconnect_if_needed()
                
                future = self.producer.send(
                    self.topic,
                    key=str(idx),
                    value=message
                )
                
                # Wait for send confirmation (with timeout)
                future.get(timeout=10)
                
                if idx % 100 == 0:
                    logger.info(f"Sent {idx + 1}/{len(df)} messages")
            
            except KafkaError as e:
                logger.error(f"Kafka error: {e}")
                # Retry connection
                self._reconnect_if_needed()
                continue
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                continue
            
            # Sleep based on replay speed
            if idx < len(df) - 1:
                sleep_time = time_diffs.iloc[idx + 1].total_seconds() / self.replay_speed
                time.sleep(max(0, sleep_time))
        
        # Flush remaining messages
        self.producer.flush()
        logger.info("Replay completed")
    
    def run(self):
        """Main run loop"""
        try:
            df = self.load_data()
            self.replay_data(df)
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Error in run loop: {e}")
            raise
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down producer...")
        if self.producer:
            self.producer.flush()
            self.producer.close(timeout=10)
        logger.info("Producer shut down")


def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    ingestor = CoinbaseIngestor()
    ingestor.run()


if __name__ == "__main__":
    main()

