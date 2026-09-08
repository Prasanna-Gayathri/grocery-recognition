# SafeScan

**An LLM-Driven Multimodal Approach to Fine-Grained Product Recognition with Allergen Detection**

SafeScan scans a grocery product's front and back cover images to classify the product, detect allergen conflicts against a user's allergy profile, and generate a nutrition health score — combining a trained multimodal classifier with LLM reasoning and retrieval-grounded verification.


**Base paper:** Pettersson, Riveiro & Löfström (2024), *Machine Vision and Applications*, [doi:10.1007/s00138-024-01549-9](https://doi.org/10.1007/s00138-024-01549-9)

---

## Overview

A customer photographs the **front** and **back** of a packaged grocery product. SafeScan:

1. Classifies the product category from the front image (image + OCR text fusion)
2. Reads the back image's ingredient/nutrition panel via OCR
3. Cross-checks ingredients against the user's declared allergens, grounded against verified reference data
4. Scores the product's nutrition using a published, deterministic algorithm — not just an LLM guess

This extends the base paper (which stops at classification) by adding LLM-based allergen detection and nutrition scoring, plus statistical confidence calibration and retrieval-augmented grounding as novelty contributions.

---

## Architecture

```
Front image ──► OCR (EasyOCR) ──┐
                                 ├──► Fusion (2048-d ResNet50 + 500-d TF-IDF)
                Front image ─────┘         │
                                            ▼
                                  Classifier (Dense NN)
                                            │
                              ┌─────────────┼─────────────┐
                              ▼                            ▼
                     Category + Confidence      Confidence Calibration
                                                (Mondrian Conformal Prediction)

Back image ──► OCR (EasyOCR) ──┬──► Allergen Check (Gemini, RAG-grounded
                                │    against Open Food Facts)
                                │
                                └──► Nutrition Scoring
                                     ├── Gemini freeform read (qualitative)
                                     └── Nutri-Score (Santé publique France
                                         published algorithm — deterministic)
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Image classifier | ResNet50 (frozen, ImageNet weights) + TF-IDF, fused, trained on TensorFlow/Keras |
| OCR | EasyOCR |
| LLM reasoning | Google Gemini API (`google-genai` SDK), free tier (`gemini-flash-latest`) |
| Retrieval grounding | Open Food Facts public API |
| Nutrition scoring | Nutri-Score algorithm (Santé publique France, 2017, general foods category) |
| Confidence calibration | Mondrian Conformal Prediction |
| Environment | Google Colab (GPU runtime) |

---

## Dataset

IIT Patna Grocery_Items dataset (Roboflow), ~76k annotations collapsed into **21 product categories**, capped at 800 images/class → ~11,900 images used for training.

**Classifier result:** 88.74% test accuracy.

---

## Repository Structure

```
├── SafeScan_Step1_IITPatna.ipynb              # Data prep: crop, OCR extraction, category collapse
├── SafeScan_Step2_IITPatna_Training.ipynb     # Feature fusion + classifier training
├── SafeScan_Notebook3_LLM_Layer.ipynb         # Front/back inference pipeline + Gemini allergen/nutrition
├── SafeScan_Notebook4_Novelty_Additions.ipynb # Calibration + RAG grounding + Nutri-Score
└── README.md
```

### Notebook summaries

**Step 1 — Data Preparation**
Crops raw dataset images, runs OCR to extract label text, collapses ~4,400 raw classes into 21 usable categories.

**Step 2 — Classifier Training**
Extracts ResNet50 image embeddings (2048-d) and TF-IDF text embeddings (500-d), concatenates into a single 2548-d fused vector, trains a dense classifier. Saves `safescan_classifier.h5` and `preprocessors.pkl`.

**Notebook 3 — LLM Layer (baseline pipeline)**
Loads the trained classifier. Takes a front image (classification) and back image (OCR → Gemini) per scan. Runs allergen detection and nutrition scoring via Gemini, with exponential-backoff retry handling for free-tier API instability.

**Notebook 4 — Novelty Additions**
Builds on Notebook 3 without modifying it:
- **Confidence Calibration** — Mondrian conformal prediction gives statistically-grounded confidence sets instead of raw softmax scores.
- **RAG Grounding** — retrieves verified ingredient/allergen data from Open Food Facts before the LLM reasons about allergen conflicts, rather than trusting the LLM's own knowledge alone.
- **Standardized Nutrition Scoring** — splits the task: Gemini extracts raw nutrient numbers from noisy OCR text (a task LLMs are good at), and a deterministic, published Nutri-Score formula computes the actual grade (removing LLM judgment from the final score).
- **Graceful degradation** — if the Gemini API is temporarily unavailable, the report still returns whatever can be computed without it (category, OCR text, retrieved reference data) instead of failing outright.

---

## Setup

1. Open the notebooks in Google Colab with a GPU runtime.
2. Model and preprocessor files are hosted on Google Drive and pulled via `gdown` (Drive mount is unreliable in Colab and is intentionally not used). Update the file IDs in the download cells if you re-host the files.
3. You'll need a free [Gemini API key](https://aistudio.google.com/apikey), entered via a hidden prompt at runtime — never hardcoded in the notebook.
4. Run cells top to bottom. Each notebook's install cell installs only the packages Colab doesn't already provide (`google-genai`, `easyocr`, `gdown`), deliberately avoiding forced upgrades to TensorFlow/scikit-learn, which are already compatible versions pre-installed on Colab.

No paid API tier or billing is required to run any part of this project — everything runs on Gemini's free tier.

---

## Known Limitations

- **Nutri-Score is a general EU nutrient-profiling standard**, not India-specific — no finalized Indian standard (e.g. from FSSAI) currently exists to substitute it. Some nutrient fields (notably `fruit_veg_nuts_pct`) are rarely stated on packaging and default conservatively to zero.
- **Open Food Facts coverage for Indian products is inconsistent** — RAG grounding may not find a match for every scan; this is itself a quantifiable, documented gap rather than a hidden failure.
- **Confidence calibration is sensitive to calibration-set quality** — built from the same distribution as training data rather than fully independent held-out real-world photos, which can produce overly tight confidence thresholds.
- **Gemini free tier has no uptime guarantee** — transient `503` errors are handled via retry-with-backoff and graceful degradation, but a sustained outage will still surface as a clearly marked "temporarily unavailable" section rather than a full failure.
- No production backend or connected frontend currently exists — the pipeline runs within Colab notebooks.
<img width="1676" height="642" alt="image" src="https://github.com/user-attachments/assets/7a65f8f3-f990-4c08-9035-bc42394cc377" />

---

## Acknowledgements

- Dataset: IIT Patna Grocery_Items via Roboflow
- Allergen/ingredient reference data: [Open Food Facts](https://world.openfoodfacts.org/)
- Nutrition scoring standard: Nutri-Score, Santé publique France
