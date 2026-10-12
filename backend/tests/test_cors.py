"""CORS fix verification (F02). Runs standalone — no GROQ_API_KEY needed."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.core.config import settings

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
def ping():
    return {"ok": True}


client = TestClient(app)


def test_allowed_origin():
    r = client.get("/ping", headers={"Origin": "http://localhost:3000"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000", (
        f"Expected allow-origin header, got: {r.headers.get('access-control-allow-origin')}"
    )


def test_allowed_origin_vercel():
    r = client.get("/ping", headers={"Origin": "https://contest-mind.vercel.app"})
    assert r.headers.get("access-control-allow-origin") == "https://contest-mind.vercel.app"


def test_disallowed_origin_blocked():
    r = client.get("/ping", headers={"Origin": "https://evil.com"})
    assert r.headers.get("access-control-allow-origin") is None, (
        f"Evil origin must NOT be allowed, got: {r.headers.get('access-control-allow-origin')}"
    )


def test_no_origin_header():
    r = client.get("/ping")
    assert r.status_code == 200


def test_cors_config_not_wildcard():
    assert settings.cors_origins, "cors_origins must not be empty"
    assert ".*" not in settings.cors_origins, "Wildcard regex must not be present"
    assert len(settings.cors_origins) > 0


if __name__ == "__main__":
    tests = [
        test_allowed_origin,
        test_allowed_origin_vercel,
        test_disallowed_origin_blocked,
        test_no_origin_header,
        test_cors_config_not_wildcard,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
        except Exception as e:
            print(f"  ERROR {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)
