#!/usr/bin/env python3
"""
LinkedIn CSV Data Processor
Utility script for processing LinkedIn connection data
"""

import csv
import json
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

class LinkedInDataProcessor:
    """Processes LinkedIn export data"""
    
    @staticmethod
    def validate_csv_format(csv_file_path: str) -> Dict[str, Any]:
        """Validate the format of the LinkedIn CSV file"""
        try:
            df = pd.read_csv(csv_file_path)
            
            # Check for required columns
            required_columns = ['First Name', 'Last Name']
            optional_columns = ['Email Address', 'Company', 'Position']
            
            found_columns = df.columns.tolist()
            missing_required = [col for col in required_columns if col not in found_columns]
            available_optional = [col for col in optional_columns if col in found_columns]
            
            return {
                "valid": len(missing_required) == 0,
                "total_rows": len(df),
                "columns": found_columns,
                "missing_required": missing_required,
                "available_optional": available_optional,
                "sample_data": df.head(3).to_dict('records') if len(df) > 0 else []
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    @staticmethod
    def clean_contact_data(raw_data: Dict[str, Any]) -> Dict[str, str]:
        """Clean and standardize contact data"""
        cleaned = {}
        
        # Combine first and last name
        first_name = str(raw_data.get('First Name', '')).strip()
        last_name = str(raw_data.get('Last Name', '')).strip()
        cleaned['name'] = f"{first_name} {last_name}".strip()
        
        # Clean other fields
        cleaned['position'] = str(raw_data.get('Position', '')).strip()
        cleaned['company'] = str(raw_data.get('Company', '')).strip()
        cleaned['email'] = str(raw_data.get('Email Address', '')).strip()
        
        # Remove 'nan' values
        for key, value in cleaned.items():
            if value.lower() == 'nan' or value == 'None':
                cleaned[key] = ''
        
        return cleaned
    
    @staticmethod
    def export_for_analysis(contacts: List[Dict], output_file: str):
        """Export cleaned contacts for further analysis"""
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['name', 'position', 'company', 'email']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for contact in contacts:
                writer.writerow(contact)
        
        print(f"✅ Exported {len(contacts)} cleaned contacts to {output_file}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python data_processor.py <linkedin_csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # Validate CSV format
    validation = LinkedInDataProcessor.validate_csv_format(csv_file)
    
    if not validation['valid']:
        print(f"❌ Invalid CSV format: {validation.get('error', 'Missing required columns')}")
        if 'missing_required' in validation:
            print(f"Missing columns: {validation['missing_required']}")
        sys.exit(1)
    
    print(f"✅ Valid CSV with {validation['total_rows']} rows")
    print(f"Available columns: {validation['columns']}")
    
    # Process data
    df = pd.read_csv(csv_file)
    cleaned_contacts = []
    
    for _, row in df.iterrows():
        cleaned = LinkedInDataProcessor.clean_contact_data(row.to_dict())
        if cleaned['name'] and cleaned['name'] != " ":
            cleaned_contacts.append(cleaned)
    
    # Export cleaned data
    output_file = csv_file.replace('.csv', '_cleaned.csv')
    LinkedInDataProcessor.export_for_analysis(cleaned_contacts, output_file)
    
    print(f"\n📊 Summary:")
    print(f"  - Total rows: {validation['total_rows']}")
    print(f"  - Valid contacts: {len(cleaned_contacts)}")
    print(f"  - Cleaned file: {output_file}")
