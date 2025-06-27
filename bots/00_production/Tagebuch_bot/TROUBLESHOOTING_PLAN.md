# 🔧 Tagebuch Bot - Troubleshooting Plan

## 🐛 Issues Identified

### 1. **Duplicate Messages**
- **Problem**: Bot is sending duplicate messages for all commands and responses
- **Root Cause**: Likely multiple event handlers or bot instances running
- **Symptoms**: Every message appears twice in Discord

### 2. **Database Property Error**
- **Problem**: "Datum is not a property that exists" error when saving to Notion
- **Root Cause**: Notion database properties use English names, but code expects German names
- **Expected German**: `Datum`, `Titel`, `Text`
- **Likely English**: `Date`, `Title`, `Text`

### 3. **Command Registration Issues**
- **Problem**: Commands show "Command not found" but still execute
- **Symptoms**: `!tagebuch_help`, `!tagebuch_test`, `!tagebuch_reminder` not properly registered

## 🔧 Fixes to Implement

### Fix 1: Database Property Names
- Check actual Notion database properties
- Update `notion_manager.py` to use correct property names
- Add dynamic property detection or configuration

### Fix 2: Duplicate Message Prevention
- Ensure only one bot instance is running
- Check for duplicate event handlers
- Add message deduplication logic if needed

### Fix 3: Command Registration
- Verify bot command registration
- Check for command conflicts
- Ensure proper command prefix handling

## 📋 Implementation Steps

1. **Stop current bot instance** to prevent conflicts
2. **Check and fix database properties** in NotionManager
3. **Restart bot** with fixes
4. **Test all functionality** systematically
5. **Document final configuration**

## 🧪 Testing Checklist

- [ ] Bot starts without errors
- [ ] Commands work without duplication
- [ ] Journal entries save to Notion successfully
- [ ] Database properties match correctly
- [ ] No duplicate messages
- [ ] Daily reminder system works 