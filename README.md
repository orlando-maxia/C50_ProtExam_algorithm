# Breast DCIS Protocol Variable Extraction

This repository contains a first version of a **rule-based extraction algorithm** for CAP breast protocol examinations (DCIS biopsy template), focused on these variables:

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

## Approach (V1)

1. Convert the source document (Word/PDF/JPG scans) to OCR text.
2. Run `breast_protocol_extractor.py` against that text.
3. Detect selected options using checkmark patterns (`[x]`, `☒`, etc.) and option dictionaries.
4. Return structured JSON.

## Usage

```bash
python breast_protocol_extractor.py path/to/ocr_output.txt
```

## Notes

- This is a baseline algorithm to start iteration.
- OCR quality strongly impacts extraction quality.
- Next iteration can include:
  - layout-aware parsing (line positions / bounding boxes)
  - typo-tolerant matching (fuzzy matching)
  - confidence scores per extracted variable
