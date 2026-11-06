# 数据出处、授权与校验

研究使用 BUS-BRA 和 BrEaST 的公开版本。仓库中的原始影像和掩膜从已校验的官方压缩包逐文件解压，保留目录结构和文件内容。[复现脚本](../reproducibility/README.md)的图像评分模式使用完整官方压缩包。

## BUS-BRA 1.0

[Zenodo 数据记录与原包下载](https://zenodo.org/records/8231412) · [解压目录](raw/BUS-BRA/BUSBRA) · [原授权声明](raw/BUS-BRA/BUSBRA/LICENSE.txt)。

数据使用和再分发须保留版权及许可声明并引用数据论文。Gómez-Flores W, Gregorio-Calas MJ, Pereira WCA. BUS-BRA: A breast ultrasound dataset for assessing computer-aided diagnosis systems. *Medical Physics*. [10.1002/mp.16812](https://doi.org/10.1002/mp.16812)。

## BrEaST Version 1

[TCIA 数据记录与原包下载](https://www.cancerimagingarchive.net/collection/breast-lesions-usg/) · [解压目录与原版工作簿](raw/BrEaST) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · [注册授权元数据](https://api.datacite.org/dois/10.7937/9WKK-Q141)。

Pawłowska, A., Ćwierz-Pieńkowska, A., Domalik, A., Jaguś, D., Kasprzak, P., Matkowski, R., Fura, Ł., Nowicki, A., & Zolek, N. (2024). A Curated Benchmark Dataset for Ultrasound Based Breast Lesion Analysis (Breast-Lesions-USG) (Version 1) [dataset]. The Cancer Imaging Archive. [10.7937/9WKK-Q141](https://doi.org/10.7937/9WKK-Q141)。

使用或再分发 BrEaST 时须保留上述数据引用、DOI 和[数据使用政策](https://www.cancerimagingarchive.net/data-usage-policies-and-restrictions/)的链接，并遵守其中关于参与者隐私的要求。[数据论文](https://doi.org/10.1038/s41597-024-02984-z)。

## 输入文件的 SHA-256

| 原始输入 | SHA-256 |
| --- | --- |
| BUSBRA.zip | ba3e6ed19cc37c682d8d39e25435bbf8a555a12cb7e641b5f2117685c95580ff |
| BrEaST-Lesions_USG-images_and_masks-Dec-15-2023.zip | c32e49cdfa54042e065582d0cb35978b5fc5e5b5e461b33bf773fb50cfdad355 |
| BrEaST-Lesions-USG-clinical-data-Dec-15-2023.xlsx | 89a8874496a6f1f93960390b963f7369b90f7e72ee08a738f2d17e37f5eff8bf |
| [SAM ViT-B 权重](https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth) | ec2df62732614e57411cdcf32a23ffdf28910380d03139ee0f4fcbe91eb8c912 |

[原始患者分组清单](manifests)保留实验开始时的清单和外部纳入记录。[复现清单](../reproducibility/manifests)锁定复跑的输入。[study_lock.json](../reproducibility/study_lock.json)另列了复现输入、模型版本和评分设置。
