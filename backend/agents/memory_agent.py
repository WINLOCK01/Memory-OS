from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from backend.core.vector_store import vector_store
from backend.core.config import settings
from typing import List, Dict
import os
import time
import logging

logger = logging.getLogger("memoryos.agent")


SYSTEM_PROMPT = """You are MemoryOS, an intelligent second brain assistant.
You have access to the user's personal knowledge base — everything they have read, watched, or noted.

When answering:
- Ground your answer in the retrieved memories below
- Cite sources by mentioning the source name/URL
- Highlight connections between different pieces of knowledge
- Be concise but insightful
- If you don't find relevant memories, say so honestly

Retrieved Memories:
{context}

Answer the user's question based on their personal knowledge base."""


def format_context(memories: List[Dict]) -> str:
    """Format retrieved memories into context string."""
    parts = []
    for i, mem in enumerate(memories):
        source = mem["metadata"].get("source", "unknown")
        parts.append(f"[Memory {i+1}] Source: {source}\n{mem['content']}")
    return "\n\n---\n\n".join(parts)


class MemoryAgent:
    def __init__(self):
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{question}")
        ])

    def _get_llm(self, model: str):
        if "gemini" in model.lower() and "/" not in model:
            return ChatGoogleGenerativeAI(model=model, google_api_key=settings.google_api_key, temperature=0.3)
        if "/" in model or "openrouter" in model.lower():
            # Support OpenRouter standard format (provider/model)
            return ChatOpenAI(
                model=model, 
                api_key=settings.openrouter_api_key, 
                base_url="https://openrouter.ai/api/v1", 
                temperature=0.3
            )
        return ChatOpenAI(model=model, api_key=settings.openai_api_key, temperature=0.3)

    def query(self, question: str, model: str = "gemini-2.0-flash", filters: Dict = None) -> Dict:
        """Query the memory agent and return answer + sources."""
        memories = vector_store.search(question, n_results=6, filters=filters)
        context = format_context(memories)

        llm = self._get_llm(model)
        chain = self.prompt | llm | StrOutputParser()

        # Retry up to 3 times on rate-limit errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                answer = chain.invoke({"question": question, "context": context})
                break
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
                    wait_sec = 15 * (2 ** attempt)  # 15s, 30s, 60s
                    logger.warning("Rate limited by Gemini API. Waiting %ds before retry %d/%d...", wait_sec, attempt + 1, max_retries)
                    time.sleep(wait_sec)
                    if attempt == max_retries - 1:
                        answer = "⚠️ The AI model is rate-limited right now. Please wait 30 seconds and try again."
                else:
                    raise

        sources = list({m["metadata"].get("source", "") for m in memories})
        return {
            "answer": answer,
            "sources": sources,
            "memories_used": len(memories),
            "memories": memories
        }

    def summarize_topic(self, topic: str, model: str = "gpt-4o") -> str:
        """Generate a summary of everything known about a topic."""
        memories = vector_store.search(topic, n_results=10)
        if not memories:
            return f"No memories found about '{topic}'."
        context = format_context(memories)
        prompt = f"Based on these memories, write a comprehensive summary about: {topic}\n\n{context}"
        llm = self._get_llm(model)
        response = llm.invoke(prompt)
        return response.content

memory_agent = MemoryAgent()
