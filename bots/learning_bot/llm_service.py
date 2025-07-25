import os
import logging
from typing import List, Optional
from langchain.schema import Document as LangchainDocument
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

logger = logging.getLogger(__name__)

class LLMService:
    """Handles LLM interactions for response generation."""
    
    def __init__(self):
        """Initialize the LLM service."""
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        # Initialize the LLM with OpenRouter
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            model="deepseek/deepseek-r1-0528-qwen3-8b:free",
            api_key=self.api_key
        )
        
        # Create the prompt template for regular Q&A
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant that answers questions based on the provided context.
            If you cannot find the answer in the context, say so. Do not make up information.
            Always be concise and clear in your responses."""),
            ("human", "Context: {context}\n\nQuestion: {question}")
        ])
        
        # Create the prompt template for detailed learning
        self.learning_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert learning facilitator who creates comprehensive, actionable learning content.
            Your task is to transform raw content into well-structured, actionable learning experiences.
            Always provide practical, immediately applicable insights that help users turn knowledge into action."""),
            ("human", "{content}")
        ])
        
        # Create the chains
        self.chain = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        self.learning_chain = (
            {"content": RunnablePassthrough()}
            | self.learning_prompt
            | self.llm
            | StrOutputParser()
        )
    
    def generate_response(self, question: str, context_docs: List[LangchainDocument]) -> str:
        """
        Generate a response based on the question and context documents.
        
        Args:
            question: The question to answer
            context_docs: List of relevant documents for context
            
        Returns:
            Generated response
        """
        try:
            # Combine context documents
            context = "\n\n".join(doc.page_content for doc in context_docs)
            
            # Generate response
            response = self.chain.invoke({
                "context": context,
                "question": question
            })
            
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I encountered an error while generating the response. Please try again."
    
    def generate_detailed_learning(self, learning_content: str) -> str:
        """
        Generate a detailed learning response with comprehensive structure.
        
        Args:
            learning_content: The content/prompt for generating detailed learning
            
        Returns:
            Structured learning response
        """
        try:
            # Generate comprehensive learning response
            response = self.learning_chain.invoke(learning_content)
            return response
        except Exception as e:
            logger.error(f"Error generating detailed learning: {e}")
            return "I apologize, but I encountered an error while generating your learning content. Please try again." 