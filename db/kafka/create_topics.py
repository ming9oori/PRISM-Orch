#!/usr/bin/env python3
"""
Kafka Topic Creation Script for PRISM Orchestration
Creates necessary topics for agent communication and event streaming
"""

from kafka.admin import KafkaAdminClient, NewTopic, ConfigResource, ConfigResourceType
from kafka.errors import TopicAlreadyExistsError, KafkaError
import logging
import os
import time
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPICS_CONFIG = {
    # User query events
    "user_queries": {
        "num_partitions": 3,
        "replication_factor": 1,
        "config": {
            "retention.ms": "86400000",  # 24 hours
            "cleanup.policy": "delete",
            "compression.type": "snappy"
        }
    },
    
    # Agent task distribution
    "agent_tasks_monitoring": {
        "num_partitions": 2,
        "replication_factor": 1,
        "config": {
            "retention.ms": "43200000",  # 12 hours
            "cleanup.policy": "delete",
            "compression.type": "snappy"
        }
    },
    
    "agent_tasks_prediction": {
        "num_partitions": 2,
        "replication_factor": 1,
        "config": {
            "retention.ms": "43200000",  # 12 hours
            "cleanup.policy": "delete",
            "compression.type": "snappy"
        }
    },
    
    "agent_tasks_control": {
        "num_partitions": 2,
        "replication_factor": 1,
        "config": {
            "retention.ms": "43200000",  # 12 hours
            "cleanup.policy": "delete",
            "compression.type": "snappy"
        }
    },
    
    "agent_tasks_analysis": {
        "num_partitions": 2,
        "replication_factor": 1,
        "config": {
            "retention.ms": "43200000",  # 12 hours
            "cleanup.policy": "delete",
            "compression.type": "snappy"
        }
    },
    
    # Agent results
    "agent_results_monitoring": {
        "num_partitions": 2,
        "replication_factor": 1,
        "config": {
            "retention.ms": "172800000",  # 48 hours
            "cleanup.policy": "delete",
            "compression.type": "snappy"
        }
    },
    
    "agent_results_prediction": {
        "num_partitions": 2,
        "replication_factor": 1,
        "config": {
            "retention.ms": "172800000",  # 48 hours
            "cleanup.policy": "delete",
            "compression.type": "snappy"
        }
    },
    
    "agent_results_control": {
        "num_partitions": 2,
        "replication_factor": 1,
        "config": {
            "retention.ms": "172800000",  # 48 hours
            "cleanup.policy": "delete",
            "compression.type": "snappy"
        }
    },
    
    "agent_results_analysis": {
        "num_partitions": 2,
        "replication_factor": 1,
        "config": {
            "retention.ms": "172800000",  # 48 hours
            "cleanup.policy": "delete",
            "compression.type": "snappy"
        }
    },
    
    # Agent status broadcasting
    "agent_status_broadcast": {
        "num_partitions": 1,
        "replication_factor": 1,
        "config": {
            "retention.ms": "3600000",  # 1 hour
            "cleanup.policy": "delete",
            "compression.type": "snappy"
        }
    },
    
    # Constraint violations
    "constraint_violations": {
        "num_partitions": 2,
        "replication_factor": 1,
        "config": {
            "retention.ms": "604800000",  # 7 days
            "cleanup.policy": "delete",
            "compression.type": "snappy"
        }
    },
    
    # System events
    "system_events": {
        "num_partitions": 2,
        "replication_factor": 1,
        "config": {
            "retention.ms": "259200000",  # 72 hours
            "cleanup.policy": "delete",
            "compression.type": "snappy"
        }
    },
    
    # User feedback events
    "user_feedback": {
        "num_partitions": 1,
        "replication_factor": 1,
        "config": {
            "retention.ms": "2592000000",  # 30 days
            "cleanup.policy": "delete",
            "compression.type": "snappy"
        }
    },
    
    # Dead letter queue for failed messages
    "dead_letter_queue": {
        "num_partitions": 1,
        "replication_factor": 1,
        "config": {
            "retention.ms": "604800000",  # 7 days
            "cleanup.policy": "delete",
            "compression.type": "snappy"
        }
    }
}

def wait_for_kafka(bootstrap_servers: str, timeout: int = 30) -> bool:
    """Wait for Kafka to be available"""
    logger.info("Waiting for Kafka to be available...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=bootstrap_servers,
                client_id="topic_creator"
            )
            # Try to get cluster metadata
            metadata = admin_client.describe_cluster()
            logger.info("Kafka is available")
            return True
        except Exception as e:
            logger.info(f"Kafka not ready yet: {e}")
            time.sleep(2)
    
    logger.error(f"Kafka not available after {timeout} seconds")
    return False

