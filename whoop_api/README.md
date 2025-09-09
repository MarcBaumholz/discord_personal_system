# WHOOP API Integration

A comprehensive Python client for accessing WHOOP data via the official v2 API. This package provides OAuth 2.0 authentication, rate limiting, webhook support, and access to all major WHOOP endpoints.

## 🚀 Quick Start

### Prerequisites

1. **Active WHOOP Membership**: You need an active WHOOP subscription
2. **Python 3.8+**: Required for the client library
3. **WHOOP Developer Account**: Register at [developer.whoop.com](https://developer.whoop.com)

### Step 1: Register Your Application

1. Go to [WHOOP Developer Dashboard](https://developer.whoop.com)
2. Sign in with your WHOOP account
3. Click "Create New Application"
4. Fill in the application details:
   - **Application Name**: Your app name (e.g., "My WHOOP Data Analyzer")
   - **Description**: Brief description of your app
   - **Redirect URI**: `http://localhost:8080/callback` (for testing)
5. Save your **Client ID** and **Client Secret** - you'll need these!

### Step 2: Install Dependencies

```bash
cd whoop_api
pip install -r requirements.txt
```

### Step 3: Configure Environment

1. Copy the example configuration:
```bash
cp config.env.example .env
```

2. Edit `.env` with your credentials:
```env
WHOOP_CLIENT_ID=your_client_id_here
WHOOP_CLIENT_SECRET=your_client_secret_here
WHOOP_REDIRECT_URI=http://localhost:8080/callback
```

### Step 4: Run Basic Example

```bash
python examples/basic_usage.py
```

This will:
1. Generate an authorization URL
2. Guide you through the OAuth flow
3. Fetch and display your basic WHOOP data

## 📊 Available Data

The WHOOP API v2 provides access to:

### User Profile
- User ID, email, name
- Body measurements (height, weight, max heart rate)

### Physiological Data
- **Cycles**: Daily physiological summaries with strain scores
- **Sleep**: Detailed sleep stages, efficiency, and performance metrics
- **Recovery**: Recovery scores, HRV, resting heart rate, SpO2
- **Workouts**: Exercise data with strain, heart rate zones, energy expenditure

### Data Scope
- **Time Range**: Access historical data (limited by your membership duration)
- **Real-time**: Webhook support for new data notifications
- **Rate Limits**: 100 requests/minute, 10,000 requests/day (can be increased)

## 🔧 API Usage

### Basic Authentication

```python
from src.config import WhoopConfig
from src.oauth import WhoopOAuth, extract_code_from_url
from src.client import WhoopClient

# Load configuration
config = WhoopConfig.from_env()

# Initialize OAuth
oauth = WhoopOAuth(config)

# Get authorization URL
auth_url = oauth.get_authorization_url()
print(f"Visit: {auth_url}")

# After user authorizes, get callback URL
callback_url = input("Paste callback URL: ")
code, state = extract_code_from_url(callback_url)

# Exchange code for tokens
token_response = oauth.exchange_code_for_token(code)

# Initialize API client
client = WhoopClient(config, oauth)
```

### Fetching Data

```python
# Get user profile
profile = client.get_user_profile()
print(f"User: {profile.email}")

# Get recent cycles (last 7 days)
from datetime import datetime, timedelta
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

cycles = client.get_cycles(start=start_date, end=end_date)
for cycle in cycles.records:
    print(f"Cycle: {cycle['start']} - Strain: {cycle.get('score', {}).get('strain')}")

# Get sleep data
sleep_data = client.get_sleep_data(start=start_date, end=end_date)
for sleep in sleep_data.records:
    print(f"Sleep: {sleep['start']} - Score: {sleep.get('score')}")

# Get recovery data
recovery_data = client.get_recovery_data(start=start_date, end=end_date)
for recovery in recovery_data.records:
    print(f"Recovery: {recovery['start']} - Score: {recovery.get('score')}")

# Get workouts
workouts = client.get_workouts(start=start_date, end=end_date)
for workout in workouts.records:
    print(f"Workout: {workout['start']} - Sport: {workout.get('sport_name')}")
```

### Pagination

```python
# Get all cycles with automatic pagination
all_cycles = client.get_all_cycles(start=start_date, end=end_date)
print(f"Total cycles: {len(all_cycles)}")

# Manual pagination
cycles = client.get_cycles(limit=25)
while cycles.next_token:
    print(f"Fetched {len(cycles.records)} cycles")
    cycles = client.get_cycles(next_token=cycles.next_token)
```

## 🔄 Webhook Support

### Start Webhook Server

```bash
python examples/webhook_server.py
```

### Configure in WHOOP Dashboard

1. Go to your app settings in WHOOP Developer Dashboard
2. Set webhook URL: `https://your-domain.com/webhook`
3. Set webhook secret (matches `WEBHOOK_SECRET` in your `.env`)

### Handle Events

```python
from flask import Flask, request
from src.models import WhoopWebhookEvent

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    data = request.get_json()
    event = WhoopWebhookEvent(**data)
    
    if event.event_type == 'cycle.created':
        print(f"New cycle for user {event.user_id}")
    elif event.event_type == 'sleep.created':
        print(f"New sleep record for user {event.user_id}")
    # ... handle other event types
    
    return {'status': 'success'}, 200
```

## 📈 Data Export

Export all your data to CSV files:

```bash
python examples/data_export.py
```

This creates a `whoop_export/` directory with:
- `cycles.csv` - Daily physiological data
- `sleep.csv` - Sleep records and stages
- `recovery.csv` - Recovery metrics
- `workouts.csv` - Exercise data
- `metadata.json` - Export information and user profile

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_client.py -v
```

## 📋 Examples

- **`basic_usage.py`**: Complete OAuth flow and data fetching
- **`data_export.py`**: Export all data to CSV files
- **`webhook_server.py`**: Real-time webhook server

## ⚠️ Important Notes

### Rate Limiting
- Default: 100 requests/minute, 10,000 requests/day
- Automatic rate limiting built-in
- Contact WHOOP to request higher limits

### Data Availability
- **Real-time HR**: Not available via API (BLE broadcast only)
- **Historical Data**: Limited by your membership duration
- **v1 Deprecation**: v1 API will be removed after October 1, 2025

### Security
- Store credentials securely (use `.env` files)
- Never commit secrets to version control
- Use HTTPS for webhook endpoints
- Verify webhook signatures

## 🆘 Troubleshooting

### Common Issues

1. **"Invalid client credentials"**
   - Check your Client ID and Secret
   - Ensure they match your WHOOP app settings

2. **"Invalid redirect URI"**
   - Verify redirect URI matches your app configuration
   - Use `http://localhost:8080/callback` for testing

3. **"Rate limit exceeded"**
   - Wait for rate limit to reset
   - Implement exponential backoff
   - Request higher limits from WHOOP

4. **"Token expired"**
   - Refresh tokens automatically
   - Re-authenticate if refresh fails

### Getting Help

- [WHOOP Developer Documentation](https://developer.whoop.com)
- [API Reference](https://developer.whoop.com/api)
- [OAuth Guide](https://developer.whoop.com/docs/developing/oauth)
- [Rate Limiting](https://developer.whoop.com/docs/developing/rate-limiting)

## 📄 License

This project is provided as-is for educational and personal use. Please respect WHOOP's API Terms of Use.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

---

**Ready to get started?** Run `python examples/basic_usage.py` and follow the prompts!
