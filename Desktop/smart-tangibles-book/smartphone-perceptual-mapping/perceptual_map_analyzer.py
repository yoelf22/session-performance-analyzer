#!/usr/bin/env python3
"""
Perceptual Map Analyzer - Advanced Analysis and Visualization
============================================================

Advanced perceptual mapping tool with popularity-based bubble sizing,
correlation analysis, and strategic insights generation.

Usage:
    python perceptual_map_analyzer.py

Requirements:
    pip install pandas numpy matplotlib seaborn scipy

Features:
    - Create perceptual maps for any dimension combination
    - Popularity-based bubble sizing
    - Correlation analysis between dimensions and popularity
    - Strategic insights and opportunity identification
    - Export capabilities for all 28 dimension combinations
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib.patches import Ellipse
import itertools
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class PerceptualMapAnalyzer:
    """
    Advanced perceptual mapping tool that can create maps for any combination 
    of dimensions and analyze competitive positioning with popularity insights.
    """
    
    def __init__(self, average_ratings_df, include_popularity=True):
        """
        Initialize with average brand ratings data
        
        Args:
            average_ratings_df: DataFrame with phone data and ratings
            include_popularity: Whether to add popularity data for bubble sizing
        """
        self.data = average_ratings_df.copy()
        
        # If popularity not in data, add it
        if include_popularity and 'popularity' not in self.data.columns:
            self.data = self._add_popularity_data(self.data)
        
        # Identify dimension columns (exclude metadata columns)
        self.dimensions = [col for col in self.data.columns 
                          if col not in ['phone_model', 'brand', 'tier', 'popularity']]
        
        # Define color schemes for brands
        self.brand_colors = {
            'Apple': '#007AFF',
            'Samsung': '#1f77b4', 
            'Google': '#ff7f0e',
            'OnePlus': '#2ca02c',
            'Xiaomi': '#d62728'
        }
        
        # Define markers for tiers
        self.tier_markers = {
            'Premium': 'o',
            'Mid-range': 's', 
            'Budget': '^'
        }
        
        # Bubble size range for popularity scaling - more acute differences
        self.min_bubble_size = 50
        self.max_bubble_size = 1200
        
        print(f"🎯 Perceptual Map Analyzer initialized")
        print(f"📱 Analyzing {len(self.data)} phone models")
        print(f"📊 {len(self.dimensions)} dimensions available")
        print(f"🎨 Popularity-based bubble sizing: {'Enabled' if 'popularity' in self.data.columns else 'Disabled'}")
        
    def _add_popularity_data(self, df):
        """Add realistic popularity data if not present."""
        popularity_data = {
            'iPhone 15 Pro': 85,
            'iPhone 15': 78,
            'Samsung Galaxy S24 Ultra': 72,
            'Samsung Galaxy S24': 68,
            'Samsung Galaxy A54': 65,
            'Xiaomi Redmi Note 13': 58,
            'Google Pixel 7a': 52,
            'Google Pixel 8 Pro': 45,
            'Google Pixel 8': 42,
            'Xiaomi 14 Pro': 38,
            'OnePlus 12': 35,
            'OnePlus Nord 3': 28
        }
        
        df['popularity'] = df['phone_model'].map(popularity_data)
        return df
    
    def _calculate_bubble_size(self, popularity_score):
        """Calculate bubble size based on popularity score."""
        if pd.isna(popularity_score):
            return self.min_bubble_size
            
        # Scale popularity to bubble size range
        normalized_pop = (popularity_score - 1) / 99  # Normalize to 0-1
        size = self.min_bubble_size + (normalized_pop * (self.max_bubble_size - self.min_bubble_size))
        return size
    
    def _add_smart_labels_with_leaders(self, ax, x_dimension, y_dimension):
        """Add labels with short leader lines at 2-3 diameter distance from circle center."""
        import numpy as np
        
        for _, row in self.data.iterrows():
            label = row['phone_model'].replace('Samsung Galaxy ', 'Galaxy ')
            label = label.replace('Google Pixel ', 'Pixel ')
            
            # Calculate bubble radius in data coordinates
            bubble_size = self._calculate_bubble_size(row.get('popularity', 50))
            # Convert matplotlib size to radius (size is area, so sqrt to get radius)
            radius_points = np.sqrt(bubble_size) / 2
            
            # Convert radius from points to data coordinates (approximate)
            x_range = ax.get_xlim()[1] - ax.get_xlim()[0]
            y_range = ax.get_ylim()[1] - ax.get_ylim()[0]
            fig_width_inches = ax.figure.get_figwidth()
            fig_height_inches = ax.figure.get_figheight()
            
            # Rough conversion from points to data units
            radius_data_x = (radius_points / 72) * (x_range / fig_width_inches)
            radius_data_y = (radius_points / 72) * (y_range / fig_height_inches)
            
            # Position label at 2.5 diameters to the left of circle center
            label_offset_x = -2.5 * 2 * radius_data_x  # 2.5 diameters
            label_offset_y = 0  # Keep at same height as circle center
            
            label_x = row[x_dimension] + label_offset_x
            label_y = row[y_dimension] + label_offset_y
            
            # Get brand color and make it lighter for background
            brand = row['brand']
            bubble_color = self.brand_colors.get(brand, '#666666')
            
            # Convert hex to lighter shade for background
            def lighten_color(hex_color, factor=0.3):
                """Convert hex color to lighter shade"""
                import matplotlib.colors as mcolors
                rgb = mcolors.hex2color(hex_color)
                # Lighten by mixing with white
                light_rgb = [min(1, c + (1-c) * factor) for c in rgb]
                return mcolors.rgb2hex(light_rgb)
            
            bg_color = lighten_color(bubble_color, 0.7)  # Very light version
            
            # Add the label
            ax.annotate(label, 
                       xy=(row[x_dimension], row[y_dimension]),  # Point to circle center
                       xytext=(label_x, label_y),  # Label position
                       xycoords='data',
                       textcoords='data',
                       fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', 
                               facecolor=bg_color, alpha=0.9, 
                               edgecolor=bubble_color, linewidth=1),
                       arrowprops=dict(arrowstyle='-', 
                                     color=bubble_color, alpha=0.7, linewidth=1),
                       ha='right', va='center')
    
    def create_perceptual_map(self, x_dimension, y_dimension, 
                            title=None, save_path=None, 
                            show_quadrant_labels=True,
                            show_brand_ellipses=False,
                            show_popularity_legend=True,
                            figsize=(11.2, 8)):
        """
        Create a perceptual map for any two dimensions with bubble sizes based on popularity
        """
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Get data for the two dimensions
        x_data = self.data[x_dimension]
        y_data = self.data[y_dimension]
        
        # Create scatter plot with popularity-based bubble sizes
        for _, row in self.data.iterrows():
            brand = row['brand']
            tier = row['tier']
            popularity = row.get('popularity', 50)
            
            color = self.brand_colors.get(brand, '#666666')
            marker = 'o'  # Use circles for all phones regardless of tier
            bubble_size = self._calculate_bubble_size(popularity)
            
            # Create scatter plot
            ax.scatter(row[x_dimension], row[y_dimension], 
                      c=color, marker=marker, s=bubble_size, 
                      alpha=0.7, edgecolors='black', linewidth=1.5)
        
        # Add smart labels with leader lines
        self._add_smart_labels_with_leaders(ax, x_dimension, y_dimension)
        
        # Add reference lines at means
        ax.axhline(y_data.mean(), color='gray', linestyle='--', alpha=0.5, linewidth=1)
        ax.axvline(x_data.mean(), color='gray', linestyle='--', alpha=0.5, linewidth=1)
        
        # Customize axes
        ax.set_xlabel(x_dimension.replace('_', ' ').title(), fontsize=14, fontweight='bold')
        ax.set_ylabel(y_dimension.replace('_', ' ').title(), fontsize=14, fontweight='bold')
        
        # Set axis limits with padding
        x_min, x_max = x_data.min(), x_data.max()
        y_min, y_max = y_data.min(), y_data.max()
        x_padding = (x_max - x_min) * 0.15
        y_padding = (y_max - y_min) * 0.15
        
        ax.set_xlim(x_min - x_padding, x_max + x_padding)
        ax.set_ylim(y_min - y_padding, y_max + y_padding)
        
        # Add quadrant labels if requested
        if show_quadrant_labels:
            quadrant_configs = [
                (x_max - x_padding/3, y_max - y_padding/3, 'Leaders', 'lightgreen'),
                (x_min + x_padding/3, y_max - y_padding/3, 'Niche Players', 'lightblue'),
                (x_min + x_padding/3, y_min + y_padding/3, 'Challenged', 'lightcoral'),
                (x_max - x_padding/3, y_min + y_padding/3, 'Specialists', 'lightyellow')
            ]
            
            for x_pos, y_pos, label, color in quadrant_configs:
                ax.text(x_pos, y_pos, label, ha='center', va='center',
                       fontsize=12, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor=color, alpha=0.8))
        
        # Create legend
        self._create_enhanced_legend(ax, show_popularity_legend)
        
        # Add title
        if title is None:
            title = f'Smartphone Perceptual Map: {x_dimension.replace("_", " ")} vs {y_dimension.replace("_", " ")}'
            if 'popularity' in self.data.columns:
                title += '\n(Bubble size = Market popularity)'
        
        ax.set_title(title, fontsize=16, fontweight='bold', pad=25)
        
        # Add grid
        ax.grid(True, alpha=0.3, linestyle=':')
        
        plt.tight_layout()
        
        # Save if path provided
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"📁 Map saved to: {save_path}")
        
        plt.show()
        return fig, ax
    
    def _create_enhanced_legend(self, ax, show_popularity_legend):
        """Create comprehensive legend including brands, tiers, and popularity sizes."""
        
        # Brand legend
        brand_handles = []
        for brand, color in self.brand_colors.items():
            if brand in self.data['brand'].values:
                handle = plt.Line2D([0], [0], marker='o', color='w', 
                                  markerfacecolor=color, markersize=12,
                                  markeredgecolor='black', markeredgewidth=1.5, 
                                  label=brand, linestyle='None')
                brand_handles.append(handle)
        
        # Create brand legend
        if brand_handles:
            brand_legend = ax.legend(handles=brand_handles, title='Brands', 
                                   loc='upper left', bbox_to_anchor=(1.02, 1),
                                   fontsize=10, title_fontsize=12)
            brand_legend.get_title().set_fontweight('bold')
            ax.add_artist(brand_legend)
    
    def analyze_popularity_performance_relationship(self, dimension):
        """Analyze relationship between popularity and performance on a dimension."""
        if 'popularity' not in self.data.columns:
            return "Popularity data not available"
        
        correlation, p_value = stats.pearsonr(self.data['popularity'], self.data[dimension])
        
        analysis = {
            'dimension': dimension,
            'correlation_coefficient': round(correlation, 3),
            'p_value': round(p_value, 3),
            'correlation_strength': self._interpret_correlation(correlation),
            'significant': p_value < 0.05,
            'insights': []
        }
        
        # Generate insights
        if analysis['significant']:
            if abs(correlation) > 0.5:
                direction = "positive" if correlation > 0 else "negative"
                analysis['insights'].append(f"Strong {direction} correlation between popularity and {dimension.replace('_', ' ')}")
            elif abs(correlation) > 0.3:
                direction = "positive" if correlation > 0 else "negative"  
                analysis['insights'].append(f"Moderate {direction} correlation between popularity and {dimension.replace('_', ' ')}")
        else:
            analysis['insights'].append(f"No significant correlation between popularity and {dimension.replace('_', ' ')}")
        
        # Find outliers
        performance_mean = self.data[dimension].mean()
        popularity_mean = self.data['popularity'].mean()
        
        high_perf_low_pop = self.data[(self.data[dimension] > performance_mean) & 
                                     (self.data['popularity'] < popularity_mean)]
        
        if len(high_perf_low_pop) > 0:
            models = high_perf_low_pop['phone_model'].tolist()
            analysis['insights'].append(f"Hidden gems (high {dimension.replace('_', ' ')}, low popularity): {', '.join(models)}")
        
        return analysis
    
    def _interpret_correlation(self, correlation):
        """Interpret correlation coefficient strength."""
        abs_corr = abs(correlation)
        if abs_corr >= 0.7:
            return "Very Strong"
        elif abs_corr >= 0.5:
            return "Strong"
        elif abs_corr >= 0.3:
            return "Moderate"
        elif abs_corr >= 0.1:
            return "Weak"
        else:
            return "Very Weak"
    
    def create_correlation_matrix(self, include_popularity=True, figsize=(12, 10)):
        """Create correlation matrix heatmap of all dimensions."""
        
        # Select columns for correlation
        corr_columns = self.dimensions.copy()
        if include_popularity and 'popularity' in self.data.columns:
            corr_columns.append('popularity')
        
        # Calculate correlation matrix
        corr_matrix = self.data[corr_columns].corr()
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=figsize)
        
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        
        sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='RdYlBu_r',
                   center=0, square=True, linewidths=0.5, 
                   cbar_kws={"shrink": .8}, fmt='.3f', ax=ax)
        
        ax.set_title('Dimension Correlation Matrix\n(Including Popularity)', 
                    fontsize=16, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.show()
        
        return corr_matrix
    
    def generate_all_dimension_maps(self, output_dir='perceptual_maps', file_format='png'):
        """Generate perceptual maps for all possible dimension combinations."""
        import os
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        dimension_pairs = list(itertools.combinations(self.dimensions, 2))
        
        print(f"📊 Generating {len(dimension_pairs)} perceptual maps...")
        
        for i, (dim_x, dim_y) in enumerate(dimension_pairs, 1):
            print(f"  Creating map {i}/{len(dimension_pairs)}: {dim_x} vs {dim_y}")
            
            # Create filename
            filename = f"{dim_x}_vs_{dim_y}.{file_format}"
            filepath = os.path.join(output_dir, filename)
            
            # Create map
            fig, ax = self.create_perceptual_map(dim_x, dim_y, 
                                              save_path=filepath,
                                              show_quadrant_labels=True)
            
            plt.close(fig)  # Close figure to save memory
        
        print(f"✅ All {len(dimension_pairs)} maps generated in '{output_dir}' directory")
        return dimension_pairs

def create_sample_dataset():
    """Create sample dataset for demonstration if CSV files not available."""
    sample_data = pd.DataFrame({
        'phone_model': [
            'iPhone 15 Pro', 'iPhone 15', 'Samsung Galaxy S24 Ultra', 'Samsung Galaxy S24',
            'Google Pixel 8 Pro', 'Google Pixel 8', 'OnePlus 12', 'Xiaomi 14 Pro',
            'Samsung Galaxy A54', 'Google Pixel 7a', 'OnePlus Nord 3', 'Xiaomi Redmi Note 13'
        ],
        'brand': [
            'Apple', 'Apple', 'Samsung', 'Samsung',
            'Google', 'Google', 'OnePlus', 'Xiaomi', 
            'Samsung', 'Google', 'OnePlus', 'Xiaomi'
        ],
        'tier': [
            'Premium', 'Premium', 'Premium', 'Premium',
            'Premium', 'Premium', 'Premium', 'Premium',
            'Mid-range', 'Mid-range', 'Mid-range', 'Budget'
        ],
        'popularity': [85, 78, 72, 68, 45, 42, 35, 38, 65, 52, 28, 58],
        'Camera_Quality': [8.5, 8.0, 9.0, 8.3, 8.8, 8.4, 7.8, 7.9, 6.8, 7.8, 6.5, 5.8],
        'Battery_Life': [7.5, 7.2, 8.2, 7.8, 7.6, 7.2, 8.4, 8.1, 7.5, 6.9, 7.8, 8.2],
        'Performance': [9.2, 8.8, 8.9, 8.5, 8.2, 7.9, 8.7, 8.4, 6.5, 6.8, 7.2, 5.9],
        'Price_Value': [4.0, 4.8, 5.5, 6.2, 6.8, 7.5, 7.8, 8.5, 7.9, 8.2, 8.0, 8.8],
        'Build_Quality': [9.0, 8.7, 8.8, 8.4, 7.9, 7.6, 8.0, 7.7, 6.9, 6.5, 6.8, 5.5],
        'Display_Quality': [8.8, 8.3, 9.2, 8.7, 8.4, 8.0, 8.5, 8.2, 7.2, 7.0, 7.4, 6.2],
        'Design_Appeal': [9.1, 8.8, 8.3, 8.0, 7.5, 7.2, 7.9, 7.6, 7.1, 6.8, 6.9, 5.9],
        'Feature_Richness': [8.0, 7.5, 9.1, 8.5, 7.8, 7.4, 8.2, 8.7, 7.0, 6.7, 7.1, 6.8]
    })
    
    print(f"📝 Created sample dataset with {len(sample_data)} phone models")
    return sample_data

def main():
    """Main execution function with interactive options."""
    print("🎯 Perceptual Map Analyzer")
    print("=" * 40)
    
    # Check if running as standalone or with generated data
    try:
        # Try to load generated data
        df = pd.read_csv('average_brand_ratings.csv')
        print(f"✅ Using generated data: {len(df)} phone models")
        
        # Initialize analyzer
        analyzer = PerceptualMapAnalyzer(df, include_popularity=True)
        
    except FileNotFoundError:
        print("📝 CSV files not found. Using sample dataset...")
        
        # Use sample data
        sample_df = create_sample_dataset()
        analyzer = PerceptualMapAnalyzer(sample_df, include_popularity=True)
    
    print(f"\n📋 Available Options:")
    print(f"1. Quick Demo - Sample maps and analysis")
    print(f"2. Custom Analysis - Choose your own dimensions") 
    print(f"3. Generate All Maps - Create all 28 combinations")
    print(f"4. Correlation Analysis - Show relationships")
    
    choice = input("\n🎯 Select option (1-4) or press Enter for Quick Demo: ").strip()
    
    if choice == '2':
        print(f"\n📊 Available Dimensions:")
        for i, dim in enumerate(analyzer.dimensions, 1):
            print(f"  {i}. {dim.replace('_', ' ')}")
        
        x_dim = analyzer.dimensions[0]  # Default
        y_dim = analyzer.dimensions[1]  # Default
        
        try:
            x_choice = int(input("Select X-axis dimension (number): ")) - 1
            y_choice = int(input("Select Y-axis dimension (number): ")) - 1
            x_dim = analyzer.dimensions[x_choice]
            y_dim = analyzer.dimensions[y_choice]
        except (ValueError, IndexError):
            print("Using default dimensions...")
        
        analyzer.create_perceptual_map(x_dim, y_dim)
        
    elif choice == '3':
        analyzer.generate_all_dimension_maps()
        
    elif choice == '4':
        print(f"\n📊 Correlation Analysis:")
        corr_matrix = analyzer.create_correlation_matrix()
        
    else:  # Default Quick Demo
        print(f"\n🚀 Quick Demo - Sample Analysis")
        
        # Create sample maps
        analyzer.create_perceptual_map('Camera_Quality', 'Price_Value')
        
        # Show correlation analysis
        print(f"\n📊 Correlation Analysis:")
        corr_matrix = analyzer.create_correlation_matrix()
        
        # Popularity analysis
        analysis = analyzer.analyze_popularity_performance_relationship('Performance')
        print(f"\n🏆 Performance vs Popularity:")
        print(f"Correlation: {analysis['correlation_coefficient']} ({analysis['correlation_strength']})")
        
        print(f"\n✅ Quick demo complete!")

if __name__ == "__main__":
    main()
