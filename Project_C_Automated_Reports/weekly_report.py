
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches
from scipy import stats

print("="*70)
print("WEEKLY EXECUTIVE SUMMARY GENERATOR")
print("="*70)

# Load week's data
print("\nLoading weekly data...")
df = pd.read_excel("weekly_data.xlsx.xlsx", sheet_name="Query result")
print(f"Loaded {len(df):,} bets")

# Parse dates
df['bet_date'] = pd.to_datetime(df['bet_date'])
df['day_name'] = df['bet_date'].dt.day_name()
df['date_only'] = df['bet_date'].dt.date

week_start = df['bet_date'].min()
week_end = df['bet_date'].max()
week_num = week_start.isocalendar()[1]
year = week_start.year

print(f"Week: {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}")
print(f"Week #{week_num}")

# Overall KPIs
total_bets = len(df)
unique_players = df['bettor'].nunique()
total_stake = df['usd_amount'].sum()
total_ggr = df['usd_ggr'].sum()
house_hold = (total_ggr / total_stake * 100) if total_stake > 0 else 0

print(f"\nWEEK SUMMARY:")
print(f"  Bets: {total_bets:,}")
print(f"  Players: {unique_players:,}")
print(f"  Stake: ${total_stake:,.2f}")
print(f"  GGR: ${total_ggr:,.2f}")
print(f"  Hold: {house_hold:.2f}%")

# Daily breakdown
daily = df.groupby('date_only').agg(
    Bets=('bet_id','count'),
    Players=('bettor','nunique'),
    Stake=('usd_amount','sum'),
    GGR=('usd_ggr','sum')
).reset_index()
daily['Hold_%'] = (daily['GGR'] / daily['Stake'] * 100)
daily['Day'] = pd.to_datetime(daily['date_only']).dt.day_name()

print("\nDAILY BREAKDOWN:")
print(daily[['Day','Bets','Stake','GGR','Hold_%']].to_string(index=False))

# Player stats
player_stats = df.groupby('bettor').agg(
    Bets=('bet_id','count'),
    Stake=('usd_amount','sum'),
    GGR=('usd_ggr','sum'),
    Win_Rate=('usd_ggr', lambda x: (x<0).sum()/len(x)*100),
).reset_index()
player_stats['Profit'] = -player_stats['GGR']

# High-risk players (top 15)
high_risk = player_stats[player_stats['Profit'] > 500].sort_values('Profit', ascending=False).head(15)
print(f"\nHigh-profit players (>$500): {len(player_stats[player_stats['Profit']>500])}")

# Sport analysis
sport_stats = df.groupby('sports').agg(
    Bets=('bet_id','count'),
    Stake=('usd_amount','sum'),
    GGR=('usd_ggr','sum')
).reset_index()
sport_stats['Hold_%'] = (sport_stats['GGR'] / sport_stats['Stake'] * 100)
sport_stats['Loss'] = -sport_stats[sport_stats['GGR']<0]['GGR']
sport_stats = sport_stats.sort_values('Stake', ascending=False)

top_losses_sport = sport_stats[sport_stats['GGR']<0].sort_values('GGR').head(5)

# League analysis
league_stats = df.groupby('league').agg(
    Bets=('bet_id','count'),
    Stake=('usd_amount','sum'),
    GGR=('usd_ggr','sum')
).reset_index()
league_stats['Hold_%'] = (league_stats['GGR'] / league_stats['Stake'] * 100)
top_losses_league = league_stats[league_stats['GGR']<0].sort_values('GGR').head(10)

# Market analysis
market_stats = df.groupby('market').agg(
    Bets=('bet_id','count'),
    Stake=('usd_amount','sum'),
    GGR=('usd_ggr','sum')
).reset_index()
market_stats['Hold_%'] = (market_stats['GGR'] / market_stats['Stake'] * 100)
top_losses_market = market_stats[market_stats['GGR']<0].sort_values('GGR').head(5)

# Bot detection
df['timestamp'] = df['bet_date'].astype(str) + ' ' + df['bet_time'].astype(str)
bot_suspects = df.groupby(['bettor','timestamp']).size().reset_index(name='count')
bot_suspects = bot_suspects[bot_suspects['count'] > 1]
bot_count = bot_suspects['bettor'].nunique()

print(f"Bot suspects: {bot_count}")

# Generate PDF
print("\nGenerating Weekly Executive Summary PDF...")
pdf_path = f"outputs/weekly_executive_summary_{year}_W{week_num}.pdf"

