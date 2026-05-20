
import pandas as pd
import numpy as np
from datetime import datetime
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches
from scipy import stats
from sklearn.ensemble import IsolationForest

print("="*60)
print("DAILY RISK REPORT GENERATOR")
print("="*60)

# Load today's data
print("\nLoading data...")
df = pd.read_excel("mydata.xlsx.xlsx", sheet_name="Raw_Data")
print(f"Loaded {len(df):,} bets from today")

report_date = df['bet_date'].iloc[0].strftime('%Y-%m-%d') if len(df)>0 else datetime.now().strftime('%Y-%m-%d')
print(f"Report date: {report_date}")

# KPIs
total_bets = len(df)
unique_players = df['bettor'].nunique()
total_stake = df['usd_amount'].sum()
total_ggr = df['usd_ggr'].sum()
house_hold = (total_ggr / total_stake * 100) if total_stake > 0 else 0

print(f"\nDAILY KPIs:")
print(f"  Bets: {total_bets:,}")
print(f"  Players: {unique_players:,}")
print(f"  Stake: ${total_stake:,.2f}")
print(f"  GGR: ${total_ggr:,.2f}")
print(f"  Hold: {house_hold:.2f}%")

# Player stats
player_stats = df.groupby('bettor').agg(
    Bets=('bet_id','count'),
    Stake=('usd_amount','sum'),
    GGR=('usd_ggr','sum'),
    Win_Rate=('usd_ggr', lambda x: (x<0).sum()/len(x)*100),
    Avg_Stake=('usd_amount','mean')
).reset_index()

# ML Anomaly Detection (quick version)
print("\nRunning ML anomaly detection...")
features = player_stats[['Bets','Stake','Avg_Stake','Win_Rate']].fillna(0)
player_stats['zscore_max'] = features.apply(lambda x: np.abs(stats.zscore(x)).max(), axis=1)

if len(player_stats) >= 10:
    iso = IsolationForest(contamination=0.1, random_state=42)
    player_stats['anomaly'] = iso.fit_predict(features) == -1
else:
    player_stats['anomaly'] = False

player_stats['risk_score'] = (
    (player_stats['zscore_max'] > 3).astype(int) + 
    player_stats['anomaly'].astype(int)
)

high_risk = player_stats[player_stats['risk_score'] >= 1].sort_values('Stake', ascending=False).head(10)
print(f"High-risk players detected: {len(player_stats[player_stats['risk_score']>=1])}")

# Bot Detection (same second)
df['timestamp'] = df['bet_date'].astype(str) + ' ' + df['bet_time'].astype(str)
bot_suspects = df.groupby(['bettor','timestamp']).size().reset_index(name='count')
bot_suspects = bot_suspects[bot_suspects['count'] > 1]
bot_players = bot_suspects['bettor'].unique()
print(f"Bot suspects (same-second bets): {len(bot_players)}")

# Sport breakdown
sport_stats = df.groupby('sports').agg(
    Bets=('bet_id','count'),
    Stake=('usd_amount','sum'),
    GGR=('usd_ggr','sum')
).reset_index()
sport_stats['Hold_%'] = (sport_stats['GGR'] / sport_stats['Stake'] * 100)
sport_stats = sport_stats.sort_values('Stake', ascending=False).head(8)

# Generate PDF
print("\nGenerating PDF report...")
pdf_path = f"outputs/daily_risk_report_{report_date}.pdf"

fig = plt.figure(figsize=(11, 8.5))
fig.suptitle(f'DAILY RISK REPORT — {report_date}', fontsize=18, fontweight='bold', y=0.98)

