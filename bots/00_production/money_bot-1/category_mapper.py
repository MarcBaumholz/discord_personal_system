#!/usr/bin/env python3
"""
Manual Category Mapper for Money Bot
Maps text patterns to expense categories without using AI
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class CategoryPattern:
    """Pattern for matching text to categories"""
    keywords: List[str]
    category: str
    description: str
    priority: int = 1  # Higher priority = more specific match

class ManualCategoryMapper:
    """Maps expense text to categories using pattern matching"""
    
    def __init__(self):
        """Initialize with predefined category patterns"""
        self.patterns = self._initialize_patterns()
        self.amount_patterns = [
            r'€\s*(\d+(?:[.,]\d{1,2})?)',  # €25.50, €25,50
            r'(\d+(?:[.,]\d{1,2})?)\s*€',  # 25.50€, 25,50€
            r'(\d+(?:[.,]\d{1,2})?)\s*euro',  # 25.50 euro
            r'(\d+(?:[.,]\d{1,2})?)\s*eur',   # 25.50 eur
            r'(\d+(?:[.,]\d{1,2})?)\s*€',     # 25.50€
            r'(\d+(?:[.,]\d{1,2})?)\s*euros', # 25.50 euros
            r'(\d+(?:[.,]\d{1,2})?)\s*EUR',   # 25.50 EUR
            r'(\d+(?:[.,]\d{1,2})?)\s*€\s*',  # 25.50€ (with space after)
            r'^(\d+(?:[.,]\d{1,2})?)\s+',     # 25.50 at start of text
        ]
    
    def _initialize_patterns(self) -> List[CategoryPattern]:
        """Initialize category patterns based on common German expense patterns"""
        return [
            # Transport - Gas stations, fuel, public transport
            CategoryPattern(
                keywords=['aral', 'shell', 'esso', 'total', 'tankstelle', 'tanken', 'fuel', 'diesel', 'benzin', 'gas', 'tank'],
                category='Transport',
                description='Fuel/Gas station',
                priority=3
            ),
            CategoryPattern(
                keywords=['db', 'deutsche bahn', 'zug', 'bahn', 's-bahn', 'u-bahn', 'bus', 'tram', 'ticket', 'fahrkarte'],
                category='Transport',
                description='Public transport',
                priority=2
            ),
            CategoryPattern(
                keywords=['uber', 'taxi', 'fahrdienst', 'lyft'],
                category='Transport',
                description='Ride sharing/Taxi',
                priority=2
            ),
            
            # Food - Groceries, restaurants, delivery
            CategoryPattern(
                keywords=['rewe', 'edeka', 'lidl', 'aldi', 'kaufland', 'penny', 'netto', 'real', 'supermarkt', 'grocery', 'lebensmittel'],
                category='Food',
                description='Groceries',
                priority=3
            ),
            CategoryPattern(
                keywords=['mcdonalds', 'mcdonald', 'burger king', 'subway', 'kfc', 'pizza hut', 'dominos', 'restaurant', 'gaststätte', 'café', 'cafe', 'lunch', 'dinner', 'breakfast', 'essen', 'food'],
                category='Food',
                description='Restaurant/Fast food',
                priority=2
            ),
            CategoryPattern(
                keywords=['lieferando', 'ubereats', 'deliveroo', 'foodpanda', 'lieferung', 'delivery'],
                category='Food',
                description='Food delivery',
                priority=2
            ),
            CategoryPattern(
                keywords=['bäcker', 'baecker', 'bakery', 'brot', 'brötchen', 'kuchen'],
                category='Food',
                description='Bakery',
                priority=2
            ),
            
            # Shopping - Retail, online shopping
            CategoryPattern(
                keywords=['amazon', 'zalando', 'h&m', 'zara', 'uniqlo', 'primark', 'c&a', 'kik', 'tk maxx'],
                category='Shopping',
                description='Clothing/Online shopping',
                priority=2
            ),
            CategoryPattern(
                keywords=['mediamarkt', 'saturn', 'apple', 'samsung', 'electronics', 'elektronik', 'handy', 'phone'],
                category='Shopping',
                description='Electronics',
                priority=2
            ),
            CategoryPattern(
                keywords=['ikea', 'bauhaus', 'obi', 'hornbach', 'baumarkt', 'möbel', 'furniture'],
                category='Shopping',
                description='Furniture/Home improvement',
                priority=2
            ),
            
            # Bills - Utilities, insurance, subscriptions
            CategoryPattern(
                keywords=['strom', 'electricity', 'gas', 'wasser', 'water', 'heizung', 'heating', 'miete', 'rent'],
                category='Bills',
                description='Utilities',
                priority=3
            ),
            CategoryPattern(
                keywords=['versicherung', 'insurance', 'krankenkasse', 'health insurance', 'haftpflicht'],
                category='Bills',
                description='Insurance',
                priority=3
            ),
            CategoryPattern(
                keywords=['netflix', 'spotify', 'amazon prime', 'disney+', 'youtube premium', 'subscription', 'abo'],
                category='Bills',
                description='Subscriptions',
                priority=2
            ),
            CategoryPattern(
                keywords=['internet', 'telefon', 'phone bill', 'handyvertrag', 'mobile'],
                category='Bills',
                description='Telecommunications',
                priority=2
            ),
            
            # Entertainment - Movies, games, events
            CategoryPattern(
                keywords=['kino', 'cinema', 'movie', 'film', 'theater', 'konzert', 'concert', 'event'],
                category='Entertainment',
                description='Movies/Events',
                priority=2
            ),
            CategoryPattern(
                keywords=['steam', 'playstation', 'xbox', 'nintendo', 'game', 'spiel', 'gaming'],
                category='Entertainment',
                description='Gaming',
                priority=2
            ),
            CategoryPattern(
                keywords=['bar', 'pub', 'club', 'disco', 'party', 'drinks', 'getränke'],
                category='Entertainment',
                description='Nightlife/Drinks',
                priority=2
            ),
            
            # Health - Medical, pharmacy, fitness
            CategoryPattern(
                keywords=['apotheke', 'pharmacy', 'medikamente', 'medicine', 'arzt', 'doctor', 'krankenhaus', 'hospital'],
                category='Health',
                description='Medical/Pharmacy',
                priority=3
            ),
            CategoryPattern(
                keywords=['fitness', 'gym', 'sport', 'sports', 'fitnessstudio', 'training'],
                category='Health',
                description='Fitness/Sports',
                priority=2
            ),
            
            # Other common patterns
            CategoryPattern(
                keywords=['parken', 'parking', 'parkhaus', 'garage'],
                category='Transport',
                description='Parking',
                priority=1
            ),
            CategoryPattern(
                keywords=['kaffee', 'coffee', 'starbucks', 'costa', 'tchibo'],
                category='Food',
                description='Coffee',
                priority=1
            ),
        ]
    
    def extract_amount(self, text: str) -> Optional[float]:
        """Extract monetary amount from text"""
        text_lower = text.lower()
        
        for pattern in self.amount_patterns:
            match = re.search(pattern, text_lower)
            if match:
                amount_str = match.group(1)
                # Convert German decimal format (comma) to float
                amount_str = amount_str.replace(',', '.')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        return None
    
    def categorize_text(self, text: str) -> Tuple[Optional[str], str, int]:
        """
        Categorize text based on patterns
        Returns: (category, description, confidence_score)
        """
        text_lower = text.lower()
        matches = []
        
        # Check each pattern
        for pattern in self.patterns:
            for keyword in pattern.keywords:
                if keyword in text_lower:
                    matches.append((pattern, keyword))
                    break  # Only match once per pattern
        
        if not matches:
            return None, "No pattern match found", 0
        
        # Sort by priority (higher is better) and return best match
        matches.sort(key=lambda x: x[0].priority, reverse=True)
        best_match = matches[0][0]
        
        # Calculate confidence based on priority and number of keyword matches
        confidence = best_match.priority * 10
        if len(matches) > 1:
            confidence += 5  # Bonus for multiple keyword matches
        
        return best_match.category, best_match.description, confidence
    
    def analyze_expense(self, text: str) -> Dict[str, any]:
        """
        Analyze expense text and return structured data
        Returns: {
            'amount': float or None,
            'category': str or None,
            'description': str,
            'confidence': int,
            'method': 'manual' or 'ai_fallback'
        }
        """
        # Extract amount
        amount = self.extract_amount(text)
        
        # Categorize text
        category, description, confidence = self.categorize_text(text)
        
        return {
            'amount': amount,
            'category': category,
            'description': description or text[:100],  # Use original text if no description
            'confidence': confidence,
            'method': 'manual'
        }
    
    def get_category_suggestions(self, text: str) -> List[Tuple[str, str, int]]:
        """
        Get all possible category matches for a text
        Returns: List of (category, description, confidence) tuples
        """
        text_lower = text.lower()
        suggestions = []
        
        for pattern in self.patterns:
            for keyword in pattern.keywords:
                if keyword in text_lower:
                    suggestions.append((pattern.category, pattern.description, pattern.priority))
                    break
        
        # Sort by priority
        suggestions.sort(key=lambda x: x[2], reverse=True)
        return suggestions

# Test the mapper
if __name__ == "__main__":
    mapper = ManualCategoryMapper()
    
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
    
    print("🧪 Testing Manual Category Mapper")
    print("=" * 50)
    
    for test in test_cases:
        result = mapper.analyze_expense(test)
        print(f"\nText: {test}")
        print(f"Amount: €{result['amount']:.2f}" if result['amount'] else "Amount: None")
        print(f"Category: {result['category']}")
        print(f"Description: {result['description']}")
        print(f"Confidence: {result['confidence']}/100")
        print(f"Method: {result['method']}")
