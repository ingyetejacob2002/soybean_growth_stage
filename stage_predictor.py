"""
stage_predictor.py
==================
Turns the five things a user can enter into model features and predicts the soybean stage group.
This is the module the web application should import.

    from stage_predictor import predict_stage
    predict_stage("2018-05-15", "2018-07-20", latitude=45.0, longitude=-93.0,
                  maturity_group=1.5, nodes_per_plant=8)
"""
import json
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

_DIR = Path(__file__).parent / "model"
_BUNDLE = joblib.load(_DIR / "soybean_stage_svm.joblib")
_CARD = json.loads((_DIR / "model_card.json").read_text())
_RANGES = _CARD["training_ranges"]
_LABELS = {"Vegetative": "Vegetative (VE to V-stages before flowering)",
           "Flowering": "Flowering (R1 to R2)", "Pod": "Pod development (R3 to R4)",
           "Seed": "Seed development (R5 to R6)", "Maturity": "Maturity (R7 to R8)"}


def predict_stage(planting_date, observation_date, latitude, longitude, maturity_group, nodes_per_plant):
    p, o = pd.Timestamp(planting_date), pd.Timestamp(observation_date)
    dap = (o - p).days
    if dap <= 0:
        raise ValueError("The observation date must be after the planting date.")
    if nodes_per_plant < 0:
        raise ValueError("nodes_per_plant must be zero or more.")
    feats = {"doy": o.dayofyear, "dap": dap, "plant_doy": p.dayofyear, "RM": maturity_group,
             "nodes_per_plant": nodes_per_plant, "nodes_per_dap": nodes_per_plant / dap,
             "latitude": latitude, "longitude": longitude}
    X = pd.DataFrame([feats])[_BUNDLE["features"]].values
    model, classes = _BUNDLE["model"], _BUNDLE["classes"]
    scores = model.decision_function(X)[0]
    order = np.argsort(scores)[::-1]
    warnings = []
    # small tolerance so values right at the edge of the trained range are not flagged
    tol = {"latitude": 1.0, "longitude": 1.0, "RM": 0.25, "dap": 5, "nodes_per_plant": 1}
    for f, label in (("latitude", "latitude"), ("longitude", "longitude"), ("RM", "maturity group"),
                     ("dap", "days after planting"), ("nodes_per_plant", "nodes per plant")):
        lo, hi = _RANGES[f]
        if not lo - tol[f] <= feats[f] <= hi + tol[f]:
            warnings.append(f"{label} = {feats[f]:.4g} is outside the range the model was trained on ({lo:.4g} to {hi:.4g}); treat the result as unreliable.")
    return {"stage_group": classes[order[0]], "description": _LABELS[classes[order[0]]],
            "second_choice": classes[order[1]], "warnings": warnings, "features_used": feats}


if __name__ == "__main__":
    print(predict_stage("2018-05-15", "2018-07-20", 45.0, -93.0, 1.5, 8))