# Page 1 - Summary
ax1 = plt.subplot(3,2,1)
ax1.axis('off')
summary_text = f"""
EXECUTIVE SUMMARY

Total Bets: {total_bets:,}
Unique Players: {unique_players:,}
Total Stake: ${total_stake:,.2f}
Firm GGR: ${total_ggr:,.2f}
House Hold: {house_hold:.2f}%

High-Risk Players: {len(high_risk)}
Bot Suspects: {len(bot_players)}
"""
ax1.text(0.1, 0.5, summary_text, fontsize=11, verticalalignment='center', 
         family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

# Top risk players table
ax2 = plt.subplot(3,2,2)
ax2.axis('off')
ax2.text(0.5, 0.95, 'TOP 10 RISKIEST PLAYERS', ha='center', fontsize=12, fontweight='bold')
if len(high_risk) > 0:
    table_data = []
    for _, row in high_risk.head(5).iterrows():
        table_data.append([
            row['bettor'][:12]+'...',
            f"{int(row['Bets'])}",
            f"${int(row['Stake']):,}",
            f"{int(row['risk_score'])}"
        ])
    table = ax2.table(cellText=table_data, colLabels=['Bettor','Bets','Stake','Risk'],
                     cellLoc='left', loc='center', bbox=[0.05, 0.1, 0.9, 0.8])
    table.auto_set_font_size(False)
    table.set_fontsize(8)

# Sport breakdown chart
ax3 = plt.subplot(3,2,3)
bars = ax3.barh(sport_stats['sports'], sport_stats['Stake']/1000, color='steelblue')
ax3.set_xlabel('Stake ($1000s)')
ax3.set_title('Stake by Sport', fontweight='bold')
ax3.grid(axis='x', alpha=0.3)
# Add value labels
for i, (bar, val) in enumerate(zip(bars, sport_stats['Stake'])):
    ax3.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
             f'${val/1000:.1f}k', va='center', fontsize=8, fontweight='bold')

# Hold % by sport
ax4 = plt.subplot(3,2,4)
colors = ['red' if x < 0 else 'green' for x in sport_stats['Hold_%']]
bars2 = ax4.barh(sport_stats['sports'], sport_stats['Hold_%'], color=colors)
ax4.set_xlabel('Hold %')
ax4.set_title('House Hold % by Sport', fontweight='bold')
ax4.axvline(0, color='black', linewidth=0.8)
ax4.grid(axis='x', alpha=0.3)
# Add value labels
for i, (bar, val) in enumerate(zip(bars2, sport_stats['Hold_%'])):
    x_pos = bar.get_width() + (2 if val > 0 else -2)
    ha = 'left' if val > 0 else 'right'
    ax4.text(x_pos, bar.get_y() + bar.get_height()/2, 
             f'{val:.1f}%', va='center', ha=ha, fontsize=8, fontweight='bold')

# Bot suspects
ax5 = plt.subplot(3,2,5)
ax5.axis('off')
ax5.text(0.5, 0.95, 'BOT SUSPECTS (Same-Second Bets)', ha='center', fontsize=12, fontweight='bold')
if len(bot_players) > 0:
    bot_data = []
    for bp in bot_players[:5]:
        bot_bets = df[df['bettor'] == bp]
        bot_data.append([bp[:12]+'...', len(bot_bets), bot_bets['sports'].iloc[0]])
    bot_table = ax5.table(cellText=bot_data, colLabels=['Bettor','Bets','Sport'],
                         cellLoc='left', loc='center', bbox=[0.05, 0.1, 0.9, 0.8])
    bot_table.auto_set_font_size(False)
    bot_table.set_fontsize(8)

# Alerts
ax6 = plt.subplot(3,2,6)
ax6.axis('off')
ax6.text(0.5, 0.95, '🚨 ALERTS', ha='center', fontsize=12, fontweight='bold', color='red')
alerts = []
if house_hold < -5:
    alerts.append(f"⚠ Negative hold: {house_hold:.1f}%")
if len(bot_players) > 10:
    alerts.append(f"⚠ {len(bot_players)} bot suspects detected")
if len(high_risk) > 20:
    alerts.append(f"⚠ {len(high_risk)} high-risk players")
if not alerts:
    alerts = ["✓ No critical alerts"]
alert_text = "\n".join(alerts)
ax6.text(0.1, 0.5, alert_text, fontsize=10, verticalalignment='center',
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

plt.tight_layout()
plt.savefig(pdf_path, dpi=150, bbox_inches='tight')
plt.close()

print(f"\n✓ Report saved: {pdf_path}")
print("="*60)
