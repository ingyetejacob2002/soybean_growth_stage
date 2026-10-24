"""
export_model.py
===============
Trains the FINAL application model (SVM, RBF kernel) on all 11 site-years, using the lean "app"
feature set and the 5-group target (Vegetative / Flowering / Pod / Seed / Maturity), then saves:

  model/soybean_stage_svm.joblib   fitted pipeline + feature list + class names
  model/model_card.json            metrics, per-class results, training ranges, caveats
  results/confusion_matrix_stage_group_svm.png

The reported performance is NOT measured on the final model's own training data. It comes from the
nested leave-one-site-year-out run (train_models.py stage_group:app), where every site-year was
predicted by a model that never saw it.

Usage:  python export_model.py   (needs results/predictions_stage_group_app.csv and nested_results.csv)
"""
import json
import warnings
from pathlib import Path

import joblib
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import GridSearchCV, GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC

warnings.filterwarnings("ignore")
FEATURES = ["doy", "dap", "plant_doy", "RM", "nodes_per_plant", "nodes_per_dap", "latitude", "longitude"]
ORDER = ["Vegetative", "Flowering", "Pod", "Seed", "Maturity"]
Path("model").mkdir(exist_ok=True)
Path("results").mkdir(exist_ok=True)

df = pd.read_csv("soybean_growth_stage_dataset.csv")
X, g = df[FEATURES].values, df["site_id"].values
le = LabelEncoder()
y = le.fit_transform(df["stage_group"])

gs = GridSearchCV(Pipeline([("sc", StandardScaler()), ("m", SVC(kernel="rbf", gamma="scale"))]),
                  {"m__C": [1, 10, 100]}, cv=GroupKFold(n_splits=5), scoring="f1_macro", refit=True)
gs.fit(X, y, groups=g)
print("chosen C:", gs.best_params_, " cross-validated macro-F1 on tuning folds:", round(gs.best_score_, 3))
joblib.dump({"model": gs.best_estimator_, "features": FEATURES, "classes": list(le.classes_)},
            "model/soybean_stage_svm.joblib")

# ---- honest performance = nested out-of-fold predictions
pred = pd.read_csv("results/predictions_stage_group_app.csv")
nested = pd.read_csv("results/nested_results.csv")
row = nested[(nested.target == "stage_group") & (nested.feature_set == "app") & (nested.model == "SVM (RBF)")].iloc[0]
rep = classification_report(pred["y_true"], pred["SVM (RBF)"], labels=ORDER, output_dict=True, zero_division=0)
cm = confusion_matrix(pred["y_true"], pred["SVM (RBF)"], labels=ORDER)
cmn = cm / cm.sum(axis=1, keepdims=True)

fig, ax = plt.subplots(figsize=(6.2, 5.2))
im = ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
ax.set_xticks(range(5)); ax.set_xticklabels(ORDER, rotation=30, ha="right")
ax.set_yticks(range(5)); ax.set_yticklabels(ORDER)
for i in range(5):
    for j in range(5):
        ax.text(j, i, f"{cmn[i, j]:.2f}\n(n={cm[i, j]})", ha="center", va="center", fontsize=8,
                color="white" if cmn[i, j] > 0.5 else "black")
ax.set_xlabel("Predicted stage group"); ax.set_ylabel("Observed stage group")
ax.set_title("SVM, leave-one-site-year-out (row-normalised)")
fig.colorbar(im, fraction=0.046); fig.tight_layout()
fig.savefig("results/confusion_matrix_stage_group_svm.png", dpi=200)

card = {
    "model": "Support Vector Machine (RBF kernel) with standardised inputs",
    "task": "5-group soybean growth stage classification: " + ", ".join(ORDER),
    "features": FEATURES,
    "chosen_hyperparameters": {k: str(v) for k, v in gs.best_params_.items()},
    "trained_on": {"rows": int(len(df)), "plots": int(df.plot_id.nunique()), "site_years": int(df.site_id.nunique()),
                   "source": "Severo Silva et al. (2025), Dryad, doi:10.5061/dryad.2bvq83c20"},
    "validation": "nested leave-one-site-year-out (outer) with GroupKFold(3) tuning (inner)",
    "performance_unseen_sites": {"accuracy": round(row.accuracy, 3), "macro_precision": round(row.macro_precision, 3),
                                 "macro_recall": round(row.macro_recall, 3), "macro_f1": round(row.macro_f1, 3),
                                 "mcc": round(row.mcc, 3), "majority_class_accuracy": round(df.stage_group.value_counts(normalize=True).max(), 3)},
    "per_class_unseen_sites": {c: {k: round(rep[c][k], 3) for k in ("precision", "recall", "f1-score")} | {"support": int(rep[c]["support"])} for c in ORDER},
    "training_ranges": {f: [float(df[f].min()), float(df[f].max())] for f in FEATURES},
    "caveats": [
        "Trained only on US soybean trials (Arkansas, Minnesota, Ohio, Virginia, Wisconsin; 2017-2018).",
        "Latitude/longitude are strong inputs; predictions outside the trained latitude/longitude range are extrapolation.",
        "Predicts 5 stage groups, not individual Fehr stages (11-class accuracy was only about 49%).",
        "No weather inputs; stage timing also depends on temperature, which is not modelled.",
    ],
}
Path("model/model_card.json").write_text(json.dumps(card, indent=2))
print(json.dumps(card["performance_unseen_sites"], indent=2))
print(json.dumps(card["per_class_unseen_sites"], indent=2))
