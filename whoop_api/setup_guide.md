# WHOOP API Setup Guide - Step by Step

## What You Need to Do

### 1. Prerequisites ✅
- [ ] Active WHOOP membership (required for API access)
- [ ] Python 3.8+ installed on your system
- [ ] Internet connection

### 2. Register Your WHOOP Developer Application

**Step 2.1: Go to WHOOP Developer Dashboard**
1. Visit: https://developer.whoop.com
2. Sign in with your WHOOP account credentials
3. If you don't see the developer dashboard, ensure you have an active WHOOP membership

**Step 2.2: Create New Application**
1. Click "Create New Application" or "New App"
2. Fill in the application details:
   - **Application Name**: `My WHOOP Data Access` (or any name you prefer)
   - **Description**: `Personal data access and analysis`
   - **Website**: `http://localhost` (for testing)
   - **Redirect URI**: `http://localhost:8080/callback` ⚠️ **IMPORTANT: Use exactly this URL**

**Step 2.3: Save Your Credentials**
1. After creating the app, you'll see:
   - **Client ID**: Copy this (looks like: `abc123def456...`)
   - **Client Secret**: Copy this (looks like: `xyz789uvw012...`)
2. ⚠️ **SAVE THESE SECURELY** - you'll need them in the next step

### 3. Configure the WHOOP API Client

**Step 3.1: Set Up Environment File**
1. Navigate to the `whoop_api` directory:
   ```bash
   cd /home/pi/Documents/discord/whoop_api
   ```

2. Copy the example configuration:
   ```bash
   cp config.env.example .env
   ```

3. Edit the `.env` file with your credentials:
   ```bash
   nano .env
   ```

4. Replace the placeholder values:
   ```env
   WHOOP_CLIENT_ID=your_actual_client_id_here
   WHOOP_CLIENT_SECRET=your_actual_client_secret_here
   WHOOP_REDIRECT_URI=http://localhost:8080/callback
   ```

**Step 3.2: Install Dependencies**
```bash
pip install -r requirements.txt
```

### 4. Test Your Setup

**Step 4.1: Run the Basic Example**
```bash
python examples/basic_usage.py
```

**Step 4.2: Follow the OAuth Flow**
1. The script will display an authorization URL
2. Copy and paste this URL into your web browser
3. Sign in to your WHOOP account
4. Grant permissions to your application
5. You'll be redirected to a URL like: `http://localhost:8080/callback?code=ABC123...`
6. Copy the **entire URL** and paste it back into the terminal
7. The script will fetch and display your WHOOP data

## What I Need From You

### Required Information:
1. **Your WHOOP Account**: You need an active WHOOP membership
2. **Client ID**: From your WHOOP developer application
3. **Client Secret**: From your WHOOP developer application
4. **Confirmation**: That you've successfully completed the OAuth flow

### Optional Information:
- **Data Range**: How far back do you want to fetch data? (default: last 30 days)
- **Specific Data Types**: Which data interests you most? (cycles, sleep, recovery, workouts)
- **Export Format**: Do you want CSV files, JSON, or direct API access?

## Troubleshooting Common Issues

### Issue: "Invalid client credentials"
**Solution**: Double-check your Client ID and Client Secret in the `.env` file

### Issue: "Invalid redirect URI"
**Solution**: Ensure your WHOOP app is configured with exactly: `http://localhost:8080/callback`

### Issue: "No authorization code found"
**Solution**: Make sure you copy the **entire callback URL**, not just the code part

### Issue: "Rate limit exceeded"
**Solution**: Wait a few minutes and try again. The API has built-in rate limiting.

### Issue: "Connection failed"
**Solution**: Check your internet connection and WHOOP service status

## Next Steps After Setup

Once you've successfully completed the basic example:

1. **Explore Your Data**: Run `python examples/data_export.py` to export all data to CSV
2. **Set Up Webhooks**: Run `python examples/webhook_server.py` for real-time updates
3. **Custom Analysis**: Use the API client in your own Python scripts
4. **Data Visualization**: Import CSV files into Excel, Python pandas, or other tools

## Security Notes

- ⚠️ **Never share your Client Secret** with anyone
- ⚠️ **Don't commit the `.env` file** to version control
- ⚠️ **Keep your credentials secure** - treat them like passwords
- ✅ **The redirect URI is safe** - it's just for the OAuth flow

## Support

If you encounter issues:
1. Check this troubleshooting guide
2. Review the [WHOOP Developer Documentation](https://developer.whoop.com)
3. Ensure your WHOOP membership is active
4. Verify your application settings in the WHOOP dashboard

---

**Ready to start?** Follow the steps above and let me know when you have your Client ID and Client Secret!
