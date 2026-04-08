from __future__ import annotations

import json
import os
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


def classify_report_type(report_text: str) -> Literal["standard", "invasive"]:
    """
    Classify report text into protocol type.

    Returns:
        "standard" for DCIS protocol or "invasive" for invasive protocol.
    """
    api_key = _read_api_key()

    # TODO: Call external agent API with api_key and report_text.
    # TODO: Replace placeholder logic with real API response parsing.

    _ = report_text  # placeholder to silence unused variable warnings
    _ = api_key
    return "standard"


def extract_additional_findings_and_biomarkers(report_text: str) -> dict[str, list[str]]:
    api_key = _read_api_key()

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    system = (
        "Extract additional findings and biomarker studies from the pathology report. "
        "Return strict JSON with keys: additional_findings (list of strings) and "
        "biomarker_studies (list of strings). If none, return empty lists."
    )

    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": report_text[:8000]},
        ],
    )

    raw = _response_output_text(response).strip()
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {"additional_findings": [], "biomarker_studies": []}

    additional_findings = data.get("additional_findings") or []
    biomarker_studies = data.get("biomarker_studies") or []

    if not isinstance(additional_findings, list):
        additional_findings = []
    if not isinstance(biomarker_studies, list):
        biomarker_studies = []

    return {
        "additional_findings": [str(x) for x in additional_findings if str(x).strip()],
        "biomarker_studies": [str(x) for x in biomarker_studies if str(x).strip()],
    }
