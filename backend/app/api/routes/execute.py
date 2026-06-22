"""
Code execution route.

Execution strategy (in order of preference):
  1. Piston public API  (emkc.org) — no key, no local deps
  2. Local subprocess  (g++ / python3 / java on the host)

Both paths feed into output comparison when expected_output is provided.
"""
import asyncio
import logging
import os
import re
import subprocess
import tempfile
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException

from app.schemas.execute import ExecuteRequest, ExecuteResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Constants ─────────────────────────────────────────────────────────────────

WANDBOX_URL = "https://wandbox.org/api/compile.json"
WANDBOX_TIMEOUT = 20.0
RUN_TIMEOUT_SEC = 10
COMPILE_TIMEOUT_SEC = 45

# Maps frontend language id → Wandbox compiler name
LANGUAGE_MAP = {
    "cpp":        "gcc-head",
    "c++":        "gcc-head",
    "python":     "cpython-3.12.0",
    "python3":    "cpython-3.12.0",
    "java":       "openjdk-head",
    "javascript": "nodejs-head",
    "js":         "nodejs-head",
}

SUPPORTED_LANGUAGES = sorted(set(LANGUAGE_MAP.keys()))


# ── Output comparison ─────────────────────────────────────────────────────────

def _compare_output(actual: str, expected: str) -> bool:
    """Whitespace-tolerant comparison (trim each line, normalize endings)."""
    def normalize(s: str) -> str:
        return "\n".join(line.rstrip() for line in s.strip().splitlines())

    return normalize(actual) == normalize(expected)


def _finalize(result: ExecuteResponse, expected_output: Optional[str]) -> ExecuteResponse:
    """Attach verdict and optional expected-output comparison to the result."""
    if result.status in ("compile_error", "tle", "error"):
        return result  # verdict already set

    if result.exit_code != 0:
        result.status = "runtime_error"
    elif expected_output is not None:
        matched = _compare_output(result.stdout, expected_output)
        result.matched_expected = matched
        result.status = "accepted" if matched else "wrong_answer"
    else:
        result.status = "ok"

    return result


# ── Wandbox execution ──────────────────────────────────────────────────────────

async def _run_via_piston(request: ExecuteRequest) -> ExecuteResponse:
    """Execute via the Wandbox public API (replaces Piston which threw 401). Raises RuntimeError if unavailable."""
    lang_key = request.language.lower()
    compiler = LANGUAGE_MAP.get(lang_key, "gcc-head")

    payload = {
        "compiler": compiler,
        "code": request.code,
        "stdin": request.stdin or "",
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=WANDBOX_TIMEOUT, headers=headers) as client:
        resp = await client.post(WANDBOX_URL, json=payload)

    if resp.status_code != 200:
        raise RuntimeError(f"Wandbox returned HTTP {resp.status_code}")

    data = resp.json()
    status = data.get("status", "1")
    
    # Wandbox returns "0" for success, but compile errors are captured in "compiler_error"
    compiler_error = data.get("compiler_error", "")
    if compiler_error:
        return ExecuteResponse(
            stdout="",
            stderr=compiler_error,
            exit_code=1,
            status="compile_error",
        )

    return ExecuteResponse(
        stdout=data.get("program_output", ""),
        stderr=data.get("program_error", ""),
        exit_code=0 if status == "0" else 1,

    )


# ── Local subprocess execution ────────────────────────────────────────────────

def _run_python_local(tmpdir: str, code: str, stdin: str) -> ExecuteResponse:
    code_file = os.path.join(tmpdir, "solution.py")
    with open(code_file, "w", encoding="utf-8") as f:
        f.write(code)

    py = "python" if os.name == "nt" else "python3"
    try:
        r = subprocess.run(
            [py, code_file],
            input=stdin, capture_output=True, text=True, timeout=RUN_TIMEOUT_SEC,
        )
        return ExecuteResponse(stdout=r.stdout, stderr=r.stderr, exit_code=r.returncode)
    except subprocess.TimeoutExpired:
        return ExecuteResponse(stderr="Time Limit Exceeded (10 s)", exit_code=1, status="tle")
    except FileNotFoundError:
        return ExecuteResponse(stderr=f"'{py}' not found on server", exit_code=1, status="error",
                               error="Python interpreter not installed")


