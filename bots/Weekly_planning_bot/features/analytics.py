import discord
from discord.ext import commands
import logging
import asyncio
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
import io
import numpy as np
from collections import defaultdict

from core.database import get_database
from core.models import TaskCategory, Priority

logger = logging.getLogger('weekly_planning_bot.analytics')

class AnalyticsEngine:
    """Advanced analytics engine for productivity insights"""
    
    def __init__(self):
        self.db = get_database()
    
    async def generate_productivity_trends(self, user_id: int, weeks: int = 8) -> Dict[str, Any]:
        """Generate productivity trends over specified weeks"""
        try:
            analytics_data = await self.db.get_user_analytics(user_id, weeks)
            
            if 'error' in analytics_data:
                return analytics_data
            
            weekly_trends = analytics_data.get('weekly_trends', [])
            
            if not weekly_trends:
                return {'message': 'Not enough data for trend analysis'}
            
            # Calculate trend direction
            completion_rates = [week['completion_rate'] for week in weekly_trends]
            
            # Linear regression for trend
            if len(completion_rates) >= 2:
                x = np.arange(len(completion_rates))
                z = np.polyfit(x, completion_rates, 1)
                trend_slope = z[0]
                
                if trend_slope > 0.02:
                    trend_direction = "📈 Improving"
                    trend_color = discord.Color.green()
                elif trend_slope < -0.02:
                    trend_direction = "📉 Declining"
                    trend_color = discord.Color.red()
                else:
                    trend_direction = "➡️ Stable"
                    trend_color = discord.Color.blue()
            else:
                trend_direction = "➡️ Stable"
                trend_color = discord.Color.blue()
                trend_slope = 0
            
            # Productivity score calculation
            avg_completion = analytics_data.get('average_completion_rate', 0)
            consistency_score = self._calculate_consistency(completion_rates)
            productivity_score = (avg_completion * 0.7) + (consistency_score * 0.3)
            
            # Predictions for next week
            if len(completion_rates) >= 3:
                predicted_completion = completion_rates[-1] + trend_slope
                predicted_completion = max(0, min(1, predicted_completion))  # Clamp between 0 and 1
            else:
                predicted_completion = avg_completion
            
            return {
                'weeks_analyzed': len(weekly_trends),
                'average_completion_rate': avg_completion,
                'trend_direction': trend_direction,
                'trend_color': trend_color,
                'trend_slope': trend_slope,
                'productivity_score': productivity_score,
                'consistency_score': consistency_score,
                'predicted_next_week': predicted_completion,
                'weekly_data': weekly_trends,
                'completion_rates': completion_rates,
                **analytics_data
            }
            
        except Exception as e:
            logger.error(f"Error generating productivity trends: {e}")
            return {'error': str(e)}
    
    def _calculate_consistency(self, values: List[float]) -> float:
        """Calculate consistency score (0-1, higher is more consistent)"""
        if len(values) < 2:
            return 1.0
        
        std_dev = np.std(values)
        # Normalize standard deviation to 0-1 scale (lower std = higher consistency)
        consistency = max(0, 1 - (std_dev * 2))
        return consistency
    
    async def generate_time_analysis(self, user_id: int, weeks: int = 4) -> Dict[str, Any]:
        """Analyze time allocation and usage patterns"""
        try:
            # Get user's weekly plans for analysis
            analytics_data = await self.db.get_user_analytics(user_id, weeks)
            
            if not analytics_data or 'day_completion' not in analytics_data:
                return {'message': 'Not enough data for time analysis'}
            
            day_completion = analytics_data['day_completion']
            
            # Analyze daily patterns
            weekday_avg = 0
            weekend_avg = 0
            weekday_count = 0
            weekend_count = 0
            
            weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            weekends = ['Saturday', 'Sunday']
            
            for day, stats in day_completion.items():
                if day in weekdays:
                    weekday_avg += stats['rate']
                    weekday_count += 1
                elif day in weekends:
                    weekend_avg += stats['rate']
                    weekend_count += 1
            
            weekday_avg = weekday_avg / weekday_count if weekday_count > 0 else 0
            weekend_avg = weekend_avg / weekend_count if weekend_count > 0 else 0
            
            # Work-life balance analysis
            category_breakdown = analytics_data.get('category_breakdown', {})
            
            work_categories = ['work']
            personal_categories = ['health', 'personal', 'learning', 'social']
            life_categories = ['family', 'chores', 'general']
            
            work_tasks = sum(cat.get('total', 0) for name, cat in category_breakdown.items() if name in work_categories)
            personal_tasks = sum(cat.get('total', 0) for name, cat in category_breakdown.items() if name in personal_categories)
            life_tasks = sum(cat.get('total', 0) for name, cat in category_breakdown.items() if name in life_categories)
            
            total_tasks = work_tasks + personal_tasks + life_tasks
            
            if total_tasks > 0:
                work_ratio = work_tasks / total_tasks
                personal_ratio = personal_tasks / total_tasks
                life_ratio = life_tasks / total_tasks
            else:
                work_ratio = personal_ratio = life_ratio = 0
            
            # Balance assessment
            if work_ratio > 0.6:
                balance_assessment = "⚠️ Work-heavy - consider more personal time"
                balance_color = discord.Color.orange()
            elif personal_ratio < 0.2:
                balance_assessment = "💡 Low personal development - add learning/health goals"
                balance_color = discord.Color.yellow()
            elif life_ratio < 0.1:
                balance_assessment = "🏠 Missing life management tasks"
                balance_color = discord.Color.blue()
            else:
                balance_assessment = "✅ Good work-life balance"
                balance_color = discord.Color.green()
            
            return {
                'weekday_performance': weekday_avg,
                'weekend_performance': weekend_avg,
                'work_ratio': work_ratio,
                'personal_ratio': personal_ratio,
                'life_ratio': life_ratio,
                'balance_assessment': balance_assessment,
                'balance_color': balance_color,
                'day_completion': day_completion,
                'category_breakdown': category_breakdown,
                'total_tasks_analyzed': total_tasks
            }
            
        except Exception as e:
            logger.error(f"Error in time analysis: {e}")
            return {'error': str(e)}
    
    async def generate_goal_tracking(self, user_id: int, weeks: int = 12) -> Dict[str, Any]:
        """Track goal achievement patterns and provide insights"""
        try:
            # This would ideally parse goals from weekly plans and track completion
            # For now, we'll use task completion as a proxy for goal achievement
            
            analytics_data = await self.db.get_user_analytics(user_id, weeks)
            
            if not analytics_data or 'weekly_trends' not in analytics_data:
                return {'message': 'Not enough data for goal tracking'}
            
            weekly_trends = analytics_data['weekly_trends']
            
            # Goal achievement simulation (in real implementation, this would parse actual goals)
            goal_patterns = []
            achievement_rates = []
            
            for week_data in weekly_trends:
                completion_rate = week_data['completion_rate']
                
                # Simulate goal achievement based on completion rate
                if completion_rate >= 0.8:
                    achievement = "Exceeded"
                elif completion_rate >= 0.6:
                    achievement = "Met"
                elif completion_rate >= 0.4:
                    achievement = "Partially Met"
                else:
                    achievement = "Not Met"
                
                goal_patterns.append({
                    'week': week_data['week'],
                    'achievement': achievement,
                    'completion_rate': completion_rate
                })
                
                achievement_rates.append(completion_rate)
            
            # Calculate goal achievement statistics
            exceeded_count = sum(1 for g in goal_patterns if g['achievement'] == "Exceeded")
            met_count = sum(1 for g in goal_patterns if g['achievement'] == "Met")
            partial_count = sum(1 for g in goal_patterns if g['achievement'] == "Partially Met")
            not_met_count = sum(1 for g in goal_patterns if g['achievement'] == "Not Met")
            
            total_weeks = len(goal_patterns)
            
            # Goal setting recommendations
            avg_achievement = sum(achievement_rates) / len(achievement_rates) if achievement_rates else 0
            
            if avg_achievement > 0.85:
                recommendation = "🎯 You're consistently exceeding goals! Consider setting more ambitious targets."
            elif avg_achievement > 0.65:
                recommendation = "✅ Great goal achievement! Keep up the momentum."
            elif avg_achievement > 0.45:
                recommendation = "📈 Good progress! Try breaking down larger goals into smaller tasks."
            else:
                recommendation = "💡 Consider setting smaller, more achievable goals to build momentum."
            
            return {
                'weeks_tracked': total_weeks,
                'average_achievement_rate': avg_achievement,
                'exceeded_goals': exceeded_count,
                'met_goals': met_count,
                'partial_goals': partial_count,
                'not_met_goals': not_met_count,
                'goal_patterns': goal_patterns,
                'recommendation': recommendation,
                'achievement_trend': self._calculate_trend(achievement_rates)
            }
            
        except Exception as e:
            logger.error(f"Error in goal tracking: {e}")
            return {'error': str(e)}
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "Stable"
        
        recent_avg = sum(values[-3:]) / min(3, len(values))
        early_avg = sum(values[:3]) / min(3, len(values))
        
        diff = recent_avg - early_avg
        
        if diff > 0.1:
            return "Improving"
        elif diff < -0.1:
            return "Declining"
        else:
            return "Stable"
    
    async def create_productivity_chart(self, user_id: int, weeks: int = 8) -> Optional[io.BytesIO]:
        """Create a productivity chart image"""
        try:
            analytics_data = await self.generate_productivity_trends(user_id, weeks)
            
            if 'error' in analytics_data or 'weekly_data' not in analytics_data:
                return None
            
            weekly_data = analytics_data['weekly_data']
            
            # Prepare data for plotting
            dates = [datetime.strptime(week['week'], '%Y-%m-%d') for week in weekly_data]
            completion_rates = [week['completion_rate'] * 100 for week in weekly_data]
            
            # Create figure
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            fig.suptitle('📊 Productivity Analytics Dashboard', fontsize=16, fontweight='bold')
            
            # Plot 1: Completion Rate Trend
            ax1.plot(dates, completion_rates, marker='o', linewidth=2, markersize=6, color='#5865F2')
            ax1.fill_between(dates, completion_rates, alpha=0.3, color='#5865F2')
            ax1.set_title('Weekly Completion Rate Trend', fontweight='bold')
            ax1.set_ylabel('Completion Rate (%)')
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(0, 100)
            
            # Add trend line
            if len(completion_rates) >= 2:
                x_numeric = range(len(dates))
                z = np.polyfit(x_numeric, completion_rates, 1)
                p = np.poly1d(z)
                ax1.plot(dates, p(x_numeric), "--", alpha=0.8, color='red', linewidth=2)
            
            # Format x-axis
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax1.xaxis.set_major_locator(mdates.WeekdayLocator())
            
            # Plot 2: Task Volume
            task_counts = [week['total_tasks'] for week in weekly_data]
            ax2.bar(dates, task_counts, alpha=0.7, color='#57F287', width=5)
            ax2.set_title('Weekly Task Volume', fontweight='bold')
            ax2.set_ylabel('Number of Tasks')
            ax2.set_xlabel('Week')
            ax2.grid(True, alpha=0.3)
            
            # Format x-axis
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax2.xaxis.set_major_locator(mdates.WeekdayLocator())
            
            plt.tight_layout()
            
            # Save to bytes
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plt.close(fig)
            
            return buffer
            
        except Exception as e:
            logger.error(f"Error creating productivity chart: {e}")
            return None

