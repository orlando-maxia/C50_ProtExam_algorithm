# Breast Histopathology Structuring Algorithm (Plain Text First)

This project now focuses on **plain text pathology reports** (for example the `r.document_plain_text` field from your database), not only OCR from forms/images.

## Goal

Structure free-text breast histopathology reports into CAP-aligned variables:

- Procedure
- Specimen laterality
- Tumor site
- Specify clock position
- Histologic type
- Architectural pattern
- Nuclear grade
- Necrosis
- Microcalcifications
- Additional findings
- Biomarker studies

## How it works

`breast_protocol_extractor.py` uses hybrid rules:

1. **Form-like extraction** if checkboxes are present.
2. **Narrative extraction** for plain clinical text (Spanish + English pattern matching).
3. **Normalization to canonical CAP-like values**.
4. **Graceful defaults** when a variable is absent in the report (`Not specified`, `Cannot be determined`).

## Example use case

Input text can be a paragraph like:

- `Paciente femenina ... BIOPSIA CON AGUJA GRUESA (TRU-CUT) ... MAMA DERECHA ... R 9A ... LESION FIBROEPITELIAL COMPATIBLE CON FIBROADENOMA ...`

Output JSON returns structured fields and preserves missing variables as explicit defaults.

## Usage

```bash
python breast_protocol_extractor.py path/to/report_plain_text.txt
```

## Current limitations

- Rule-based patterns can miss uncommon phrasing.
- Complex negations may require NLP-level parsing.
- Biomarker extraction currently detects mentions, not final quantitative values.
