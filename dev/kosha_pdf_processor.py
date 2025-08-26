#!/usr/bin/env python3
"""
KOSHA PDF Processor for Weaviate Vector Database Initialization

This script downloads KOSHA guidance PDFs, converts them to markdown using MarkItDown,
and ingests them into Weaviate vector database with text2vec-transformers encoding.
"""

import json
import os
import sys
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
from urllib.request import urlretrieve, urlopen
from urllib.error import URLError, HTTPError

import weaviate
from markitdown import MarkItDown

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KOSHAPDFProcessor:
    def __init__(self, 
                 weaviate_url: str = "http://weaviate:8080",
                 data_dir: str = "./data/kosha_pdfs",
                 json_file: str = "./assets/kosha_guidance_download_links.json"):
        """
        Initialize the KOSHA PDF processor
        
        Args:
            weaviate_url: Weaviate instance URL
            data_dir: Directory to store downloaded PDFs and converted markdown
            json_file: Path to KOSHA guidance links JSON file
        """
        self.weaviate_url = weaviate_url
        self.data_dir = Path(data_dir)
        self.json_file = Path(json_file)
        
        # Create data directories
        self.pdf_dir = self.data_dir / "pdfs"
        self.markdown_dir = self.data_dir / "markdown"
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.markdown_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize MarkItDown
        self.md_converter = MarkItDown()
        
        # Initialize Weaviate client
        self.weaviate_client = None
        self._init_weaviate_client()
        
    def _init_weaviate_client(self):
        """Initialize Weaviate client with retries"""
        max_retries = 30
        retry_delay = 10
        
        for attempt in range(max_retries):
            try:
                self.weaviate_client = weaviate.Client(self.weaviate_url)
                
                # Test connection
                if self.weaviate_client.is_ready():
                    logger.info("Successfully connected to Weaviate")
                    return
                else:
                    raise ConnectionError("Weaviate is not ready")
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed to connect to Weaviate: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("Failed to connect to Weaviate after all retries")
                    sys.exit(1)
    
    def _create_weaviate_schemas(self):
        """Create Weaviate schemas for both Knowledge DB and Agent Memory DB"""
        
        # 1. External Knowledge DB Schema (KOSHA Guidance Documents)
        knowledge_schema = {
            "class": "OrchKnowledge",
            "description": "External Knowledge DB - KOSHA Safety and Health Technical Guidance Documents",
            "vectorizer": "text2vec-transformers",
            "moduleConfig": {
                "text2vec-transformers": {
                    "vectorizeClassName": False
                }
            },
            "properties": [
                {
                    "name": "document_number",
                    "dataType": ["text"],
                    "description": "KOSHA document number (e.g., P-180-2023)"
                },
                {
                    "name": "title",
                    "dataType": ["text"],
                    "description": "Document title"
                },
                {
                    "name": "year",
                    "dataType": ["int"],
                    "description": "Publication year"
                },
                {
                    "name": "category",
                    "dataType": ["text"],
                    "description": "Document category"
                },
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Full document content in markdown format",
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "content_chunk",
                    "dataType": ["text"],
                    "description": "Chunked content for vector search",
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "chunk_index",
                    "dataType": ["int"],
                    "description": "Index of the content chunk"
                },
                {
                    "name": "download_url",
                    "dataType": ["text"],
                    "description": "Original PDF download URL"
                },
                {
                    "name": "file_hash",
                    "dataType": ["text"],
                    "description": "SHA256 hash of the original PDF file"
                },
                {
                    "name": "knowledge_type",
                    "dataType": ["text"],
                    "description": "Type of knowledge: guidance, sop, technical_doc"
                }
            ]
        }
        
        # 2. Agent Memory DB Schema (Past Incidents, Learning Data)
        memory_schema = {
            "class": "OrchMemory",
            "description": "Agent Memory DB - Past incidents, solutions, and learning data",
            "vectorizer": "text2vec-transformers",
            "moduleConfig": {
                "text2vec-transformers": {
                    "vectorizeClassName": False
                }
            },
            "properties": [
                {
                    "name": "incident_id",
                    "dataType": ["text"],
                    "description": "Unique incident identifier"
                },
                {
                    "name": "user_query",
                    "dataType": ["text"],
                    "description": "Original user question/request"
                },
                {
                    "name": "equipment_type",
                    "dataType": ["text"],
                    "description": "Type of equipment involved"
                },
                {
                    "name": "equipment_id",
                    "dataType": ["text"],
                    "description": "Specific equipment identifier"
                },
                {
                    "name": "issue_type",
                    "dataType": ["text"],
                    "description": "Category of issue (pressure, temperature, vibration, etc.)"
                },
                {
                    "name": "root_cause",
                    "dataType": ["text"],
                    "description": "Identified root cause of the incident"
                },
                {
                    "name": "solution_applied",
                    "dataType": ["text"],
                    "description": "Solution that was applied to resolve the incident"
                },
                {
                    "name": "success_rate",
                    "dataType": ["number"],
                    "description": "Success rate of the applied solution (0.0 - 1.0)"
                },
                {
                    "name": "resolution_time",
                    "dataType": ["int"],
                    "description": "Time taken to resolve in minutes"
                },
                {
                    "name": "incident_summary",
                    "dataType": ["text"],
                    "description": "Summary of the entire incident resolution process",
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "vectorizePropertyName": False
                        }
                    }
                },
                {
                    "name": "created_at",
                    "dataType": ["date"],
                    "description": "When this memory was created"
                },
                {
                    "name": "severity_level",
                    "dataType": ["text"],
                    "description": "Incident severity: low, medium, high, critical"
                },
                {
                    "name": "tags",
                    "dataType": ["text[]"],
                    "description": "Tags for easy categorization and search"
                }
            ]
        }
        
        # Check existing schemas and create if needed
        try:
            existing_schema = self.weaviate_client.schema.get()
            existing_classes = [cls["class"] for cls in existing_schema.get("classes", [])]
            
            # Create Knowledge DB schema
            if "OrchKnowledge" not in existing_classes:
                self.weaviate_client.schema.create_class(knowledge_schema)
                logger.info("✅ Created OrchKnowledge schema (External Knowledge DB)")
            else:
                logger.info("OrchKnowledge class already exists")
            
            # Create Memory DB schema  
            if "OrchMemory" not in existing_classes:
                self.weaviate_client.schema.create_class(memory_schema)
                logger.info("✅ Created OrchMemory schema (Agent Memory DB)")
            else:
                logger.info("OrchMemory class already exists")
                
        except Exception as e:
            logger.error(f"Failed to create schemas: {e}")
            raise
    
    def _load_kosha_links(self) -> List[Dict]:
        """Load KOSHA guidance links from JSON file"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('guidelines', [])
        except Exception as e:
            logger.error(f"Failed to load KOSHA links from {self.json_file}: {e}")
            raise
    
    def _download_pdf(self, url: str, filename: str) -> Optional[str]:
        """
        Download PDF from URL
        
        Args:
            url: PDF download URL
            filename: Local filename to save
            
        Returns:
            Path to downloaded file or None if failed
        """
        file_path = self.pdf_dir / filename
        
        # Skip if already exists
        if file_path.exists():
            logger.info(f"PDF already exists: {filename}")
            return str(file_path)
        
        try:
            logger.info(f"Downloading PDF: {filename}")
            urlretrieve(url, file_path)
            
            # Verify file was downloaded and is not empty
            if file_path.exists() and file_path.stat().st_size > 0:
                return str(file_path)
            else:
                logger.error(f"Downloaded file is empty or doesn't exist: {filename}")
                if file_path.exists():
                    file_path.unlink()
                return None
                
        except (URLError, HTTPError) as e:
            logger.error(f"Failed to download {filename}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading {filename}: {e}")
            return None
    
    def _convert_pdf_to_markdown(self, pdf_path: str, document_number: str) -> Optional[str]:
        """
        Convert PDF to markdown using MarkItDown
        
        Args:
            pdf_path: Path to PDF file
            document_number: KOSHA document number
            
        Returns:
            Markdown content or None if conversion failed
        """
        markdown_file = self.markdown_dir / f"{document_number}.md"
        
        # Skip if markdown already exists
        if markdown_file.exists():
            logger.info(f"Markdown already exists: {document_number}.md")
            try:
                with open(markdown_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to read existing markdown {markdown_file}: {e}")
                # Continue to reconvert
        
        try:
            logger.info(f"Converting PDF to markdown: {document_number}")
            result = self.md_converter.convert(pdf_path)
            
            if result and result.text_content:
                # Save markdown file
                with open(markdown_file, 'w', encoding='utf-8') as f:
                    f.write(result.text_content)
                
                logger.info(f"Saved markdown: {markdown_file}")
                return result.text_content
            else:
                logger.error(f"Failed to convert PDF to markdown: {document_number}")
                return None
                
        except Exception as e:
            logger.error(f"Error converting PDF to markdown for {document_number}: {e}")
            return None
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _chunk_content(self, content: str, chunk_size: int = 1000) -> List[str]:
        """
        Split content into chunks for better vector search
        
        Args:
            content: Text content to chunk
            chunk_size: Approximate size of each chunk in characters
            
        Returns:
            List of content chunks
        """
        if not content:
            return []
        
        # Simple chunking by paragraphs and sentences
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) < chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks if chunks else [content]
    
    def _check_document_exists_in_weaviate(self, document_number: str) -> bool:
        """
        Check if document already exists in OrchKnowledge
        
        Args:
            document_number: KOSHA document number
            
        Returns:
            True if document exists, False otherwise
        """
        try:
            query = (
                self.weaviate_client.query
                .get("OrchKnowledge", ["document_number"])
                .with_where({
                    "path": ["document_number"],
                    "operator": "Equal",
                    "valueText": document_number
                })
                .with_limit(1)
            )
            
            result = query.do()
            
            if result and "data" in result and "Get" in result["data"]:
                documents = result["data"]["Get"]["OrchKnowledge"]
                return len(documents) > 0
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking document existence in Weaviate for {document_number}: {e}")
            return False
    
    def _ingest_document(self, guidance_data: Dict, markdown_content: str, pdf_path: str):
        """
        Ingest document into Weaviate
        
        Args:
            guidance_data: Document metadata from JSON
            markdown_content: Converted markdown content
            pdf_path: Path to original PDF file
        """
        document_number = guidance_data["document_number"]
        
        # Check if document already exists in Weaviate
        if self._check_document_exists_in_weaviate(document_number):
            logger.info(f"Document {document_number} already exists in Weaviate, skipping ingestion")
            return
        
        try:
            file_hash = self._calculate_file_hash(pdf_path)
            chunks = self._chunk_content(markdown_content)
            
            logger.info(f"Ingesting document {document_number} with {len(chunks)} chunks")
            
            # Create data objects for each chunk
            for i, chunk in enumerate(chunks):
                data_object = {
                    "document_number": guidance_data["document_number"],
                    "title": guidance_data["title"],
                    "year": guidance_data["year"],
                    "category": guidance_data.get("category", ""),
                    "content": markdown_content if i == 0 else "",  # Full content only in first chunk
                    "content_chunk": chunk,
                    "chunk_index": i,
                    "download_url": guidance_data["download_url"],
                    "file_hash": file_hash,
                    "knowledge_type": "guidance"  # Type of knowledge
                }
                
                # Add to OrchKnowledge (External Knowledge DB)
                self.weaviate_client.data_object.create(
                    data_object,
                    "OrchKnowledge"
                )
            
            logger.info(f"Successfully ingested {guidance_data['document_number']}")
            
        except Exception as e:
            logger.error(f"Failed to ingest document {guidance_data['document_number']}: {e}")
    
    def process_all_documents(self, max_documents: Optional[int] = None):
        """
        Process all KOSHA guidance documents
        
        Args:
            max_documents: Maximum number of documents to process (for testing)
        """
        logger.info("Starting KOSHA PDF processing")
        
        # Create Weaviate schemas for Knowledge DB and Memory DB
        self._create_weaviate_schemas()
        
        # Load document links
        guidance_list = self._load_kosha_links()
        
        if max_documents:
            guidance_list = guidance_list[:max_documents]
            logger.info(f"Processing limited set of {len(guidance_list)} documents")
        else:
            logger.info(f"Processing {len(guidance_list)} documents")
        
        processed_count = 0
        failed_count = 0
        
        for guidance in guidance_list:
            document_number = guidance["document_number"]
            download_url = guidance["download_url"]
            
            try:
                # Generate filename
                filename = f"{document_number}.pdf"
                
                # Download PDF
                pdf_path = self._download_pdf(download_url, filename)
                if not pdf_path:
                    logger.error(f"Failed to download {document_number}")
                    failed_count += 1
                    continue
                
                # Convert to markdown
                markdown_content = self._convert_pdf_to_markdown(pdf_path, document_number)
                if not markdown_content:
                    logger.error(f"Failed to convert {document_number} to markdown")
                    failed_count += 1
                    continue
                
                # Ingest into Weaviate
                self._ingest_document(guidance, markdown_content, pdf_path)
                processed_count += 1
                
                # Progress logging
                progress_percent = (processed_count / len(guidance_list)) * 100
                logger.info(f"✅ Completed processing {document_number} ({processed_count}/{len(guidance_list)}, {progress_percent:.1f}%)")
                
                # Small delay to avoid overwhelming the servers
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to process {document_number}: {e}")
                failed_count += 1
                continue
        
        logger.info(f"Processing completed. Success: {processed_count}, Failed: {failed_count}")

def main():
    """Main function"""
    # Environment variables
    weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
    max_docs = os.getenv("MAX_DOCUMENTS")
    max_documents = int(max_docs) if max_docs else None
    
    # Initialize processor
    processor = KOSHAPDFProcessor(weaviate_url=weaviate_url)
    
    # Process documents
    processor.process_all_documents(max_documents=max_documents)

if __name__ == "__main__":
    main()