import unittest
from pathlib import Path
import os
from document_processor import DocumentProcessor
from vector_store import VectorStore
from llm_service import LLMService

class TestDocumentProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = DocumentProcessor()
        self.test_dir = Path("test_documents")
        self.test_dir.mkdir(exist_ok=True)
        
        # Create a test text file
        self.test_file = self.test_dir / "test.txt"
        with open(self.test_file, "w") as f:
            f.write("This is a test document.\nIt has multiple lines.\nFor testing purposes.")
    
    def tearDown(self):
        # Clean up test files
        if self.test_file.exists():
            self.test_file.unlink()
        if self.test_dir.exists():
            self.test_dir.rmdir()
    
    def test_process_document(self):
        # Test document processing
        text = "This is a test document for processing."
        docs = self.processor.process_document(text)
        self.assertTrue(len(docs) > 0)
        self.assertEqual(docs[0].page_content, text)
        self.assertEqual(docs[0].metadata["source"], "document")

class TestVectorStore(unittest.TestCase):
    def setUp(self):
        self.store = VectorStore(persist_directory="test_vector_store")
    
    def tearDown(self):
        # Clean up test vector store
        if Path("test_vector_store").exists():
            for file in Path("test_vector_store").glob("*"):
                file.unlink()
            Path("test_vector_store").rmdir()
    
    def test_add_and_search(self):
        # Test adding and searching documents
        test_docs = [
            "This is a test document about Python.",
            "Python is a programming language.",
            "Python is used for machine learning."
        ]
        
        # Add documents
        self.assertTrue(self.store.add_documents(test_docs))
        
        # Search for relevant documents
        results = self.store.similarity_search("What is Python?")
        self.assertTrue(len(results) > 0)
        
        # Test clearing
        self.assertTrue(self.store.clear())

class TestLLMService(unittest.TestCase):
    def setUp(self):
        if not os.getenv("OPENROUTER_API_KEY"):
            self.skipTest("OpenRouter API key not set")
        self.llm = LLMService()
    
    def test_generate_response(self):
        # Test response generation
        question = "What is Python?"
        context = "Python is a high-level programming language."
        
        response = self.llm.generate_response(question, [context])
        self.assertTrue(isinstance(response, str))
        self.assertTrue(len(response) > 0)

if __name__ == '__main__':
    unittest.main() 