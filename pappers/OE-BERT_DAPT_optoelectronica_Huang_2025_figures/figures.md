# Figuras extraídas

**Fuente:** `/media/santi/ALMACEN_GRANDE_1/ilovepappers/pappers/OE-BERT_DAPT_optoelectronica_Huang_2025.pdf`
**Total figuras:** 19

---

## FIG_001 · Picture · Página 1

![fig_001](images/fig_001_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_002 · Picture · Página 1

![fig_002](images/fig_002_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_003 · Picture · Página 1

![fig_003](images/fig_003_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_004 · Picture · Página 1

![fig_004](images/fig_004_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_005 · Picture · Página 1

![fig_005](images/fig_005_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_006 · Picture · Página 1

![fig_006](images/fig_006_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_007 · Picture · Página 1

![fig_007](images/fig_007_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_008 · Picture · Página 1

![fig_008](images/fig_008_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_009 · Picture · Página 1

![fig_009](images/fig_009_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_010 · Picture · Página 1

![fig_010](images/fig_010_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_011 · Picture · Página 2

![fig_011](images/fig_011_Figure_1_Applications_of_BERT-like_mode.png)

**Caption:** Figure 1. Applications of BERT-like models in academic research. Left. BERT-like models are built with the transformer architecture, which computes the attention between text tokens. The attention scores can be exploited to conduct dependency parsing and relation discovery. The models can also be fine-tuned to tackle specialized downstream tasks. Top. The question-answering (QA) capability of BERT-like models can be applied to tasks such as text-mining for material databases and topic modeling for research trend analysis. Right. The models can also be fine-tuned to perform text classification, which has wide application in literature review and bibliography management. Bottom. BERT-like models can be modified to produce contextual text embeddings that can be used in document retrieval based on the embedding similarities. The advancement in LLMs and RAG systems have also promoted the application of embedding models.

---

## FIG_012 · Picture · Página 2

![fig_012](images/fig_012_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_013 · Picture · Página 2

![fig_013](images/fig_013_Figure_2_Training_pipeline_for_the_opto.png)

**Caption:** Figure 2. Training pipeline for the optoelectronics-adapted language models developed in this study. The starting BERT-like models, pretrained on general English text (ALBERT, BERT, and RoBERTa) were domain adaptive pretrained on optoelectronics research literature, yielding the OEadapted models. Each resulting OE model was then fine-tuned on three downstream tasks: abstract classification, question-answering, and textembedding, using task-specific training data sets. The resulting nine models represent the final utility models; such as the OE-RoBERTa model that serves for QA or the OE-ALBERT model that serves for abstract classification.

---

## FIG_014 · Picture · Página 4

![fig_014](images/fig_014_Figure_3_Keyword_frequency_bar_chart_fo.png)

**Caption:** Figure 3. Keyword frequency bar chart for normalized keywords found in 20k Science Direct publications about optoelectronics These 20 normalized keywords outlined three major mutually exclusive categories in terms of material functions: light-emitting, lightharvesting, and photocatalysis categories.

---

## FIG_015 · Picture · Página 5

![fig_015](images/fig_015_no_caption.png)

**Caption:** _Sin caption_

---

## FIG_016 · Picture · Página 5

![fig_016](images/fig_016_Figure_4_Pretraining_loss_and_token_pre.png)

**Caption:** Figure 4. Pretraining loss and token prediction accuracy progress of BERT, ALBERT, and RoBERTa when further pretrained on optoelectronics literature in order to produce OE-BERT, OEALBERT and OE-RoBERTa, respectively. All three language models achieved a similar masked token prediction accuracy at the end of the DAPT process, while their progress of loss values are more separated with the OE-RoBERTa model affording the lowest loss value.

---

## FIG_017 · Picture · Página 7

![fig_017](images/fig_017_Figure_5_Confusion_matrix_of_the_classi.png)

**Caption:** Figure 5. Confusion matrix of the classification results on titles concatenated with abstracts from top cited optoelectronics papers in 2023, using the OE-RoBERTa case-lowered classification model. Most confusions occur between the 'light-harvesting' class and the 'other topics' class.

---

## FIG_018 · Picture · Página 8

![fig_018](images/fig_018_Figure_6_Performance_evolution_on_the_T.png)

**Caption:** Figure 6. Performance evolution on the TADF-numerical QA data set of the OE-BERT and OE-RoBERTa models against the progress of their optoelectronics DAPT process as defined by the number of epochs of the DAPT process. a) The progressive evolution of the Exact Match metric. b) The progressive evolution of the F 1 metric. The metric scores of OE-BERT and OE-RoBERTa evolves highly parallel for both Exact Match and F 1 .

---

## FIG_019 · Picture · Página 10

![fig_019](images/fig_019_Figure_7_Recall_k_results_plotted_agai.png)

**Caption:** Figure 7. Recall @k results plotted against k for 1 ≤ k ≤ 20 when testing on the test set of the OE-Ttl-Abs-303k data set using the gte-base-en-v1.5 model, the OE-RoBERTa embedding model (all layers fine-tuned), and the OE-RoBERTa embedding model (pooling layers fine-tuned). The OE-RoBERTa embedding model that had all its layers fine-tuned outperformed the state-of-theart embedding model that is of a similar size, gte-base-env1.5 , on this optoelectronics in-domain retrieval task.
