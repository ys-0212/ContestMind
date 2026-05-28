import logging
from typing import List, Dict, Any

from app.services.chroma_service import ChromaService
from app.services.llm.base import BaseLLMService
from app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

from supabase import Client

class ChatService:
    def __init__(self, chroma_service: ChromaService, llm_service: BaseLLMService, supabase_client: Client | None = None):
        self.chroma_service = chroma_service
        self.llm_service = llm_service
        self.supabase = supabase_client

    def generate_chat_response(self, request: ChatRequest) -> ChatResponse:
        context_blocks = []
        sources = []
        
        # 1. Fetch existing session history from Supabase if session_id is provided
        db_history = []
        if self.supabase and request.session_id:
            try:
                res = self.supabase.table("chat_messages")\
                    .select("role, content")\
                    .eq("session_id", request.session_id)\
                    .order("created_at", desc=False)\
                    .execute()
                if res.data:
                    # Take last 6 messages for context
                    db_history = res.data[-6:]
            except Exception as e:
                logger.error(f"Error fetching chat history from Supabase: {e}")

        # 2. Save User Message to Supabase
        if self.supabase and request.session_id:
            try:
                self.supabase.table("chat_messages").insert({
                    "session_id": request.session_id,
                    "role": "user",
                    "content": request.query
                }).execute()
            except Exception as e:
                logger.error(f"Error saving user message to Supabase: {e}")

        if self.chroma_service:
            try:
                # Perform semantic search on the query
                results = self.chroma_service.query(request.query, top_k=3)
                if results:
                    for idx, match in enumerate(results):
                        # Only include relevant matches
                        if match.get("distance", 2.0) < 1.6:
                            doc = match.get("document", "")
                            meta = match.get("metadata", {})
                            prob_id = meta.get("problem_id", f"Document {idx+1}")
                            
                            context_blocks.append(f"--- SOURCE: Problem {prob_id} ---\n{doc}\n")
                            sources.append(str(prob_id))
            except Exception as e:
                logger.error(f"Error querying ChromaDB for chat context: {e}")

        context_str = "\n".join(context_blocks)
        
        # Build history context
        history_str = ""
        if db_history:
            history_lines = [f"{msg['role'].upper()}: {msg['content']}" for msg in db_history]
            history_str = "\n".join(history_lines)
        elif request.history:
            # Fallback to local history
            history_lines = []
            for msg in request.history[-4:]:
                role = msg.role.upper()
                history_lines.append(f"{role}: {msg.content}")
            history_str = "\n".join(history_lines)

        # Build structured workspace context from optional problem fields
        workspace_parts = []
        if request.problem_id:
            info = [f"Problem: {request.problem_id}"]
            if request.problem_title:
                info.append(f"Title: {request.problem_title}")
            if request.problem_rating:
                info.append(f"Difficulty: {request.problem_rating}")
            if request.problem_tags:
                info.append(f"Tags: {', '.join(request.problem_tags)}")
            workspace_parts.append("\n".join(info))

        if request.user_code:
            workspace_parts.append(f"User's Current Code:\n```\n{request.user_code}\n```")

        if request.run_status:
            exec_lines = [f"Last Execution Verdict: {request.run_status.upper().replace('_', ' ')}"]
            if request.stdin_used:
                exec_lines.append(f"Input used:\n{request.stdin_used}")
            if request.run_stdout:
                exec_lines.append(f"Actual output:\n{request.run_stdout}")
            if request.expected_output and request.run_status == "wrong_answer":
                exec_lines.append(f"Expected output:\n{request.expected_output}")
            if request.run_stderr:
                exec_lines.append(f"Compiler/Runtime error:\n{request.run_stderr}")
            workspace_parts.append("\n".join(exec_lines))

        workspace_ctx = "\n\n".join(workspace_parts)

        prompt = f"""
You are ContestMind, an elite AI Competitive Programming Coach and live debugging assistant.
You have full awareness of the user's problem workspace: their code, last execution result, and the problem being solved.
Use this context proactively — if the user asks "why WA?", diagnose using their actual code and test case.

{("PROBLEM WORKSPACE CONTEXT:\n" + workspace_ctx + "\n") if workspace_ctx else ""}
USER QUESTION:
{request.query}

{("PREVIOUS CONVERSATION HISTORY:\n" + history_str + "\n") if history_str else ""}

{("RELEVANT EDITORIAL CONTEXT FROM DATABASE:\n" + context_str + "\n") if context_str else ""}

INSTRUCTIONS:
1. You have the user's code and execution context above — USE IT when diagnosing WA, TLE, RE, or CE.
2. For general algorithmic questions (e.g., "How does Dijkstra work?"), answer clearly from your competitive programming knowledge.
3. Default to **pseudo-code** first; write actual C++/Python only when the user explicitly asks for a specific language.
4. If asked about a specific problem without editorial context, guide using the tags and standard techniques.
5. Be concise, technically precise, and coach-like — this is a live contest environment.

ANSWER:
"""
        
        try:
            llm_response = self.llm_service.generate_text(prompt)
            response_text = llm_response.strip()

            # 3. Save Assistant Message to Supabase
            if self.supabase and request.session_id:
                try:
                    self.supabase.table("chat_messages").insert({
                        "session_id": request.session_id,
                        "role": "assistant",
                        "content": response_text
                    }).execute()
                except Exception as e:
                    logger.error(f"Error saving assistant message to Supabase: {e}")

        except Exception as e:
            logger.error(f"LLM chat generation failed: {e}")
            response_text = "I apologize, but I encountered an error while trying to generate a response. Please try again."

        return ChatResponse(
            response_text=response_text
        )
