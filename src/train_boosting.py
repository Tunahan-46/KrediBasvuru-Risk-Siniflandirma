"""
Adım 6 – Ana model adayları: XGBoost ve LightGBM + Optuna (4. hafta, Hedef 4.1)

Üçüncü haftanın ön işleme hattı EĞİTİM kümesinde uydurulur; iki gradyan
artırma modeli aynı özellikler üzerinde eğitilir. Hiperparametreler Optuna
(TPE) ile DOĞRULAMA kümesindeki ROC-AUC'ye göre ayarlanır; erken durdurma da
doğrulama kümesinde yapılır. Test kümesi AÇILMAZ.

Üretilenler:
  models/main_model_uncalibrated.joblib   Ön işleme + en iyi model (kalibre edilmemiş)
  models/main_model_meta.json             Seçilen model, parametreler, ölçütler
  reports/boosting_log.md                 Ölçüt tablosu, en iyi parametreler, özellik önemleri
  reports/optuna_trials.csv               Tüm denemeler
  reports/figures/roc_compare.png         LR / XGBoost / LightGBM ROC eğrileri (doğrulama)
  reports/figures/importance_main.png     En iyi modelin özellik önemleri (gain)
  reports/figures/optuna_history.png      Deneme geçmişi

--trials 0 verilirse Optuna araması yapılmaz; sabit (elle seçilmiş) parametrelerle
erken durdurmalı tek eğitim yapılır (hafif koşu, 4. hafta).

Kullanım:
  python src/train_boosting.py --indir data/processed --trials 40
  python src/train_boosting.py --trials 0 --n-jobs 4 --max-trees 1000   # hafif koşu
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import optuna
import pandas as pd
from lightgbm import LGBMClassifier, early_stopping
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preprocess import RAW_COLUMNS, build_preprocessor  # noqa: E402
from train_baseline import evaluate  # noqa: E402

optuna.logging.set_verbosity(optuna.logging.WARNING)
N_JOBS = 8
MAX_TREES = 3000

FIXED_XGB = {"learning_rate": 0.05, "max_depth": 5, "min_child_weight": 10.0, "subsample": 0.8, "colsample_bytree": 0.8, "reg_lambda": 1.0, "reg_alpha": 0.0, "gamma": 0.0, "scale_pos_weight": 1.0}
FIXED_LGBM = {"learning_rate": 0.05, "num_leaves": 31, "min_child_samples": 100, "subsample": 0.8, "colsample_bytree": 0.8, "reg_lambda": 1.0, "reg_alpha": 0.0, "scale_pos_weight": 1.0}
EARLY_STOP = 100


def xgb_space(trial: optuna.Trial, pos_ratio: float) -> dict:
    return {
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "max_depth": trial.suggest_int("max_depth", 2, 8),
        "min_child_weight": trial.suggest_float("min_child_weight", 1, 100, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-2, 10, log=True),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10, log=True),
        "gamma": trial.suggest_float("gamma", 0, 5),
        "scale_pos_weight": trial.suggest_categorical("scale_pos_weight", [1.0, round(pos_ratio, 2)]),
    }


def lgbm_space(trial: optuna.Trial, pos_ratio: float) -> dict:
    return {
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 8, 128, log=True),
        "min_child_samples": trial.suggest_int("min_child_samples", 20, 500, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-2, 10, log=True),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10, log=True),
        "scale_pos_weight": trial.suggest_categorical("scale_pos_weight", [1.0, round(pos_ratio, 2)]),
    }


def make_xgb(params: dict, n_estimators: int, seed: int, early_stop: bool) -> XGBClassifier:
    return XGBClassifier(
        n_estimators=n_estimators, tree_method="hist", eval_metric="auc", n_jobs=N_JOBS, random_state=seed,
        early_stopping_rounds=EARLY_STOP if early_stop else None, **params,
    )


def make_lgbm(params: dict, n_estimators: int, seed: int) -> LGBMClassifier:
    return LGBMClassifier(n_estimators=n_estimators, subsample_freq=1, n_jobs=N_JOBS, random_state=seed, verbose=-1, **params)


def tune(kind: str, Xt, y_tr, Xv, y_va, trials: int, timeout: int, seed: int) -> tuple[optuna.Study, dict]:
    pos_ratio = float((y_tr == 0).sum() / (y_tr == 1).sum())
    best_iters: dict[int, int] = {}

    def objective(trial: optuna.Trial) -> float:
        if kind == "xgb":
            model = make_xgb(xgb_space(trial, pos_ratio), MAX_TREES, seed, early_stop=True)
            model.fit(Xt, y_tr, eval_set=[(Xv, y_va)], verbose=False)
            best_iters[trial.number] = int(model.best_iteration) + 1
        else:
            model = make_lgbm(lgbm_space(trial, pos_ratio), MAX_TREES, seed)
            model.fit(Xt, y_tr, eval_set=[(Xv, y_va)], eval_metric="auc", callbacks=[early_stopping(EARLY_STOP, verbose=False)])
            best_iters[trial.number] = int(model.best_iteration_)
        p = model.predict_proba(Xv)[:, 1]
        return roc_auc_score(y_va, p)

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed), study_name=kind)
    study.optimize(objective, n_trials=trials, timeout=timeout, show_progress_bar=False)
    best = dict(study.best_params)
    best["n_estimators"] = best_iters[study.best_trial.number]
    return study, best


def md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(f"{v:.4f}" if isinstance(v, float) else str(v) for v in r) + " |")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--indir", default="data/processed")
    parser.add_argument("--trials", type=int, default=40)
    parser.add_argument("--timeout", type=int, default=1500, help="Her çalışma için en çok saniye")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-jobs", type=int, default=8)
    parser.add_argument("--max-trees", type=int, default=3000)
    parser.add_argument("--baseline", default="models/baseline_logreg.joblib")
    parser.add_argument("--model-out", default="models/main_model_uncalibrated.joblib")
    parser.add_argument("--meta-out", default="models/main_model_meta.json")
    parser.add_argument("--report", default="reports/boosting_log.md")
    parser.add_argument("--trials-out", default="reports/optuna_trials.csv")
    parser.add_argument("--figdir", default="reports/figures")
    args = parser.parse_args()
    global N_JOBS, MAX_TREES
    N_JOBS, MAX_TREES = args.n_jobs, args.max_trees

    indir = Path(args.indir)
    train = pd.read_parquet(indir / "train.parquet")
    valid = pd.read_parquet(indir / "valid.parquet")
    # test.parquet bilinçli olarak OKUNMAZ.
    X_tr, y_tr = train[RAW_COLUMNS], train["target"].to_numpy()
    X_va, y_va = valid[RAW_COLUMNS], valid["target"].to_numpy()

    prep = build_preprocessor().fit(X_tr)          # parametreler yalnızca eğitimden
    Xt = prep.transform(X_tr).astype(np.float32)
    Xv = prep.transform(X_va).astype(np.float32)
    feat_names = list(prep.get_feature_names_out())
    pos_ratio = float((y_tr == 0).sum() / (y_tr == 1).sum())
    print(f"Eğitim {len(train):,}, doğrulama {len(valid):,}, özellik {Xt.shape[1]}, iyi/kötü oranı {pos_ratio:.2f}", flush=True)

    rows, preds, times, studies, best_params, models = [], {}, {}, {}, {}, {}

    # Temel çizgi (3. hafta) – aynı tabloya
    if Path(args.baseline).exists():
        lr = joblib.load(args.baseline)
        preds["Lojistik regresyon (3. hafta)"] = (lr.predict_proba(X_tr)[:, 1], lr.predict_proba(X_va)[:, 1])

    # Ayarsız (varsayılan) modeller – ayarlamanın katkısını görmek için
    t0 = time.time()
    xgb_def = make_xgb({"learning_rate": 0.05, "max_depth": 6}, 500, args.seed, early_stop=False).fit(Xt, y_tr)
    times["XGBoost varsayılan"] = time.time() - t0
    preds["XGBoost varsayılan"] = (xgb_def.predict_proba(Xt)[:, 1], xgb_def.predict_proba(Xv)[:, 1])
    t0 = time.time()
    lgb_def = make_lgbm({"learning_rate": 0.05, "num_leaves": 31}, 500, args.seed).fit(Xt, y_tr)
    times["LightGBM varsayılan"] = time.time() - t0
    preds["LightGBM varsayılan"] = (lgb_def.predict_proba(Xt)[:, 1], lgb_def.predict_proba(Xv)[:, 1])

    # Ana adaylar: Optuna ile ayarlama (trials > 0) ya da sabit parametre + erken durdurma (trials == 0)
    cand = []
    for kind, label in [("xgb", "XGBoost"), ("lgbm", "LightGBM")]:
        if args.trials > 0:
            label += " (Optuna)"
            t0 = time.time()
            study, best = tune(kind, Xt, y_tr, Xv, y_va, args.trials, args.timeout, args.seed)
            times[label + " – arama"] = time.time() - t0
            studies[label] = study
            n_est = best.pop("n_estimators")
        else:
            label += " (sabit parametre, erken durdurma)"
            best = dict(FIXED_XGB if kind == "xgb" else FIXED_LGBM)
            t0 = time.time()
            if kind == "xgb":
                es = make_xgb(best, MAX_TREES, args.seed, early_stop=True).fit(Xt, y_tr, eval_set=[(Xv, y_va)], verbose=False)
                n_est = int(es.best_iteration) + 1
            else:
                es = make_lgbm(best, MAX_TREES, args.seed).fit(Xt, y_tr, eval_set=[(Xv, y_va)], eval_metric="auc",
                                                                   callbacks=[early_stopping(EARLY_STOP, verbose=False)])
                n_est = int(es.best_iteration_)
            times[label + " – erken durdurma"] = time.time() - t0
        t0 = time.time()
        if kind == "xgb":
            model = make_xgb(best, n_est, args.seed, early_stop=False).fit(Xt, y_tr)
        else:
            model = make_lgbm(best, n_est, args.seed).fit(Xt, y_tr)
        times[label] = time.time() - t0
        best["n_estimators"] = n_est
        best_params[label] = best
        models[label] = model
        cand.append(label)
        preds[label] = (model.predict_proba(Xt)[:, 1], model.predict_proba(Xv)[:, 1])
        extra = f"{len(studies[label].trials)} deneme, " if label in studies else ""
        print(f"{label}: {extra}doğrulama AUC {roc_auc_score(y_va, preds[label][1]):.4f}, ağaç {n_est}", flush=True)

    for name, (p_tr, p_va) in preds.items():
        r_tr = evaluate(name + " – eğitim", y_tr, p_tr)
        r_va = evaluate(name + " – doğrulama", y_va, p_va)
        rows += [r_tr, r_va]
    metrics = pd.DataFrame(rows)

    tuned = {k: roc_auc_score(y_va, v[1]) for k, v in preds.items() if k in cand}
    best_label = max(tuned, key=tuned.get)
    best_model = models[best_label]
    print("Seçilen ana model:", best_label)

    # Özellik önemleri (gain)
    if isinstance(best_model, XGBClassifier):
        gain = best_model.get_booster().get_score(importance_type="gain")
        imp = pd.Series({feat_names[int(k[1:])]: v for k, v in gain.items()})
    else:
        imp = pd.Series(best_model.booster_.feature_importance(importance_type="gain"), index=feat_names)
    imp = (imp / imp.sum()).sort_values(ascending=False)
    imp_df = imp.rename("pay").reset_index().rename(columns={"index": "ozellik"})

    # Çizimler
    figdir = Path(args.figdir); figdir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(5, 5))
    for name in ["Lojistik regresyon (3. hafta)"] + cand:
        if name in preds:
            fpr, tpr, _ = roc_curve(y_va, preds[name][1])
            plt.plot(fpr, tpr, label=f"{name} (AUC={roc_auc_score(y_va, preds[name][1]):.3f})")
    plt.plot([0, 1], [0, 1], "k--", lw=0.8)
    plt.xlabel("Yanlış pozitif oranı"); plt.ylabel("Doğru pozitif oranı")
    plt.title("ROC eğrileri – doğrulama kümesi (2014)"); plt.legend(loc="lower right", fontsize=8); plt.tight_layout()
    plt.savefig(figdir / "roc_compare.png", dpi=150); plt.close()

    top = imp.head(15)[::-1]
    plt.figure(figsize=(6, 5))
    plt.barh(top.index, top.values * 100)
    plt.xlabel("Toplam kazanca katkı (%)"); plt.title(f"Özellik önemleri – {best_label}"); plt.tight_layout()
    plt.savefig(figdir / "importance_main.png", dpi=150); plt.close()

    if studies:
        plt.figure(figsize=(6, 4))
        for label, study in studies.items():
            vals = [t.value for t in study.trials if t.value is not None]
            plt.plot(range(1, len(vals) + 1), np.maximum.accumulate(vals), label=f"{label} – en iyi")
            plt.scatter(range(1, len(vals) + 1), vals, s=8, alpha=0.5)
        plt.xlabel("Deneme"); plt.ylabel("Doğrulama ROC-AUC"); plt.title("Optuna deneme geçmişi"); plt.legend(fontsize=8); plt.tight_layout()
        plt.savefig(figdir / "optuna_history.png", dpi=150); plt.close()
        frames = []
        for label, study in studies.items():
            df = study.trials_dataframe(attrs=("number", "value", "params", "duration"))
            df.insert(0, "model", label)
            frames.append(df)
        Path(args.trials_out).parent.mkdir(parents=True, exist_ok=True)
        pd.concat(frames).to_csv(args.trials_out, index=False)

    # Model + meta
    pipe = Pipeline([("prep", prep), ("clf", best_model)])
    Path(args.model_out).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, args.model_out)
    va_metrics = {k: {m: float(v) for m, v in evaluate(k, y_va, p[1]).items() if m != "Model"} for k, p in preds.items()}
    meta = {
        "selected": best_label,
        "params": best_params[best_label],
        "n_trials": {k: len(st.trials) for k, st in studies.items()}, "mode": "optuna" if args.trials > 0 else "fixed",
        "valid_metrics": va_metrics,
        "feature_importance": {k: float(v) for k, v in imp.items()},
        "train_rows": int(len(train)), "valid_rows": int(len(valid)), "n_features": int(Xt.shape[1]),
        "seconds": {k: round(v, 1) for k, v in times.items()},
    }
    Path(args.meta_out).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Ana model günlüğü – XGBoost / LightGBM + Optuna (src/train_boosting.py)", "",
        f"Eğitim: {len(train):,} kayıt (2007–2013), doğrulama: {len(valid):,} kayıt (2014). Test kümesi açılmadı.",
        (f"Özellik sayısı: {Xt.shape[1]} (3. hafta ön işleme hattı). Optuna TPE, her model için en çok {args.trials} deneme / {args.timeout} sn; "
         f"amaç doğrulama ROC-AUC; erken durdurma {EARLY_STOP} tur (doğrulama kümesinde). Tohum {args.seed}." if args.trials > 0 else
         f"Özellik sayısı: {Xt.shape[1]} (3. hafta ön işleme hattı). Hafif koşu: Optuna yok, sabit parametreler; ağaç sayısı doğrulama kümesinde "
         f"erken durdurma ({EARLY_STOP} tur, en çok {MAX_TREES}) ile seçildi. {N_JOBS} çekirdek, tohum {args.seed}."), "",
        "## Ölçütler", "", md(metrics), "",
        f"Seçilen ana model: **{best_label}**.", "",
        "## En iyi parametreler", "",
        *[f"- {k}: `{json.dumps(v, ensure_ascii=False)}`" for k, v in best_params.items()],
        "", "## Deneme sayısı ve süreler", "",
        *[f"- {k}: {len(st.trials)} deneme" for k, st in studies.items()],
        *[f"- {k}: {v:.1f} sn" for k, v in times.items()],
        "", f"## Özellik önemleri – {best_label} (gain, toplamın payı)", "", md(imp_df), "",
        f"Çıktılar: `{args.model_out}`, `{args.meta_out}`, `{figdir}/roc_compare.png`, `{figdir}/importance_main.png`" + (f", `{args.trials_out}`, `{figdir}/optuna_history.png`" if studies else ""),
    ]
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
