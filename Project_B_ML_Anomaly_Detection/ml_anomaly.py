import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest

print("Loading data...")
bets_df = pd.read_excel("mydata.xlsx.xlsx", sheet_name="Raw_Date")
print(f"Loaded {len(bets_df)} bets")

ordinar_bets = bets_df[bets_df["bet_type"] == "Ordinar"]
express_bets = bets_df[bets_df["bet_type"] == "Express"]

player_stats = bets_df.groupby("bettor").agg(
    Total_Bets=("bet_id", "count"),
    Total_Stake=("usd_amount", "sum"),
    Avg_Stake=("usd_amount", "mean"),
    Total_GGR=("usd_ggr", "sum"),
    Win_Rate=("usd_ggr", lambda x: (x < 0).sum() / len(x))
).reset_index()

ordinar_stats = ordinar_bets.groupby("bettor").agg(
    Ordinar_Bets=("bet_id", "count"),
    Avg_Odds_Single=("odds", "mean")
).reset_index()

express_stats = express_bets.groupby("bettor").agg(
    Express_Bets=("bet_id", "count")
).reset_index()

player_stats = player_stats.merge(ordinar_stats, on="bettor", how="left")
player_stats = player_stats.merge(express_stats, on="bettor", how="left")
player_stats["Ordinar_Bets"] = player_stats["Ordinar_Bets"].fillna(0)
player_stats["Express_Bets"] = player_stats["Express_Bets"].fillna(0)
player_stats["Avg_Odds_Single"] = player_stats["Avg_Odds_Single"].fillna(0)

print(f"Analyzing {len(player_stats)} players...")

features = ["Ordinar_Bets", "Total_Stake", "Avg_Stake", "Win_Rate", "Avg_Odds_Single"]

for feature in features:
    player_stats[f"zscore_{feature}"] = np.abs(stats.zscore(player_stats[feature]))
player_stats["Max_ZScore"] = player_stats[[f"zscore_{f}" for f in features]].max(axis=1)

def iqr_outlier(series):
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    return (series < Q1 - 1.5 * IQR) | (series > Q3 + 1.5 * IQR)

iqr_flags = pd.DataFrame()
for feature in features:
    iqr_flags[feature] = iqr_outlier(player_stats[feature])
player_stats["IQR_Flags"] = iqr_flags.sum(axis=1)

X = player_stats[features].fillna(0)
iso_forest = IsolationForest(contamination=0.1, random_state=42)
player_stats["IF_Score"] = iso_forest.fit_predict(X)
player_stats["IF_Anomaly"] = player_stats["IF_Score"] == -1

player_stats["Anomaly_Score"] = (
    (player_stats["Max_ZScore"] > 3).astype(int) +
    (player_stats["IQR_Flags"] >= 2).astype(int) +
    player_stats["IF_Anomaly"].astype(int)
)

def classify_anomaly(score):
    if score == 3:
        return "CRITICAL"
    elif score == 2:
        return "HIGH"
    elif score == 1:
        return "MEDIUM"
    return "NORMAL"

player_stats["Anomaly_Level"] = player_stats["Anomaly_Score"].apply(classify_anomaly)

print(player_stats["Anomaly_Level"].value_counts())

output_cols = ["bettor", "Total_Bets", "Ordinar_Bets", "Express_Bets",
               "Total_Stake", "Avg_Stake", "Win_Rate", "Avg_Odds_Single",
               "Max_ZScore", "IQR_Flags", "IF_Anomaly", "Anomaly_Score", "Anomaly_Level"]

result_df = player_stats[output_cols].sort_values("Anomaly_Score", ascending=False)
result_df.to_excel("outputs/ml_anomaly_detection.xlsx", index=False)
print("Saved to outputs/ml_anomaly_detection.xlsx")
print("Done!")
