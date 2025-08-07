#!/usr/bin/env python3
"""
Weaviate Schema Initialization Script for PRISM Orchestration
Creates the ExternalKnowledge class and sets up the vector database schema
"""

import weaviate
import json
import os
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Weaviate connection configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "weaviate_api_key")

def get_weaviate_client():
    """Initialize and return Weaviate client"""
    try:
        client = weaviate.Client(
            url=WEAVIATE_URL,
            timeout_config=(5, 60)  # (connection, read) timeout
        )
        logger.info("Connected to Weaviate successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Weaviate: {e}")
        raise

def get_external_knowledge_schema() -> Dict[str, Any]:
    """Define the ExternalKnowledge class schema"""
    return {
        "class": "ExternalKnowledge",
        "description": "External knowledge documents for RAG system in orchestration module",
        "vectorizer": "none",  # Use manual vectors for now
        "properties": [
            {
                "name": "knowledge_id",
                "dataType": ["string"],
                "description": "UUID reference to PostgreSQL metadata table",
            },
            {
                "name": "document_title",
                "dataType": ["text"],
                "description": "Title of the document",
            },
            {
                "name": "content_text",
                "dataType": ["text"],
                "description": "Full document content for vectorization",
            },
            {
                "name": "document_type",
                "dataType": ["string"],
                "description": "Type of document (RESEARCH_PAPER, MANUAL, GUIDELINE, FAQ)",
            },
            {
                "name": "content_chunks",
                "dataType": ["text[]"],
                "description": "Chunked content for detailed retrieval",
            },
            {
                "name": "tags",
                "dataType": ["string[]"],
                "description": "Document tags for filtering",
            },
            {
                "name": "embedder_info",
                "dataType": ["string"],
                "description": "Information about the embedding model used",
            },
            {
                "name": "version",
                "dataType": ["string"],
                "description": "Document version",
            },
            {
                "name": "created_at",
                "dataType": ["date"],
                "description": "Document creation timestamp",
            },
            {
                "name": "metadata",
                "dataType": ["text"],
                "description": "Additional metadata as JSON string",
            }
        ],
        "vectorIndexConfig": {
            "distance": "cosine",
            "efConstruction": 256,
            "maxConnections": 64
        },
        "shardingConfig": {
            "virtualPerPhysical": 128,
            "desiredCount": 1,
            "actualCount": 1,
            "desiredVirtualCount": 128,
            "actualVirtualCount": 128,
            "key": "_id",
            "strategy": "hash",
            "function": "murmur3"
        }
    }

def create_schema(client: weaviate.Client):
    """Create the Weaviate schema"""
    try:
        # Check if schema already exists
        existing_schema = client.schema.get()
        existing_classes = [cls["class"] for cls in existing_schema.get("classes", [])]
        
        if "ExternalKnowledge" in existing_classes:
            logger.info("ExternalKnowledge class already exists")
            return True
        
        # Create the schema
        schema = get_external_knowledge_schema()
        client.schema.create_class(schema)
        logger.info("ExternalKnowledge class created successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create schema: {e}")
        return False

def create_sample_data(client: weaviate.Client):
    """Create sample knowledge documents for testing"""
    sample_documents = [
        {
            "knowledge_id": "550e8400-e29b-41d4-a716-446655440001",
            "document_title": "Manufacturing Process Guidelines",
            "content_text": "This document outlines the standard manufacturing processes for autonomous systems. It includes safety protocols, quality control measures, and optimization techniques for industrial automation.",
            "document_type": "GUIDELINE",
            "content_chunks": [
                "Safety protocols for autonomous manufacturing systems",
                "Quality control measures and testing procedures",
                "Optimization techniques for industrial processes"
            ],
            "tags": ["manufacturing", "automation", "safety", "quality"],
            "embedder_info": "sentence-transformers/all-MiniLM-L6-v2",
            "version": "1.0",
            "created_at": "2025-08-07T00:00:00Z",
            "metadata": json.dumps({
                "author": "Manufacturing Team",
                "department": "Production",
                "classification": "internal"
            })
        },
        {
            "knowledge_id": "550e8400-e29b-41d4-a716-446655440002",
            "document_title": "AI Agent Coordination Patterns",
            "content_text": "Research paper on effective coordination patterns for multi-agent systems in manufacturing environments. Covers communication protocols, task allocation algorithms, and conflict resolution strategies.",
            "document_type": "RESEARCH_PAPER",
            "content_chunks": [
                "Multi-agent communication protocols",
                "Task allocation and scheduling algorithms",
                "Conflict resolution in distributed systems"
            ],
            "tags": ["ai", "multi-agent", "coordination", "research"],
            "embedder_info": "sentence-transformers/all-MiniLM-L6-v2",
            "version": "2.1",
            "created_at": "2025-08-07T00:00:00Z",
            "metadata": json.dumps({
                "author": "Research Team",
                "department": "R&D",
                "classification": "confidential"
            })
        },
        {
            "knowledge_id": "550e8400-e29b-41d4-a716-446655440003",
            "document_title": "System Troubleshooting FAQ",
            "content_text": "Frequently asked questions and solutions for common system issues in the orchestration module. Includes error codes, diagnostic procedures, and recovery steps.",
            "document_type": "FAQ",
            "content_chunks": [
                "Common error codes and their meanings",
                "Diagnostic procedures for system health",
                "Recovery and rollback procedures"
            ],
            "tags": ["troubleshooting", "faq", "support", "errors"],
            "embedder_info": "sentence-transformers/all-MiniLM-L6-v2",
            "version": "1.3",
            "created_at": "2025-08-07T00:00:00Z",
            "metadata": json.dumps({
                "author": "Support Team",
                "department": "Operations",
                "classification": "internal"
            })
        }
    ]
    
    try:
        # Add sample documents to Weaviate
        with client.batch as batch:
            batch.batch_size = 10
            
            for doc in sample_documents:
                batch.add_data_object(
                    data_object=doc,
                    class_name="ExternalKnowledge"
                )
        
        logger.info(f"Added {len(sample_documents)} sample documents")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create sample data: {e}")
        return False

def test_hybrid_search(client: weaviate.Client):
    """Test search functionality (keyword-based since no vectorizer)"""
    try:
        # Test query - use keyword search instead of vector search
        test_query = "manufacturing"
        
        # Perform keyword search (BM25)
        result = (
            client.query.get("ExternalKnowledge", [
                "knowledge_id", 
                "document_title", 
                "document_type", 
                "content_text"
            ])
            .with_bm25(
                query=test_query,
                properties=["document_title^2", "content_text"]
            )
            .with_limit(5)
            .do()
        )
        
        if "errors" in result:
            logger.error(f"Search test failed: {result['errors']}")
            return False
        
        documents = result["data"]["Get"]["ExternalKnowledge"]
        logger.info(f"Search test successful, found {len(documents)} documents")
        
        for i, doc in enumerate(documents, 1):
            logger.info(f"Result {i}: {doc['document_title']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Search test failed: {e}")
        return False

def main():
    """Main initialization function"""
    logger.info("Starting Weaviate schema initialization...")
    
    try:
        # Get client
        client = get_weaviate_client()
        
        # Check if Weaviate is ready
        if not client.is_ready():
            logger.error("Weaviate is not ready")
            return False
        
        # Create schema
        if not create_schema(client):
            return False
        
        # Create sample data
        if not create_sample_data(client):
            return False
        
        # Test search functionality
        if not test_hybrid_search(client):
            return False
        
        logger.info("Weaviate initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)