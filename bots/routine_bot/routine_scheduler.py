import logging
import asyncio
from datetime import datetime, timedelta
import pytz
import discord

logger = logging.getLogger('routine_bot.routine_scheduler')

class RoutineScheduler:
    """Manages the scheduling and posting of routine messages"""
    
    def __init__(self, bot, notion_manager, openrouter_service, channel_id):
        """
        Initialize the routine scheduler
        
        Args:
            bot: Discord bot instance
            notion_manager: NotionManager instance
            openrouter_service: OpenRouterService instance
            channel_id: Discord channel ID to post messages
        """
        self.bot = bot
        self.notion_manager = notion_manager
        self.openrouter_service = openrouter_service
        self.channel_id = channel_id
        self.timezone = pytz.timezone('Europe/Berlin')
        
        # Track the last posted time segments to avoid duplicates
        self.last_posted = {
            'morning': None,
            'afternoon': None,
            'evening': None,
            'daily': None
        }
        
        # Track routine step messages for reactions
        self.routine_step_messages = {}
        
        # Track recently posted routines to avoid duplicates
        self.recently_posted_routines = {}
        self.duplicate_prevention_time = 300  # 5 minutes in seconds
        
        logger.info("Initializing Routine Scheduler")
    
    async def check_and_post_routines(self):
        """Check current time and post routines if needed"""
        now = datetime.now(self.timezone)
        current_hour = now.hour
        
        try:
            # Define time windows for posting
            morning_window = (5, 9)    # 5:00 AM - 9:59 AM
            afternoon_window = (11, 14) # 11:00 AM - 2:59 PM
            evening_window = (16, 20)   # 4:00 PM - 8:59 PM
            
            # Check for scheduled morning routine at 8am
            if current_hour == 8 and now.minute < 5:  # Between 8:00 and 8:04 AM
                if not self._already_posted_today('morning'):
                    await self.post_morning_routine()
                    self.last_posted['morning'] = now.date()
            
            # Check for scheduled evening routine at 10pm
            elif current_hour == 22 and now.minute < 5:  # Between 10:00 and 10:04 PM
                if not self._already_posted_today('evening'):
                    await self.post_evening_routine()
                    self.last_posted['evening'] = now.date()
            
            # Old time window routine checks
            elif morning_window[0] <= current_hour <= morning_window[1]:
                # Check if we've already posted today's morning routine
                if not self._already_posted_today('morning') and current_hour != 8:  # Avoid duplication with 8am check
                    await self.post_routine_for_time('Morning')
                    self.last_posted['morning'] = now.date()
            
            elif afternoon_window[0] <= current_hour <= afternoon_window[1]:
                # Check if we've already posted today's afternoon routine
                if not self._already_posted_today('afternoon'):
                    await self.post_routine_for_time('Afternoon')
                    self.last_posted['afternoon'] = now.date()
            
            elif evening_window[0] <= current_hour <= evening_window[1]:
                # Check if we've already posted today's evening routine
                if not self._already_posted_today('evening') and current_hour != 22:  # Avoid duplication with 10pm check
                    await self.post_routine_for_time('Evening')
                    self.last_posted['evening'] = now.date()
            
            # Check if we need to post a daily summary (done in the early morning)
            if 6 <= current_hour <= 7:
                # Check if we've already posted today's daily summary
                if not self._already_posted_today('daily'):
                    await self.post_todays_routines()
                    self.last_posted['daily'] = now.date()
                    
        except Exception as e:
            logger.error(f"Error in check_and_post_routines: {e}")
    
    def _already_posted_today(self, time_segment):
        """Check if we've already posted a routine for this time segment today"""
        today = datetime.now(self.timezone).date()
        return self.last_posted.get(time_segment) == today
    
    async def process_emoji_reaction(self, message, emoji, user):
        """Process emoji reactions on routine step messages"""
        try:
            # Check if the message is a routine steps message
            message_id = message.id
            if message_id in self.routine_step_messages:
                routine_info = self.routine_step_messages[message_id]
                
                # Get the message type (combined or individual step)
                message_type = routine_info.get('message_type', 'individual')
                
                # Handle reactions based on message type
                if message_type == 'combined':
                    # Handle number emoji reactions (1️⃣, 2️⃣, etc.)
                    number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
                    
                    if emoji.name in number_emojis:
                        # Get the step index from the emoji
                        step_idx = number_emojis.index(emoji.name)
                        
                        if 0 <= step_idx < len(routine_info['steps']):
                            # Toggle the step's completion status
                            routine_info['completed_steps'][step_idx] = not routine_info['completed_steps'][step_idx]
                            
                            # Create updated message content with checkmarks for completed steps
                            await self._update_steps_message(message, routine_info)
                    
                    # Handle checkmark reaction for marking the entire routine as complete
                    elif emoji.name == "✅":
                        # Mark all steps as completed
                        for i in range(len(routine_info['completed_steps'])):
                            routine_info['completed_steps'][i] = True
                            
                        # Update the message with all steps marked
                        await self._update_steps_message(message, routine_info)
                        
                        # Update the routine status in Notion
                        await self.notion_manager.update_routine_status(routine_info['routine_id'], "Completed")
                        
                        # Send a completion message
                        channel = self.bot.get_channel(self.channel_id)
                        if channel:
                            await channel.send(f"🎉 Congratulations! You've completed your **{routine_info['routine_name']}** routine!")
                
                # Legacy handling for individual step messages
                else:
                    # Update progress in tracking dict
                    if emoji.name == "✅":
                        step_idx = int(routine_info['step_idx'])
                        if 0 <= step_idx < len(routine_info['steps']):
                            routine_info['completed_steps'][step_idx] = True
                            
                            # Check if all steps are completed
                            if all(routine_info['completed_steps']):
                                # Update the routine status in Notion
                                await self.notion_manager.update_routine_status(routine_info['routine_id'], "Completed")
                                
                                # Send a completion message
                                channel = self.bot.get_channel(self.channel_id)
                                if channel:
                                    await channel.send(f"🎉 Congratulations! You've completed your **{routine_info['routine_name']}** routine!")
                
        except Exception as e:
            logger.error(f"Error processing emoji reaction: {e}")
    
    async def _update_steps_message(self, message, routine_info):
        """Update the steps message with completed steps marked"""
        try:
            steps = routine_info['steps']
            completed_steps = routine_info['completed_steps']
            
            # Create updated message content
            updated_message = ""
            for i, step in enumerate(steps):
                # Add checkmark for completed steps
                if completed_steps[i]:
                    updated_message += f"✅ {i+1}. {step}\n"
                else:
                    updated_message += f"{i+1}. {step}\n"
            
            # Add progress information
            completed_count = sum(1 for done in completed_steps if done)
            total_count = len(steps)
            percentage = int((completed_count / total_count) * 100) if total_count > 0 else 0
            
            progress_bar = "["
            filled_blocks = int(percentage / 10)
            for i in range(10):
                if i < filled_blocks:
                    progress_bar += "■"
                else:
                    progress_bar += "□"
            progress_bar += "]"
            
            updated_message += f"\nProgress: {progress_bar} {percentage}% ({completed_count}/{total_count})"
            
            # Update the message
            await message.edit(content=updated_message)
            
        except Exception as e:
            logger.error(f"Error updating steps message: {e}")
    
    async def post_morning_routine(self):
        """Post morning routine with detailed steps"""
        try:
            # Get routines by time of day first
            routines = self.notion_manager.get_routines_by_time('Morning')
            
            # If no routines found by time of day, try to find by name containing 'morning'
            if not routines:
                logger.info("No routines found with Time of Day = 'Morning', checking names")
                routines = self.notion_manager.get_routines_by_name_contains('morning')
            
            if not routines:
                logger.info("No morning routines found by any method")
                # Try fallback to channel
                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    await channel.send("☀️ No morning routines found. Please add a routine with 'Morning' as the Time of Day or 'morning' in the name.")
                return
            
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                logger.error(f"Channel not found: {self.channel_id}")
                return
            
            # Send introduction message once
            await channel.send("☀️ **Good Morning!** Here's your morning routine:")
            
            # Process unique routines only (no duplicates)
            processed_routines = set()
            for routine in routines:
                routine_id = routine.get('id')
                if routine_id not in processed_routines:
                    processed_routines.add(routine_id)
                    await self._post_routine_with_steps(channel, routine)
                
        except Exception as e:
            logger.error(f"Error posting morning routine: {e}")
    
    async def post_evening_routine(self):
        """Post evening routine with detailed steps"""
        try:
            # Get routines by time of day first
            routines = self.notion_manager.get_routines_by_time('Evening')
            
            # If no routines found by time of day, try to find by name containing 'evening'
            if not routines:
                logger.info("No routines found with Time of Day = 'Evening', checking names")
                routines = self.notion_manager.get_routines_by_name_contains('evening')
            
            if not routines:
                logger.info("No evening routines found by any method")
                # Try fallback to channel
                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    await channel.send("🌙 No evening routines found. Please add a routine with 'Evening' as the Time of Day or 'evening' in the name.")
                return
            
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                logger.error(f"Channel not found: {self.channel_id}")
                return
            
            # Send introduction message once
            await channel.send("🌙 **Good Evening!** Here's your evening routine:")
            
            # Process unique routines only (no duplicates)
            processed_routines = set()
            for routine in routines:
                routine_id = routine.get('id')
                if routine_id not in processed_routines:
                    processed_routines.add(routine_id)
                    await self._post_routine_with_steps(channel, routine)
                
        except Exception as e:
            logger.error(f"Error posting evening routine: {e}")
    
    async def _post_routine_with_steps(self, channel, routine):
        """Post a routine with its detailed steps as an interactive checklist"""
        try:
            routine_id = routine.get('id')
            routine_name = routine.get('name')
            
            # Check if this routine was recently posted to prevent duplicates
            current_time = datetime.now(self.timezone).timestamp()
            routine_key = f"{routine_id}_{routine_name}"
            
            if routine_key in self.recently_posted_routines:
                last_posted_time = self.recently_posted_routines[routine_key]
                if current_time - last_posted_time < self.duplicate_prevention_time:
                    logger.info(f"Skipping duplicate post for routine '{routine_name}' (posted {int(current_time - last_posted_time)} seconds ago)")
                    return
            
            # Mark this routine as recently posted
            self.recently_posted_routines[routine_key] = current_time
            
            # Get the raw notes from the routine
            raw_notes = routine.get('notes', '')
            
            # Try to use the raw notes directly for better accuracy
            if raw_notes:
                logger.info(f"Using raw notes for routine '{routine_name}'")
                raw_steps = []
                for line in raw_notes.split('\n'):
                    line = line.strip()
                    if line and not line.isspace():
                        # Remove leading numbers, bullets, etc.
                        import re
                        clean_line = re.sub(r'^[\d\.\-\*\•\⁃\◦\○\▪\■\□\▫\❏\❑\❒\➤\➣\➢\➡\→\►\➔\✓\✔\✗\✘\☐\☑\☒]+\s*', '', line)
                        if clean_line:
                            raw_steps.append(clean_line.strip())
                
                if raw_steps:
                    steps = raw_steps
                    logger.info(f"Extracted {len(steps)} steps from raw notes")
                else:
                    # Try DeepSeek
                    try:
                        steps = self.openrouter_service.generate_structured_routine_steps(routine)
                        logger.info(f"Generated {len(steps)} steps with DeepSeek")
                    except Exception as e:
                        logger.error(f"Error with DeepSeek: {e}")
                        steps = self.notion_manager.get_routine_steps(routine_id)
            else:
                # Try DeepSeek
                try:
                    steps = self.openrouter_service.generate_structured_routine_steps(routine)
                    logger.info(f"Generated {len(steps)} steps with DeepSeek")
                except Exception as e:
                    logger.error(f"Error with DeepSeek: {e}")
                    steps = self.notion_manager.get_routine_steps(routine_id)
            
            if not steps or len(steps) == 0:
                # No detailed steps, just post the routine name
                await channel.send(f"📝 **{routine_name}**")
                return
            
            # Send routine header with appropriate emoji
            time_of_day = routine.get('time_of_day', '').lower() if routine.get('time_of_day') else ''
            routine_name_lower = routine_name.lower()
            
            if 'morning' in routine_name_lower or 'morning' in time_of_day:
                header_emoji = "☀️"
            elif 'evening' in routine_name_lower or 'evening' in time_of_day:
                header_emoji = "🌙"
            else:
                header_emoji = "📝"
            
            await channel.send(f"{header_emoji} **{routine_name}** - Follow these steps:")
            
            # Format the steps in a visually appealing way
            steps_message = ""
            for i, step in enumerate(steps, 1):
                steps_message += f"{i}. {step}\n"
            
            # Send message with steps
            step_msg = await channel.send(steps_message)
            
            # Add number reactions for each step (up to 10 steps)
            number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            for i, step in enumerate(steps):
                if i < len(number_emojis):  # Only add reactions for up to 10 steps
                    await step_msg.add_reaction(number_emojis[i])
            
            # Add a checkmark for marking the entire routine as complete
            await step_msg.add_reaction("✅")
            
            # Track this message for reaction handling
            self.routine_step_messages[step_msg.id] = {
                'routine_id': routine_id,
                'routine_name': routine_name,
                'steps': steps,
                'completed_steps': [False] * len(steps),
                'message_type': 'combined'  # Flag for combined message format
            }
            
            # End of routine marker
            await channel.send("─────────────────────")
            
        except Exception as e:
            logger.error(f"Error posting routine with steps: {e}")
    
    async def handle_emoji_trigger(self, message):
        """Handle emoji triggers in messages"""
        content = message.content
        
        try:
            # Clear old entries from recently posted routines
            current_time = datetime.now(self.timezone).timestamp()
            self.recently_posted_routines = {k: v for k, v in self.recently_posted_routines.items() 
                                           if current_time - v < self.duplicate_prevention_time}
            
            # Check for morning routine emoji trigger (:one:)
            if "1️⃣" in content or ":one:" in content:
                await self.post_morning_routine()
                
            # Check for evening routine emoji trigger (:two:)
            elif "2️⃣" in content or ":two:" in content:
                await self.post_evening_routine()
                
        except Exception as e:
            logger.error(f"Error handling emoji trigger: {e}")
    
    async def post_routine_for_time(self, time_of_day):
        """Post routines for a specific time of day"""
        try:
            logger.info(f"Posting routines for {time_of_day}")
            
            # Get the routines for this time of day
            routines = self.notion_manager.get_routines_by_time(time_of_day)
            
            if not routines:
                logger.info(f"No routines found for {time_of_day}")
                return
            
            # Format the routines using OpenRouter
            message = self.openrouter_service.format_routine_message(routines, time_of_day)
            
            # Post the message to Discord
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                await channel.send(message)
                logger.info(f"Posted {time_of_day} routines to channel")
            else:
                logger.error(f"Channel not found: {self.channel_id}")
                
        except Exception as e:
            logger.error(f"Error posting routine for {time_of_day}: {e}")
    
    async def post_todays_routines(self, ctx=None):
        """Post all routines for today"""
        try:
            logger.info("Posting all routines for today")
            
            # Get all routines for today
            routines = self.notion_manager.get_routines_for_day()
            
            if not routines:
                message = "No routines scheduled for today."
            else:
                # Format the routines using OpenRouter
                message = self.openrouter_service.format_routine_message(routines)
            
            # Post the message to Discord
            if ctx:
                # If called from a command, reply in the same context
                await ctx.send(message)
            else:
                # Otherwise post to the designated channel
                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    await channel.send(message)
                else:
                    logger.error(f"Channel not found: {self.channel_id}")
                    
            logger.info("Posted today's routines")
                
        except Exception as e:
            logger.error(f"Error posting today's routines: {e}")
            if ctx:
                await ctx.send("Sorry, there was an error retrieving your routines.")
    
    async def post_tomorrows_routines(self, ctx):
        """Post all routines for tomorrow"""
        try:
            logger.info("Posting all routines for tomorrow")
            
            # Calculate tomorrow's date
            tomorrow = datetime.now(self.timezone).date() + timedelta(days=1)
            
            # Get all routines for tomorrow
            routines = self.notion_manager.get_routines_for_day(tomorrow)
            
            if not routines:
                await ctx.send("No routines scheduled for tomorrow.")
            else:
                # Format the routines using OpenRouter
                message = self.openrouter_service.format_routine_message(routines, None, tomorrow)
                
                # Post the message
                await ctx.send(message)
                
            logger.info("Posted tomorrow's routines")
                
        except Exception as e:
            logger.error(f"Error posting tomorrow's routines: {e}")
            await ctx.send("Sorry, there was an error retrieving tomorrow's routines.") 