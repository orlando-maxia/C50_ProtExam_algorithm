"""Breast histopathology variable extraction from plain-text reports.

Designed for real-world pathology narratives (for example `r.document_plain_text`
from a database), while still aligned to CAP DCIS biopsy variables.
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
    """Rule-based extractor for CAP breast DCIS biopsy protocol."""

    field_options: dict[str, list[str]] = {
        "procedure": [
            "Needle biopsy",
            "Fine needle aspiration",
            "Core needle biopsy (Tru-cut)",
            "Excisional biopsy",
            "Not specified",
        ],
        "specimen_laterality": ["Right", "Left", "Bilateral", "Not specified"],
        "tumor_site": [
            "Upper outer quadrant",
            "Lower outer quadrant",
            "Upper inner quadrant",
            "Lower inner quadrant",
            "Central",
            "Nipple",
            "Axillary tail",
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
            "Cannot be determined",
        ],
        "necrosis": [
            "Not identified",
            "Present, focal (small foci or single cell necrosis)",
            "Present, central (expansive \"comedo\" necrosis)",
            "Cannot be determined",
        ],
        "microcalcifications": [
            "Not identified",
            "Present in DCIS",
            "Present in non-neoplastic tissue",
        ],
    }

class BreastInvasiveProtocolExtractor:
    """Rule-based extractor for CAP invasive carcinoma of the breast biopsy protocol."""

    field_options: dict[str, list[str]] = {
        # ---------------------------------------------------------------------
        # 1. SPECIMEN
        # ---------------------------------------------------------------------
        "procedure": [
            "Needle biopsy",
            "Fine needle aspiration",
            "Other",
            "Not specified",
        ],
        "specimen_laterality": [
            "Right",
            "Left",
            "Not specified",
        ],
        # ---------------------------------------------------------------------
        # 2. TUMOR SITE
        # ---------------------------------------------------------------------
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
        # ---------------------------------------------------------------------
        # 3. HISTOLOGIC TYPE
        # Based on the main checklist page plus the explanatory pages
        # ---------------------------------------------------------------------
        "histologic_type": [
            "No residual invasive carcinoma",
            "Invasive carcinoma of no special type (ductal)",
            "Micro-invasive carcinoma",
            "Invasive lobular carcinoma",
            "Invasive carcinoma with mixed ductal and lobular features",
            "Invasive carcinoma with mixed features",
            "Invasive carcinoma with features of",
            "Tubular carcinoma",
            "Invasive cribriform carcinoma",
            "Mucinous carcinoma",
            "Invasive micropapillary carcinoma",
            "Apocrine adenocarcinoma",
            # Metaplastic carcinoma
            "Metaplastic carcinoma",
            "Metaplastic carcinoma NOS",
            "Low grade adenosquamous carcinoma",
            "Fibromatosis-like metaplastic carcinoma",
            "Spindle cell carcinoma",
            "Squamous cell carcinoma",
            "Metaplastic carcinoma with mesenchymal differentiation",
            # Papillary / special papillary types
            "Encapsulated papillary carcinoma with invasion",
            "Solid papillary carcinoma with invasion",
            "Intraductal papillary adenocarcinoma with invasion",
            "Invasive papillary carcinoma",
            # Adenoid cystic and special salivary-gland-like types
            "Adenoid cystic carcinoma",
            "Classic adenoid cystic carcinoma",
            "Solid-basaloid adenoid cystic carcinoma",
            "Adenoid cystic carcinoma with high-grade transformation",
            "Secretory carcinoma",
            "Mucoepidermoid carcinoma",
            "Polymorphous adenocarcinoma",
            "Tall cell carcinoma with reversed polarity",
            "Adenomyoepithelioma with carcinoma",
            "Epithelial-myoepithelial carcinoma",
            # Neuroendocrine
            "Neuroendocrine tumor",
            "Neuroendocrine tumor NOS",
            "Neuroendocrine tumor, grade 1",
            "Neuroendocrine tumor, grade 2",
            "Neuroendocrine carcinoma",
            "Neuroendocrine carcinoma NOS",
            "Neuroendocrine carcinoma, small cell",
            "Neuroendocrine carcinoma, large cell",
            # Other rare histologies
            "Oncocytic carcinoma",
            "Lipid-rich carcinoma",
            "Glycogen-rich carcinoma",
            "Sebaceous carcinoma",
            "Mucinous cystadenocarcinoma NOS",
            "Acinar cell carcinoma",
            # Fallback / unspecified
            "Invasive carcinoma, type cannot be determined",
            "Other histologic type not listed",
        ],
        # ---------------------------------------------------------------------
        # 4. HISTOLOGIC GRADE (Nottingham Histologic Score)
        # ---------------------------------------------------------------------
        "histologic_grade_applicability": [
            "Not applicable (no residual carcinoma or microinvasion only)",
            "Nottingham Score",
        ],
        "glandular_tubular_differentiation": [
            "Score 1 (greater than 75% of tumor area forming glandular / tubular structures)",
            "Score 2 (10% to 75% of tumor area forming glandular / tubular structures)",
            "Score 3 (less than 10% of tumor area forming glandular / tubular structures)",
            "Score cannot be determined",
        ],
        "nuclear_pleomorphism": [
            "Score 1 (Nuclei small with little increase in size in comparison with normal breast epithelial cells, regular outlines, uniform nuclear chromatin, little variation in size)",
            "Score 2 (Cells larger than normal with open vesicular nuclei, visible nucleoli, and moderate variability in both size and shape)",
            "Score 3 (Vesicular nuclei, often with prominent nucleoli, exhibiting marked variation in size and shape, occasionally with very large and bizarre forms)",
            "Score cannot be determined",
        ],
        "mitotic_rate": [
            "Score 1",
            "Score 2",
            "Score 3",
            "Score cannot be determined",
        ],
        "overall_grade": [
            "Grade 1 (scores of 3, 4 or 5)",
            "Grade 2 (scores of 6 or 7)",
            "Grade 3 (scores of 8 or 9)",
            "Score cannot be determined",
        ],
        # ---------------------------------------------------------------------
        # 5. LARGEST INVASIVE FOCUS IN THIS LIMITED BIOPSY SAMPLE
        # ---------------------------------------------------------------------
        "largest_invasive_focus_method": [
            "Exact measurement in Millimeters (mm)",
            "At least in Millimeters (mm)",
            "Cannot be determined",
        ],
        # ---------------------------------------------------------------------
        # 6. DUCTAL CARCINOMA IN SITU (DCIS)
        # ---------------------------------------------------------------------
        "dcis_status": [
            "Not identified",
            "Present",
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
        "dcis_nuclear_grade": [
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
            "Cannot be excluded",
        ],
        # ---------------------------------------------------------------------
        # 7. LYMPHATIC / VASCULAR INVASION
        # ---------------------------------------------------------------------
        "lymphatic_vascular_invasion": [
            "Not identified",
            "Present",
            "Cannot be determined",
        ],
        # ---------------------------------------------------------------------
        # 8. MICROCALCIFICATIONS
        # ---------------------------------------------------------------------
        "microcalcifications": [
            "Not identified",
            "Present in DCIS",
            "Present in invasive carcinoma",
            "Present in non-neoplastic tissue",
            "Other",
        ],
        # ---------------------------------------------------------------------
        # 9. ADDITIONAL FINDINGS / SPECIAL STUDIES / COMMENTS
        # ---------------------------------------------------------------------
        "additional_findings_status": [
            "Present",
            "Not identified",
        ],
        "breast_biomarker_studies_status": [
            "Pending",
            "Performed",
            "Not performed",
            "Unknown",
        ],
    }
    # -------------------------------------------------------------------------
    # Free-text / specify fields
    # -------------------------------------------------------------------------
    free_text_fields: list[str] = [
        "procedure_other",
        "tumor_site_other",
        "distance_from_nipple_cm",
        "histologic_type_features_specify",
        "histologic_type_other",
        "histologic_type_comment",
        "largest_invasive_focus_exact_mm",
        "largest_invasive_focus_at_least_mm",
        "largest_invasive_focus_cannot_determine_explain",
        "architectural_pattern_other",
        "dcis_nuclear_grade_other",
        "necrosis_other",
        "microcalcifications_other",
        "additional_findings_specify",
        "breast_biomarker_studies_specify_pending",
        "comments",
    ]

    # Narrative-text mappings (Spanish + English) -> CAP values.
    narrative_patterns: dict[str, list[tuple[str, str]]] = {
        "procedure": [
            (r"\btru[\s\-]?cut\b|biopsia con aguja gruesa|core\s+needle\s+biopsy", "Core needle biopsy (Tru-cut)"),
            (r"\bneedle\s+biopsy\b|biopsia\s+con\s+aguja", "Needle biopsy"),
            (r"\bfine\s+needle\s+aspiration\b|aspiraci[oó]n\s+con\s+aguja\s+fina", "Fine needle aspiration"),
            (r"\bexcisional\s+biopsy\b|biopsia\s+escisional", "Excisional biopsy"),
        ],
        "specimen_laterality": [
            (r"\bmama\s+derecha\b|\bderecha\b|\bright\b", "Right"),
            (r"\bmama\s+izquierda\b|\bizquierda\b|\bleft\b", "Left"),
            (r"\bbilateral\b|ambas\s+mamas", "Bilateral"),
        ],
        "tumor_site": [
            (r"cola\s+axilar|\bcola\b|axillary\s+tail", "Axillary tail"),
            (r"upper\s+outer\s+quadrant|cuadrante\s+supero\s*externo", "Upper outer quadrant"),
            (r"lower\s+outer\s+quadrant|cuadrante\s+infero\s*externo", "Lower outer quadrant"),
            (r"upper\s+inner\s+quadrant|cuadrante\s+supero\s*interno", "Upper inner quadrant"),
            (r"lower\s+inner\s+quadrant|cuadrante\s+infero\s*interno", "Lower inner quadrant"),
            (r"\bpez[oó]n\b|\bnipple\b", "Nipple"),
            (r"\bcentral\b", "Central"),
            (r"\br\s*([1-9]|1[0-2])[a-z]?\b|([1-9]|1[0-2])\s*o'?clock", "Clock position"),
        ],
        "histologic_type": [
            (r"ductal\s+carcinoma\s+in\s+situ|\bdcis\b|carcinoma\s+ductal\s+in\s+situ", "Ductal carcinoma in situ (DCIS)"),
            (r"paget", "Paget disease"),
            (r"encapsulated\s+papillary", "Encapsulated papillary carcinoma without invasive carcinoma"),
            (r"solid\s+papillary", "Solid papillary carcinoma without invasive carcinoma"),
        ],
        "architectural_pattern": [
            (r"comedo", "Comedo"),
            (r"cribriform", "Cribriform"),
            (r"micropapillary|micropapilar", "Micropapillary"),
            (r"papillary|papilar", "Papillary"),
            (r"\bsolid\b|s[oó]lido", "Solid"),
        ],
        "nuclear_grade": [
            (r"grade\s*i\b|grado\s*i\b|bajo", "Grade I (low)"),
            (r"grade\s*ii\b|grado\s*ii\b|intermedio", "Grade II (intermediate)"),
            (r"grade\s*iii\b|grado\s*iii\b|alto", "Grade III (high)"),
        ],
        "necrosis": [
            (r"no\s+necrosis|sin\s+necrosis", "Not identified"),
            (r"focal\s+necrosis|necrosis\s+focal", "Present, focal (small foci or single cell necrosis)"),
            (r"comedo\s+necrosis|necrosis\s+tipo\s+comedo|central\s+necrosis", "Present, central (expansive \"comedo\" necrosis)"),
        ],
        "microcalcifications": [
            (r"microcalcifications?\s+not\s+identified|sin\s+microcalcificaciones", "Not identified"),
            (r"microcalcifications?.*dcis|microcalcificaciones?.*dcis", "Present in DCIS"),
            (r"microcalcifications?.*non\-?neoplastic|microcalcificaciones?.*tejido\s+no\s+neopl[aá]sico", "Present in non-neoplastic tissue"),
        ],
    }

    additional_findings_patterns = [
        r"fibroadenoma",
        r"metaplasia\s+apocrina",
        r"cambios\s+fibroqu[ií]sticos",
        r"sclerosing\s+adenosis|adenosis\s+esclerosante",
    ]

    biomarker_patterns = [
        r"\bER\b", r"\bPR\b", r"HER2", r"Ki\-?67", r"biomarcadores?", r"receptores?\s+hormonales?"
    ]

    def extract(self, text: str) -> ExtractedInvasiveProtocol:
        normalized = self._normalize(text)
        has_checkboxes = self._has_checkbox_marks(normalized)

        procedure = self._extract_field(normalized, "procedure", has_checkboxes)
        specimen_laterality = self._extract_field(normalized, "specimen_laterality", has_checkboxes)
        tumor_site = self._extract_field(normalized, "tumor_site", has_checkboxes)
        specify_clock_position = self._extract_clock_positions(normalized)

        if specify_clock_position and "Clock position" not in tumor_site:
            tumor_site.append("Clock position")

        return ExtractedInvasiveProtocol(
            procedure=procedure or ["Not specified"],
            specimen_laterality=specimen_laterality or ["Not specified"],
            tumor_site=tumor_site or ["Not specified"],
            specify_clock_position=specify_clock_position,            histologic_type=self._extract_field(normalized, "histologic_type", has_checkboxes),
            histologic_grade_applicability=self._extract_field(normalized, "histologic_grade_applicability", has_checkboxes),
            glandular_tubular_differentiation=self._extract_field(normalized, "glandular_tubular_differentiation", has_checkboxes),
            nuclear_pleomorphism=self._extract_field(normalized, "nuclear_pleomorphism", has_checkboxes),
            mitotic_rate=self._extract_field(normalized, "mitotic_rate", has_checkboxes),
            overall_grade=self._extract_field(normalized, "overall_grade", has_checkboxes),
            largest_invasive_focus_method=self._extract_field(normalized, "largest_invasive_focus_method", has_checkboxes),
            dcis_status=self._extract_field(normalized, "dcis_status", has_checkboxes),
            architectural_pattern=self._extract_field(normalized, "architectural_pattern", has_checkboxes),
            dcis_nuclear_grade=self._extract_field(normalized, "dcis_nuclear_grade", has_checkboxes),
            necrosis=self._extract_field(normalized, "necrosis", has_checkboxes),
            lymphatic_vascular_invasion=self._extract_field(normalized, "lymphatic_vascular_invasion", has_checkboxes),
            microcalcifications=self._extract_field(normalized, "microcalcifications", has_checkboxes),
            additional_findings_status=self._extract_field(normalized, "additional_findings_status", has_checkboxes),
            breast_biomarker_studies_status=self._extract_field(normalized, "breast_biomarker_studies_status", has_checkboxes),
            additional_findings=self._extract_additional_findings(normalized),
            biomarker_studies=self._extract_biomarker_mentions(normalized),
        )

    def _normalize(self, text: str) -> str:
        text = text.replace("\r\n", "\n")
        text = re.sub(r"[\u200b\xa0]", " ", text)
        return text.lower()

    def _extract_field(self, text: str, field: str, has_checkboxes: bool) -> list[str]:
        selected: list[str] = []

        # 1) Form-like checkmark extraction when present
        for choice in self.field_options[field]:
            if self._is_checked(text, choice):
                selected.append(choice)

        # 2) Narrative matching for plain text reports
        # If checkbox marks are present, avoid narrative fallback because option text
        # lines often include unselected values and can cause false positives.
        if not has_checkboxes:
            for pattern, canonical in self.narrative_patterns.get(field, []):
                if re.search(pattern, text, flags=re.IGNORECASE) and canonical not in selected:
                    selected.append(canonical)

        return selected

    def _is_checked(self, text: str, option: str) -> bool:
        checked = r"(?:\[x\]|\[X\]|☒|☑|✅|\(x\)|\(X\))"
        opt = re.escape(option.lower())
        return bool(re.search(rf"{checked}\s*{opt}|{opt}\s*{checked}", text, flags=re.IGNORECASE))

    def _has_checkbox_marks(self, text: str) -> bool:
        return bool(re.search(r"\[x\]|\[X\]|☒|☑|✅|\(x\)|\(X\)", text))

    def _extract_clock_positions(self, text: str) -> list[str]:
        out: list[str] = []
        numbers = re.findall(r"\br\s*([1-9]|1[0-2])[a-z]?\b|\b([1-9]|1[0-2])\s*o'?clock\b", text, flags=re.IGNORECASE)
        for g1, g2 in numbers:
            num = g1 or g2
            value = f"{int(num)} o'clock"
            if value not in out:
                out.append(value)
        return out

    def _extract_additional_findings(self, text: str) -> list[str]:
        findings: list[str] = []
        for pat in self.additional_findings_patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                findings.append(m.group(0))
        return findings

    def _extract_biomarker_mentions(self, text: str) -> list[str]:
        biomarkers: list[str] = []
        for pat in self.biomarker_patterns:
            if re.search(pat, text, flags=re.IGNORECASE):
                label = pat.replace("\\b", "")
                biomarkers.append(label)
        return biomarkers


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Extract CAP-like breast protocol fields from plain text")
    parser.add_argument("input_file", help="Path to plain text report (for example r.document_plain_text export)")
    args = parser.parse_args()

    with open(args.input_file, "r", encoding="utf-8") as f:
        text = f.read()

    extractor = BreastProtocolExtractor()
    result = extractor.extract(text)
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

