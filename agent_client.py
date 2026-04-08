from __future__ import annotations

import json
from typing import Literal


API_KEY_PATH = r"C:\\Users\\orlando.caballero\\Downloads\\oaiak2"


def _read_api_key() -> str:
    try:
        with open(API_KEY_PATH, "r", encoding="utf-8") as handle:
            api_key = handle.read().strip()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"API key file not found: {API_KEY_PATH}") from exc
    if not api_key:
        raise ValueError("API key file is empty.")
    return api_key


def _response_output_text(response) -> str:
    text = getattr(response, "output_text", None)
    if text:
        return text

    output = getattr(response, "output", None)
    if not output:
        return ""

    for item in output:
        if getattr(item, "type", None) != "message":
            continue
        for part in getattr(item, "content", []) or []:
            if getattr(part, "type", None) == "output_text":
                return getattr(part, "text", "")

    return ""


def extract_structured_report(report_text: str) -> dict[str, object]:
    api_key = _read_api_key()

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    system = (
        "You are a pathology report extractor. Classify the report as either "
        "standard (DCIS biopsy protocol) or invasive (invasive carcinoma biopsy protocol). "
        "Return STRICT JSON with keys: protocol_type and fields. "
        "protocol_type must be 'standard' or 'invasive'. "
        "fields must contain only the fields for that protocol and all values must be lists of strings, "
        "except for standard.additional_findings and standard.biomarker_studies which are strings or null. "
        "If a field is not stated, use an empty list or null."
    )

    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": report_text[:8000]},
        ],
    )

    raw = _response_output_text(response).strip()
    if not raw:
        return {}

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def classify_report_type(report_text: str) -> Literal["standard", "invasive"]:
    payload = extract_structured_report(report_text)
    protocol_type = payload.get("protocol_type")
    if protocol_type == "invasive":
        return "invasive"
    return "standard"
