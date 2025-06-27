# Personal RSS Bot - Testing & Daily News Implementation Plan

## Overview
This document outlines the plan to test the existing Personal RSS Bot and implement a daily !news trigger at 8:30 AM as requested by the user.

## Current State Analysis

### ✅ What's Already Implemented
- **Complete bot architecture** with modular components:
  - `main.py` - Main orchestration and scheduling
  - `database.py` - SQLite database management  
  - `rss_manager.py` - RSS feed fetching and parsing
  - `llm_processor.py` - AI-powered content analysis
  - `discord_publisher.py` - Discord bot and messaging
- **Discord commands** including `!news` command for on-demand summaries
- **Weekly scheduling system** (currently set to Sundays at 9:00 AM)
- **RSS feed configuration** (`config/rss_feeds.json` with 20+ feeds)
- **Database schema** for articles, feeds, and summaries
- **LLM integration** for relevance scoring and summarization

### 📋 What Needs to be Done
1. **Environment Setup** - Create `.env` file with proper credentials
2. **Testing** - Verify all components work correctly
3. **Daily Scheduling** - Add 8:30 AM daily !news trigger
4. **Validation** - Ensure bot runs reliably

## Implementation Steps

### Step 1: Environment Configuration
- Create `.env` file from `config.example` template
- Configure Discord bot token and channel ID
- Set up OpenRouter API key for LLM integration
- Verify RSS feed sources are accessible

### Step 2: Component Testing (Sequential)
1. **Database Testing** - Verify SQLite database creation and operations
2. **RSS Feed Testing** - Test feed fetching from configured sources
3. **LLM Processing Testing** - Verify AI content analysis works
4. **Discord Bot Testing** - Test bot connection and commands
5. **Integration Testing** - Test full workflow

### Step 3: Daily News Trigger Implementation
- **Current**: Weekly scheduling on Sundays at 9:00 AM
- **New**: Add daily scheduling at 8:30 AM for !news command
- **Approach**: Extend existing scheduler with additional trigger
- **Configuration**: Add new environment variables for daily schedule

### Step 4: Production Deployment
- Test in virtual environment
- Verify logging and error handling
- Set up background service for continuous operation

## Technical Implementation Details

### Daily Scheduling Configuration
```python
# Additional environment variables needed:
DAILY_NEWS_ENABLED=true
DAILY_NEWS_HOUR=8
DAILY_NEWS_MINUTE=30
DAILY_NEWS_TIMEZONE=UTC
```

### Scheduler Enhancement
The existing `AsyncIOScheduler` will be extended with:
- Daily cron trigger for 8:30 AM
- Separate from weekly summary trigger
- Uses existing `!news` command workflow

### Code Changes Required
1. **main.py**: Add daily scheduling logic
2. **config loading**: Add daily schedule configuration
3. **scheduler setup**: Register daily trigger alongside weekly trigger

## Testing Strategy

### Phase 1: Basic Functionality Testing
- [ ] Environment configuration validation
- [ ] Database connectivity and schema creation
- [ ] RSS feed accessibility and parsing
- [ ] Discord bot authentication and channel access

### Phase 2: Component Integration Testing  
- [ ] RSS → Database → LLM → Discord workflow
- [ ] Error handling and fallback mechanisms
- [ ] Performance and rate limiting
- [ ] Content quality and relevance scoring

### Phase 3: Scheduling Testing
- [ ] Manual trigger testing for !news command
- [ ] Daily scheduler setup and timing verification
- [ ] Weekly scheduler compatibility
- [ ] Graceful shutdown and restart handling

### Phase 4: Production Readiness
- [ ] Logging and monitoring setup
- [ ] Background service configuration
- [ ] Error recovery and alerting
- [ ] Resource usage optimization

## Success Criteria

### Functional Requirements
- ✅ Bot successfully connects to Discord
- ✅ RSS feeds are fetched and processed daily
- ✅ LLM analysis provides relevant content scoring
- ✅ Daily !news summary is posted at 8:30 AM
- ✅ Weekly summary continues to work on Sundays at 9:00 AM

### Quality Requirements
- 📊 Zero critical errors in daily operation
- 📊 Response time < 30 seconds for !news command
- 📊 Summary quality score > 0.7 for included articles
- 📊 Daily uptime > 99%

### User Experience Requirements
- 🎯 Daily news summary contains 5-10 relevant articles
- 🎯 Content covers configured topic areas (AI, productivity, etc.)
- 🎯 Summaries are concise and actionable
- 🎯 Manual !news command works on-demand

## Risk Mitigation

### High Priority Risks
- **API Rate Limits**: Implement exponential backoff and monitoring
- **RSS Feed Failures**: Graceful handling of unavailable feeds
- **LLM API Costs**: Budget monitoring and usage tracking
- **Discord API Changes**: Use stable API versions

### Medium Priority Risks
- **Content Quality**: Regular review of relevance scoring
- **Scheduling Conflicts**: Proper timezone handling
- **Database Growth**: Implement cleanup routines
- **Memory Usage**: Monitor and optimize resource usage

## Timeline

### Immediate (Today)
- Environment setup and basic testing
- Verify existing components work
- Test !news command manually

### Short-term (1-2 days)  
- Implement daily scheduling trigger
- Integration testing and debugging
- Production deployment setup

### Ongoing (Weekly review)
- Monitor performance and content quality
- Adjust RSS feeds and relevance scoring
- User feedback incorporation

## Next Actions

1. **Set up environment** - Create `.env` file with credentials
2. **Test existing bot** - Verify all components work
3. **Implement daily trigger** - Add 8:30 AM scheduling
4. **Deploy and monitor** - Run in production with logging

This plan ensures a methodical approach to testing and enhancing the RSS bot while maintaining reliability and quality standards. 