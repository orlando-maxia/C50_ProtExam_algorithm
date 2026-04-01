"""Breast cancer protocol variable extraction.

This module extracts structured variables from OCR text generated from
CAP DCIS breast biopsy protocol documents.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
import re
from typing import Iterable

CHECKED_PATTERNS = [r"\[x\]", r"\[X\]", r"☒", r"☑", r"✅", r"\(x\)", r"\(X\)"]


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


class BreastProtocolExtractor:
    """Rule-based extractor for CAP breast DCIS biopsy protocol."""

    field_options: dict[str, list[str]] = {
        "procedure": [
            "Needle biopsy",
            "Fine needle aspiration",
            "Other",
            "Not specified",
        ],
        "specimen_laterality": ["Right", "Left", "Not specified"],
        "tumor_site": [
            "Upper outer quadrant",
            "Lower outer quadrant",
            "Upper inner quadrant",
            "Lower inner quadrant",
            "Central",
            "Nipple",
            "Clock position",
            "Other",
            "Not specified",
        ],
        "specify_clock_position": [f"{i} o'clock" for i in range(1, 13)],
        "histologic_type": [
            "Ductal carcinoma in situ (DCIS)",
            "Paget disease",
            "Encapsulated papillary carcinoma without invasive carcinoma",
            "Solid papillary carcinoma without invasive carcinoma",
        ],
        "architectural_pattern": [
            "Comedo",
            "Paget disease (DCIS involving nipple skin)",
            "Cribriform",
            "Micropapillary",
            "Papillary",
            "Solid",
            "Other",
        ],
        "nuclear_grade": [
            "Grade I (low)",
            "Grade II (intermediate)",
            "Grade III (high)",
            "Other",
            "Cannot be determined",
        ],
        "necrosis": [
            "Not identified",
            "Present, focal (small foci or single cell necrosis)",
            "Present, central (expansive \"comedo\" necrosis)",
            "Other",
            "Cannot be determined",
        ],
        "microcalcifications": [
            "Not identified",
            "Present in DCIS",
            "Present in non-neoplastic tissue",
            "Other",
        ],
    }

    def extract(self, text: str) -> ExtractedProtocol:
        normalized = self._normalize(text)

        return ExtractedProtocol(
            procedure=self._extract_multiselect(normalized, "procedure"),
            specimen_laterality=self._extract_multiselect(normalized, "specimen_laterality"),
            tumor_site=self._extract_multiselect(normalized, "tumor_site"),
            specify_clock_position=self._extract_multiselect(normalized, "specify_clock_position"),
            histologic_type=self._extract_multiselect(normalized, "histologic_type"),
            architectural_pattern=self._extract_multiselect(normalized, "architectural_pattern"),
            nuclear_grade=self._extract_multiselect(normalized, "nuclear_grade"),
            necrosis=self._extract_multiselect(normalized, "necrosis"),
            microcalcifications=self._extract_multiselect(normalized, "microcalcifications"),
            additional_findings=self._extract_free_text(normalized, "Additional Findings (specify)"),
            biomarker_studies=self._extract_free_text(normalized, "Breast Biomarker Studies (specify pending studies)"),
        )

    def _normalize(self, text: str) -> str:
        text = text.replace("\r\n", "\n")
        text = re.sub(r"[\u200b\xa0]", " ", text)
        return text

    def _extract_multiselect(self, text: str, field: str) -> list[str]:
        choices = self.field_options[field]
        selected: list[str] = []
        for choice in choices:
            if self._is_checked(text, choice):
                selected.append(choice)

        # fallback: if no explicit checkmarks found, detect unambiguous single-value fields
        if not selected and field in {"specimen_laterality", "nuclear_grade"}:
            selected = self._fallback_single_choice(text, choices)
        return selected

    def _is_checked(self, text: str, option: str) -> bool:
        opt = re.escape(option)
        checked = "|".join(CHECKED_PATTERNS)

        patterns = [
            rf"(?:{checked})\s*{opt}",
            rf"{opt}\s*(?:{checked})",
            rf"_{2,}\s*{opt}",  # OCR can convert checked box to line marks
        ]
        return any(re.search(pat, text, flags=re.IGNORECASE) for pat in patterns)

    def _fallback_single_choice(self, text: str, options: Iterable[str]) -> list[str]:
        present = [o for o in options if re.search(re.escape(o), text, flags=re.IGNORECASE)]
        return present if len(present) == 1 else []

    def _extract_free_text(self, text: str, label: str) -> str | None:
        pat = re.compile(rf"{re.escape(label)}\s*:\s*(.+)")
        m = pat.search(text)
        if not m:
            return None

        value = m.group(1).strip(" _\t")
        if not value:
            return None
        return value


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Extract fields from CAP breast protocol OCR text")
    parser.add_argument("input_file", help="Path to OCR text file")
    args = parser.parse_args()

    with open(args.input_file, "r", encoding="utf-8") as f:
        text = f.read()

    extractor = BreastProtocolExtractor()
    result = extractor.extract(text)
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
