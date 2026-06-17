"""User-scoped retrieval settings."""
import json
import os
import tempfile
from pathlib import Path
from threading import Lock
from typing import Any, Dict


DEFAULT_RETRIEVAL_SETTINGS = {
    "use_reranker": True,
    "translate_query": True,
    "top_k": 10,
    "initial_k": 20,
}

SETTING_LIMITS = {
    "top_k": (1, 20),
    "initial_k": (5, 100),
}


class RetrievalSettingsService:
    """Persist lightweight retrieval preferences in a local JSON file."""

    def __init__(self) -> None:
        data_dir = Path(os.getenv("VECTOR_SEARCH_DATA_DIR", Path(__file__).resolve().parents[2] / "data"))
        data_dir.mkdir(parents=True, exist_ok=True)
        self.settings_path = data_dir / "retrieval-settings.json"
        self._lock = Lock()

    def get_settings(self, user_id: Any) -> Dict[str, Any]:
        key = self._user_key(user_id)
        with self._lock:
            all_settings = self._read_all()
            stored = all_settings.get(key, {})
            return {**DEFAULT_RETRIEVAL_SETTINGS, **self._clean_settings(stored)}

    def update_settings(self, user_id: Any, updates: Dict[str, Any]) -> Dict[str, Any]:
        key = self._user_key(user_id)
        with self._lock:
            all_settings = self._read_all()
            current = {**DEFAULT_RETRIEVAL_SETTINGS, **self._clean_settings(all_settings.get(key, {}))}
            current.update(self._clean_settings(updates))
            all_settings[key] = current
            self._write_all(all_settings)
            return current

    def resolve_use_reranker(self, user_id: Any, explicit_value: Any = None) -> bool:
        if explicit_value is not None:
            return bool(explicit_value)
        return self.get_settings(user_id)["use_reranker"]

    def resolve_translate_query(self, user_id: Any, explicit_value: Any = None) -> bool:
        if explicit_value is not None:
            return bool(explicit_value)
        return self.get_settings(user_id)["translate_query"]

    def resolve_top_k(self, user_id: Any, explicit_value: Any = None) -> int:
        if explicit_value is not None:
            return self._clamp_int(explicit_value, *SETTING_LIMITS["top_k"])
        return int(self.get_settings(user_id)["top_k"])

    def resolve_initial_k(self, user_id: Any, explicit_value: Any = None, top_k: int | None = None) -> int:
        if explicit_value is not None:
            initial_k = self._clamp_int(explicit_value, *SETTING_LIMITS["initial_k"])
        else:
            initial_k = int(self.get_settings(user_id)["initial_k"])
        if top_k is not None:
            initial_k = max(initial_k, top_k)
        return initial_k

    def _read_all(self) -> Dict[str, Dict[str, Any]]:
        if not self.settings_path.exists():
            return {}
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _write_all(self, data: Dict[str, Dict[str, Any]]) -> None:
        fd, tmp_name = tempfile.mkstemp(
            prefix=f"{self.settings_path.name}.",
            suffix=".tmp",
            dir=str(self.settings_path.parent),
            text=True,
        )
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
        os.chmod(tmp_name, 0o664)
        os.replace(tmp_name, self.settings_path)

    @staticmethod
    def _clean_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = {}
        for key in ("use_reranker", "translate_query"):
            if key in settings and settings[key] is not None:
                cleaned[key] = bool(settings[key])
        for key, limits in SETTING_LIMITS.items():
            if key in settings and settings[key] is not None:
                cleaned[key] = RetrievalSettingsService._clamp_int(settings[key], *limits)
        return cleaned

    @staticmethod
    def _clamp_int(value: Any, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = minimum
        return max(minimum, min(maximum, parsed))

    @staticmethod
    def _user_key(user_id: Any) -> str:
        return str(user_id or "anonymous")


_settings_service: RetrievalSettingsService | None = None


def get_retrieval_settings_service() -> RetrievalSettingsService:
    global _settings_service
    if _settings_service is None:
        _settings_service = RetrievalSettingsService()
    return _settings_service
