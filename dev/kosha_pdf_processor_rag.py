#!/usr/bin/env python3
"""
KOSHA PDF Processor using prism-core RAGSearchTool

이 스크립트는 prism-core의 RAGSearchTool을 사용하여 KOSHA 문서를 
Weaviate의 compliance 도메인에 업로드합니다.
"""

import json
import os
import sys
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional
from urllib.request import urlretrieve
from urllib.error import URLError, HTTPError

from markitdown import MarkItDown

# Python path setup for local development
sys.path.append('/app/src')
sys.path.append('/app')  # Add for local prism_core

# PRISM-Orch tools import
try:
    from src.orchestration.tools import OrchToolSetup
    ORCH_TOOLS_AVAILABLE = True
    logger_msg = "PRISM-Orch OrchToolSetup 사용"
except ImportError:
    ORCH_TOOLS_AVAILABLE = False
    logger_msg = "PRISM-Orch tools 없음 - 직접 prism-core 사용"
    # Fallback to direct prism-core import
    try:
        from prism_core.core.tools.rag_search_tool import RAGSearchTool
        from prism_core.core.tools.schemas import ToolRequest
        PRISM_CORE_AVAILABLE = True
        logger_msg = "직접 prism-core 사용 (pydantic-settings 포함)"
    except ImportError as e:
        PRISM_CORE_AVAILABLE = False
        logger_msg = f"prism-core import 실패: {e}"
        RAGSearchTool = None
        ToolRequest = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KOSHAPDFProcessorRAG:
    def __init__(self, 
                 weaviate_url: str = "http://weaviate:8080",
                 openai_base_url: str = "http://localhost:8000/v1",
                 openai_api_key: str = "dummy-key",
                 data_dir: str = "./data/kosha_pdfs",
                 json_file: str = "./assets/kosha_guidance_download_links.json",
                 encoder_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
                 vector_dim: int = 768,
                 class_prefix: str = "KOSHA"):
        """
        Initialize KOSHA PDF processor using OrchToolSetup RAGSearchTool
        
        Args:
            weaviate_url: Weaviate instance URL
            openai_base_url: OpenAI compatible API URL
            openai_api_key: OpenAI API key
            data_dir: Directory to store downloaded PDFs
            json_file: Path to KOSHA guidance links JSON
            encoder_model: Model for text encoding  
            vector_dim: Vector dimensions
            class_prefix: Prefix for Weaviate class names (KOSHACompliance, KOSHAHistory, KOSHAResearch)
        """
        self.weaviate_url = weaviate_url
        self.data_dir = Path(data_dir)
        self.json_file = Path(json_file)
        
        # Create data directories
        self.pdf_dir = self.data_dir / "pdfs"
        self.markdown_dir = self.data_dir / "markdown"
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.markdown_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize MarkItDown converter
        self.md_converter = MarkItDown()
        
        # Initialize RAGSearchTool using OrchToolSetup or fallback
        self.rag_tool = None
        if ORCH_TOOLS_AVAILABLE:
            try:
                # Use OrchToolSetup for consistent tool management
                from src.core.config import settings as orch_settings
                
                # Override settings for KOSHA specific configuration
                tool_setup = OrchToolSetup()
                tool_setup.weaviate_url = weaviate_url
                tool_setup.openai_base_url = openai_base_url
                tool_setup.openai_api_key = openai_api_key
                tool_setup.encoder_model = encoder_model
                tool_setup.vector_dim = vector_dim
                tool_setup.client_id = "kosha_processor"
                tool_setup.class_prefix = class_prefix  # Will create KOSHACompliance, KOSHAHistory, KOSHAResearch
                
                # Setup tools and get RAG tool
                tool_registry = tool_setup.setup_tools()
                self.rag_tool = tool_setup.get_rag_tool()
                
                logger.info(f"✅ OrchToolSetup RAGSearchTool 초기화 완료 (prefix: {class_prefix})")
                
            except Exception as e:
                logger.warning(f"⚠️  OrchToolSetup 초기화 실패: {e}")
                self.rag_tool = None
        
        # Fallback to direct prism-core RAGSearchTool
        if not self.rag_tool and PRISM_CORE_AVAILABLE:
            try:
                # Initialize RAGSearchTool with KOSHA prefix
                # The tool will use the provided parameters directly
                self.rag_tool = RAGSearchTool(
                    weaviate_url=weaviate_url,
                    encoder_model=encoder_model,
                    vector_dim=vector_dim,
                    client_id="kosha_processor",
                    class_prefix=class_prefix
                )
                logger.info(f"✅ Direct prism-core RAGSearchTool 초기화 완료 (prefix: {class_prefix})")
                
            except Exception as e:
                logger.error(f"❌ RAGSearchTool 초기화 실패: {e}")
                raise
        
        if not self.rag_tool:
            logger.error("❌ RAGSearchTool을 초기화할 수 없습니다")
            raise RuntimeError("RAGSearchTool initialization failed")
        
        # Wait for Weaviate to be ready
        self._wait_for_weaviate()
        
        logger.info(f"Initialized KOSHA processor with class prefix: {class_prefix} ({logger_msg})")
    
    def _wait_for_weaviate(self):
        """Wait for Weaviate to be ready"""
        max_retries = 30
        retry_delay = 10
        
        import requests
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{self.weaviate_url}/v1/.well-known/ready", timeout=5)
                if response.status_code == 200:
                    logger.info("Successfully connected to Weaviate")
                    return
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("Failed to connect to Weaviate after all retries")
                    sys.exit(1)
    
    def _load_kosha_links(self) -> List[Dict]:
        """Load KOSHA guidance links from JSON file"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('guidelines', [])
        except Exception as e:
            logger.error(f"Failed to load KOSHA links: {e}")
            raise
    
    def _validate_pdf(self, file_path: Path) -> bool:
        """Validate that a file is actually a PDF"""
        if not file_path.exists() or file_path.stat().st_size < 100:
            return False
        
        try:
            # Check PDF magic number
            with open(file_path, 'rb') as f:
                header = f.read(10)
                if not header.startswith(b'%PDF-'):
                    logger.warning(f"File is not a valid PDF (invalid header): {file_path.name}")
                    return False
            
            # Check if it's HTML disguised as PDF
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(500).lower()
                if any(tag in content for tag in ['<html', '<!doctype', '<head>', '<body>']):
                    logger.warning(f"File is HTML disguised as PDF: {file_path.name}")
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"PDF validation failed for {file_path.name}: {e}")
            return False
    
    def _download_pdf(self, url: str, filename: str) -> Optional[str]:
        """Download and validate PDF from URL"""
        file_path = self.pdf_dir / filename
        
        # Check if file exists and is valid
        if file_path.exists():
            if self._validate_pdf(file_path):
                logger.info(f"PDF already exists: {filename}")
                return str(file_path)
            else:
                logger.warning(f"Existing PDF is corrupted, re-downloading: {filename}")
                file_path.unlink()
        
        try:
            logger.info(f"Downloading: {filename}")
            urlretrieve(url, file_path)
            
            # Validate downloaded file
            if file_path.exists() and self._validate_pdf(file_path):
                logger.info(f"Successfully downloaded and validated: {filename}")
                return str(file_path)
            else:
                logger.error(f"Downloaded file failed validation: {filename}")
                if file_path.exists():
                    file_path.unlink()
                return None
                
        except (URLError, HTTPError) as e:
            logger.error(f"Download failed {filename}: {e}")
            if file_path.exists():
                file_path.unlink()
            return None
    
    def _convert_pdf_to_markdown(self, pdf_path: str, document_number: str) -> Optional[str]:
        """Convert PDF to markdown using MarkItDown"""
        markdown_file = self.markdown_dir / f"{document_number}.md"
        
        if markdown_file.exists():
            logger.info(f"Markdown already exists: {document_number}.md")
            try:
                with open(markdown_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to read markdown: {e}")
        
        try:
            logger.info(f"Converting to markdown: {document_number}")
            result = self.md_converter.convert(pdf_path)
            
            if result and result.text_content:
                with open(markdown_file, 'w', encoding='utf-8') as f:
                    f.write(result.text_content)
                logger.info(f"Saved markdown: {markdown_file}")
                return result.text_content
            else:
                logger.error(f"Conversion failed: {document_number}")
                return None
                
        except Exception as e:
            logger.error(f"Error converting PDF: {e}")
            return None
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _chunk_content(self, content: str, chunk_size: int = 1500) -> List[str]:
        """Split content into chunks for better vector search"""
        if not content:
            return []
        
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
    
    def _prepare_document_for_rag(self, guidance_data: Dict, chunk: str, chunk_index: int, 
                                   total_chunks: int, file_hash: str) -> Dict[str, any]:
        """Prepare document in RAGSearchTool format"""
        # Create metadata as structured dict
        metadata = {
            "regulation_id": guidance_data["document_number"],
            "regulation_type": "KOSHA_guidance",
            "year": guidance_data["year"],
            "category": guidance_data.get("category", "safety"),
            "industry": "manufacturing",
            "risk_level": "medium",
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "download_url": guidance_data["download_url"],
            "file_hash": file_hash,
            "source": f"KOSHA-{guidance_data['document_number']}"
        }
        
        # RAGSearchTool expects: title, content, metadata
        return {
            "title": f"{guidance_data['title']} - Part {chunk_index + 1}/{total_chunks}",
            "content": chunk,
            "metadata": metadata  # Pass as dict, will be converted to string in RAGSearchTool
        }
    
    def cleanup_corrupted_files(self):
        """Clean up corrupted PDF and markdown files"""
        logger.info("🧹 Cleaning up corrupted files...")
        
        cleaned_pdfs = 0
        cleaned_markdowns = 0
        
        # Clean PDFs
        for pdf_file in self.pdf_dir.glob("*.pdf"):
            if not self._validate_pdf(pdf_file):
                logger.warning(f"Removing corrupted PDF: {pdf_file.name}")
                pdf_file.unlink()
                cleaned_pdfs += 1
                
                # Also remove corresponding markdown if exists
                markdown_file = self.markdown_dir / f"{pdf_file.stem}.md"
                if markdown_file.exists():
                    markdown_file.unlink()
                    cleaned_markdowns += 1
                    logger.info(f"Removed corresponding markdown: {markdown_file.name}")
        
        if cleaned_pdfs > 0:
            logger.info(f"🗑️ Cleaned up {cleaned_pdfs} corrupted PDFs and {cleaned_markdowns} markdown files")
        else:
            logger.info("✅ No corrupted files found")
    
    def process_all_documents(self, max_documents: Optional[int] = None):
        """Process all KOSHA guidance documents"""
        logger.info("Starting KOSHA PDF processing with RAGSearchTool")
        
        # Clean up corrupted files first
        self.cleanup_corrupted_files()
        
        # Load document links
        guidance_list = self._load_kosha_links()
        
        if max_documents:
            guidance_list = guidance_list[:max_documents]
            logger.info(f"Processing {len(guidance_list)} documents (limited)")
        else:
            logger.info(f"Processing {len(guidance_list)} documents")
        
        processed_count = 0
        failed_count = 0
        all_documents_for_upload = []
        
        # First, process all documents and prepare for batch upload
        for guidance in guidance_list:
            document_number = guidance["document_number"]
            download_url = guidance["download_url"]
            
            try:
                # Check if already exists
                doc_title_pattern = f"{guidance['title']} - Part"
                if self.rag_tool.check_document_exists(doc_title_pattern, domain="compliance"):
                    logger.info(f"Document {document_number} already exists in compliance domain")
                    processed_count += 1
                    continue
                
                # Download PDF
                filename = f"{document_number}.pdf"
                pdf_path = self._download_pdf(download_url, filename)
                if not pdf_path:
                    failed_count += 1
                    continue
                
                # Convert to markdown
                markdown_content = self._convert_pdf_to_markdown(pdf_path, document_number)
                if not markdown_content:
                    failed_count += 1
                    continue
                
                # Prepare documents for upload
                file_hash = self._calculate_file_hash(pdf_path)
                chunks = self._chunk_content(markdown_content)
                
                logger.info(f"Preparing {document_number} with {len(chunks)} chunks")
                
                for i, chunk in enumerate(chunks):
                    doc = self._prepare_document_for_rag(
                        guidance, chunk, i, len(chunks), file_hash
                    )
                    all_documents_for_upload.append(doc)
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to process {document_number}: {e}")
                failed_count += 1
        
        # Batch upload all documents to compliance domain
        if all_documents_for_upload:
            logger.info(f"Uploading {len(all_documents_for_upload)} chunks to compliance domain")
            
            # Use batch upload for better performance
            result = self.rag_tool.batch_upload_documents(
                documents=all_documents_for_upload,
                domain="compliance",
                batch_size=50
            )
            
            logger.info(f"Upload result: {result}")
            
            # Log to history domain
            history_doc = {
                "title": f"KOSHA Processing Batch - {time.strftime('%Y%m%d_%H%M%S')}",
                "content": f"Processed {processed_count} KOSHA documents with {len(all_documents_for_upload)} chunks. Failed: {failed_count}",
                "metadata": {
                    "processor": "kosha_pdf_processor_rag",
                    "documents_processed": processed_count,
                    "documents_failed": failed_count,
                    "total_chunks": len(all_documents_for_upload),
                    "upload_result": str(result)
                }
            }
            
            self.rag_tool.upload_documents([history_doc], domain="history")
        
        logger.info(f"✅ Processing completed. Success: {processed_count}, Failed: {failed_count}")
        
        # Test search in compliance domain
        if processed_count > 0 and PRISM_CORE_AVAILABLE:
            logger.info("Testing compliance domain search...")
            import asyncio
            
            test_request = ToolRequest(
                tool_name="rag_search",
                parameters={
                    "query": "안전 규정",
                    "top_k": 3,
                    "domain": "compliance"
                }
            )
            
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(self.rag_tool.execute(test_request))
            logger.info(f"Search test result: {result.success}, found {result.data.get('count', 0)} results")


def main():
    """Main function"""
    # Environment variables
    weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
    openai_base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1")
    openai_api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
    max_docs = os.getenv("MAX_DOCUMENTS")
    max_documents = int(max_docs) if max_docs else None
    encoder_model = os.getenv("ENCODER_MODEL", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
    vector_dim = int(os.getenv("VECTOR_DIM", "768"))
    class_prefix = os.getenv("CLASS_PREFIX", "KOSHA")
    
    logger.info(f"🚀 Starting KOSHA PDF Processor with {logger_msg}")
    
    # Initialize and run processor
    processor = KOSHAPDFProcessorRAG(
        weaviate_url=weaviate_url,
        openai_base_url=openai_base_url,
        openai_api_key=openai_api_key,
        encoder_model=encoder_model,
        vector_dim=vector_dim,
        class_prefix=class_prefix
    )
    
    processor.process_all_documents(max_documents=max_documents)


if __name__ == "__main__":
    main()