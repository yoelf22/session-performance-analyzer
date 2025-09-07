#!/usr/bin/env python3
"""
Smartphone Qualitative Dataset Generator
========================================

Generates realistic user interview data for perceptual mapping analysis.
Creates 50 simulated user interviews with demographic diversity and
natural language attribute expressions.

Usage:
    python qualitative_dataset_generator.py

Output:
    - qualitative_user_interviews.csv
    - Console summary of generated data
"""

import pandas as pd
import random
import csv
from datetime import datetime, timedelta
from collections import Counter
import re

class QualitativeDatasetGenerator:
    """Generates realistic smartphone user interview datasets."""
    
    def __init__(self):
        # Set seed for reproducible results
        random.seed(42)
        
        # Demographics data
        self.countries = ['USA', 'UK', 'Canada', 'Australia', 'New Zealand', 'South Africa']
        self.age_groups = ['18-25', '26-35', '36-45', '46-55', '56-65', '65+']
        self.occupations = [
            'Student', 'Software Developer', 'Teacher', 'Marketing Manager', 
            'Sales Representative', 'Nurse', 'Engineer', 'Designer', 'Accountant',
            'Consultant', 'Retail Worker', 'Business Owner', 'Writer', 'Analyst',
            'Doctor', 'Lawyer', 'Architect', 'Chef', 'Artist', 'Photographer'
        ]
        
        # Comprehensive attribute pool reflecting real user priorities
        self.attribute_pool = [
            # Camera Quality
            "Camera quality is my top priority",
            "I need excellent photo capabilities",
            "Photography features are essential",
            "Camera performance matters most",
            "I want professional-grade camera",
            "Photo and video quality is crucial",
            "Great camera for social media",
            
            # Battery Life
            "Battery life needs to last all day", 
            "Long lasting battery is essential",
            "I hate charging my phone constantly",
            "Battery performance is key",
            "All-day battery life is a must",
            "I need reliable battery duration",
            "Good battery backup is important",
            
            # Performance
            "Fast performance and smooth operation",
            "I need a phone that doesn't lag",
            "Processing speed is important",
            "Smooth user experience matters",
            "Fast app loading and multitasking",
            "Powerful processor performance",
            "No stuttering or freezing",
            "Gaming performance matters",
            
            # Price/Value
            "Good value for money",
            "Affordable pricing is important", 
            "I want bang for my buck",
            "Price-to-features ratio matters",
            "Budget-friendly options preferred",
            "Cost-effective choice",
            "Reasonable pricing",
            
            # Build Quality
            "Solid build quality and durability",
            "Premium materials and construction",
            "Sturdy and well-built device",
            "Quality craftsmanship",
            "Durable and reliable build",
            "High-quality materials",
            "Robust construction",
            "Water resistance is important",
            
            # Display Quality
            "Beautiful display and screen quality",
            "Vibrant colors and sharp screen",
            "Large, clear display",
            "High-resolution screen",
            "Excellent display technology",
            "Bright and crisp screen",
            "Great viewing experience",
            
            # Design Appeal
            "Sleek and attractive design",
            "Modern and stylish appearance",
            "Beautiful aesthetic appeal",
            "Premium design language",
            "Elegant and sophisticated look",
            "Eye-catching design",
            "Fashionable appearance",
            
            # Features
            "Rich feature set and functionality",
            "Comprehensive features package",
            "Wide range of capabilities",
            "Feature-rich experience",
            "Lots of useful functions",
            "Extensive feature offering",
            "Complete feature set",
            "5G connectivity support",
            
            # Brand/Trust
            "Brand reputation and reliability",
            "Trusted brand with good support",
            "Established brand credibility",
            "Brand reliability matters",
            "Good brand track record",
            "Reputable manufacturer",
            "Brand trustworthiness",
            
            # Innovation
            "Latest technology and innovation",
            "Cutting-edge features",
            "Advanced technological capabilities",
            "Innovative design and features",
            "State-of-the-art technology",
            "Forward-thinking innovation",
            "Next-generation technology",
            
            # Ecosystem
            "Integration with other devices",
            "Seamless ecosystem connectivity",
            "Works well with my other gadgets",
            "Good device synchronization",
            "Ecosystem compatibility",
            "Cross-device integration",
            "Unified device experience",
            
            # Storage
            "Adequate storage space",
            "Plenty of memory for apps and photos",
            "Sufficient storage capacity",
            "Good internal storage",
            "Expandable storage options",
            "Ample storage space",
            "Large storage capacity",
            
            # Usability
            "Easy to use interface",
            "Intuitive user experience",
            "Simple and straightforward",
            "User-friendly design",
            "Easy navigation",
            "Security and privacy features",
            "Fast charging capabilities",
            "Wireless charging support",
            "Good resale value",
            "Regular software updates"
        ]
        
    def generate_user_profile(self):
        """Generate a random user demographic profile."""
        return {
            'user_id': f"USER_{random.randint(1000, 9999)}",
            'country': random.choice(self.countries),
            'age_group': random.choice(self.age_groups),
            'occupation': random.choice(self.occupations),
        }
    
    def generate_user_attributes(self, num_attributes=None):
        """Generate realistic user attributes with natural variation."""
        if num_attributes is None:
            num_attributes = random.randint(3, 6)
        
        # Select attributes without replacement
        user_attributes = random.sample(self.attribute_pool, num_attributes)
        
        # Add some natural language variation
        varied_attributes = []
        for attr in user_attributes:
            variations = [
                attr,
                f"For me, {attr.lower()}",
                f"I really value {attr.lower()}",
                f"What matters to me is {attr.lower()}",
                f"I prioritize {attr.lower()}"
            ]
            varied_attributes.append(random.choice(variations))
        
        return varied_attributes
    
    def generate_complete_dataset(self, num_users=50):
        """Generate complete dataset with realistic user diversity."""
        print("🎯 Generating Qualitative Dataset...")
        print(f"Creating {num_users} user interviews...")
        
        dataset = []
        interview_dates = []
        
        # Generate interview dates over 3 months
        start_date = datetime(2025, 1, 15)
        for i in range(num_users):
            interview_date = start_date + timedelta(days=random.randint(0, 90))
            interview_dates.append(interview_date.strftime("%Y-%m-%d"))
        
        for i in range(num_users):
            user_profile = self.generate_user_profile()
            user_attributes = self.generate_user_attributes()
            
            # Create separate row for each attribute
            for j, attribute in enumerate(user_attributes, 1):
                dataset.append({
                    'user_id': user_profile['user_id'],
                    'country': user_profile['country'],
                    'age_group': user_profile['age_group'],
                    'occupation': user_profile['occupation'],
                    'interview_date': interview_dates[i],
                    'attribute_number': j,
                    'attribute_text': attribute,
                    'total_attributes_mentioned': len(user_attributes)
                })
        
        return pd.DataFrame(dataset)
    
    def analyze_attributes(self, df):
        """Analyze the generated attributes to identify key themes."""
        print("\n🔍 Analyzing Generated Attributes...")
        
        # Extract all attribute texts
        all_attributes = df['attribute_text'].tolist()
        
        # Perform keyword analysis
        all_words = []
        for attr in all_attributes:
            # Extract meaningful words (length > 3)
            words = re.findall(r'\b[a-zA-Z]+\b', attr.lower())
            all_words.extend([word for word in words if len(word) > 3])
        
        # Count word frequency
        word_freq = Counter(all_words)
        
        print(f"📊 Most mentioned keywords:")
        for word, count in word_freq.most_common(15):
            print(f"  {word}: {count} mentions")
        
        # Identify potential dimensions through clustering
        dimensions = self._identify_dimensions(word_freq)
        
        print(f"\n🎯 Identified Key Positioning Dimensions:")
        for i, (dim_name, data) in enumerate(dimensions.items(), 1):
            print(f"  {i}. {dim_name}: {data['description']} ({data['frequency']} mentions)")
        
        return dimensions
    
    def _identify_dimensions(self, word_freq, min_frequency=5):
        """Identify positioning dimensions from word frequency analysis."""
        dimensions = {}
        
        # Camera/Photography dimension
        camera_keywords = ['camera', 'photo', 'photography', 'pictures', 'video', 'social']
        camera_score = sum(word_freq.get(word, 0) for word in camera_keywords)
        if camera_score >= min_frequency:
            dimensions['Camera_Quality'] = {
                'keywords': camera_keywords,
                'frequency': camera_score,
                'description': 'Photography and video capabilities'
            }
        
        # Battery dimension
        battery_keywords = ['battery', 'charging', 'power', 'lasting', 'duration']
        battery_score = sum(word_freq.get(word, 0) for word in battery_keywords)
        if battery_score >= min_frequency:
            dimensions['Battery_Life'] = {
                'keywords': battery_keywords,
                'frequency': battery_score,
                'description': 'Battery performance and longevity'
            }
        
        # Performance dimension
        performance_keywords = ['performance', 'fast', 'speed', 'smooth', 'processing', 'gaming']
        performance_score = sum(word_freq.get(word, 0) for word in performance_keywords)
        if performance_score >= min_frequency:
            dimensions['Performance'] = {
                'keywords': performance_keywords,
                'frequency': performance_score,
                'description': 'Processing speed and responsiveness'
            }
        
        # Price/Value dimension
        price_keywords = ['price', 'value', 'money', 'affordable', 'cost', 'budget', 'cheap']
        price_score = sum(word_freq.get(word, 0) for word in price_keywords)
        if price_score >= min_frequency:
            dimensions['Price_Value'] = {
                'keywords': price_keywords,
                'frequency': price_score,
                'description': 'Price and value perception'
            }
        
        # Build Quality dimension
        quality_keywords = ['quality', 'build', 'durable', 'premium', 'materials', 'construction']
        quality_score = sum(word_freq.get(word, 0) for word in quality_keywords)
        if quality_score >= min_frequency:
            dimensions['Build_Quality'] = {
                'keywords': quality_keywords,
                'frequency': quality_score,
                'description': 'Construction quality and durability'
            }
        
        # Display dimension
        display_keywords = ['display', 'screen', 'colors', 'clear', 'resolution', 'viewing']
        display_score = sum(word_freq.get(word, 0) for word in display_keywords)
        if display_score >= min_frequency:
            dimensions['Display_Quality'] = {
                'keywords': display_keywords,
                'frequency': display_score,
                'description': 'Screen quality and visual experience'
            }
        
        # Design dimension
        design_keywords = ['design', 'appearance', 'style', 'aesthetic', 'look', 'attractive']
        design_score = sum(word_freq.get(word, 0) for word in design_keywords)
        if design_score >= min_frequency:
            dimensions['Design_Appeal'] = {
                'keywords': design_keywords,
                'frequency': design_score,
                'description': 'Visual design and aesthetics'
            }
        
        # Features dimension
        feature_keywords = ['features', 'functionality', 'capabilities', 'functions']
        feature_score = sum(word_freq.get(word, 0) for word in feature_keywords)
        if feature_score >= min_frequency:
            dimensions['Feature_Richness'] = {
                'keywords': feature_keywords,
                'frequency': feature_score,
                'description': 'Breadth of features and functionality'
            }
        
        return dimensions
    
    def export_dataset(self, df, filename='qualitative_user_interviews.csv'):
        """Export dataset to CSV file."""
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"\n💾 Dataset exported to: {filename}")
        
        # Display dataset summary
        print(f"\n📈 Dataset Summary:")
        print(f"  Total records: {len(df)}")
        print(f"  Unique users: {df['user_id'].nunique()}")
        print(f"  Countries: {df['country'].nunique()}")
        print(f"  Age groups: {df['age_group'].nunique()}")
        print(f"  Unique attributes: {df['attribute_text'].nunique()}")
        
        # Display sample data
        print(f"\n📋 Sample Data (first 5 records):")
        print(df.head().to_string(index=False))
        
        return filename
    
    def display_sample_interviews(self, df, num_samples=5):
        """Display sample interviews in readable format."""
        print(f"\n💬 Sample User Interviews:")
        print("="*60)
        
        sample_users = df['user_id'].unique()[:num_samples]
        
        for i, user_id in enumerate(sample_users, 1):
            user_data = df[df['user_id'] == user_id]
            first_row = user_data.iloc[0]
            
            print(f"\nInterview #{i}")
            print(f"User ID: {user_id}")
            print(f"Demographics: {first_row['age_group']}, {first_row['occupation']}, {first_row['country']}")
            print(f"Interview Date: {first_row['interview_date']}")
            print("Researcher: What factors are most important when choosing a smartphone?")
            print("Response:")
            
            for _, row in user_data.iterrows():
                print(f"  {row['attribute_number']}. {row['attribute_text']}")
            
            print("-" * 60)

def main():
    """Main execution function."""
    print("🚀 Smartphone Qualitative Dataset Generator")
    print("=" * 50)
    
    # Initialize generator
    generator = QualitativeDatasetGenerator()
    
    # Generate dataset
    dataset = generator.generate_complete_dataset(num_users=50)
    
    # Display sample interviews
    generator.display_sample_interviews(dataset, num_samples=5)
    
    # Analyze attributes
    dimensions = generator.analyze_attributes(dataset)
    
    # Export dataset
    filename = generator.export_dataset(dataset)
    
    print(f"\n✅ Qualitative dataset generation complete!")
    print(f"📁 Generated: {filename}")
    print(f"🎯 Identified {len(dimensions)} positioning dimensions")
    print(f"💡 Ready for quantitative assessment phase!")

if __name__ == "__main__":
    main()
