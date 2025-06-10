# Discord Bots Test Suite

A comprehensive testing framework for all Discord bots in this collection.

## 🚀 Quick Start

### Install Dependencies

```bash
# Install test dependencies
pip install -r test/requirements.txt

# Or install specific packages
pip install pytest pytest-asyncio pytest-cov
```

### Run All Tests

```bash
# Run complete test suite
python test/run_tests.py

# Or use pytest directly
pytest test/ -v
```

### Run Specific Bot Tests

```bash
# Test a specific bot
python test/run_tests.py bot:daily_todo

# Or use pytest directly
pytest test/test_daily_todo_bot.py -v
```

## 📋 Available Tests

### Bot Test Files

- `test_daily_todo_bot.py` - Daily Todo Bot tests
- `test_weekly_planning_bot.py` - Weekly Planning Bot tests  
- `test_wishlist_bot.py` - Wishlist Bot tests
- `test_meal_plan_bot.py` - Meal Plan Bot tests
- `test_preisvergleich_bot.py` - Preisvergleich Bot tests
- `test_finance_bot.py` - Finance Bot tests
- `test_routine_bot.py` - Routine Bot tests

### Test Categories

Each bot test covers:

- ✅ **Core Functionality** - Main bot features and commands
- ✅ **API Integration** - Notion, OpenRouter, Todoist APIs
- ✅ **Discord Integration** - Message handling, reactions, embeds
- ✅ **Error Handling** - Graceful failure and fallback behavior
- ✅ **Data Processing** - Parsing, formatting, validation
- ✅ **Async Operations** - Proper async/await handling

## 🛠️ Test Runner Commands

### Basic Commands

```bash
# Check dependencies
python test/run_tests.py check

# List available tests
python test/run_tests.py list

# Setup test environment
python test/run_tests.py setup

# Run specific bot tests
python test/run_tests.py bot:wishlist
```

### Advanced Options

```bash
# Run tests with coverage
pytest test/ --cov=bots --cov-report=html

# Run tests in parallel
pytest test/ -n auto

# Run specific test function
pytest test/test_daily_todo_bot.py::TestDailyTodoBot::test_load_completed_todos

# Stop on first failure
pytest test/ -x

# Show test durations
pytest test/ --durations=10
```

## 🧪 Test Structure

### Test Files Organization

```
test/
├── conftest.py              # Shared fixtures and configuration
├── run_tests.py             # Main test runner
├── requirements.txt         # Test dependencies
├── README.md               # This file
├── test_daily_todo_bot.py  # Daily todo bot tests
├── test_weekly_planning_bot.py  # Weekly planning tests
├── test_wishlist_bot.py    # Wishlist bot tests
├── test_meal_plan_bot.py   # Meal plan bot tests
├── test_preisvergleich_bot.py  # Price comparison tests
├── test_finance_bot.py     # Finance bot tests
├── test_routine_bot.py     # Routine bot tests
└── test_reports/           # Generated test reports
    ├── coverage_html/      # HTML coverage reports
    └── junit.xml          # JUnit XML for CI/CD
```

### Shared Fixtures (conftest.py)

- `mock_discord_bot` - Mocked Discord bot instance
- `mock_discord_channel` - Mocked Discord channel
- `mock_discord_message` - Mocked Discord message
- `mock_notion_client` - Mocked Notion API client
- `mock_openrouter_response` - Mocked OpenRouter API response
- `mock_env_vars` - Test environment variables
- `sample_*` - Sample data for testing

## 🔧 Writing New Tests

### Test Class Structure

```python
import pytest
from unittest.mock import Mock, AsyncMock, patch

class TestYourBot:
    """Test suite for Your Bot"""
    
    @pytest.fixture
    def your_service(self, mock_env_vars):
        """Create your service instance"""
        service = YourService()
        yield service
    
    def test_synchronous_function(self, your_service):
        """Test a synchronous function"""
        result = your_service.some_function("input")
        assert result == "expected_output"
    
    @pytest.mark.asyncio
    async def test_async_function(self, your_service):
        """Test an asynchronous function"""
        result = await your_service.async_function("input")
        assert result == "expected_output"
```

### Best Practices

1. **Use Descriptive Names** - Test names should explain what they test
2. **Mock External Dependencies** - Don't make real API calls in tests
3. **Test Edge Cases** - Test both success and failure scenarios
4. **Use Fixtures** - Reuse common setup code with fixtures
5. **Async Testing** - Mark async tests with `@pytest.mark.asyncio`
6. **Assertions** - Use specific assertions that explain failures

### Mocking Examples

```python
# Mock API responses
@patch('requests.post')
def test_api_call(mock_post):
    mock_post.return_value.json.return_value = {"success": True}
    # ... test code

# Mock Discord channel
async def test_send_message(mock_discord_channel):
    await bot.send_message(mock_discord_channel, "Hello")
    mock_discord_channel.send.assert_called_once_with("Hello")

# Mock environment variables
@patch.dict(os.environ, {"API_KEY": "test_key"})
def test_with_env_var():
    # ... test code
```

## 📊 Coverage Reports

### Generate Coverage Reports

```bash
# Terminal coverage report
pytest test/ --cov=bots --cov-report=term-missing

# HTML coverage report
pytest test/ --cov=bots --cov-report=html:test_reports/coverage_html

# XML coverage report (for CI/CD)
pytest test/ --cov=bots --cov-report=xml:test_reports/coverage.xml
```

### Coverage Targets

- **Minimum Coverage**: 70%
- **Target Coverage**: 85%
- **Focus Areas**: Core business logic, API integrations, error handling

## 🔍 Debugging Tests

### Debug Failed Tests

```bash
# Run with verbose output
pytest test/ -v -s

# Run with pdb debugger
pytest test/ --pdb

# Run specific failed test
pytest test/test_bot.py::TestClass::test_method -v

# Show local variables on failure
pytest test/ -l
```

### Common Issues

1. **Async Test Errors** - Make sure to use `@pytest.mark.asyncio`
2. **Import Errors** - Check that bot modules are in the Python path
3. **Mock Issues** - Ensure mocks are properly configured and patches applied
4. **Environment Variables** - Use the `mock_env_vars` fixture

## 🚢 CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Discord Bots

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r test/requirements.txt
    
    - name: Run tests
      run: |
        python test/run_tests.py
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: test_reports/coverage.xml
```

### Docker Testing

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install -r test/requirements.txt

CMD ["python", "test/run_tests.py"]
```

## 🎯 Test Results

Tests are designed to validate:

- **Functionality** - All bot features work as expected
- **Reliability** - Bots handle errors gracefully
- **Performance** - Operations complete within reasonable time
- **Integration** - External APIs are properly integrated
- **Security** - No sensitive data leaks in logs or errors

## 🤝 Contributing

When adding new tests:

1. Follow the existing test structure
2. Add appropriate fixtures to `conftest.py` if needed
3. Include both positive and negative test cases
4. Mock all external dependencies
5. Update this README if adding new test categories

## 📚 Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Discord.py Testing](https://discordpy.readthedocs.io/en/stable/faq.html#testing)

---

Happy testing! 🎉 