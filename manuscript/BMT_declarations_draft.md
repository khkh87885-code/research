# BME–BMT ethical and legal declarations

**作者审阅稿。** 方括号是需要作者确认的内容。定稿时把确认后的声明填入期刊的独立 Word 表单。数据和代码的分享渠道也要与实际安排相符。 [期刊投稿指南](https://www.degruyterbrill.com/publication/journal_key/BMTE/downloadAsset/BMTE_Instructions%20for%20Authors.pdf) · [官方声明表单](https://www.degruyterbrill.com/publication/journal_key/BMTE/downloadAsset/BMTE_Template%20for%20Ethical%20and%20Legal%20Declarations.docx) · [数据共享政策 Tier 2](https://degruyter-live-craftcms-assets.s3.amazonaws.com/Policy-2_20240625.pdf)

## Research ethics

This retrospective study consisted of secondary analysis of anonymized breast ultrasound images and manual lesion masks from two publicly released datasets.

[Insert the institutional determination for this secondary analysis, including the responsible body and reference number or date where applicable.]

**作者核对。** BrEaST 原论文记载的数据采集伦理批准编号是 2/BNR/2022。该编号对应 BrEaST 原研究。本稿的伦理声明应依据作者所在机构对二次分析的实际认定。 [BrEaST 原论文](https://doi.org/10.1038/s41597-024-02984-z)

## Informed consent

[Insert the confirmed applicability of informed consent for the present secondary analysis and the documented basis for that determination.]

**作者核对。** BrEaST 原论文报告原研究免于获取书面知情同意。此处填写本研究适用的结论。 [BrEaST 原论文](https://doi.org/10.1038/s41597-024-02984-z)

## Data availability

This study used the publicly released BUS-BRA dataset (version 1.0, DOI 10.5281/zenodo.8231412) and the BrEaST dataset (version 1, DOI 10.7937/9WKK-Q141). The original ultrasound images and reference masks are available through the respective dataset records. [BUS-BRA at Zenodo](https://doi.org/10.5281/zenodo.8231412) · [BrEaST at TCIA](https://doi.org/10.7937/9WKK-Q141)

The study-specific case manifests and derived case-level scores have been assembled in a reproducibility package for review. [Insert the confirmed access route for these materials and any applicable conditions.]

## Code availability

The scripts for generating the case-level SAM scores and reproducing the statistical analyses are included in the study's reproducibility package. [Insert the verified repository record or the agreed access route.]

**作者核对。** 原数据 DOI 已核对。衍生逐例评分和代码目前为本地审阅包，公开许可与分享渠道待确认。

## Use of large language models, AI and machine learning tools

OpenAI Codex assisted with research code and figure preparation and with drafting and editing manuscript materials. [Confirm this description and document the authors' review and approval of the submitted material.]

**Methods 中的模型用途。** We used the pretrained Segment Anything Model with the ViT-B backbone to generate one initial and four perturbed lesion masks per image. The reproducibility package records the source commit and checkpoint hash. [Official SAM source](https://github.com/facebookresearch/segment-anything/tree/dca509fe793f601edb92606367a655c15ac00fdf)

## Author contributions

[Insert each author's name and confirmed contributions. Confirm author order, corresponding author, approval of the final version and accountability with all authors.]

## Conflict of interest

[Insert the confirmed disclosure for all authors, using the journal's default wording if applicable.]

## Research funding

[Insert the funder and award number for each source of support, or the journal's default wording if applicable.]

## Acknowledgments

[Confirm any individuals or groups whose contributions should be acknowledged. Cite the original BUS-BRA and BrEaST articles in the manuscript.] [BUS-BRA paper](https://doi.org/10.1002/mp.16812) · [BrEaST paper](https://doi.org/10.1038/s41597-024-02984-z)

## Trial registration

This study was a retrospective secondary analysis of public datasets. [Confirm the appropriate entry in the journal form.]

