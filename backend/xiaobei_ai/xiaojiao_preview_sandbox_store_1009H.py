"""
Preview-only Xiaojiao Work State sandbox store.

This adapter is intentionally outside production persistence. It is designed for
local preview route experiments and audit smoke tests before any real Work State
Store is approved.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
SANDBOX_STORE_PATH = ROOT / "outputs" / "xiaojiao_preview_sandbox_store_1009H" / "store.json"
STORE_VERSION = "1009H-backend-sandbox-v1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def seed_store() -> Dict[str, Any]:
    return {
        "store_version": STORE_VERSION,
        "preview_route_only": True,
        "production_store_enabled": False,
        "real_database_written": False,
        "formal_apply_performed": False,
        "work_states": {
            "work_state_art_teacher_today_1009": {
                "work_state_id": "work_state_art_teacher_today_1009",
                "teacher_id": "teacher_art_001",
                "teacher_role": "小学美术教师",
                "subject": "美术",
                "grade": "四年级",
                "class_id": "class_grade4_1",
                "week": 3,
                "weekday": "周三",
                "current_surface": "light_entry",
                "current_work_object_id": "lesson_design_L003",
                "updated_at": _now(),
                "version": 1,
                "source": "backend_sandbox_seed",
            }
        },
        "work_objects": {
            "lesson_design_L003": {
                "work_object_id": "lesson_design_L003",
                "work_object_type": "lesson_design",
                "title": "《色彩的感觉》课时设计草稿",
                "status": "draft",
                "review_status": "none",
            },
            "handout_L003": {
                "work_object_id": "handout_L003",
                "work_object_type": "handout",
                "title": "《色彩的感觉》学习单",
                "status": "draft",
                "review_status": "none",
            },
        },
        "event_logs": [],
        "work_object_patches": [],
        "teacher_review_gates": [],
        "provider_cost_events": [],
    }


def _ensure_parent() -> None:
    SANDBOX_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_store() -> Dict[str, Any]:
    if not SANDBOX_STORE_PATH.exists():
        return seed_store()
    return json.loads(SANDBOX_STORE_PATH.read_text(encoding="utf-8"))


def save_store(store: Dict[str, Any]) -> Dict[str, Any]:
    data = copy.deepcopy(store)
    data["preview_route_only"] = True
    data["production_store_enabled"] = False
    data["real_database_written"] = False
    data["formal_apply_performed"] = False
    _ensure_parent()
    SANDBOX_STORE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def reset_sandbox_store() -> Dict[str, Any]:
    return save_store(seed_store())


def load_work_state(work_state_id: str = "work_state_art_teacher_today_1009") -> Dict[str, Any]:
    return copy.deepcopy(load_store()["work_states"][work_state_id])


def save_work_state(work_state: Dict[str, Any]) -> Dict[str, Any]:
    store = load_store()
    item = copy.deepcopy(work_state)
    item["updated_at"] = _now()
    item["version"] = int(item.get("version") or 0) + 1
    item["source"] = "backend_sandbox_store"
    store.setdefault("work_states", {})[item["work_state_id"]] = item
    save_store(store)
    return item


def load_work_objects() -> Dict[str, Any]:
    return copy.deepcopy(load_store().get("work_objects", {}))


def save_work_object(work_object: Dict[str, Any]) -> Dict[str, Any]:
    store = load_store()
    item = copy.deepcopy(work_object)
    store.setdefault("work_objects", {})[item["work_object_id"]] = item
    save_store(store)
    return item


def append_event(event: Dict[str, Any]) -> Dict[str, Any]:
    store = load_store()
    item = copy.deepcopy(event)
    item.setdefault("event_id", f"evt_{int(datetime.now().timestamp() * 1000)}")
    item.setdefault("created_at", _now())
    item.setdefault("source", "backend_sandbox_store")
    item["formal_apply_performed"] = False
    store.setdefault("event_logs", []).append(item)
    save_store(store)
    return item


def create_work_object_patch(patch: Dict[str, Any]) -> Dict[str, Any]:
    store = load_store()
    item = copy.deepcopy(patch)
    item.setdefault("patch_id", f"patch_{int(datetime.now().timestamp() * 1000)}")
    item["teacher_review_required"] = True
    item["formal_apply_performed"] = False
    item.setdefault("patch_status", "pending_teacher_review")
    item.setdefault("created_at", _now())
    store.setdefault("work_object_patches", []).append(item)
    save_store(store)
    return item


def create_teacher_review_gate(gate: Dict[str, Any]) -> Dict[str, Any]:
    store = load_store()
    item = copy.deepcopy(gate)
    item.setdefault("review_id", f"review_{int(datetime.now().timestamp() * 1000)}")
    item.setdefault("decision_options", ["confirm", "revise_then_confirm", "defer", "discard"])
    item.setdefault("review_status", "pending")
    item["final_apply_allowed"] = False
    item["formal_apply_performed"] = False
    store.setdefault("teacher_review_gates", []).append(item)
    save_store(store)
    return item


def update_teacher_review_gate(review_id: str, decision: str) -> Dict[str, Any]:
    store = load_store()
    for item in store.setdefault("teacher_review_gates", []):
        if item.get("review_id") == review_id:
            item["teacher_decision"] = decision
            item["review_status"] = "confirmed" if decision == "confirm" else decision
            item["reviewed_at"] = _now()
            item["final_apply_allowed"] = False
            item["formal_apply_performed"] = False
            save_store(store)
            return copy.deepcopy(item)
    raise KeyError(f"review gate not found: {review_id}")


def estimate_provider_cost(action: str, input_tokens: int = 0, output_tokens: int = 0) -> Dict[str, Any]:
    # Pricing is intentionally not guessed. 1009J keeps the cost gate incomplete
    # until a provider pricing table is approved.
    return {
        "action": action,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_cny": None,
        "cost_gate_incomplete": True,
        "reason": "provider pricing table not configured",
        "next_cost_action": "add approved provider pricing config before batch or background generation",
    }


def record_provider_cost_event(action: str, input_tokens: int = 0, output_tokens: int = 0) -> Dict[str, Any]:
    store = load_store()
    event = estimate_provider_cost(action, input_tokens, output_tokens)
    event["event_id"] = f"cost_evt_{int(datetime.now().timestamp() * 1000)}"
    event["created_at"] = _now()
    event["batch_generation_allowed"] = False
    event["background_generation_allowed"] = False
    event["default_route_auto_provider_call_allowed"] = False
    store.setdefault("provider_cost_events", []).append(event)
    save_store(store)
    return copy.deepcopy(event)


def export_sandbox_snapshot() -> Dict[str, Any]:
    store = load_store()
    snapshot = copy.deepcopy(store)
    snapshot["exported_at"] = _now()
    snapshot["redacted"] = True
    snapshot["api_key_leakage_detected"] = False
    return snapshot
