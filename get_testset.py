#!/usr/bin/env python3
"""
Script to fetch testset details using Scorecard SDK
"""

import os
from scorecard_ai import Scorecard
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Scorecard client
scorecard = Scorecard(
    environment="staging", 
    api_key=os.getenv("SCORECARD_API_KEY")
)

# Testset ID
testset_id = "17858"
project_id = "206"

try:
    # Get the testset details
    testset = scorecard.testsets.get(testset_id=testset_id)
    
    print(f"Testset ID: {testset.id}")
    print(f"Testset Name: {testset.name}")
    if hasattr(testset, 'description'):
        print(f"Testset Description: {testset.description}")
    
    # Print all available attributes to see what's available
    print(f"Testset attributes: {[attr for attr in dir(testset) if not attr.startswith('_')]}")
    
    # Try common attributes
    for attr in ['project_id', 'projectId', 'created_at', 'updated_at', 'createdAt', 'updatedAt']:
        if hasattr(testset, attr):
            print(f"{attr}: {getattr(testset, attr)}")
    
    # Get testcases in the testset - try different approaches
    try:
        # Try direct testcases access
        testcases = scorecard.testcases.list(testset_id=testset_id)
        print(f"\nNumber of testcases: {len(testcases.data)}")
        
        for i, testcase in enumerate(testcases.data):
            print(f"\n--- Testcase {i+1} ---")
            print(f"ID: {testcase.id}")
            
            # Print all available attributes
            attrs = [attr for attr in dir(testcase) if not attr.startswith('_')]
            print(f"Available attributes: {attrs}")
            
            # Try to access common testcase attributes
            for attr in ['inputs', 'expected_outputs', 'metadata', 'tags', 'data', 'content']:
                if hasattr(testcase, attr):
                    value = getattr(testcase, attr)
                    print(f"{attr}: {value}")
                    
    except Exception as e:
        print(f"Error getting testcases with direct approach: {e}")
        
        # Try alternative approach
        try:
            # Check what methods are available on testsets
            print(f"Testsets methods: {[method for method in dir(scorecard.testsets) if not method.startswith('_')]}")
            
        except Exception as e2:
            print(f"Error exploring testsets methods: {e2}")
    
    # Print the full testset object for debugging
    print(f"\n--- Full Testset Object ---")
    print(f"Testset attributes: {[attr for attr in dir(testset) if not attr.startswith('_')]}")
    print(testset)
    
except Exception as e:
    print(f"Error fetching testset: {e}")