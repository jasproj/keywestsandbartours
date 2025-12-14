#!/usr/bin/env python3
"""Convert FareHarbor marketplace CSV to tours-data.json format for Key West Sandbar Tours"""

import csv
import json
import re

def extract_location(location_str):
    """Extract the city/area from the full location string"""
    if not location_str:
        return "Key West"
    
    # Format is like: United States/Florida/Key West
    parts = location_str.split('/')
    if len(parts) >= 3:
        return parts[-1].strip()
    return "Key West"

def get_island(location):
    """Map location to island/area for filtering"""
    location_lower = location.lower()
    
    # Check for specific areas
    if 'stock island' in location_lower:
        return 'stock island'
    elif 'marathon' in location_lower:
        return 'marathon'
    elif 'islamorada' in location_lower:
        return 'islamorada'
    elif 'big pine' in location_lower or 'pine key' in location_lower:
        return 'big pine key'
    elif 'sugarloaf' in location_lower or 'summerland' in location_lower:
        return 'lower keys'
    elif 'key largo' in location_lower:
        return 'key largo'
    elif 'tavernier' in location_lower:
        return 'islamorada'
    else:
        return 'key west'

def parse_tags(tags_str):
    """Parse tags from dash-separated string"""
    if not tags_str:
        return []
    return [tag.strip() for tag in tags_str.split('-') if tag.strip()]

def clean_name(name):
    """Clean up tour name"""
    # Remove extra whitespace
    name = ' '.join(name.split())
    return name

def convert_csv_to_json(csv_path, json_path):
    """Convert CSV to JSON format"""
    tours = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            location = extract_location(row.get('location', ''))
            island = get_island(location)
            quality_score = int(row.get('quality_score', 0)) if row.get('quality_score') else 0
            
            # Only include tours with quality score > 0 (active tours)
            if quality_score <= 0:
                continue
            
            tour = {
                "id": row.get('item_id', ''),
                "name": clean_name(row.get('item_name', '')),
                "company": row.get('company_name', ''),
                "island": island,
                "location": location,
                "tags": parse_tags(row.get('tags', '')),
                "image": row.get('image_url', ''),
                "qualityScore": quality_score,
                "bookingLink": row.get('regular_link', '')
            }
            
            tours.append(tour)
    
    # Sort by quality score descending
    tours.sort(key=lambda x: x['qualityScore'], reverse=True)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(tours, f, indent=2, ensure_ascii=False)
    
    # Print stats
    print(f"Total tours: {len(tours)}")
    
    # Count by area
    area_counts = {}
    for tour in tours:
        area = tour['island']
        area_counts[area] = area_counts.get(area, 0) + 1
    
    print("\nTours by area:")
    for area, count in sorted(area_counts.items(), key=lambda x: -x[1]):
        print(f"  {area}: {count}")
    
    return tours

if __name__ == "__main__":
    import sys
    
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "marketplace-top-items-2025-12-14.csv"
    json_path = sys.argv[2] if len(sys.argv) > 2 else "tours-data.json"
    
    convert_csv_to_json(csv_path, json_path)
    print(f"\nSaved to {json_path}")