class AnalyticsCog(commands.Cog):
    """Analytics command cog"""
    
    def __init__(self, bot):
        self.bot = bot
        self.analytics = AnalyticsEngine()
        self.db = get_database()
    
    @commands.command(name="analytics", aliases=["stats", "insights"])
    async def analytics_dashboard(self, ctx, report_type: str = "overview", weeks: int = 8):
        """Advanced analytics dashboard
        
        Usage:
        !analytics - Full productivity dashboard
        !analytics trends [weeks] - Productivity trends
        !analytics time [weeks] - Time allocation analysis
        !analytics goals [weeks] - Goal tracking insights
        !analytics chart [weeks] - Visual productivity chart
        """
        try:
            user = await self.db.get_or_create_user(str(ctx.author.id), ctx.author.display_name)
            
            if report_type == "chart":
                await self.send_productivity_chart(ctx, user['id'], weeks)
                return
            
            if report_type == "trends":
                await self.send_trends_report(ctx, user['id'], weeks)
                return
            
            if report_type == "time":
                await self.send_time_analysis(ctx, user['id'], weeks)
                return
            
            if report_type == "goals":
                await self.send_goals_report(ctx, user['id'], weeks)
                return
            
            # Default: comprehensive overview
            await self.send_comprehensive_dashboard(ctx, user['id'], weeks)
            
        except Exception as e:
            logger.error(f"Error in analytics dashboard: {e}")
            await ctx.send("❌ Error generating analytics. Please try again.")
    
    async def send_comprehensive_dashboard(self, ctx, user_id: int, weeks: int):
        """Send comprehensive analytics dashboard"""
        try:
            # Generate all analytics
            trends = await self.analytics.generate_productivity_trends(user_id, weeks)
            time_analysis = await self.analytics.generate_time_analysis(user_id, min(weeks, 4))
            goals = await self.analytics.generate_goal_tracking(user_id, min(weeks, 12))
            
            # Create main embed
            embed = discord.Embed(
                title="📊 Comprehensive Analytics Dashboard",
                description=f"Your productivity insights for the last {weeks} weeks",
                color=discord.Color.blue()
            )
            
            # Productivity Overview
            if 'average_completion_rate' in trends:
                avg_completion = trends['average_completion_rate']
                productivity_score = trends.get('productivity_score', 0)
                consistency = trends.get('consistency_score', 0)
                
                embed.add_field(
                    name="🎯 Productivity Overview",
                    value=f"**Average Completion:** {avg_completion:.1%}\n"
                          f"**Productivity Score:** {productivity_score:.1%}\n"
                          f"**Consistency:** {consistency:.1%}\n"
                          f"**Trend:** {trends.get('trend_direction', 'Unknown')}",
                    inline=True
                )
            
            # Time Allocation
            if 'work_ratio' in time_analysis:
                work_ratio = time_analysis['work_ratio']
                personal_ratio = time_analysis['personal_ratio']
                life_ratio = time_analysis['life_ratio']
                
                embed.add_field(
                    name="⏰ Time Allocation",
                    value=f"**Work:** {work_ratio:.1%}\n"
                          f"**Personal:** {personal_ratio:.1%}\n"
                          f"**Life:** {life_ratio:.1%}\n"
                          f"**Balance:** {time_analysis.get('balance_assessment', 'Unknown')[:20]}...",
                    inline=True
                )
            
            # Goal Achievement
            if 'average_achievement_rate' in goals:
                goal_rate = goals['average_achievement_rate']
                exceeded = goals.get('exceeded_goals', 0)
                met = goals.get('met_goals', 0)
                
                embed.add_field(
                    name="🏆 Goal Achievement",
                    value=f"**Achievement Rate:** {goal_rate:.1%}\n"
                          f"**Exceeded:** {exceeded} weeks\n"
                          f"**Met:** {met} weeks\n"
                          f"**Trend:** {goals.get('achievement_trend', 'Unknown')}",
                    inline=True
                )
            
            # Daily Performance
            if 'day_completion' in trends:
                day_completion = trends['day_completion']
                best_day = trends.get('most_productive_day')
                worst_day = trends.get('least_productive_day')
                
                if best_day and worst_day:
                    embed.add_field(
                        name="📅 Daily Performance",
                        value=f"**Best Day:** {best_day}\n"
                              f"**Needs Work:** {worst_day}\n"
                              f"**Weekday Avg:** {time_analysis.get('weekday_performance', 0):.1%}\n"
                              f"**Weekend Avg:** {time_analysis.get('weekend_performance', 0):.1%}",
                        inline=True
                    )
            
            # Category Breakdown
            if 'category_breakdown' in trends:
                category_breakdown = trends['category_breakdown']
                top_categories = sorted(
                    category_breakdown.items(),
                    key=lambda x: x[1].get('total', 0),
                    reverse=True
                )[:3]
                
                category_text = ""
                for category, stats in top_categories:
                    emoji = TaskCategory.get_emoji(category)
                    rate = stats.get('completed', 0) / stats.get('total', 1)
                    category_text += f"{emoji} {category.title()}: {rate:.0%}\n"
                
                if category_text:
                    embed.add_field(
                        name="📂 Top Categories",
                        value=category_text,
                        inline=True
                    )
            
            # Predictions & Recommendations
            predictions = ""
            if 'predicted_next_week' in trends:
                predicted = trends['predicted_next_week']
                predictions += f"**Next Week:** {predicted:.1%} completion predicted\n"
            
            if 'recommendation' in goals:
                recommendations = goals['recommendation'][:50] + "..."
                predictions += f"**Tip:** {recommendations}"
            
            if predictions:
                embed.add_field(
                    name="🔮 Insights & Predictions",
                    value=predictions,
                    inline=False
                )
            
            embed.set_footer(
                text="💡 Use !analytics trends/time/goals/chart for detailed reports"
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in comprehensive dashboard: {e}")
            await ctx.send("❌ Error generating comprehensive dashboard.")
    
    async def send_productivity_chart(self, ctx, user_id: int, weeks: int):
        """Send productivity chart visualization"""
        try:
            await ctx.send("📊 Generating your productivity chart...")
            
            chart_buffer = await self.analytics.create_productivity_chart(user_id, weeks)
            
            if chart_buffer:
                file = discord.File(chart_buffer, filename="productivity_chart.png")
                
                embed = discord.Embed(
                    title="📈 Your Productivity Trends",
                    description=f"Visual analysis of your last {weeks} weeks",
                    color=discord.Color.green()
                )
                embed.set_image(url="attachment://productivity_chart.png")
                
                await ctx.send(embed=embed, file=file)
            else:
                await ctx.send("❌ Could not generate productivity chart. Not enough data.")
                
        except Exception as e:
            logger.error(f"Error sending productivity chart: {e}")
            await ctx.send("❌ Error generating chart.")
    
    async def send_trends_report(self, ctx, user_id: int, weeks: int):
        """Send detailed trends report"""
        try:
            trends = await self.analytics.generate_productivity_trends(user_id, weeks)
            
            if 'error' in trends:
                await ctx.send(f"❌ {trends['error']}")
                return
            
            if 'message' in trends:
                await ctx.send(f"ℹ️ {trends['message']}")
                return
            
            embed = discord.Embed(
                title="📈 Productivity Trends Analysis",
                description=f"Detailed trends for the last {weeks} weeks",
                color=trends.get('trend_color', discord.Color.blue())
            )
            
            # Trend summary
            embed.add_field(
                name="📊 Trend Summary",
                value=f"**Direction:** {trends.get('trend_direction', 'Unknown')}\n"
                      f"**Average Completion:** {trends.get('average_completion_rate', 0):.1%}\n"
                      f"**Productivity Score:** {trends.get('productivity_score', 0):.1%}\n"
                      f"**Consistency:** {trends.get('consistency_score', 0):.1%}",
                inline=False
            )
            
            # Weekly breakdown
            weekly_data = trends.get('weekly_data', [])
            if weekly_data:
                recent_weeks = weekly_data[-4:]  # Last 4 weeks
                weekly_text = ""
                for week in recent_weeks:
                    week_date = datetime.strptime(week['week'], '%Y-%m-%d').strftime('%m/%d')
                    completion = week['completion_rate']
                    bar = "█" * int(completion * 10) + "░" * (10 - int(completion * 10))
                    weekly_text += f"Week {week_date}: {completion:.1%} {bar}\n"
                
                embed.add_field(
                    name="📅 Recent Weeks",
                    value=weekly_text,
                    inline=False
                )
            
            # Predictions
            if 'predicted_next_week' in trends:
                predicted = trends['predicted_next_week']
                embed.add_field(
                    name="🔮 Next Week Prediction",
                    value=f"Based on your trends, you're likely to achieve **{predicted:.1%}** completion next week.",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in trends report: {e}")
            await ctx.send("❌ Error generating trends report.")

async def setup(bot):
    """Set up the Analytics cog"""
    await bot.add_cog(AnalyticsCog(bot)) 