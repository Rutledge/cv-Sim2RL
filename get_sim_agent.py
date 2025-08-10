#!/usr/bin/env python3
"""
Script to fetch sim agent system details using Scorecard SDK
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

# Sim agent ID from the URL
sim_agent_id = "97d50674-a8d8-471c-baa6-42f44281a655"

try:
    # Get the sim agent system details
    system = scorecard.systems.get(system_id=sim_agent_id)
    
    print(f"System ID: {system.id}")
    print(f"System Name: {system.name}")
    print(f"System Description: {system.description}")
    
    if system.production_version:
        print(f"Production Version ID: {system.production_version.id}")
        
        # Try to access all available attributes
        version = system.production_version
        print(f"Production Version attributes: {dir(version)}")
        
        # Try common attribute names
        for attr in ['system_prompt', 'prompt', 'instructions', 'model', 'temperature', 'tools', 'config']:
            if hasattr(version, attr):
                print(f"Production Version {attr}: {getattr(version, attr)}")
        
        # Get the full version details
        try:
            full_version = scorecard.systems.versions.get(system_id=sim_agent_id, version_id=version.id)
            print(f"\n--- Full Version Details ---")
            print(f"Full Version attributes: {dir(full_version)}")
            
            for attr in ['system_prompt', 'prompt', 'instructions', 'model', 'temperature', 'tools', 'config']:
                if hasattr(full_version, attr):
                    value = getattr(full_version, attr)
                    print(f"{attr}: {value}")
        except Exception as e:
            print(f"Error getting full version: {e}")
            
    # Print the full system object for debugging
    print("\n--- Full System Object ---")
    print(system)
    
except Exception as e:
    print(f"Error fetching sim agent: {e}")