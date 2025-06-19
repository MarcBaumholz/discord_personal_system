#!/usr/bin/env python3
"""
Chart Generator for Monthly Calorie Reports
Creates beautiful visualizations of calorie data using matplotlib
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from datetime import datetime, date
from typing import Dict, Any, Optional
import os
from calendar import monthrange
import locale

# Set German locale for month names (fallback to English if not available)
try:
    locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'German')
    except locale.Error:
        pass  # Keep English locale

class CalorieChartGenerator:
    """Generates charts and visualizations for calorie data"""
    
    def __init__(self):
        # Set up matplotlib style
        plt.style.use('default')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.alpha'] = 0.3
        
    def create_monthly_chart(self, df: pd.DataFrame, stats: Dict[str, Any], output_path: str) -> bool:
        """
        Create a comprehensive monthly calorie chart
        
        Args:
            df: DataFrame with 'date' and 'calories' columns
            stats: Dictionary with monthly statistics
            output_path: Path to save the chart image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if df.empty:
                print("⚠️ No data to plot")
                return False
            
            # Create figure with subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[3, 1])
            
            # Convert date column to datetime if needed
            df['date'] = pd.to_datetime(df['date'])
            
            # Main chart - Daily calories
            ax1.plot(df['date'], df['calories'], 
                    marker='o', linewidth=2, markersize=6, 
                    color='#2E8B57', markerfacecolor='#32CD32', 
                    markeredgecolor='#2E8B57', markeredgewidth=1)
            
            # Add average line
            avg_calories = stats['average_daily']
            ax1.axhline(y=avg_calories, color='#FF6B6B', linestyle='--', 
                       linewidth=2, alpha=0.8, label=f'Durchschnitt: {avg_calories} kcal')
            
            # Customize main chart
            ax1.set_title(f'📊 Tägliche Kalorienaufnahme - {stats["username"]} '
                         f'({self._get_month_name(stats["month"])} {stats["year"]})',
                         fontsize=16, fontweight='bold', pad=20)
            ax1.set_ylabel('Kalorien (kcal)', fontsize=12, fontweight='bold')
            ax1.legend(loc='upper right')
            
            # Format x-axis for main chart
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
            ax1.xaxis.set_major_locator(mdates.DayLocator(interval=2))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
            
            # Add value annotations on peaks
            self._add_peak_annotations(ax1, df)
            
            # Summary statistics box
            self._add_stats_box(ax1, stats)
            
            # Secondary chart - Weekly averages
            weekly_data = self._create_weekly_data(df)
            if len(weekly_data) > 1:
                bars = ax2.bar(range(len(weekly_data)), 
                              [w['avg_calories'] for w in weekly_data],
                              color='#87CEEB', alpha=0.7, edgecolor='#4682B4', linewidth=1)
                
                ax2.set_title('📈 Wöchentliche Durchschnittswerte', fontsize=12, fontweight='bold')
                ax2.set_ylabel('Ø Kalorien', fontsize=10)
                ax2.set_xlabel('Woche im Monat', fontsize=10)
                ax2.set_xticks(range(len(weekly_data)))
                ax2.set_xticklabels([f'Woche {i+1}' for i in range(len(weekly_data))])
                
                # Add value labels on bars
                for i, (bar, week_data) in enumerate(zip(bars, weekly_data)):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height + 20,
                            f'{int(height)}', ha='center', va='bottom', fontsize=9)
            
            # Overall styling
            fig.suptitle(f'🍽️ Monatsbericht Kalorienaufnahme', 
                        fontsize=18, fontweight='bold', y=0.98)
            
            plt.tight_layout()
            plt.subplots_adjust(top=0.93, hspace=0.3)
            
            # Save the chart
            plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            print(f"✅ Chart saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating chart: {e}")
            return False
    
    def _add_peak_annotations(self, ax, df: pd.DataFrame):
        """Add annotations for highest and lowest calorie days"""
        try:
            if len(df) < 2:
                return
                
            max_idx = df['calories'].idxmax()
            min_idx = df['calories'].idxmin()
            
            max_date = df.loc[max_idx, 'date']
            max_cal = df.loc[max_idx, 'calories']
            min_date = df.loc[min_idx, 'date']
            min_cal = df.loc[min_idx, 'calories']
            
            # Highest point
            ax.annotate(f'Höchster Tag\n{max_cal} kcal', 
                       xy=(max_date, max_cal), xytext=(10, 20),
                       textcoords='offset points', fontsize=9,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFE4B5', alpha=0.8),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
            
            # Lowest point (only if significantly different)
            if max_cal - min_cal > 200:  # Only annotate if difference is significant
                ax.annotate(f'Niedrigster Tag\n{min_cal} kcal', 
                           xy=(min_date, min_cal), xytext=(10, -30),
                           textcoords='offset points', fontsize=9,
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='#E6E6FA', alpha=0.8),
                           arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        except Exception as e:
            print(f"⚠️ Error adding annotations: {e}")
    
    def _add_stats_box(self, ax, stats: Dict[str, Any]):
        """Add a statistics box to the chart"""
        try:
            stats_text = f"""📊 Monatsstatistiken:
• Gesamtkalorien: {stats['total_calories']:,} kcal
• Durchschnitt/Tag: {stats['average_daily']} kcal
• Höchster Tag: {stats['max_daily']} kcal
• Niedrigster Tag: {stats['min_daily']} kcal
• Getrackte Tage: {stats['days_tracked']}"""
            
            # Position box in upper left corner
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                   fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='#F0F8FF', alpha=0.9))
        except Exception as e:
            print(f"⚠️ Error adding stats box: {e}")
    
    def _create_weekly_data(self, df: pd.DataFrame) -> list:
        """Create weekly summary data"""
        try:
            df['week'] = df['date'].dt.isocalendar().week
            weekly_groups = df.groupby('week')
            
            weekly_data = []
            for week_num, group in weekly_groups:
                weekly_data.append({
                    'week': week_num,
                    'avg_calories': int(group['calories'].mean()),
                    'total_calories': int(group['calories'].sum()),
                    'days': len(group)
                })
            
            return weekly_data
        except Exception as e:
            print(f"⚠️ Error creating weekly data: {e}")
            return []
    
    def _get_month_name(self, month: int) -> str:
        """Get German month name"""
        month_names = {
            1: 'Januar', 2: 'Februar', 3: 'März', 4: 'April',
            5: 'Mai', 6: 'Juni', 7: 'Juli', 8: 'August',
            9: 'September', 10: 'Oktober', 11: 'November', 12: 'Dezember'
        }
        return month_names.get(month, f'Monat {month}')
    
    def create_comparison_chart(self, current_stats: Dict[str, Any], 
                              previous_stats: Dict[str, Any], output_path: str) -> bool:
        """
        Create a comparison chart between current and previous month
        
        Args:
            current_stats: Current month statistics
            previous_stats: Previous month statistics  
            output_path: Path to save the chart
            
        Returns:
            True if successful, False otherwise
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            categories = ['Gesamtkalorien', 'Durchschnitt/Tag', 'Höchster Tag', 'Getrackte Tage']
            current_values = [
                current_stats['total_calories'], 
                current_stats['average_daily'],
                current_stats['max_daily'],
                current_stats['days_tracked']
            ]
            previous_values = [
                previous_stats['total_calories'], 
                previous_stats['average_daily'],
                previous_stats['max_daily'],
                previous_stats['days_tracked']
            ]
            
            x = range(len(categories))
            width = 0.35
            
            bars1 = ax.bar([i - width/2 for i in x], current_values, width, 
                          label=f'{self._get_month_name(current_stats["month"])} {current_stats["year"]}',
                          color='#32CD32', alpha=0.8)
            bars2 = ax.bar([i + width/2 for i in x], previous_values, width,
                          label=f'{self._get_month_name(previous_stats["month"])} {previous_stats["year"]}',
                          color='#87CEEB', alpha=0.8)
            
            ax.set_xlabel('Kategorien')
            ax.set_ylabel('Werte')
            ax.set_title(f'📊 Monatsvergleich - {current_stats["username"]}', 
                        fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(categories)
            ax.legend()
            
            # Add value labels on bars
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}', ha='center', va='bottom')
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Comparison chart saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating comparison chart: {e}")
            return False

# Test function
def test_chart_generation():
    """Test function for chart generation"""
    try:
        # Create test data
        test_dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        test_calories = [1800 + (i % 7) * 200 + (i % 3) * 100 for i in range(len(test_dates))]
        
        df = pd.DataFrame({
            'date': test_dates,
            'calories': test_calories
        })
        
        stats = {
            'username': 'TestUser',
            'month': 1,
            'year': 2024,
            'total_calories': sum(test_calories),
            'average_daily': int(sum(test_calories) / len(test_calories)),
            'max_daily': max(test_calories),
            'min_daily': min(test_calories),
            'days_tracked': len(test_calories)
        }
        
        generator = CalorieChartGenerator()
        success = generator.create_monthly_chart(df, stats, 'test_chart.png')
        
        if success:
            print("✅ Test chart generation successful!")
            print(f"📊 Test stats: {stats}")
        else:
            print("❌ Test chart generation failed")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_chart_generation() 