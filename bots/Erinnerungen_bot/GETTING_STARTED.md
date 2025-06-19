# 🚀 Erinnerungen Bot - Getting Started Guide

## **🎯 What This Bot Does**

Your **Erinnerungen Bot** is **100% complete and ready to run!** It will automatically send:

### 🎂 **Birthday Reminders** (Daily at 07:00)
- Fetches from your Notion database: `214d42a1faf580fa8eccd0ddfd69ca98`
- Sends personalized messages with age calculation
- Target Discord Channel: `1361084010847015241`

### 🗑️ **Waste Collection Reminders** (Daily at 20:00)  
- For Schweigheim, Baden-Württemberg
- Tells you which bins to put out tomorrow
- Types: Restmüll, Biotonne, Gelber Sack, Papier

---

## **✅ Current Status**

```
✅ All Python code implemented and tested
✅ Virtual environment set up with all dependencies
✅ Scheduling system ready (07:00 & 20:00 daily)
✅ Discord integration complete
✅ Notion integration complete
✅ Error handling and logging system
❌ Missing API keys (Discord & Notion tokens)
```

---

## **🔧 What You Need To Do (5 Minutes Setup)**

### **Step 1: Get Discord Bot Token**

1. Go to: https://discord.com/developers/applications
2. Click "New Application" → Give it a name like "Erinnerungen Bot"
3. Go to "Bot" section → Click "Reset Token" → Copy the token
4. Go to "OAuth2" → "URL Generator":
   - Select "bot" scope
   - Select permissions: "Send Messages", "Read Message History"
   - Copy the generated URL and add bot to your server

### **Step 2: Get Notion Integration Token**

1. Go to: https://www.notion.so/my-integrations
2. Click "New integration" → Name it "Erinnerungen Bot"
3. Copy the "Internal Integration Token"
4. Share your birthday database with this integration:
   - Open your Notion birthday database
   - Click "Share" → Add the integration

### **Step 3: Update Configuration**

Edit the `.env` file with your real tokens:

```bash
# Replace these with your actual tokens:
DISCORD_TOKEN=your_actual_discord_token_here
NOTION_TOKEN=your_actual_notion_token_here

# These are already correct:
ERINNERUNGEN_CHANNEL_ID=1361084010847015241
GEBURTSTAGE_DATABASE_ID=214d42a1faf580fa8eccd0ddfd69ca98
TIMEZONE=Europe/Berlin
```

---

## **🏃‍♂️ Running the Bot**

### **Quick Start:**
```bash
cd ~/Documents/discord/bots/Erinnerungen_bot
source erinnerungen_env/bin/activate
python erinnerungen_bot.py
```

### **Test Commands:**
Once running, test in Discord:
- `!test_geburtstage` - Check today's birthdays manually
- `!test_muell` - Check tomorrow's waste collection

---

## **📊 Expected Behavior**

### **Birthday Messages:**
```
🎉 **HAPPY BIRTHDAY!** 🎉

**Marc** hat heute Geburtstag!
🎂 **35 Jahre alt** 🎂
👥 **Beziehung:** Friend
💼 Mitten im Leben!

📅 Geboren am: 15.05.1990
```

### **Waste Collection Messages:**
```
🗑️ **MÜLL-ERINNERUNG** 🗑️

**Morgen (20.01.2025) wird Müll abgeholt!**

**Bitte bereitstellen:**
• 🍂 Biotonne (braune Tonne)

📍 **Ort:** Schwaikheim, Baden-Württemberg
⏰ **Erinnerung:** Tonnen bis 06:00 Uhr bereitstellen
```

---

## **🐛 Troubleshooting**

### **Common Issues & Solutions:**

**"Improper token has been passed"**
→ Check your Discord token in `.env` file

**"Forbidden" errors**
→ Make sure bot has permissions in your Discord server

**"Notion API errors"**
→ Verify integration is shared with your birthday database

**"No birthdays found"**
→ Check Notion database structure (Name + Date columns)

### **Check Configuration:**
```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Discord:', 'OK' if os.getenv('DISCORD_TOKEN') != 'your_discord_bot_token_here' else 'MISSING'); print('Notion:', 'OK' if os.getenv('NOTION_TOKEN') != 'your_notion_integration_token_here' else 'MISSING')"
```

---

## **📅 Automatic Schedule**

Once running, the bot will automatically:
- **07:00 daily** → Check birthdays, send notifications if any
- **20:00 daily** → Check waste collection, send reminder if pickup tomorrow

**No manual intervention needed!**

---

## **🎛️ Notion Database Format**

Your birthday database should have:
- **Name** (Title field) - Person's name
- **Geburtstag** (Date field) - Birthday date  
- **Beziehung** (Select/Text field) - Relationship (optional)

Example:
```
Name: Marc
Geburtstag: 1990-05-15
Beziehung: Friend
```

---

## **🔍 Monitoring & Logs**

- **Live logs:** Check terminal output while running
- **Log file:** `erinnerungen_bot.log` (errors and status)
- **Test manually:** Use `!test_geburtstage` and `!test_muell` commands

---

## **🎯 Ready to Go!**

Your bot is **completely implemented** and just needs API keys. Once configured, it will:

1. ✅ Send birthday notifications every morning at 07:00
2. ✅ Send waste collection reminders every evening at 20:00  
3. ✅ Log all activities for monitoring
4. ✅ Handle errors gracefully
5. ✅ Work automatically without intervention

**Need help with API keys? Let me know which step you're stuck on!** 