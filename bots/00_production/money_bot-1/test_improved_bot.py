#!/usr/bin/env python3
"""
Test script for the improved money bot with manual categorization
"""
import asyncio
import sys
import os
from category_mapper import ManualCategoryMapper

# Add the current directory to the path so we can import the bot
sys.path.append(os.path.dirname(__file__))

async def test_manual_categorization():
    """Test the manual categorization system"""
    print("🧪 Testing Improved Money Bot - Manual Categorization")
    print("=" * 60)
    
    # Initialize the category mapper
    mapper = ManualCategoryMapper()
    
    # Test cases that should work with manual categorization
    test_cases = [
        "€72.41 fuel at Aral",
        "25.50 euros groceries at Rewe", 
        "18.90 lunch at McDonald's",
        "€15.50 DB ticket",
        "€29.99 Netflix subscription",
        "€45.00 Amazon order",
        "€12.50 coffee at Starbucks",
        "€8.90 parking",
        "€120.00 electricity bill",
        "€25.00 pharmacy",
        "€60.00 gym membership"
    ]
    
    print("\n📊 Manual Categorization Results:")
    print("-" * 40)
    
    manual_success = 0
    ai_fallback_needed = 0
    
    for test in test_cases:
        result = mapper.analyze_expense(test)
        
        if result['amount'] is not None and result['category'] is not None:
            print(f"✅ {test}")
            print(f"   Amount: €{result['amount']:.2f}")
            print(f"   Category: {result['category']}")
            print(f"   Confidence: {result['confidence']}%")
            manual_success += 1
        else:
            print(f"❌ {test}")
            print(f"   Amount: {result['amount']}")
            print(f"   Category: {result['category']}")
            print(f"   → Would need AI fallback")
            ai_fallback_needed += 1
        print()
    
    print(f"📈 Summary:")
    print(f"   Manual success: {manual_success}/{len(test_cases)} ({manual_success/len(test_cases)*100:.1f}%)")
    print(f"   AI fallback needed: {ai_fallback_needed}/{len(test_cases)} ({ai_fallback_needed/len(test_cases)*100:.1f}%)")
    
    if manual_success >= len(test_cases) * 0.8:  # 80% success rate
        print("\n✅ Manual categorization is working well!")
        print("🤖 AI will only be used for edge cases.")
    else:
        print("\n⚠️ Manual categorization needs improvement.")
        print("🤖 AI will be used more frequently.")
    
    return manual_success, ai_fallback_needed

async def test_edge_cases():
    """Test edge cases that might need AI fallback"""
    print("\n🔍 Testing Edge Cases:")
    print("-" * 30)
    
    mapper = ManualCategoryMapper()
    
    edge_cases = [
        "€50.00 birthday gift for mom",
        "€15.00 donation to charity", 
        "€200.00 hotel booking",
        "€35.00 concert tickets",
        "€80.00 car repair",
        "€12.00 magazine subscription"
    ]
    
    for test in edge_cases:
        result = mapper.analyze_expense(test)
        print(f"Text: {test}")
        print(f"Amount: €{result['amount']:.2f}" if result['amount'] else "Amount: None")
        print(f"Category: {result['category']}")
        print(f"Confidence: {result['confidence']}%")
        print()

if __name__ == "__main__":
    async def main():
        manual_success, ai_fallback = await test_manual_categorization()
        await test_edge_cases()
        
        print("\n🎯 Conclusion:")
        print("The improved money bot now uses:")
        print("• ⚡ Manual categorization FIRST (fast and accurate)")
        print("• 🤖 AI fallback ONLY when manual fails")
        print("• 📊 Confidence scoring for transparency")
        print("• 🚀 Much faster response times")
    
    asyncio.run(main())
