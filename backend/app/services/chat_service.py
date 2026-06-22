import logging
from typing import List, Optional

from app.services.vector_service import VectorService
from app.services.llm.base import BaseLLMService
from app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

from supabase import Client


class ChatService:
    def __init__(
        self,
        chroma_service: VectorService,
        llm_service: BaseLLMService,
        supabase_client: Client | None = None,
        problem_service=None,
    ):
        self.chroma_service = chroma_service
        self.llm_service = llm_service
        self.supabase = supabase_client
        self.problem_service = problem_service

    # ── Editorial resolution ──────────────────────────────────────────────────

    def _resolve_editorial(self, request: ChatRequest) -> Optional[str]:
        """
        Return the best available editorial text for the problem in the request.

        Resolution order (first non-empty wins):
          1. Frontend already sent editorial text (problem has editorial field populated)
          2. Backend problem_service direct lookup (TYPE A scraped problems)
          3. Vector DB targeted chunk retrieval (indexed editorial chunks)
        """
        # Tier 1: frontend provided it directly
        if request.editorial and request.editorial.strip():
            logger.info(f"Editorial source: frontend field for {request.problem_id}")
            return request.editorial.strip()

        if not request.problem_id:
            return None

        # Tier 2: direct problem service lookup
        if self.problem_service:
            try:
                problem = self.problem_service.get_problem(request.problem_id)
                if problem and problem.editorial and problem.editorial.strip():
                    logger.info(f"Editorial source: problem_service for {request.problem_id}")
                    return problem.editorial.strip()
            except Exception as e:
                logger.warning(f"problem_service editorial lookup failed for {request.problem_id}: {e}")

        # Tier 3: vector DB targeted retrieval
        if self.chroma_service:
            try:
                title = request.problem_title or ""
                chunks = self.chroma_service.get_editorial_chunks(request.problem_id, title, top_k=5)
                if chunks:
                    combined = "\n\n".join(c["document"] for c in chunks if c.get("document"))
                    if combined.strip():
                        logger.info(f"Editorial source: vector DB chunks ({len(chunks)}) for {request.problem_id}")
                        return combined.strip()
            except Exception as e:
                logger.warning(f"Vector DB editorial lookup failed for {request.problem_id}: {e}")

        return None

    # ── Prompt builders ───────────────────────────────────────────────────────

    @staticmethod
    def _build_workspace_context(request: ChatRequest) -> str:
        """Assemble the workspace snapshot shown in all prompts."""
        parts = []

        if request.problem_id:
            info = [f"Problem: {request.problem_id}"]
            if request.problem_title:
                info.append(f"Title: {request.problem_title}")
            if request.problem_rating:
                info.append(f"Difficulty: {request.problem_rating}")
            if request.problem_tags:
                info.append(f"Tags: {', '.join(request.problem_tags)}")
            parts.append("\n".join(info))

        if request.problem_statement:
            parts.append(f"Problem Statement:\n```\n{request.problem_statement}\n```")

        if request.hints:
            parts.append(f"Revealed Hints:\n```\n{request.hints}\n```")

        if request.user_code:
            parts.append(f"User's Current Code:\n```\n{request.user_code}\n```")

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
            parts.append("\n".join(exec_lines))

        return "\n\n".join(parts)

    @staticmethod
    def _build_history_context(db_history: list, request_history: list) -> str:
        if db_history:
            lines = [f"{m['role'].upper()}: {m['content']}" for m in db_history]
            return "\n".join(lines)
        if request_history:
            lines = [f"{m.role.upper()}: {m.content}" for m in request_history[-4:]]
            return "\n".join(lines)
        return ""

    def _build_editorial_grounded_prompt(
        self,
        request: ChatRequest,
        editorial: str,
        workspace_ctx: str,
        history_str: str,
    ) -> str:
        truncated_editorial = editorial[:6000] if len(editorial) > 6000 else editorial
        tags_str = ", ".join(request.problem_tags) if request.problem_tags else "untagged"
        rating_str = str(request.problem_rating) if request.problem_rating else "unrated"

        return f"""You are ContestMind, an expert competitive programming coach.

==== OFFICIAL EDITORIAL — PRIMARY SOURCE OF TRUTH ====
Problem: {request.problem_id or "unknown"} | {request.problem_title or ""} | Rating: {rating_str} | Tags: {tags_str}

{truncated_editorial}
=======================================================

This is the authoritative solution approach. Your entire response MUST be grounded in this editorial.
Do NOT independently re-derive, guess, or invent an alternative approach.

{("PROBLEM WORKSPACE CONTEXT:\n" + workspace_ctx + "\n") if workspace_ctx else ""}
{("PREVIOUS CONVERSATION:\n" + history_str + "\n") if history_str else ""}
USER QUESTION:
{request.query}

EDITORIAL-GROUNDED INSTRUCTIONS:
1. Ground every explanation, hint, and code suggestion in the editorial above.
2. When giving hints, reveal only what the student's question requires — scaffold progressively, don't spoil the full solution.
3. When asked to generate code, derive it from the editorial's algorithmic description. Use the student's language from the workspace context if specified.
4. When diagnosing WA/TLE/CE: compare the editorial's correct approach against the student's actual code and test output above — pinpoint the exact divergence.
5. If the editorial is unclear on a point, say so explicitly rather than guessing.
6. Explain the WHY behind each step — don't just list steps.
7. Keep the response concise and coach-like; this is a live problem session.

ANSWER:"""

    def _build_reasoning_prompt(
        self,
        request: ChatRequest,
        workspace_ctx: str,
        history_str: str,
        general_context: str,
    ) -> str:
        tags_str = ", ".join(request.problem_tags) if request.problem_tags else "unknown"
        rating_str = str(request.problem_rating) if request.problem_rating else "unknown"

        return f"""You are ContestMind, an elite AI Competitive Programming Coach.

No editorial is available for this problem. Reason carefully from the problem structure, constraints, and tags.

{("PROBLEM WORKSPACE CONTEXT:\n" + workspace_ctx + "\n") if workspace_ctx else ""}
{("PREVIOUS CONVERSATION:\n" + history_str + "\n") if history_str else ""}
{("RELEVANT CONTEXT FROM KNOWLEDGE BASE:\n" + general_context + "\n") if general_context else ""}
USER QUESTION:
{request.query}

REASONING-MODE INSTRUCTIONS:
1. Reason from first principles: constraints → complexity target → algorithmic technique.
2. Tags ({tags_str}) and rating ({rating_str}) are strong signals for the expected approach — use them.
3. When uncertain about the correct approach, express that uncertainty clearly. Wrong confidence on a hard problem is worse than honest doubt.
4. Default to pseudocode first; write actual C++/Python/Java only when the student explicitly asks for a specific language.
5. When diagnosing WA/TLE/CE, use the student's actual code and test output from the workspace context above.
6. For problems rated 2000+, acknowledge that your suggested approach should be verified before trusting it.

ANSWER:"""

    # ── Main entry point ──────────────────────────────────────────────────────

    def generate_chat_response(self, request: ChatRequest) -> ChatResponse:
        # 1. Fetch session history from Supabase
        db_history: list = []
        if self.supabase and request.session_id:
            try:
                res = (
                    self.supabase.table("chat_messages")
                    .select("role, content")
                    .eq("session_id", request.session_id)
                    .order("created_at", desc=False)
                    .execute()
                )
                if res.data:
                    db_history = res.data[-6:]
            except Exception as e:
                logger.error(f"Error fetching chat history: {e}")

        # 2. Save user message
        if self.supabase and request.session_id:
            try:
                self.supabase.table("chat_messages").insert({
                    "session_id": request.session_id,
                    "role": "user",
                    "content": request.query,
                }).execute()
            except Exception as e:
                logger.error(f"Error saving user message: {e}")

        # 3. Resolve editorial (tiered: frontend → problem_service → vector DB)
        editorial = self._resolve_editorial(request)
        is_editorial_grounded = bool(editorial)

        # 4. General semantic context (only used in reasoning mode when no editorial)
        general_context = ""
        if not editorial and self.chroma_service:
            try:
                results = self.chroma_service.query(request.query, top_k=3)
                relevant = [r for r in results if r.get("distance", 2.0) < 1.6]
                if relevant:
                    blocks = []
                    for idx, match in enumerate(relevant):
                        doc = match.get("document", "")
                        meta = match.get("metadata", {})
                        prob_id = meta.get("problem_id", f"ref-{idx + 1}")
                        blocks.append(f"--- SOURCE: Problem {prob_id} ---\n{doc}")
                    general_context = "\n".join(blocks)
            except Exception as e:
                logger.error(f"Vector search failed: {e}")

        # 5. Build shared context blocks
        workspace_ctx = self._build_workspace_context(request)
        history_str = self._build_history_context(db_history, request.history or [])

        # 6. Build tiered prompt
        if editorial:
            prompt = self._build_editorial_grounded_prompt(request, editorial, workspace_ctx, history_str)
            logger.info(f"Chat mode: EDITORIAL GROUNDED for {request.problem_id}")
        else:
            prompt = self._build_reasoning_prompt(request, workspace_ctx, history_str, general_context)
            logger.info(f"Chat mode: REASONING for {request.problem_id or 'general'}")

        # 7. Call LLM
        try:
            llm_response = self.llm_service.generate_text(prompt)
            response_text = llm_response.strip()
        except Exception as e:
            logger.error(f"LLM chat generation failed: {e}")
            response_text = "I encountered an error generating a response. Please try again."

        # 8. Save assistant message
        if self.supabase and request.session_id:
            try:
                self.supabase.table("chat_messages").insert({
                    "session_id": request.session_id,
                    "role": "assistant",
                    "content": response_text,
                }).execute()
            except Exception as e:
                logger.error(f"Error saving assistant message: {e}")

        return ChatResponse(
            response_text=response_text,
            is_editorial_grounded=is_editorial_grounded,
        )
