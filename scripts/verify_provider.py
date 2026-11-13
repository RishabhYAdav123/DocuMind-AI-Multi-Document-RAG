"""Check Gemini model access and structured generation without logging credentials."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from google import genai
from google.genai import errors, types
from config.settings import Settings
from src.llm_service import GeminiService, ProviderError


def main() -> int:
    settings = Settings()
    result = {"checked_at": datetime.now(timezone.utc).isoformat(), "provider": "gemini",
              "configured_model": settings.llm_model, "credential_present": bool(settings.google_api_key.get_secret_value()),
              "model_access": "not_checked", "structured_generation": "not_run"}
    try:
        with genai.Client(api_key=settings.google_api_key.get_secret_value(),
                          http_options=types.HttpOptions(timeout=30000)) as client:
            model = client.models.get(model=settings.llm_model)
            result.update(model_access="passed", returned_model=model.name)
        rewritten = GeminiService(settings).rewrite("What was Northstar revenue in 2024?", [])
        result["structured_generation"] = "passed" if not rewritten.needs_clarification else "unexpected_clarification"
    except errors.APIError as error:
        result.update(model_access="failed", http_status=error.code)
        # Never persist provider messages, request headers or raw exception bodies.
        body = getattr(error, "details", {}) or {}
        details = body.get("error", {}).get("details", []) if isinstance(body, dict) else []
        known = {"API_KEY_INVALID", "API_KEY_EXPIRED", "API_KEY_SERVICE_BLOCKED", "SERVICE_DISABLED",
                 "BILLING_DISABLED", "ACCESS_TOKEN_EXPIRED"}
        reasons = [d.get("reason") for d in details if isinstance(d, dict) and d.get("reason") in known]
        result["reason"] = reasons[0] if reasons else "request_rejected_check_credentials_model_and_account"
    except ProviderError:
        result["structured_generation"] = "failed_check_credentials_quota_and_model"
    except Exception:
        result["model_access"] = "connection_or_configuration_error"
    (ROOT / "evaluation/provider_verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["structured_generation"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
