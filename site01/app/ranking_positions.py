"""
Ranking positions CSV parser
Manages the number of available positions per ranking/class/division
"""
import csv
import os
from flask import current_app

class RankingPositions:
    def __init__(self, csv_path=None):
        """Initialize ranking positions manager
        
        Args:
            csv_path: Path to CSV file. If None, uses default app/data/ranking_positions.csv
        """
        if csv_path is None:
            # Default path relative to app directory
            app_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(app_dir, 'data', 'ranking_positions.csv')
        
        self.csv_path = csv_path
        self.positions = {}  # Dict: (qualifica, classe_gara, categoria) -> posti_disponibili
        self.load_csv()
    
    def load_csv(self):
        """Load ranking positions from CSV file"""
        self.positions = {}
        
        if not os.path.exists(self.csv_path):
            current_app.logger.warning(f"Ranking positions CSV not found: {self.csv_path}")
            return
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = (
                        row['qualifica'].strip(),
                        row['classe_gara'].strip(),
                        row['categoria'].strip()
                    )
                    self.positions[key] = int(row['posti_disponibili'])
            
            current_app.logger.info(f"Loaded {len(self.positions)} ranking position configurations")
        
        except Exception as e:
            current_app.logger.error(f"Error loading ranking positions CSV: {e}")
    
    def get_positions(self, qualifica, classe_gara, categoria):
        """Get number of available positions for a specific ranking/class/division
        
        Args:
            qualifica: Ranking code (e.g. "RegionaleIndoor2026Veneto")
            classe_gara: Class (e.g. "Senior Maschile")
            categoria: Division (e.g. "Arco Olimpico")
            
        Returns:
            Number of positions or None if not configured
        """
        key = (qualifica.strip(), classe_gara.strip(), categoria.strip())
        return self.positions.get(key)
    
    def reload(self):
        """Reload CSV file (useful after manual updates)"""
        self.load_csv()
    
    def get_all_positions(self):
        """Get all configured positions as a list of dicts
        
        Returns:
            List of dicts with qualifica, classe_gara, categoria, posti_disponibili
        """
        result = []
        for (qualifica, classe_gara, categoria), posti in self.positions.items():
            result.append({
                'qualifica': qualifica,
                'classe_gara': classe_gara,
                'categoria': categoria,
                'posti_disponibili': posti
            })
        return result


# Global instance
_ranking_positions = None

def get_ranking_positions():
    """Get global RankingPositions instance (singleton pattern)"""
    global _ranking_positions
    if _ranking_positions is None:
        _ranking_positions = RankingPositions()
    return _ranking_positions
