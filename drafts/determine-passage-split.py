# %%
import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix

results_df = pd.read_csv("outputs/buffer_analysis.csv")

results_df["Passage_numeric"] = (results_df["Passage"] == "high").astype(int)

candidate_cols = [c for c in results_df.columns if c.startswith("Points_")]

print("=" * 80)
print("BEST SINGLE THRESHOLD FOR REPRODUCING PASSAGE CLASS")
print("=" * 80)

for buffer_m in sorted(results_df["Buffer_m"].unique()):

    subset = results_df[results_df["Buffer_m"] == buffer_m].copy()

    y_true = subset["Passage_numeric"]

    print(f"\n{'-' * 80}")
    print(f"Buffer: {buffer_m} m")
    print(f"{'-' * 80}")

    summary = []

    for col in candidate_cols:

        values = np.sort(subset[col].unique())

        best = {
            "accuracy": -1,
            "threshold": None,
            "direction": None,
            "cm": None,
        }

        for t in values:

            # High if >= threshold
            pred = (subset[col] >= t).astype(int)
            acc = (pred == y_true).mean()

            if acc > best["accuracy"]:
                best = {
                    "accuracy": acc,
                    "threshold": t,
                    "direction": ">=",
                    "cm": confusion_matrix(y_true, pred),
                }

            # High if < threshold
            pred = (subset[col] < t).astype(int)
            acc = (pred == y_true).mean()

            if acc > best["accuracy"]:
                best = {
                    "accuracy": acc,
                    "threshold": t,
                    "direction": "<",
                    "cm": confusion_matrix(y_true, pred),
                }

        summary.append((col, best))

    # Rank variables by accuracy
    summary.sort(key=lambda x: x[1]["accuracy"], reverse=True)

    for col, best in summary:

        print(
            f"{col:20s} "
            f"High if {col} {best['direction']} {best['threshold']:>7}   "
            f"Accuracy = {best['accuracy']:.3f}"
        )

    # Show confusion matrix for the best-performing variable
    best_col, best = summary[0]

    print("\nBest model:")
    print(f"  Variable : {best_col}")
    print(f"  Rule     : High if {best_col} {best['direction']} {best['threshold']}")
    print(f"  Accuracy : {best['accuracy']:.3f}")

    tn, fp, fn, tp = best["cm"].ravel()

    print("\nConfusion matrix")
    print("                 Pred Low   Pred High")
    print(f"Actual Low      {tn:8d} {fp:10d}")
    print(f"Actual High     {fn:8d} {tp:10d}")

# %%
