#!/usr/bin/env python3
"""
Smartphone Quantitative Assessment System
==========================================

Generates realistic quantitative brand ratings from 200 respondents
across 12 smartphone models and 8 positioning dimensions.

Usage:
    python quantitative_assessment_system.py

Output:
    - respondent_profiles.csv
    - quantitative_brand_ratings.csv
    - average_brand_ratings.csv
    - perceptual_map_combinations.csv
"""

import pandas as pd
import numpy as np
import random
import itertools
from typing import Dict, List, Tuple
import json

class QuantitativeAssessmentSystem:
    """
    System for collecting quantitative brand ratings on identified dimensions
    and generating all possible perceptual map combinations with popularity data.
    """
    
    def __init__(self):
        # Set seeds for reproducible results
        random.seed(42)
        np.random.seed(42)
        
        # Identified dimensions from qualitative analysis
        self.dimensions = {
            'Camera_Quality': 'Photography and video capabilities',
            'Battery_Life': 'Battery performance and longevity', 
            'Performance': 'Processing speed and responsiveness',
            'Price_Value': 'Price and value perception',
            'Build_Quality': 'Construction quality and durability',
            'Display_Quality': 'Screen quality and visual experience',
            'Design_Appeal': 'Visual design and aesthetics',
            'Feature_Richness': 'Breadth of features and functionality'
        }
        
        # Smartphone models with market context
        self.phone_models_info = {
            'iPhone 15 Pro': {'brand': 'Apple', 'tier': 'Premium', 'launch_year': 2023, 'popularity': 85},
            'iPhone 15': {'brand': 'Apple', 'tier': 'Premium', 'launch_year': 2023, 'popularity': 78},
            'Samsung Galaxy S24 Ultra': {'brand': 'Samsung', 'tier': 'Premium', 'launch_year': 2024, 'popularity': 72},
            'Samsung Galaxy S24': {'brand': 'Samsung', 'tier': 'Premium', 'launch_year': 2024, 'popularity': 68},
            'Google Pixel 8 Pro': {'brand': 'Google', 'tier': 'Premium', 'launch_year': 2023, 'popularity': 45},
            'Google Pixel 8': {'brand': 'Google', 'tier': 'Premium', 'launch_year': 2023, 'popularity': 42},
            'OnePlus 12': {'brand': 'OnePlus', 'tier': 'Premium', 'launch_year': 2024, 'popularity': 35},
            'Xiaomi 14 Pro': {'brand': 'Xiaomi', 'tier': 'Premium', 'launch_year': 2023, 'popularity': 38},
            'Samsung Galaxy A54': {'brand': 'Samsung', 'tier': 'Mid-range', 'launch_year': 2023, 'popularity': 65},
            'Google Pixel 7a': {'brand': 'Google', 'tier': 'Mid-range', 'launch_year': 2023, 'popularity': 52},
            'OnePlus Nord 3': {'brand': 'OnePlus', 'tier': 'Mid-range', 'launch_year': 2023, 'popularity': 28},
            'Xiaomi Redmi Note 13': {'brand': 'Xiaomi', 'tier': 'Budget', 'launch_year': 2024, 'popularity': 58}
        }
        
        # Realistic brand positioning scores (based on expert reviews and market data)
        self.brand_positioning = {
            'iPhone 15 Pro': {
                'Camera_Quality': 8.5, 'Battery_Life': 7.5, 'Performance': 9.2, 'Price_Value': 4.0,
                'Build_Quality': 9.0, 'Display_Quality': 8.8, 'Design_Appeal': 9.1, 'Feature_Richness': 8.0
            },
            'iPhone 15': {
                'Camera_Quality': 8.0, 'Battery_Life': 7.2, 'Performance': 8.8, 'Price_Value': 4.8,
                'Build_Quality': 8.7, 'Display_Quality': 8.3, 'Design_Appeal': 8.8, 'Feature_Richness': 7.5
            },
            'Samsung Galaxy S24 Ultra': {
                'Camera_Quality': 9.0, 'Battery_Life': 8.2, 'Performance': 8.9, 'Price_Value': 5.5,
                'Build_Quality': 8.8, 'Display_Quality': 9.2, 'Design_Appeal': 8.3, 'Feature_Richness': 9.1
            },
            'Samsung Galaxy S24': {
                'Camera_Quality': 8.3, 'Battery_Life': 7.8, 'Performance': 8.5, 'Price_Value': 6.2,
                'Build_Quality': 8.4, 'Display_Quality': 8.7, 'Design_Appeal': 8.0, 'Feature_Richness': 8.5
            },
            'Google Pixel 8 Pro': {
                'Camera_Quality': 8.8, 'Battery_Life': 7.6, 'Performance': 8.2, 'Price_Value': 6.8,
                'Build_Quality': 7.9, 'Display_Quality': 8.4, 'Design_Appeal': 7.5, 'Feature_Richness': 7.8
            },
            'Google Pixel 8': {
                'Camera_Quality': 8.4, 'Battery_Life': 7.2, 'Performance': 7.9, 'Price_Value': 7.5,
                'Build_Quality': 7.6, 'Display_Quality': 8.0, 'Design_Appeal': 7.2, 'Feature_Richness': 7.4
            },
            'OnePlus 12': {
                'Camera_Quality': 7.8, 'Battery_Life': 8.4, 'Performance': 8.7, 'Price_Value': 7.8,
                'Build_Quality': 8.0, 'Display_Quality': 8.5, 'Design_Appeal': 7.9, 'Feature_Richness': 8.2
            },
            'Xiaomi 14 Pro': {
                'Camera_Quality': 7.9, 'Battery_Life': 8.1, 'Performance': 8.4, 'Price_Value': 8.5,
                'Build_Quality': 7.7, 'Display_Quality': 8.2, 'Design_Appeal': 7.6, 'Feature_Richness': 8.7
            },
            'Samsung Galaxy A54': {
                'Camera_Quality': 6.8, 'Battery_Life': 7.5, 'Performance': 6.5, 'Price_Value': 7.9,
                'Build_Quality': 6.9, 'Display_Quality': 7.2, 'Design_Appeal': 7.1, 'Feature_Richness': 7.0
            },
            'Google Pixel 7a': {
                'Camera_Quality': 7.8, 'Battery_Life': 6.9, 'Performance': 6.8, 'Price_Value': 8.2,
                'Build_Quality': 6.5, 'Display_Quality': 7.0, 'Design_Appeal': 6.8, 'Feature_Richness': 6.7
            },
            'OnePlus Nord 3': {
                'Camera_Quality': 6.5, 'Battery_Life': 7.8, 'Performance': 7.2, 'Price_Value': 8.0,
                'Build_Quality': 6.8, 'Display_Quality': 7.4, 'Design_Appeal': 6.9, 'Feature_Richness': 7.1
            },
            'Xiaomi Redmi Note 13': {
                'Camera_Quality': 5.8, 'Battery_Life': 8.2, 'Performance': 5.9, 'Price_Value': 8.8,
                'Build_Quality': 5.5, 'Display_Quality': 6.2, 'Design_Appeal': 5.9, 'Feature_Richness': 6.8
            }
        }
        
        self.quantitative_data = []
        self.respondent_profiles = []
        
    def generate_respondent_profiles(self, num_respondents=200):
        """Generate diverse respondent profiles with realistic demographics."""
        print(f"👥 Generating {num_respondents} respondent profiles...")
        
        # Demographics options
        countries = ['USA', 'UK', 'Canada', 'Australia', 'New Zealand', 'South Africa']
        age_groups = ['18-25', '26-35', '36-45', '46-55', '56-65', '65+']
        occupations = [
            'Student', 'Software Developer', 'Teacher', 'Marketing Manager',
            'Sales Representative', 'Nurse', 'Engineer', 'Designer', 'Accountant',
            'Consultant', 'Retail Worker', 'Business Owner', 'Writer', 'Analyst',
            'Doctor', 'Lawyer', 'Architect', 'Chef', 'Artist', 'Photographer'
        ]
        income_levels = ['Low', 'Lower-Middle', 'Middle', 'Upper-Middle', 'High']
        tech_savviness = ['Low', 'Medium', 'High', 'Expert']
        usage_patterns = ['Light', 'Moderate', 'Heavy', 'Power User']
        brands = ['Apple', 'Samsung', 'Google', 'OnePlus', 'Xiaomi', 'Other']
        
        profiles = []
        for i in range(num_respondents):
            profile = {
                'respondent_id': f"RESP_{2000 + i}",
                'country': random.choice(countries),
                'age_group': random.choice(age_groups),
                'occupation': random.choice(occupations),
                'income_level': random.choice(income_levels),
                'tech_savviness': random.choice(tech_savviness),
                'usage_pattern': random.choice(usage_patterns),
                'current_phone_brand': random.choice(brands),
                'survey_date': f"2025-0{random.randint(4,6)}-{random.randint(1,28):02d}"
            }
            profiles.append(profile)
        
        self.respondent_profiles = profiles
        print(f"✅ Generated {len(profiles)} diverse respondent profiles")
        return profiles
    
    def generate_brand_ratings(self):
        """Generate realistic brand ratings with demographic bias modeling."""
        print("📊 Generating quantitative brand ratings...")
        
        ratings_data = []
        
        for respondent in self.respondent_profiles:
            resp_id = respondent['respondent_id']
            
            # Calculate respondent-specific biases
            bias_factors = self._calculate_respondent_bias(respondent)
            
            for phone_model, base_scores in self.brand_positioning.items():
                phone_info = self.phone_models_info[phone_model]
                
                phone_rating = {
                    'respondent_id': resp_id,
                    'phone_model': phone_model,
                    'brand': phone_info['brand'],
                    'tier': phone_info['tier'],
                    'popularity': phone_info['popularity']
                }
                
                # Generate ratings with bias and noise
                for dimension, base_score in base_scores.items():
                    # Apply demographic bias
                    bias = bias_factors.get(dimension, 0)
                    
                    # Add realistic rating noise
                    noise = np.random.normal(0, 0.8)
                    
                    # Calculate final score
                    final_score = base_score + bias + noise
                    final_score = max(1.0, min(10.0, final_score))  # Clamp to 1-10
                    
                    phone_rating[dimension] = round(final_score, 1)
                
                ratings_data.append(phone_rating)
        
        self.quantitative_data = ratings_data
        print(f"✅ Generated {len(ratings_data):,} individual brand ratings")
        return ratings_data
    
    def _calculate_respondent_bias(self, respondent):
        """Calculate demographic-based rating biases for realistic variation."""
        biases = {}
        
        # Age-based biases
        if respondent['age_group'] in ['18-25', '26-35']:
            # Younger users prioritize design and camera
            biases['Design_Appeal'] = random.uniform(-0.1, 0.4)
            biases['Camera_Quality'] = random.uniform(0, 0.3)
        elif respondent['age_group'] in ['56-65', '65+']:
            # Older users prioritize battery and value
            biases['Battery_Life'] = random.uniform(0, 0.3)
            biases['Price_Value'] = random.uniform(0.1, 0.4)
        
        # Tech savviness biases
        if respondent['tech_savviness'] == 'Expert':
            # Tech experts are more critical of performance
            biases['Performance'] = random.uniform(-0.3, 0.2)
            biases['Feature_Richness'] = random.uniform(0, 0.3)
        elif respondent['tech_savviness'] == 'Low':
            # Low tech users less sensitive to performance differences
            biases['Performance'] = random.uniform(-0.2, 0)
            biases['Price_Value'] = random.uniform(0, 0.3)
        
        # Income-based biases
        if respondent['income_level'] in ['Low', 'Lower-Middle']:
            # Price-sensitive users
            biases['Price_Value'] = random.uniform(0.2, 0.5)
            biases['Build_Quality'] = random.uniform(-0.2, 0)
        elif respondent['income_level'] == 'High':
            # Premium-focused users
            biases['Build_Quality'] = random.uniform(0, 0.3)
            biases['Design_Appeal'] = random.uniform(0, 0.2)
        
        # Usage pattern biases
        if respondent['usage_pattern'] in ['Heavy', 'Power User']:
            # Heavy users prioritize performance and battery
            biases['Performance'] = random.uniform(0, 0.2)
            biases['Battery_Life'] = random.uniform(0, 0.3)
        
        # Brand loyalty bias
        current_brand = respondent['current_phone_brand']
        for phone_model, phone_info in self.phone_models_info.items():
            if phone_info['brand'] == current_brand:
                # Slight positive bias toward current brand
                for dimension in biases:
                    if dimension not in biases:
                        biases[dimension] = 0
                    biases[dimension