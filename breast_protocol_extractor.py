"""Breast histopathology variable extraction from plain-text reports.

Designed for real-world pathology narratives (for example `r.document_plain_text`
from a database), while still aligned to CAP DCIS biopsy variables.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from typing import Literal, TypedDict

from agent_client import extract_structured_report


class AgentPayload(TypedDict):
    protocol_type: Literal["standard", "invasive"]
    fields: dict[str, object]


def _validate_agent_payload(payload: dict[str, object]) -> AgentPayload:
    if not isinstance(payload, dict):
        raise ValueError("Agent payload is not a dict.")

    protocol_type = payload.get("protocol_type")
    if protocol_type not in ("standard", "invasive"):
        raise ValueError("Agent payload missing valid protocol_type.")

    fields = payload.get("fields")
    if not isinstance(fields, dict):
        raise ValueError("Agent payload missing fields dict.")

    return {"protocol_type": protocol_type, "fields": fields}


def _list_field(fields: dict[str, object], key: str) -> list[str]:
    value = fields.get(key)
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    # TODO: Agent missing or invalid list field; decide on error handling or retry.
    return []


def _string_or_none_field(fields: dict[str, object], key: str) -> str | None:
    value = fields.get(key)
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned if cleaned else None
    if value is None:
        return None
    # TODO: Agent returned non-string for string field; decide on error handling or retry.
    return None


@dataclass
class ExtractedProtocol:
    procedure: list[str]
    specimen_laterality: list[str]
    tumor_site: list[str]
    specify_clock_position: list[str]
    histologic_type: list[str]
    architectural_pattern: list[str]
    nuclear_grade: list[str]
    necrosis: list[str]
    microcalcifications: list[str]
    additional_findings: str | None
    biomarker_studies: str | None


@dataclass
class ExtractedInvasiveProtocol:
    procedure: list[str]
    specimen_laterality: list[str]
    tumor_site: list[str]
    specify_clock_position: list[str]
    histologic_type: list[str]
    histologic_grade_applicability: list[str]
    glandular_tubular_differentiation: list[str]
    nuclear_pleomorphism: list[str]
    mitotic_rate: list[str]
    overall_grade: list[str]
    largest_invasive_focus_method: list[str]
    dcis_status: list[str]
    architectural_pattern: list[str]
    dcis_nuclear_grade: list[str]
    necrosis: list[str]
    lymphatic_vascular_invasion: list[str]
    microcalcifications: list[str]
    additional_findings_status: list[str]
    breast_biomarker_studies_status: list[str]
    additional_findings: list[str]
    biomarker_studies: list[str]


class BreastProtocolExtractor:
    """Agent-based extractor for CAP breast DCIS biopsy protocol."""

    field_options: dict[str, list[str]] = {}

    def extract(self, text: str) -> ExtractedProtocol:
        payload = _validate_agent_payload(extract_structured_report(text))
        if payload["protocol_type"] != "standard":
            raise ValueError("Agent classified report as invasive. Use the invasive extractor or extract_report().")

        fields = payload["fields"]
        return ExtractedProtocol(
            procedure=_list_field(fields, "procedure"),
            specimen_laterality=_list_field(fields, "specimen_laterality"),
            tumor_site=_list_field(fields, "tumor_site"),
            specify_clock_position=_list_field(fields, "specify_clock_position"),
            histologic_type=_list_field(fields, "histologic_type"),
            architectural_pattern=_list_field(fields, "architectural_pattern"),
            nuclear_grade=_list_field(fields, "nuclear_grade"),
            necrosis=_list_field(fields, "necrosis"),
            microcalcifications=_list_field(fields, "microcalcifications"),
            additional_findings=_string_or_none_field(fields, "additional_findings"),
            biomarker_studies=_string_or_none_field(fields, "biomarker_studies"),
        )


class BreastInvasiveProtocolExtractor:
    """Agent-based extractor for CAP invasive carcinoma of the breast biopsy protocol."""

    field_options: dict[str, list[str]] = {}

    def extract(self, text: str) -> ExtractedInvasiveProtocol:
        payload = _validate_agent_payload(extract_structured_report(text))
        if payload["protocol_type"] != "invasive":
            raise ValueError("Agent classified report as standard. Use the standard extractor or extract_report().")

        fields = payload["fields"]
        return ExtractedInvasiveProtocol(
            procedure=_list_field(fields, "procedure"),
            specimen_laterality=_list_field(fields, "specimen_laterality"),
            tumor_site=_list_field(fields, "tumor_site"),
            specify_clock_position=_list_field(fields, "specify_clock_position"),
            histologic_type=_list_field(fields, "histologic_type"),
            histologic_grade_applicability=_list_field(fields, "histologic_grade_applicability"),
            glandular_tubular_differentiation=_list_field(fields, "glandular_tubular_differentiation"),
            nuclear_pleomorphism=_list_field(fields, "nuclear_pleomorphism"),
            mitotic_rate=_list_field(fields, "mitotic_rate"),
            overall_grade=_list_field(fields, "overall_grade"),
            largest_invasive_focus_method=_list_field(fields, "largest_invasive_focus_method"),
            dcis_status=_list_field(fields, "dcis_status"),
            architectural_pattern=_list_field(fields, "architectural_pattern"),
            dcis_nuclear_grade=_list_field(fields, "dcis_nuclear_grade"),
            necrosis=_list_field(fields, "necrosis"),
            lymphatic_vascular_invasion=_list_field(fields, "lymphatic_vascular_invasion"),
            microcalcifications=_list_field(fields, "microcalcifications"),
            additional_findings_status=_list_field(fields, "additional_findings_status"),
            breast_biomarker_studies_status=_list_field(fields, "breast_biomarker_studies_status"),
            additional_findings=_list_field(fields, "additional_findings"),
            biomarker_studies=_list_field(fields, "biomarker_studies"),
        )


def extract_report(text: str) -> ExtractedProtocol | ExtractedInvasiveProtocol:
    payload = _validate_agent_payload(extract_structured_report(text))
    if payload["protocol_type"] == "invasive":
        extractor = BreastInvasiveProtocolExtractor()
    else:
        extractor = BreastProtocolExtractor()
    return extractor.extract(text)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Extract CAP-like breast protocol fields from plain text")
    parser.add_argument("input_file", help="Path to plain text report (for example r.document_plain_text export)")
    args = parser.parse_args()

    with open(args.input_file, "r", encoding="utf-8") as f:
        text = f.read()

    result = extract_report(text)
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
