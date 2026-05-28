import logging
from typing import List, Dict, Any

from .retrieval_service import RetrievalService
from .llm.base import BaseLLMService
from ..schemas.retrieval import SearchResult

logger = logging.getLogger(__name__)

class RAGService:
    # Threshold tuned for title+tag-only index (no editorial content yet).
    # Scores rarely exceed 0.3 with sparse metadata chunks; 0.1 admits meaningful tag matches.
    # Raise to 0.4–0.5 once full editorial text is indexed.
    SIMILARITY_THRESHOLD = 0.4

    def __init__(self, retrieval_service: RetrievalService, llm_service: BaseLLMService):
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service

    def _build_prompt(self, query: str, context: List[SearchResult]) -> str:
        """
        Constructs a detailed, grounded prompt for the LLM.
        """
        if not context:
            return ""

        context_str = "\n\n---\n\n".join([
            f"Source Problem ID: {res.problem_id}\n"
            f"Title: {res.title}\n"
            f"Tags: {', '.join(res.tags)}\n"
            f"Similarity Score: {res.similarity_score:.4f}\n"
            f"Content: {res.preview}"
            for res in context
        ])

        prompt = f"""
        You are an expert competitive programming coach. Your task is to explain the editorial for a problem in a simple, intuitive way for a student.

        **User's Query:** "{query}"

        **Retrieved Context from Similar Problems:**
        ---
        {context_str}
        ---

        **Instructions:**
        1.  **Strictly use the provided context.** Do not use any external knowledge.
        2.  **Synthesize an explanation.** Combine the ideas from the different sources into a single, coherent explanation for the user's query.
        3.  **Explain the intuition first.** What is the core idea or observation required to solve the problem?
        4.  **Explain the approach step-by-step.** Break down the algorithm into clear, logical steps.
        5.  **Mention the time and space complexity** of the described approach if possible.
        6.  If the context is insufficient or irrelevant, state that you cannot provide a reliable explanation based on the given information.
        7.  Keep the tone encouraging and clear.

        **Simplified Editorial:**
        """
        return prompt

    def simplify_editorial(self, query: str) -> Dict[str, Any]:
        """
        Generates a simplified editorial by retrieving context, filtering it, and using an LLM.
        """
        # 1. Retrieve context
        all_retrieved = self.retrieval_service.search(query=query, top_k=10)

        # 2. Filter and Deduplicate
        seen_ids = set()
        filtered_context: List[SearchResult] = []
        for res in all_retrieved:
            logger.info(f"Retrieved result fields: {res.model_dump()}")
            if res.problem_id not in seen_ids and res.similarity_score >= self.SIMILARITY_THRESHOLD:
                seen_ids.add(res.problem_id)
                filtered_context.append(res)
        
        # Limit to top 5 after filtering
        final_context = filtered_context[:5]

        if not final_context:
            logger.warning(f"No relevant context found for query: '{query}' after filtering.")
            return {
                "simplified_editorial": "Could not generate an explanation as no relevant context was found.",
                "retrieved_context": [],
                "sources_used": []
            }

        # 3. Build Prompt and Generate
        prompt = self._build_prompt(query, final_context)
        simplified_editorial = self.llm_service.generate_text(prompt)
        
        # 4. Prepare Response
        sources_used = [res.problem_id for res in final_context]

        return {
            "simplified_editorial": simplified_editorial,
            "retrieved_context": final_context,
            "sources_used": sources_used
        }
