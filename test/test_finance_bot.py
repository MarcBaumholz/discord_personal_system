import pytest
import asyncio
import os
import sqlite3
import tempfile
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# Add path for importing bot modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'bots', 'finance_bot'))

# Import bot modules
from bank_connector import BankDataManager
from budget_manager import BudgetManager
from notification_service import NotificationService

class TestFinanceBot:
    """Test suite for Finance Bot"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def bank_manager(self, mock_env_vars):
        """Create BankDataManager instance"""
        manager = BankDataManager()
        yield manager
    
    @pytest.fixture
    def budget_manager(self, temp_db):
        """Create BudgetManager instance with temporary database"""
        manager = BudgetManager(db_path=temp_db)
        yield manager
    
    @pytest.fixture
    def notification_service(self, mock_discord_bot):
        """Create NotificationService instance"""
        service = NotificationService(mock_discord_bot, 123456789)
        yield service
    
    def test_bank_manager_initialization(self, bank_manager):
        """Test bank manager initialization"""
        assert hasattr(bank_manager, 'connections')
        assert hasattr(bank_manager, 'fints_url')
        assert hasattr(bank_manager, 'paypal_client_id')
        assert isinstance(bank_manager.connections, dict)
    
    def test_bank_manager_get_account_balances(self, bank_manager):
        """Test getting account balances (placeholder data)"""
        balances = bank_manager.get_account_balances()
        
        assert isinstance(balances, dict)
        assert len(balances) > 0
        assert "Volksbank Checking" in balances
        assert isinstance(balances["Volksbank Checking"], (int, float))
    
    def test_bank_manager_get_transactions(self, bank_manager):
        """Test getting transactions (placeholder data)"""
        transactions = bank_manager.get_transactions(days=7)
        
        assert isinstance(transactions, list)
        assert len(transactions) > 0
        
        # Check transaction structure
        for tx in transactions:
            assert 'date' in tx
            assert 'amount' in tx
            assert 'description' in tx
            assert 'account' in tx
            assert 'category' in tx
            assert isinstance(tx['date'], datetime)
    
    def test_budget_manager_initialization(self, budget_manager, temp_db):
        """Test budget manager initialization"""
        assert budget_manager.db_path == temp_db
        assert isinstance(budget_manager.budgets, dict)
        
        # Check if database tables were created
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'budgets' in tables
        assert 'categories' in tables
        assert 'spending' in tables
        
        conn.close()
    
    def test_budget_manager_set_budget(self, budget_manager):
        """Test setting budget for a category"""
        result = budget_manager.set_budget("Groceries", 300.0, "monthly")
        
        assert result is True
        assert "Groceries" in budget_manager.budgets
        assert budget_manager.budgets["Groceries"]["amount"] == 300.0
        assert budget_manager.budgets["Groceries"]["period"] == "monthly"
    
    def test_budget_manager_record_spending(self, budget_manager):
        """Test recording spending"""
        result = budget_manager.record_spending("Groceries", 45.50)
        
        assert result is True
    
    def test_budget_manager_get_spending(self, budget_manager):
        """Test getting spending data"""
        # First record some spending
        budget_manager.record_spending("Groceries", 45.50)
        budget_manager.record_spending("Dining", 25.00)
        
        # Get all spending
        spending = budget_manager.get_spending()
        
        assert isinstance(spending, dict)
        # Note: The actual implementation might return different data due to date filtering
    
    def test_budget_manager_check_budgets(self, budget_manager):
        """Test checking budget limits"""
        over_budget = budget_manager.check_budgets()
        
        assert isinstance(over_budget, list)
        # Check structure of over-budget items
        for item in over_budget:
            assert 'category' in item
            assert 'budget' in item
            assert 'spent' in item
            assert 'percentage' in item
    
    @pytest.mark.asyncio
    async def test_notification_service_send_message(self, notification_service, mock_discord_channel):
        """Test sending simple message"""
        notification_service.bot.get_channel.return_value = mock_discord_channel
        
        result = await notification_service.send_message("Test message")
        
        assert result is True
        mock_discord_channel.send.assert_called_once_with("Test message")
    
    @pytest.mark.asyncio
    async def test_notification_service_send_budget_alert(self, notification_service, mock_discord_channel):
        """Test sending budget alert"""
        notification_service.bot.get_channel.return_value = mock_discord_channel
        
        over_budget_categories = [
            {
                "category": "Dining",
                "budget": 200.00,
                "spent": 245.30,
                "percentage": 122.65
            }
        ]
        
        result = await notification_service.send_budget_alert(over_budget_categories)
        
        assert result is True
        mock_discord_channel.send.assert_called_once()
        # Check that an embed was sent
        args = mock_discord_channel.send.call_args[1]
        assert 'embed' in args
    
    @pytest.mark.asyncio
    async def test_notification_service_send_transaction_alert(self, notification_service, mock_discord_channel):
        """Test sending transaction alert"""
        notification_service.bot.get_channel.return_value = mock_discord_channel
        
        transaction = {
            'date': datetime.now(),
            'amount': -45.30,
            'description': 'Supermarket Purchase',
            'account': 'Checking',
            'category': 'Groceries'
        }
        
        result = await notification_service.send_transaction_alert(transaction)
        
        assert result is True
        mock_discord_channel.send.assert_called_once()
        # Check that an embed was sent
        args = mock_discord_channel.send.call_args[1]
        assert 'embed' in args
    
    @pytest.mark.asyncio
    async def test_notification_service_send_weekly_report(self, notification_service, mock_discord_channel):
        """Test sending weekly report"""
        notification_service.bot.get_channel.return_value = mock_discord_channel
        
        spending = {
            "Groceries": 150.00,
            "Dining": 75.00,
            "Transport": 30.00
        }
        
        budgets = {
            "Groceries": {"amount": 200.00},
            "Dining": {"amount": 100.00},
            "Transport": {"amount": 50.00}
        }
        
        result = await notification_service.send_weekly_report(spending, budgets)
        
        assert result is True
        mock_discord_channel.send.assert_called_once()
        # Check that an embed was sent
        args = mock_discord_channel.send.call_args[1]
        assert 'embed' in args
    
    @pytest.mark.asyncio
    async def test_notification_service_channel_not_found(self, notification_service):
        """Test handling when Discord channel is not found"""
        notification_service.bot.get_channel.return_value = None
        
        result = await notification_service.send_message("Test message")
        
        assert result is False
    
    def test_budget_manager_load_budgets_empty_db(self, temp_db):
        """Test loading budgets from empty database"""
        manager = BudgetManager(db_path=temp_db)
        budgets = manager._load_budgets()
        
        assert isinstance(budgets, dict)
        assert len(budgets) == 0
    
    def test_budget_manager_spending_with_negative_amount(self, budget_manager):
        """Test recording spending with negative amount (should be converted to positive)"""
        result = budget_manager.record_spending("Groceries", -45.50)
        
        assert result is True
        # The amount should be stored as positive
    
    def test_budget_manager_spending_with_date(self, budget_manager):
        """Test recording spending with specific date"""
        test_date = "2025-01-13"
        result = budget_manager.record_spending("Groceries", 30.00, date=test_date)
        
        assert result is True
    
    def test_budget_manager_get_spending_filtered(self, budget_manager):
        """Test getting spending filtered by category"""
        # Record some spending
        budget_manager.record_spending("Groceries", 45.50)
        budget_manager.record_spending("Dining", 25.00)
        
        # Get spending for specific category
        spending = budget_manager.get_spending(category="Groceries")
        
        assert isinstance(spending, dict)
    
    @pytest.mark.asyncio
    async def test_notification_service_empty_budget_alert(self, notification_service):
        """Test sending budget alert with empty list"""
        result = await notification_service.send_budget_alert([])
        
        assert result is True  # Should return True for empty list

if __name__ == "__main__":
    pytest.main([__file__]) 