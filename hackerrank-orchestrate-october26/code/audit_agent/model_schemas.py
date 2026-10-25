"""Versioned strict JSON schemas and a deliberately small schema validator."""
from __future__ import annotations

import hashlib
import json


def obj(properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


TEXT = {"type": "string", "maxLength": 4000}
NULLABLE_TEXT = {"type": ["string", "null"], "maxLength": 4000}
SCREENSHOT_SCHEMA = obj({
    "complete": {"type": "boolean"},
    "records": {"type": "array", "maxItems": 100, "items": obj({
        **{name: NULLABLE_TEXT for name in ("system_text", "resource_text", "category_text", "result_text",
                                            "subject_text", "observed_at_text")},
        "visible_text": TEXT,
        "box": {"type": "array", "minItems": 4, "maxItems": 4,
                "items": {"type": "integer", "minimum": 0, "maximum": 20000}},
    })},
})
INTENT_SCHEMA = obj({
    "action": {"type": "string", "enum": ["delete_account", "access", "export", "correction",
                                              "marketing_opt_out", "login_help", "unknown"]},
    "affirmed": {"type": "boolean"}, "negated": {"type": "boolean"}, "conditional": {"type": "boolean"},
    "spans": {"type": "array", "maxItems": 12, "items": obj({
        "start": {"type": "integer", "minimum": 0, "maximum": 16000},
        "end": {"type": "integer", "minimum": 1, "maximum": 16000}, "text": TEXT,
    })},
})


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def strict_json(text: str):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate key")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("Non-finite JSON")
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def validate(value, schema) -> None:
    types = {"object": dict, "array": list, "string": str, "boolean": bool, "integer": int, "null": type(None)}
    allowed = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
    if not any(type(value) is types[t] for t in allowed):
        raise ValueError("Wrong JSON type")
    if value is None:
        return
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError("Enum")
    if type(value) is dict:
        if set(value) != set(schema["required"]):
            raise ValueError("Unexpected or missing properties")
        for key, item in value.items():
            validate(item, schema["properties"][key])
    elif type(value) is list:
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", 1000):
            raise ValueError("Array bound")
        for item in value:
            validate(item, schema["items"])
    elif type(value) is str and len(value) > schema.get("maxLength", 16000):
        raise ValueError("String bound")
    elif type(value) is int and not schema.get("minimum", value) <= value <= schema.get("maximum", value):
        raise ValueError("Number bound")
