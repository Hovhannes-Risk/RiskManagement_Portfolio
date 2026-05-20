import pandas as pd

print("Loading data...")
bets_df = pd.read_excel("mydata.xlsx.xlsx", sheet_name="Raw_Data")
print(f"Loaded {len(bets_df)} bets")

# Player statistics
player_stats = bets_df.groupby("bettor").agg(
    Total_Bets=("bet_id", "count"),
    Total_Stake=("usd_amount", "sum"),
    Total_GGR=("usd_ggr", "sum")
).reset_index()

# Calculate Player Profit (negative GGR = player won)
player_stats["Player_Profit"] = -player_stats["Total_GGR"]

# Filter: ≤20 bets AND profitable players
low_volume_winners = player_stats[
    (player_stats["Total_Bets"] <= 20) & 
    (player_stats["Player_Profit"] > 0)
].copy()

print(f"\nFound {len(low_volume_winners)} winning players with ≤20 bets")

# Get detailed info for these players
winner_ids = low_volume_winners["bettor"].tolist()
winner_bets = bets_df[bets_df["bettor"].isin(winner_ids)].copy()

# Detailed report
detailed_report = winner_bets.groupby("bettor").agg(
    Total_Bets=("bet_id", "count"),
    Winning_Bets=("usd_ggr", lambda x: (x < 0).sum()),
    Losing_Bets=("usd_ggr", lambda x: (x > 0).sum()),
    Total_Stake=("usd_amount", "sum"),
    Total_Profit=("usd_ggr", lambda x: -x.sum()),
    Avg_Stake=("usd_amount", "mean"),
    Win_Rate=("usd_ggr", lambda x: (x < 0).sum() / len(x) * 100),
    ROI=("usd_ggr", lambda x: (-x.sum() / (bets_df[bets_df["bettor"] == x.name]["usd_amount"].sum())) * 100),
    Sports_Played=("sports", lambda x: ", ".join(x.unique())),
    Most_Played_Sport=("sports", lambda x: x.mode()[0] if len(x.mode()) > 0 else "N/A"),
    Markets_Used=("market", lambda x: x.nunique()),
    Ordinar_Count=("bet_type", lambda x: (x == "Ordinar").sum()),
    Express_Count=("bet_type", lambda x: (x == "Express").sum())
).reset_index()

# Sort by profit
detailed_report = detailed_report.sort_values("Total_Profit", ascending=False)

# Summary
print(f"\nTOP 10 WINNING PLAYERS (≤20 bets):")
print(detailed_report[["bettor", "Total_Bets", "Total_Profit", "Win_Rate", "ROI"]].head(10))

print(f"\nTOTAL STATS:")
print(f"Total Players: {len(detailed_report)}")
print(f"Total Profit (from firm perspective): ${-detailed_report['Total_Profit'].sum():,.2f}")
print(f"Avg Profit per Player: ${detailed_report['Total_Profit'].mean():,.2f}")
print(f"Avg Win Rate: {detailed_report['Win_Rate'].mean():.1f}%")

# Save
detailed_report.to_excel("outputs/winning_low_volume_players.xlsx", index=False)
print("\nSaved to outputs/winning_low_volume_players.xlsx")
print("Done!")