def _run_cpp_local(tmpdir: str, code: str, stdin: str) -> ExecuteResponse:
    src = os.path.join(tmpdir, "solution.cpp")
    exe = os.path.join(tmpdir, "solution" + (".exe" if os.name == "nt" else ""))
    with open(src, "w", encoding="utf-8") as f:
        f.write(code)

    # Compile
    try:
        cr = subprocess.run(
            ["g++", "-std=c++17", "-o", exe, src],
            capture_output=True, text=True, timeout=COMPILE_TIMEOUT_SEC,
        )
        if cr.returncode != 0:
            return ExecuteResponse(stdout="", stderr=cr.stderr, exit_code=cr.returncode,
                                   status="compile_error")
    except subprocess.TimeoutExpired:
        return ExecuteResponse(stderr="Compilation timed out", exit_code=1, status="compile_error")
    except FileNotFoundError:
        return ExecuteResponse(stderr="'g++' not found on server", exit_code=1, status="error",
                               error="g++ compiler not installed")

    # Run
    try:
        r = subprocess.run(
            [exe], input=stdin, capture_output=True, text=True, timeout=RUN_TIMEOUT_SEC,
        )
        return ExecuteResponse(stdout=r.stdout, stderr=r.stderr, exit_code=r.returncode)
    except subprocess.TimeoutExpired:
        return ExecuteResponse(stderr="Time Limit Exceeded (10 s)", exit_code=1, status="tle")


def _run_java_local(tmpdir: str, code: str, stdin: str) -> ExecuteResponse:
    # Extract public class name (defaults to Main)
    m = re.search(r"public\s+class\s+(\w+)", code)
    class_name = m.group(1) if m else "Main"
    src = os.path.join(tmpdir, f"{class_name}.java")
    with open(src, "w", encoding="utf-8") as f:
        f.write(code)

    # Compile
    try:
        cr = subprocess.run(
            ["javac", src], capture_output=True, text=True, timeout=COMPILE_TIMEOUT_SEC, cwd=tmpdir,
        )
        if cr.returncode != 0:
            return ExecuteResponse(stdout="", stderr=cr.stderr, exit_code=cr.returncode,
                                   status="compile_error")
    except subprocess.TimeoutExpired:
        return ExecuteResponse(stderr="Compilation timed out", exit_code=1, status="compile_error")
    except FileNotFoundError:
        return ExecuteResponse(stderr="'javac' not found on server", exit_code=1, status="error",
                               error="Java compiler not installed")

    # Run
    try:
        r = subprocess.run(
            ["java", class_name], input=stdin, capture_output=True, text=True,
            timeout=RUN_TIMEOUT_SEC, cwd=tmpdir,
        )
        return ExecuteResponse(stdout=r.stdout, stderr=r.stderr, exit_code=r.returncode)
    except subprocess.TimeoutExpired:
        return ExecuteResponse(stderr="Time Limit Exceeded (10 s)", exit_code=1, status="tle")


def _run_local(request: ExecuteRequest) -> ExecuteResponse:
    """Dispatch to the correct local runner."""
    lang = request.language.lower()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            if lang in ("cpp", "c++"):
                return _run_cpp_local(tmpdir, request.code, request.stdin)
            elif lang in ("python", "python3"):
                return _run_python_local(tmpdir, request.code, request.stdin)
            elif lang == "java":
                return _run_java_local(tmpdir, request.code, request.stdin)
            else:
                return ExecuteResponse(
                    stderr=f"Language '{lang}' not supported for local execution",
                    exit_code=1, status="error",
                )
    except Exception as e:
        logger.error(f"Local execution error: {e}", exc_info=True)
        return ExecuteResponse(stderr=str(e), exit_code=1, status="error")


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("/", response_model=ExecuteResponse)
async def execute_code(request: ExecuteRequest):
    """
    Execute code and return stdout / stderr / verdict.

    Tries Piston first; falls back to local subprocess on failure.
    If expected_output is provided the response includes matched_expected
    and status becomes 'accepted' or 'wrong_answer'.
    """
    lang_key = request.language.lower()
    if lang_key not in LANGUAGE_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language '{request.language}'. Supported: {SUPPORTED_LANGUAGES}",
        )

    result: ExecuteResponse

    # 1. Try Piston
    try:
        result = await _run_via_piston(request)
        logger.info(f"Piston execution: lang={lang_key}, exit={result.exit_code}")
    except Exception as e:
        logger.warning(f"Piston unavailable ({e}) — falling back to local execution")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _run_local, request)
        logger.info(f"Local execution: lang={lang_key}, exit={result.exit_code}")

    return _finalize(result, request.expected_output)
