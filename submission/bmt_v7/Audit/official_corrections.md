# BMT official requirement corrections — v7

Verified directly from official files on **6 November 2026 (UTC)**. This report corrects the previous audit; the user's comments were treated as leads and independently checked.

## Source and verification

Official instructions: https://www.degruyterbrill.com/publication/journal_key/BMTE/downloadAsset/BMTE_Instructions%20for%20Authors.pdf

The official browser response was HTTP 200, `application/pdf`, **849,140 bytes**, **11 pages**. SHA-256 computed from the fetched PDF: `5a11215a9b3ae9af62b10667e35b15cba20cb286102347c628ec0b1a304d52dc`. A PDF library extracted pages 1, 4, and 10; page-numbered source text is preserved in [official_pdf_pages_1_4_10.json](official_pdf_pages_1_4_10.json) and [official_pdf_pages_1_4_10.txt](official_pdf_pages_1_4_10.txt). The original PDF binary is not saved locally. Quotes below normalize layout line breaks/hyphenation only; the JSON also preserves the verbatim extracted forms.

## 1. The instructions are explicitly labelled December 2024

**PDF page 1:**

> Instructions for Authors   (last update: December 2024)

**Corrected audit status: verified.** The prior “date unverified” classification is withdrawn. The current official download returns this labelled version; this statement does not establish the absence of another version elsewhere.

## 2. At least five potential reviewers are mandatory

**PDF page 4, “Rejection of manuscripts and peer review information”:**

> BME–BMT is a single-blind peer-reviewed journal. Manuscripts which fulfill the substantive and formal criteria are reviewed anonymously by at least two independent reviewers selected by the Editors. The authors must provide the names, institution, country and e-mail addresses of at least five potential reviewers. Reviewers indicated by the authors must be of institutions different from those of any of the authors and should be of different nationality. Authors may also provide names of reviewers they wish to exclude from reviewing their manuscripts.

**Corrected audit status: official mandatory requirement.** The prior claim that the five-candidate requirement was not found or was only requested by the user was incorrect and is withdrawn. This clause was also present in the earlier scraped source and was overlooked.

For each of **at least five** candidates, provide the name, institution, country, and email. Their institutions **must** differ from those of every author. The PDF says they **should** be of different nationality; do not elevate “should” into a mandatory country-count rule. The Editors' selection of at least two independent reviewers is a separate rule.

## 3. Percentages require the specified U+202F character

**PDF page 10, “Units”:**

> A narrow non-breaking space (unicode hex value: U+202F) should be presented between numbers and units, except for °. °C and % should be spaced with a narrow non-breaking space.

**Corrected audit status: verified.** Use the narrow no-break space **U+202F** (UTF-8 `E2 80 AF`) between a number and `%`; for example, `95 %`. The same sentence explicitly includes `°C` (`37 °C`) and exempts a degree sign alone (`45°`). Ordinary ASCII spaces and U+00A0 are not the character specified by this rule.

## 4. Original official declarations DOCX acquired

Official URL: https://www.degruyterbrill.com/publication/journal_key/BMTE/downloadAsset/BMTE_Template%20for%20Ethical%20and%20Legal%20Declarations.docx

Saved original response bytes at [official_declarations_template.docx](../originals/official_declarations_template.docx), **27,927 bytes**.

SHA-256: `8facc5b46d8dc245e1814a9f749e2ddc4d84e2189b20ea9f511886c38d9ef230`.

Acquisition used the regular Firecrawl live browser's network access. The complete machine-printed base64 was decoded locally; the original file was not regenerated. Local SHA-256 matches the browser hash. ZIP validation passed, and `word/document.xml` exists. This replaces the prior “original binary unavailable; text transcription only” status.

The original Word table contains these **eight named fields**, verified directly from `word/document.xml`:

| Order | Official field text |
|---|---|
| 1 | Acknowledgments |
| 2 | Research ethics |
| 3 | Informed consent |
| 4 | Author contributions (for double- anonymized journals: please use initials) |
| 5 | Use of Large Language Models, AI and Machine Learning Tools |
| 6 | Conflict of interest |
| 7 | Research funding |
| 8 | Data availability |

There are also the STATEMENT/TEXT header and two blank extension rows; they are not additional named fields. Text extracted from the original binary is saved in [official_declarations_original_extracted.txt](official_declarations_original_extracted.txt).

The official template is now available for author review and completion. The download does not establish research-ethics exemption, informed-consent status, final author approval, or verification of reviewer candidates.