with PdfPages(pdf_path) as pdf:
    # PAGE 1 - Overview
    fig = plt.figure(figsize=(11, 8.5))
    fig.suptitle(f'WEEKLY EXECUTIVE SUMMARY — Week {week_num}, {year}', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # Week info
    ax1 = plt.subplot(4,2,1)
    ax1.axis('off')
    info_text = f"""
WEEK OVERVIEW
{week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}

Total Bets: {total_bets:,}
Unique Players: {unique_players:,}
Total Stake: ${total_stake:,.2f}
Firm GGR: ${total_ggr:,.2f}
House Hold: {house_hold:.2f}%

Avg Daily Bets: {int(total_bets/7):,}
Avg Daily Stake: ${total_stake/7:,.2f}
"""
    ax1.text(0.05, 0.5, info_text, fontsize=10, verticalalignment='center',
             family='monospace', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    
    # Daily trend - Bets
    ax2 = plt.subplot(4,2,2)
    ax2.plot(daily['Day'], daily['Bets'], marker='o', linewidth=2, markersize=6, color='steelblue')
    ax2.set_title('Daily Bet Volume', fontweight='bold', fontsize=11)
    ax2.set_ylabel('Bets')
    ax2.grid(alpha=0.3)
    ax2.tick_params(axis='x', rotation=45)
    
    # Daily trend - Hold %
    ax3 = plt.subplot(4,2,3)
    colors_hold = ['red' if x<0 else 'green' for x in daily['Hold_%']]
    ax3.bar(daily['Day'], daily['Hold_%'], color=colors_hold, alpha=0.7)
    ax3.axhline(0, color='black', linewidth=0.8)
    ax3.set_title('Daily House Hold %', fontweight='bold', fontsize=11)
    ax3.set_ylabel('Hold %')
    ax3.grid(axis='y', alpha=0.3)
    ax3.tick_params(axis='x', rotation=45)
    
    # Top 5 losses by sport
    ax4 = plt.subplot(4,2,4)
    if len(top_losses_sport) > 0:
        bars = ax4.barh(top_losses_sport['sports'], -top_losses_sport['GGR']/1000, color='red', alpha=0.7)
        ax4.set_xlabel('Firm Loss ($1000s)')
        ax4.set_title('Top 5 Losses by Sport', fontweight='bold', fontsize=11)
        for bar, val in zip(bars, -top_losses_sport['GGR']):
            ax4.text(bar.get_width()+0.1, bar.get_y()+bar.get_height()/2, 
                    f'${val/1000:.1f}k', va='center', fontsize=8)
    
    # High-profit players table
    ax5 = plt.subplot(4,2,(5,6))
    ax5.axis('off')
    ax5.text(0.5, 0.98, 'TOP 10 WINNING PLAYERS (Firm Loss)', ha='center', 
             fontsize=11, fontweight='bold')
    if len(high_risk) > 0:
        table_data = []
        for _, row in high_risk.head(10).iterrows():
            table_data.append([
                row['bettor'][:14]+'...',
                f"{int(row['Bets'])}",
                f"${int(row['Stake']):,}",
                f"${int(row['Profit']):,}"
            ])
        table = ax5.table(cellText=table_data, 
                         colLabels=['Bettor','Bets','Stake','Player Profit'],
                         cellLoc='left', loc='center', bbox=[0.05, 0.05, 0.9, 0.85])
        table.auto_set_font_size(False)
        table.set_fontsize(8)
    
    # Alerts
    ax6 = plt.subplot(4,2,(7,8))
    ax6.axis('off')
    ax6.text(0.5, 0.95, '🚨 WEEK ALERTS & RECOMMENDATIONS', ha='center', 
             fontsize=11, fontweight='bold', color='red')
    
    alerts = []
    if house_hold < 0:
        alerts.append(f"⚠ NEGATIVE WEEK: {house_hold:.1f}% hold - firm lost ${-total_ggr:,.0f}")
    if bot_count > 50:
        alerts.append(f"⚠ HIGH BOT ACTIVITY: {bot_count} suspects detected")
    if len(high_risk) > 30:
        alerts.append(f"⚠ {len(high_risk)} players won >$500 this week")
    
    # Recommendations
    recs = []
    if len(top_losses_sport) > 0:
        worst_sport = top_losses_sport.iloc[0]
        recs.append(f"📍 Review {worst_sport['sports']} odds (lost ${-worst_sport['GGR']:,.0f})")
    if house_hold < 3:
        recs.append("📍 Overall hold below target - tighten margins")
    if bot_count > 20:
        recs.append(f"📍 Investigate {bot_count} bot suspects")
    
    alert_text = "\n".join(alerts) + "\n\nRECOMMENDATIONS:\n" + "\n".join(recs)
    if not alerts:
        alert_text = "✓ No critical alerts this week\n\nRECOMMENDATIONS:\n" + "\n".join(recs)
    
    ax6.text(0.05, 0.75, alert_text, fontsize=9, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    plt.tight_layout()
    pdf.savefig(fig, dpi=150, bbox_inches='tight')
    plt.close()
    
    # PAGE 2 - League & Market Analysis
    fig2 = plt.figure(figsize=(11, 8.5))
    fig2.suptitle(f'LEAGUE & MARKET ANALYSIS — Week {week_num}', 
                  fontsize=16, fontweight='bold', y=0.98)
    
    # Top losses by league
    ax7 = plt.subplot(2,1,1)
    if len(top_losses_league) > 0:
        bars = ax7.barh(top_losses_league['league'], -top_losses_league['GGR']/1000, 
                       color='darkred', alpha=0.7)
        ax7.set_xlabel('Firm Loss ($1000s)')
        ax7.set_title('Top 10 Leagues by Loss', fontweight='bold')
        ax7.grid(axis='x', alpha=0.3)
        for bar, val in zip(bars, -top_losses_league['GGR']):
            ax7.text(bar.get_width()+0.2, bar.get_y()+bar.get_height()/2,
                    f'${val/1000:.1f}k', va='center', fontsize=8, fontweight='bold')
    
    # Top losses by market
    ax8 = plt.subplot(2,1,2)
    if len(top_losses_market) > 0:
        bars = ax8.barh(top_losses_market['market'], -top_losses_market['GGR']/1000,
                       color='orange', alpha=0.7)
        ax8.set_xlabel('Firm Loss ($1000s)')
        ax8.set_title('Top 5 Markets by Loss', fontweight='bold')
        ax8.grid(axis='x', alpha=0.3)
        for bar, val in zip(bars, -top_losses_market['GGR']):
            ax8.text(bar.get_width()+0.2, bar.get_y()+bar.get_height()/2,
                    f'${val/1000:.1f}k', va='center', fontsize=8, fontweight='bold')
    
    plt.tight_layout()
    pdf.savefig(fig2, dpi=150, bbox_inches='tight')
    plt.close()

print(f"\n✓ Weekly Report saved: {pdf_path}")
print("="*70)
