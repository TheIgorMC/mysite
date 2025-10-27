"""
Archery analysis utility functions
"""
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional

def parse_date_safely(date_str, default='2000-01-01'):
    """
    Safely parse date strings in various formats.
    Returns YYYY-MM-DD format or default if parsing fails.
    """
    if not date_str:
        return default
    
    try:
        # Try common date formats
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%m/%d/%Y']:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # If no format matches, try parsing as ISO format
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime('%Y-%m-%d')
    except (ValueError, AttributeError):
        print(f"Warning: Could not parse date '{date_str}', using default")
        return default

# Get the data directory path
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
COMPETITION_DATA_FILE = os.path.join(DATA_DIR, 'competition_arrows.csv')

# Cache for competition data
_competition_data_cache = None

def load_competition_data() -> List[Dict]:
    """Load competition data from CSV file"""
    global _competition_data_cache
    
    if _competition_data_cache is not None:
        return _competition_data_cache
    
    competition_data = []
    
    try:
        with open(COMPETITION_DATA_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle empty values for arrow_count and max_score
                arrow_count = None
                max_score = None
                
                try:
                    if row['arrow_count'] and row['arrow_count'].strip():
                        arrow_count = int(row['arrow_count'])
                except (ValueError, KeyError):
                    pass
                
                try:
                    if row['max_score'] and row['max_score'].strip():
                        max_score = int(row['max_score'])
                except (ValueError, KeyError):
                    pass
                
                competition_data.append({
                    'type': row['competition_type'],
                    'category': row['category'],
                    'arrow_count': arrow_count,
                    'max_score': max_score
                })
        
        _competition_data_cache = competition_data
    except FileNotFoundError:
        # Return empty list if file doesn't exist
        pass
    except Exception as e:
        # Log error but don't crash
        print(f"Error loading competition data: {e}")
    
    return competition_data

def get_competition_info(competition_type: str) -> Optional[Dict]:
    """Get competition information by type"""
    data = load_competition_data()
    
    for comp in data:
        if comp['type'] == competition_type:
            return comp
    
    return None

def get_competition_category(competition_type: str) -> str:
    """Get category (indoor/outdoor) for a competition type"""
    info = get_competition_info(competition_type)
    return info['category'] if info else 'unknown'

def get_arrow_count(competition_type: str) -> Optional[int]:
    """Get arrow count for a competition type"""
    info = get_competition_info(competition_type)
    return info['arrow_count'] if info else None

def calculate_average_score(score: int, competition_type: str) -> Optional[float]:
    """Calculate average score per arrow for a competition"""
    arrow_count = get_arrow_count(competition_type)
    
    if arrow_count and arrow_count > 0:
        return round(score / arrow_count, 2)
    
    return None

def get_categories() -> List[str]:
    """Get list of unique categories"""
    data = load_competition_data()
    categories = set(comp['category'] for comp in data)
    return sorted(list(categories))

def get_competition_types_by_category(category: str) -> List[str]:
    """Get all competition types for a specific category"""
    data = load_competition_data()
    types = [comp['type'] for comp in data if comp['category'] == category]
    return sorted(types)

def calculate_medal_count(results: List[Dict]) -> Dict:
    """Calculate medal distribution from results"""
    medals = {
        'gold': 0,
        'silver': 0,
        'bronze': 0,
        'total': 0
    }
    
    for result in results:
        position = result.get('position')
        if position == 1:
            medals['gold'] += 1
        elif position == 2:
            medals['silver'] += 1
        elif position == 3:
            medals['bronze'] += 1
    
    medals['total'] = len(results)
    
    return medals

def calculate_percentile_stats(results: List[Dict], last_n: int = 10) -> Dict:
    """Calculate percentile statistics for recent competitions"""
    if not results:
        return {
            'avg_position': None,
            'avg_percentile': None,
            'top_finishes': 0
        }
    
    # Sort by date (most recent first) - handle None/missing dates safely
    sorted_results = sorted(
        results, 
        key=lambda x: parse_date_safely(x.get('date') or '', '2000-01-01') or '2000-01-01',
        reverse=True
    )
    
    # Take last N competitions
    recent = sorted_results[:last_n]
    
    positions = [r.get('position') for r in recent if r.get('position')]
    
    if not positions:
        return {
            'avg_position': None,
            'avg_percentile': None,
            'top_finishes': 0
        }
    
    avg_position = sum(positions) / len(positions)
    
    # Estimate percentile (rough calculation assuming ~30 participants on average)
    # This is a simplified calculation; actual percentile would need total participants
    estimated_percentile = min(100, (avg_position / 30) * 100)
    
    # Count top 3 finishes
    top_finishes = sum(1 for p in positions if p <= 3)
    
    return {
        'avg_position': round(avg_position, 1),
        'avg_percentile': round(estimated_percentile, 1),
        'top_finishes': top_finishes,
        'competitions_analyzed': len(recent)
    }

def get_best_score_by_category(results: List[Dict]) -> Dict:
    """Get best scores grouped by category"""
    data = load_competition_data()
    category_scores = {}
    
    for result in results:
        comp_type = result.get('competition_type')
        score = result.get('score')
        
        # Skip if missing data or score is None/0
        if not comp_type or score is None or score == 0:
            continue
        
        # Find category for this competition type
        category = get_competition_category(comp_type)
        
        if category not in category_scores:
            category_scores[category] = {
                'score': score,
                'competition': result.get('competition_name'),
                'date': result.get('date'),
                'type': comp_type
            }
        elif score > category_scores[category]['score']:
            category_scores[category] = {
                'score': score,
                'competition': result.get('competition_name'),
                'date': result.get('date'),
                'type': comp_type
            }
    
    return category_scores

def calculate_average_per_competition(results: List[Dict], include_average: bool = True) -> List[Dict]:
    """
    Process results and optionally add average score per arrow
    """
    processed_results = []
    
    for result in results:
        processed = result.copy()
        
        if include_average:
            score = result.get('score')
            comp_type = result.get('competition_type')
            
            if score and comp_type:
                avg = calculate_average_score(score, comp_type)
                processed['average_per_arrow'] = avg
                processed['arrow_count'] = get_arrow_count(comp_type)
        
        processed_results.append(processed)
    
    return processed_results

def filter_by_category(results: List[Dict], category: str) -> List[Dict]:
    """Filter results by category (indoor/outdoor)"""
    filtered = []
    
    for result in results:
        comp_type = result.get('competition_type')
        if comp_type and get_competition_category(comp_type) == category:
            filtered.append(result)
    
    return filtered

def get_statistics_summary(results: List[Dict], last_n: int = 10) -> Dict:
    """
    Generate comprehensive statistics summary
    """
    if not results:
        return {
            'total_competitions': 0,
            'medals': {'gold': 0, 'silver': 0, 'bronze': 0},
            'best_scores': {},
            'percentile_stats': {},
            'categories': {}
        }
    
    # Calculate medals
    medals = calculate_medal_count(results)
    
    # Calculate percentile stats
    percentile_stats = calculate_percentile_stats(results, last_n)
    
    # Get best scores by category
    best_scores = get_best_score_by_category(results)
    
    # Get category breakdown
    categories = {}
    for category in get_categories():
        cat_results = filter_by_category(results, category)
        # Filter out None scores before finding max
        valid_scores = [r.get('score', 0) for r in cat_results if r.get('score') is not None]
        categories[category] = {
            'count': len(cat_results),
            'best_score': max(valid_scores, default=0) if valid_scores else 0
        }
    
    return {
        'total_competitions': len(results),
        'medals': medals,
        'best_scores': best_scores,
        'percentile_stats': percentile_stats,
        'categories': categories
    }