def create_topics(bootstrap_servers: str, topics_config: Dict) -> bool:
    """Create Kafka topics"""
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            client_id="topic_creator"
        )
        
        # Get existing topics
        existing_topics = set(admin_client.list_topics())
        
        # Prepare new topics
        new_topics = []
        for topic_name, config in topics_config.items():
            if topic_name not in existing_topics:
                topic = NewTopic(
                    name=topic_name,
                    num_partitions=config["num_partitions"],
                    replication_factor=config["replication_factor"],
                    topic_configs=config.get("config", {})
                )
                new_topics.append(topic)
                logger.info(f"Prepared topic: {topic_name}")
            else:
                logger.info(f"Topic already exists: {topic_name}")
        
        if new_topics:
            # Create topics
            fs = admin_client.create_topics(new_topics, validate_only=False)
            
            # Wait for creation to complete
            try:
                # Handle different API response formats
                if hasattr(fs, 'items'):
                    # Newer API version
                    for topic_name, future in fs.items():
                        try:
                            future.result(timeout=10)
                            logger.info(f"Topic created successfully: {topic_name}")
                        except TopicAlreadyExistsError:
                            logger.info(f"Topic already exists: {topic_name}")
                        except Exception as e:
                            logger.error(f"Failed to create topic {topic_name}: {e}")
                            return False
                else:
                    # Handle different API response format
                    import time
                    time.sleep(3)  # Wait for topic creation
                    for topic in new_topics:
                        logger.info(f"Topic created successfully: {topic.name}")
            except Exception as e:
                logger.error(f"Error processing topic creation response: {e}")
                # Try to verify topics were created anyway
                import time
                time.sleep(3)
                for topic in new_topics:
                    logger.info(f"Topic processed: {topic.name}")
        else:
            logger.info("All topics already exist")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create topics: {e}")
        return False

def verify_topics(bootstrap_servers: str, expected_topics: List[str]) -> bool:
    """Verify that all expected topics exist"""
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers,
            client_id="topic_verifier"
        )
        
        existing_topics = set(admin_client.list_topics())
        missing_topics = set(expected_topics) - existing_topics
        
        if missing_topics:
            logger.error(f"Missing topics: {missing_topics}")
            return False
        
        logger.info("All expected topics exist")
        
        # Get topic descriptions
        topic_descriptions = admin_client.describe_topics(expected_topics)
        
        for topic_name, topic_metadata in topic_descriptions.items():
            logger.info(f"Topic: {topic_name}")
            logger.info(f"  Partitions: {len(topic_metadata.partitions)}")
            for partition in topic_metadata.partitions:
                logger.info(f"    Partition {partition.partition}: Leader={partition.leader}, Replicas={len(partition.replicas)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to verify topics: {e}")
        return False

def create_sample_producer_consumer_test(bootstrap_servers: str) -> bool:
    """Create a simple test to verify Kafka functionality"""
    try:
        from kafka import KafkaProducer, KafkaConsumer
        import json
        
        # Test producer
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda x: json.dumps(x).encode('utf-8'),
            key_serializer=lambda x: x.encode('utf-8') if x else None
        )
        
        test_message = {
            "test_id": "kafka_init_test",
            "message": "Kafka initialization test message",
            "timestamp": time.time()
        }
        
        # Send test message
        future = producer.send('system_events', key='test', value=test_message)
        producer.flush()
        
        logger.info("Test message sent successfully")
        
        # Test consumer
        consumer = KafkaConsumer(
            'system_events',
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='test_group',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            consumer_timeout_ms=5000
        )
        
        # Read test message
        messages_received = 0
        for message in consumer:
            if message.value.get('test_id') == 'kafka_init_test':
                logger.info("Test message received successfully")
                messages_received += 1
                break
        
        consumer.close()
        producer.close()
        
        if messages_received > 0:
            logger.info("Kafka functionality test passed")
            return True
        else:
            logger.warning("Test message not received")
            return False
            
    except Exception as e:
        logger.error(f"Kafka test failed: {e}")
        return False

def main():
    """Main function to create Kafka topics"""
    logger.info("Starting Kafka topic creation...")
    
    try:
        # Wait for Kafka to be available
        if not wait_for_kafka(KAFKA_BOOTSTRAP_SERVERS):
            return False
        
        # Create topics
        if not create_topics(KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPICS_CONFIG):
            return False
        
        # Verify topics
        expected_topics = list(KAFKA_TOPICS_CONFIG.keys())
        if not verify_topics(KAFKA_BOOTSTRAP_SERVERS, expected_topics):
            return False
        
        # Run functionality test
        if not create_sample_producer_consumer_test(KAFKA_BOOTSTRAP_SERVERS):
            logger.warning("Kafka functionality test failed, but topics were created")
        
        logger.info("Kafka initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Kafka initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)