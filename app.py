"""
app.py - Soybean Growth Stage Classifier (Flask prototype)

Run:   python app.py        then open  http://127.0.0.1:5000
API:   POST /api/predict    (JSON body, same fields as the form)

Needs in the same folder: stage_predictor.py, stage_art.py, templates/index.html,
and model/ (soybean_stage_svm.joblib, model_card.json).

Optional real photos: create a folder called  photos  next to app.py and put files named after the
stage keys (ve, vc, v1, vn, r1, r2, r3, r4, r5, r6, r7, r8) as .jpg / .jpeg / .png / .webp.
The app uses your photo for that stage instead of the drawing.
"""
import json
import re
from datetime import date
from pathlib import Path

from flask import Flask, Response, abort, jsonify, render_template, request, send_file

from stage_art import GROUP_INFO, GROUP_KEY, STAGE_BY_KEY, STAGES, node_guide_svg, stage_svg
from stage_predictor import predict_stage

BASE = Path(__file__).parent
PHOTO_DIR = BASE / "photos"
app = Flask(__name__)
CARD = json.loads((BASE / "model" / "model_card.json").read_text())
GROUPS = ["Vegetative", "Flowering", "Pod", "Seed", "Maturity"]
PERF = CARD["performance_unseen_sites"]
PER_CLASS = CARD["per_class_unseen_sites"]

FIELDS = {  # name: (label, min, max)
    "latitude": ("Latitude", -90, 90),
    "longitude": ("Longitude", -180, 180),
    "maturity_group": ("Maturity group", 0, 10),
    "nodes_per_plant": ("Nodes per plant", 0, 60),
}


def run_prediction(data):
    """Validate raw inputs (strings or numbers) and return (result, errors)."""
    errors = []
    try:
        planting = date.fromisoformat(str(data.get("planting_date", "")).strip())
        observed = date.fromisoformat(str(data.get("observation_date", "")).strip())
    except ValueError:
        return None, ["Enter both dates in the format YYYY-MM-DD."]
    nums = {}
    for name, (label, lo, hi) in FIELDS.items():
        try:
            v = float(str(data.get(name, "")).strip())
        except ValueError:
            errors.append(f"{label} must be a number.")
            continue
        if not lo <= v <= hi:
            errors.append(f"{label} must be between {lo} and {hi}.")
        nums[name] = v
    if observed <= planting:
        errors.append("The observation date must be after the planting date.")
    if (observed - planting).days > 400:
        errors.append("The observation date is more than 400 days after planting; check the dates.")
    if errors:
        return None, errors
    result = predict_stage(planting.isoformat(), observed.isoformat(), nums["latitude"], nums["longitude"],
                           nums["maturity_group"], nums["nodes_per_plant"])
    g = result["stage_group"]
    result["f1_for_group"] = PER_CLASS[g]["f1-score"]
    result["group_key"] = GROUP_KEY[g]
    result["second_key"] = GROUP_KEY[result["second_choice"]]
    result["index"] = GROUPS.index(g)
    result["next_group"] = GROUPS[GROUPS.index(g) + 1] if GROUPS.index(g) < len(GROUPS) - 1 else None
    result["next_key"] = GROUP_KEY[result["next_group"]] if result["next_group"] else None
    return result, []


def _photo_for(key):
    for ext in ("jpg", "jpeg", "png", "webp"):
        f = PHOTO_DIR / f"{key}.{ext}"
        if f.is_file():
            return f
    return None


@app.route("/art/<key>")
def art(key):
    """Image for a stage: your photo if one exists in photos/, otherwise the built-in drawing."""
    if not re.fullmatch(r"[a-z0-9]{2,6}", key):
        abort(404)
    if key == "nodes":
        return Response(node_guide_svg(), mimetype="image/svg+xml")
    if key not in STAGE_BY_KEY:
        abort(404)
    photo = _photo_for(key)
    if photo:
        return send_file(photo)
    return Response(stage_svg(key), mimetype="image/svg+xml", headers={"Cache-Control": "public, max-age=3600"})


@app.route("/", methods=["GET", "POST"])
def index():
    form, result, errors = {}, None, []
    if request.method == "POST":
        form = request.form.to_dict()
        result, errors = run_prediction(form)
    else:
        form = {"observation_date": date.today().isoformat()}
    return render_template(
        "index.html", form=form, result=result, errors=errors, stages=STAGES, groups=GROUPS,
        group_info=GROUP_INFO, group_key=GROUP_KEY, per_class=PER_CLASS, perf=PERF,
        has_photos={k: bool(_photo_for(k)) for k in STAGE_BY_KEY})


@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(silent=True) or {}
    result, errors = run_prediction(data)
    if errors:
        return jsonify({"errors": errors}), 400
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
