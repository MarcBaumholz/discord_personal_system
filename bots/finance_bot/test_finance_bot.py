import os
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('finance_bot_test')

# Load environment variables
load_dotenv()

# Import our modules
from bank_connector import BankDataManager
from budget_manager import BudgetManager

def test_bank_manager():
    """Test bank data manager functionality"""
    logger.info("Testing BankDataManager...")
    
    # Create bank manager
    bank_manager = BankDataManager()
    
    # Get balances
    balances = bank_manager.get_account_balances()
    logger.info(f"Account balances: {balances}")
    
    # Get transactions
    transactions = bank_manager.get_transactions(days=7)
    logger.info(f"Found {len(transactions)} transactions")
    for tx in transactions:
        logger.info(f"  {tx['date'].strftime('%Y-%m-%d')} - {tx['amount']:+.2f} EUR - {tx['description']}")
    
    logger.info("BankDataManager test complete")

def test_budget_manager():
    """Test budget manager functionality"""
    logger.info("Testing BudgetManager...")
    
    # Use a test database file
    test_db = "test_finance.db"
    
    # Delete test database if it exists
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # Create budget manager
    budget_manager = BudgetManager(db_path=test_db)
    
    # Set some budgets
    budget_manager.set_budget("Groceries", 300.0)
    budget_manager.set_budget("Dining", 200.0)
    budget_manager.set_budget("Entertainment", 100.0)
    
    # Check budgets were set correctly
    budgets = budget_manager.budgets
    logger.info(f"Budgets set: {budgets}")
    
    # Record some spending
    budget_manager.record_spending("Groceries", 75.30)
    budget_manager.record_spending("Dining", 45.50)
    budget_manager.record_spending("Entertainment", 12.99)
    
    # Get spending
    spending = budget_manager.get_spending()
    logger.info(f"Spending recorded: {spending}")
    
    # Check budgets
    over_budget = budget_manager.check_budgets()
    if over_budget:
        logger.info(f"Categories over budget: {over_budget}")
    else:
        logger.info("No categories over budget")
    
    logger.info("BudgetManager test complete")

if __name__ == "__main__":
    logger.info("Starting Finance Bot tests")
    
    # Test bank manager
    test_bank_manager()
    
    # Test budget manager
    test_budget_manager()
    
    logger.info("All tests completed") 