"""
train_models.py
===============
Tunes and evaluates seven classifiers for soybean growth stage classification using
NESTED, GROUPED cross-validation:

  outer loop : Leave-One-Site-Year-Out (11 folds)   -> unbiased estimate on unseen environments
  inner loop : GroupKFold(3) on the training sites  -> hyper-parameter tuning (scoring = macro-F1)

Usage
-----
    python train_models.py stage:full stage_group:full stage:portable stage_group:portable

Each argument is  <target>:<feature_set>
  target       : stage (11 classes) | stage_group (5 groups)
  feature_set  : full     = calendar + site + plant features (research setting)
                 portable = dap, nodes_per_plant, nodes_per_dap, RM only (features a user can enter
                            in an application; no calendar or US site information)
                 app      = doy, dap, plant_doy, RM, nodes_per_plant, nodes_per_dap, latitude, longitude
                            (no seeding rate / tillage, which were found not to help)

Outputs (in ./results/)
  nested_results.csv                  one row per target / feature set / model
  predictions_<target>_<fs>.csv       pooled out-of-fold predictions of every model
  best_params_<target>_<fs>.csv       hyper-parameters chosen in each outer fold
"""
import json
import sys
import time
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import (accuracy_score, f1_score, matthews_corrcoef,
                             precision_score, recall_score)
from sklearn.model_selection import GridSearchCV, GroupKFold, LeaveOneGroupOut
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

warnings.filterwarnings("ignore")
CSV = "soybean_growth_stage_dataset.csv"
OUTDIR = Path("results")
OUTDIR.mkdir(exist_ok=True)


def scaled(est):
    return Pipeline([("sc", StandardScaler()), ("m", est)])


def model_space():
    """name -> (estimator, parameter grid). Grids are deliberately small (single-core friendly)."""
    return {
        "Decision Tree": (DecisionTreeClassifier(min_samples_leaf=5, random_state=42),
                          {"max_depth": [6, 10, None]}),
        "Random Forest": (RandomForestClassifier(n_estimators=200, min_samples_leaf=3, n_jobs=1, random_state=42),
                          {"max_depth": [10, None]}),
        "SVM (RBF)": (scaled(SVC(kernel="rbf", gamma="scale")), {"m__C": [1, 10, 100]}),
        "k-NN": (scaled(KNeighborsClassifier()), {"m__n_neighbors": [5, 15, 31]}),
        "Naive Bayes": (scaled(GaussianNB()), {"m__var_smoothing": [1e-9, 1e-3]}),
        "MLP": (scaled(MLPClassifier(max_iter=300, alpha=1e-3, early_stopping=True, random_state=42)),
                {"m__hidden_layer_sizes": [(64,), (64, 32)]}),
        "Gradient Boosting": (HistGradientBoostingClassifier(max_iter=100, random_state=42),
                              {"learning_rate": [0.05, 0.1]}),
    }


def feature_sets(df):
    till = [c for c in df.columns if c.startswith("till_")]
    return {
        "full": ["doy", "dap", "plant_doy", "RM", "nodes_per_plant", "nodes_per_dap",
                 "latitude", "longitude", "seeding_rate"] + till,
        "portable": ["dap", "nodes_per_plant", "nodes_per_dap", "RM"],
        # lean set for the application: every input can be derived from 5 user entries
        # (planting date, observation date, field latitude/longitude, maturity group, nodes per plant)
        "app": ["doy", "dap", "plant_doy", "RM", "nodes_per_plant", "nodes_per_dap",
                "latitude", "longitude"],
    }


def run(df, target, fs_name):
    cols = feature_sets(df)[fs_name]
    X = df[cols].values
    le = LabelEncoder()
    y = le.fit_transform(df[target].values)
    groups = df["site_id"].values
    outer = LeaveOneGroupOut()
    space = model_space()
    preds = {m: np.empty(len(df), dtype=int) for m in space}
    chosen = {m: [] for m in space}
    t_all = time.time()
    for k, (tr, te) in enumerate(outer.split(X, y, groups), 1):
        t0 = time.time()
        for name, (est, grid) in space.items():
            gs = GridSearchCV(est, grid, cv=GroupKFold(n_splits=3), scoring="f1_macro", n_jobs=1, refit=True)
            gs.fit(X[tr], y[tr], groups=groups[tr])
            preds[name][te] = gs.predict(X[te])
            chosen[name].append(json.dumps(gs.best_params_, default=str))
        print(f"[{target}:{fs_name}] outer fold {k}/11 held out {groups[te][0]}  ({time.time() - t0:.0f}s, total {time.time() - t_all:.0f}s)", flush=True)

    rows = []
    for name in space:
        p = preds[name]
        rows.append({
            "target": target, "feature_set": fs_name, "model": name,
            "accuracy": accuracy_score(y, p),
            "macro_precision": precision_score(y, p, average="macro", zero_division=0),
            "macro_recall": recall_score(y, p, average="macro", zero_division=0),
            "macro_f1": f1_score(y, p, average="macro", zero_division=0),
            "mcc": matthews_corrcoef(y, p),
        })
    out = pd.DataFrame({"site_id": groups, "y_true": le.inverse_transform(y)})
    for name in space:
        out[name] = le.inverse_transform(preds[name])
    out.to_csv(OUTDIR / f"predictions_{target}_{fs_name}.csv", index=False)
    bp = pd.DataFrame({m: chosen[m] for m in space})
    bp.insert(0, "held_out_site", sorted(set(groups)))
    bp.to_csv(OUTDIR / f"best_params_{target}_{fs_name}.csv", index=False)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = pd.read_csv(CSV)
    df = pd.concat([df, pd.get_dummies(df["tillage"], prefix="till", dtype=float)], axis=1)
    combos = [a.split(":") for a in sys.argv[1:]] or [["stage", "full"]]
    res_path = OUTDIR / "nested_results.csv"
    for target, fs in combos:
        res = run(df, target, fs)
        old = pd.read_csv(res_path) if res_path.exists() else pd.DataFrame()
        if len(old):
            old = old[~((old["target"] == target) & (old["feature_set"] == fs))]
        pd.concat([old, res]).to_csv(res_path, index=False)
        print(res.round(3).to_string(index=False), flush=True)
    print("DONE", flush=True)
