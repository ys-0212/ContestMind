import logging
from typing import Optional, List
from supabase import create_client, Client

from app.core.config import settings
from app.schemas.hint import HintRequestCreate, HintRequestResponse

from app.services.problem_service import ProblemService
from app.services.llm.base import BaseLLMService
from app.schemas.llm import HintRequest, HintResponse

logger = logging.getLogger(__name__)

from app.services.chroma_service import ChromaService


def _prev_block(previous_hints: List[str]) -> str:
    """Build a 'previous hints' context block for the prompt."""
    if not previous_hints:
        return ""
    lines = "\n".join(
        f"  Hint {i + 1}: {h.strip()}"
        for i, h in enumerate(previous_hints)
        if h.strip()
    )
    return f"HINTS ALREADY REVEALED TO THE STUDENT (do NOT repeat or paraphrase these):\n{lines}\n\n"


class HintService:
    def __init__(
        self,
        problem_service: ProblemService = None,
        llm_service: BaseLLMService = None,
        chroma_service: ChromaService = None,
    ):
        self.problem_service = problem_service
        self.llm_service = llm_service
        self.chroma_service = chroma_service

        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            logger.warning("Supabase URL or Key not set. Hint tracking will be disabled/mocked.")
            self.client: Optional[Client] = None
        else:
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    # ── Main generation ───────────────────────────────────────────────────────

    def generate_hint(self, request: HintRequest) -> HintResponse:
        if not self.problem_service or not self.llm_service:
            raise ValueError("HintService not fully initialized for generation")

        problem = self.problem_service.get_problem(request.problem_id)
        if not problem:
            raise ValueError(f"Problem {request.problem_id} not found.")

        editorial_text: Optional[str] = None
        if self.chroma_service:
            try:
                query_str = f"Codeforces problem {request.problem_id} {problem.title} editorial solution"
                results = self.chroma_service.query(query_str, top_k=1)
                if results:
                    top_match = results[0]
                    meta = top_match.get("metadata", {})
                    if meta.get("problem_id") == request.problem_id:
                        editorial_text = top_match.get("document")
            except Exception as e:
                logger.warning(f"ChromaDB query failed for hint {request.problem_id}: {e}")

        level = request.current_hint_level
        prev = _prev_block(request.previous_hints)
        tags_str = ", ".join(problem.tags) if problem.tags else "no tags"
        rating_str = str(problem.rating) if problem.rating else "unknown"

        if editorial_text:
            logger.info(f"Using RAG editorial for {request.problem_id}, level {level}")
            prompt = self._editorial_prompt(
                level, problem.title, rating_str, tags_str, editorial_text, prev
            )
        else:
            logger.info(f"No editorial for {request.problem_id}, using fallback, level {level}")
            prompt = self._fallback_prompt(level, problem.title, rating_str, tags_str, prev)

        try:
            hint_text = self.llm_service.generate_text(prompt).strip()
        except Exception as e:
            logger.error(f"LLM hint generation failed: {e}")
            hint_text = "Sorry, I couldn't generate a hint right now."

        return HintResponse(
            problem_id=request.problem_id,
            hint_level=level,
            hint_text=hint_text,
        )

    # ── Prompt builders ───────────────────────────────────────────────────────

    @staticmethod
    def _editorial_prompt(
        level: int,
        title: str,
        rating: str,
        tags: str,
        editorial: str,
        prev: str,
    ) -> str:
        header = (
            f'You are an expert competitive programming coach.\n'
            f'Problem: "{title}" | Rating: {rating} | Tags: {tags}\n\n'
            f'Official editorial:\n---\n{editorial}\n---\n\n'
        )

        if level == 1:
            return header + """\
Generate HINT 1 — CONSTRAINT ANALYSIS.

YOUR ONLY JOB: Surface a critical constraint or boundary condition that rules out naive solutions.

STRICT RULES:
- Talk ONLY about input sizes, value ranges, time/memory limits, or structural constraints
- DO NOT name any algorithm, technique, or data structure (no "greedy", "DP", "binary search", "graph", etc.)
- DO NOT hint at the approach or solution strategy
- Frame it as a precise technical observation, e.g. "With n up to 2×10^5, any O(n²) approach exceeds 10^8 operations."
- Maximum 2 sentences. Be direct, no filler.

Output ONLY the hint text."""

        if level == 2:
            return header + prev + """\
Generate HINT 2 — ALGORITHMIC DIRECTION.

YOUR ONLY JOB: Name the algorithm/technique and give the key insight that makes it correct.

STRICT RULES:
- Name the specific algorithm or paradigm (Greedy, DP, Binary Search, Two Pointers, Segment Tree, etc.)
- Give the PRECISE mathematical or structural observation that justifies this choice
  — not "use DP" but "dp[i] represents the minimum cost to reach index i, using the recurrence dp[i] = min(dp[i-1]+cost(i), dp[i-2]+cost(i))"
- DO NOT provide pseudocode or implementation steps
- DO NOT repeat or paraphrase anything from the previous hints
- Advance meaningfully beyond Hint 1 — new information only
- 2-3 sentences maximum

Output ONLY the hint text."""

        # level == 3
        return header + prev + """\
Generate HINT 3 — IMPLEMENTATION GUIDE.

YOUR ONLY JOB: Provide a concrete pseudocode outline and call out the critical traps.

STRICT RULES:
- Give 3-6 ordered pseudocode steps (numbered list)
- Identify the most likely implementation pitfalls: off-by-one, overflow, wrong base case, etc.
- Mention any specific data structures, indexing conventions, or loop invariants required
- DO NOT write complete compilable code
- DO NOT repeat or paraphrase anything from the previous hints
- Be concrete enough that a student who understands the algorithm can translate this to AC

Output ONLY the hint text."""

    @staticmethod
    def _fallback_prompt(
        level: int,
        title: str,
        rating: str,
        tags: str,
        prev: str,
    ) -> str:
        header = (
            f'You are an expert competitive programming coach.\n'
            f'Problem: "{title}" | Rating: {rating} | Tags: {tags}\n'
            f'(No editorial available — use tags and rating to infer hints.)\n\n'
        )

        if level == 1:
            return header + """\
Generate HINT 1 — CONSTRAINT ANALYSIS.

YOUR ONLY JOB: Identify ONE constraint implication or feasibility bound for this problem.

STRICT RULES:
- Discuss what the rating and typical problem structure imply about time complexity
- Mention a specific limit that rules out brute-force approaches
- DO NOT name any algorithm, technique, or data structure
- DO NOT reveal or suggest the approach
- Be technically precise, not vague ("think about complexity" is bad; "O(n log n) is the target since n can reach 10^5" is good)
- Maximum 2 sentences

Output ONLY the hint text."""

        if level == 2:
            return header + prev + f"""\
Generate HINT 2 — ALGORITHMIC DIRECTION.

YOUR ONLY JOB: Based on the tags ({tags}), name the technique and give the specific insight.

STRICT RULES:
- Name the primary algorithmic technique this problem tests
- Explain the KEY insight that connects the problem structure to this technique
  — be specific: "Sort by X and greedily pair adjacent elements" not just "greedy"
- DO NOT give pseudocode or step-by-step implementation
- DO NOT repeat or paraphrase anything from the previous hints
- 2-3 sentences maximum

Output ONLY the hint text."""

        # level == 3
        return header + prev + """\
Generate HINT 3 — IMPLEMENTATION GUIDE.

YOUR ONLY JOB: Give a step-by-step pseudocode outline and warn about the common traps.

STRICT RULES:
- Write 3-5 numbered pseudocode steps
- Call out the most common pitfall for this type of problem (overflow, empty-array edge case, etc.)
- DO NOT write complete compilable code
- DO NOT repeat or paraphrase anything from the previous hints
- Be concrete enough to guide a student from idea to working implementation

Output ONLY the hint text."""

    # ── Supabase tracking ─────────────────────────────────────────────────────

    def record_hint(self, hint_request: HintRequestCreate) -> Optional[HintRequestResponse]:
        if not self.client:
            logger.error("Cannot record hint: Supabase client not initialized.")
            return None
        try:
            data = hint_request.model_dump()
            response = self.client.table("hint_requests").insert(data).execute()
            if response.data and len(response.data) > 0:
                return HintRequestResponse(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Failed to record hint request in Supabase: {e}")
            return None

    def get_max_hint_level(self, handle: str, problem_id: str) -> int:
        if not self.client:
            logger.error("Cannot fetch hint level: Supabase client not initialized.")
            return 0
        try:
            response = (
                self.client.table("hint_requests")
                .select("hint_level")
                .eq("handle", handle)
                .eq("problem_id", problem_id)
                .order("hint_level", desc=True)
                .limit(1)
                .execute()
            )
            if response.data and len(response.data) > 0:
                return response.data[0].get("hint_level", 0)
            return 0
        except Exception as e:
            logger.error(f"Failed to fetch hint level from Supabase: {e}")
            return 0
