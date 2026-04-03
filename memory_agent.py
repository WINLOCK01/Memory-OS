from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from backend.core.vector_store import vector_store
from backend.core.config import settings
from typing import List, Dict


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
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            temperature=0.3
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{question}")
        ])
        self.chain = (
            {
                "context": lambda x: format_context(
                    vector_store.search(x["question"], n_results=6)
                ),
                "question": RunnablePassthrough()
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def query(self, question: str, filters: Dict = None) -> Dict:
        """Query the memory agent and return answer + sources."""
        memories = vector_store.search(question, n_results=6, filters=filters)
        context = format_context(memories)

        answer = self.chain.invoke({"question": question, "context": context})

        sources = list({m["metadata"].get("source", "") for m in memories})
        return {
            "answer": answer,
            "sources": sources,
            "memories_used": len(memories),
            "memories": memories
        }

    def summarize_topic(self, topic: str) -> str:
        """Generate a summary of everything known about a topic."""
        memories = vector_store.search(topic, n_results=10)
        if not memories:
            return f"No memories found about '{topic}'."
        context = format_context(memories)
        prompt = f"Based on these memories, write a comprehensive summary about: {topic}\n\n{context}"
        response = self.llm.invoke(prompt)
        return response.content


memory_agent = MemoryAgent()
