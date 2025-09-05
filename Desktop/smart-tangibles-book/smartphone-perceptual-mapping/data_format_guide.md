# 📊 Data Format Guide - Using Real Research Data

> **How to replace generated data with your actual research results**

This guide shows you exactly how to format your real research data to work with the perceptual mapping system.

---

## 🎯 Quick Summary

**You can skip the data generation scripts entirely** and use your real research data by creating properly formatted CSV files.

**Key Files to Create:**
1. `average_brand_ratings.csv` - **Essential** (your quantitative survey results)
2. `qualitative_user_interviews.csv` - Optional (your interview data)

---

## 📋 Format 1: Quantitative Survey Data (Essential)

### **File Name:** `average_brand_ratings.csv`

This is the **main data file** that powers all analysis and visualizations.

### **Required Columns:**

| Column | Description | Example Values | Notes |
|--------|-------------|----------------|--------|
| `phone_model` | Product/model name | "iPhone 15 Pro", "Your Product X" | Any text |
| `brand` | Brand name | "Apple", "Samsung", "YourBrand" | Used for color coding |
| `tier` | Market tier | "Premium", "Mid-range", "Budget" | Used for shape coding |
| `popularity` | Market popularity % | 85, 45, 23 | 0-100 scale, determines bubble size |
| **Your Dimensions** | Performance scores | 8.5, 7.2, 6.8 | 1-10 scale recommended |

### **Example CSV:**
```csv
phone_model,brand,tier,popularity,Camera_Quality,Battery_Life,Performance,Price_Value,Build_Quality,User_Experience,Design_Appeal,Innovation
iPhone 15 Pro,Apple,Premium,85,8.5,7.5,9.2,4.0,9.0,8.8,9.1,8.0
Samsung Galaxy S24 Ultra,Samsung,Premium,72,9.0,8.2,8.9,5.5,8.8,9.2,8.3,9.1
Your Product Alpha,YourCompany,Premium,45,8.1,8.5,8.7,7.2,8.3,8.0,7.8,8.4
Your Product Beta,YourCompany,Mid-range,38,7.2,8.8,7.5,8.5,7.1,7.4,7.0,7.3
Competitor Product X,CompetitorA,Premium,52,7.8,7.9,8.3,6.8,7.9,8.1,8.0,7.7
```

### **Dimension Customization:**
Replace our example dimensions with **your actual survey questions**:

**Our Examples** → **Your Research**
- `Camera_Quality` → `Image_Quality`
- `Battery_Life` → `Battery_Performance` 
- `Performance` → `Speed_Responsiveness`
- `Price_Value` → `Value_for_Money`
- `Build_Quality` → `Build_Durability`
- `Display_Quality` → `Screen_Experience`
- `Design_Appeal` → `Aesthetic_Appeal`
- `Feature_Richness` → `Feature_Completeness`

**Add Your Own:**
- `Brand_Trust`
- `Customer_Support`
- `Sustainability`
- `Innovation_Level`
- `Ease_of_Use`
- `Reliability`

### **Data Sources:**
- **Survey Platform Exports** (Qualtrics, SurveyMonkey, etc.)
- **Market Research Reports** (Nielsen, Ipsos, etc.)
- **Expert Reviews** (CNET, Consumer Reports, etc.)
- **Internal Research** (Your company's data)
- **Social Media Sentiment** (Aggregated scores)

---

## 🗣️ Format 2: Qualitative Interview Data (Optional)

### **File Name:** `qualitative_user_interviews.csv`

Use this if you want the system to **automatically identify positioning dimensions** from your interview data.

### **Required Columns:**

| Column | Description | Example | Notes |
|--------|-------------|---------|--------|
| `user_id` | Unique participant ID | "P001", "USER_123" | Any format |
| `country` | Country of participant | "USA", "UK", "Canada" | For demographics |
| `age_group` | Age range | "18-25", "26-35", "45-54" | Age brackets |
| `occupation` | Job/profession | "Marketing Manager", "Student" | Any text |
| `interview_date` | Interview date | "2024-03-15" | YYYY-MM-DD format |
| `attribute_number` | Sequence per user | 1, 2, 3, 4 | Numbers per participant |
| `attribute_text` | **The actual quote** | "Camera quality is very important to me" | **Most important column** |
| `total_attributes_mentioned` | Total for this user | 4, 5, 3 | Count of attributes |

### **Example CSV:**
```csv
user_id,country,age_group,occupation,interview_date,attribute_number,attribute_text,total_attributes_mentioned
P001,USA,26-35,Marketing Manager,2024-03-15,1,"Camera quality is extremely important for my social media",4
P001,USA,26-35,Marketing Manager,2024-03-15,2,"Battery needs to last through my entire workday",4
P001,USA,26-35,Marketing Manager,2024-03-15,3,"I want good value for what I pay",4
P001,USA,26-35,Marketing Manager,2024-03-15,4,"Build quality should feel premium in my hands",4
P002,UK,18-25,Student,2024-03-16,1,"Performance for gaming is my top priority",3
P002,UK,18-25,Student,2024-03-16,2,"Design needs to look modern and stylish",3
P002,UK,18-25,Student,2024-03-16,3,"Price has to be affordable for my budget",3
P003,Canada,45-54,Engineer,2024-03-17,1,"Reliability and durability are essential",5
P003,Canada,45-54,Engineer,2024-03-17,2,"Battery life should be excellent",5
P003,Canada,45-54,Engineer,2024-03-17,3,"Display quality for reading technical documents",5
P003,Canada,45-54,Engineer,2024-03-17,4,"Brand reputation and support matter",5
P003,Canada,45-54,Engineer,2024-03-17,5,"Innovation in features attracts me",5
```

### **Data Sources:**
- **Interview Transcripts** (coded and extracted)
- **Focus Group Notes** (key quotes and themes)
- **Survey Open-Ended Responses** (text analysis)
- **Customer Feedback** (support tickets, reviews)
- **Social Media Comments** (analyzed and categorized)

---

## 🔄 Data Conversion Examples

### **From Likert Scale Survey:**
```csv
# Your survey export might look like:
Respondent,Product_A_Camera,Product_A_Battery,Product_B_Camera,Product_B_Battery
R001,5,4,3,5
R002,4,3,4,4

# Convert to our format:
phone_model,brand,tier,popularity,Camera_Quality,Battery_Life
Product A,BrandX,Premium,65,4.5,3.5
Product B,BrandY,Premium,45,3.5,4.5
```

### **From Market Research Report:**
```csv
# Report data might be:
Brand,Overall_Rating,Camera_Score,Battery_Score,Market_Share
Apple,8.5,8.8,7.2,25%
Samsung,8.2,8.5,8.0,22%

# Convert to our format:
phone_model,brand,tier,popularity,Camera_Quality,Battery_Life
iPhone 15,Apple,Premium,85,8.8,7.2
Galaxy S24,Samsung,Premium,72,8.5,8.0
```

### **From Expert Reviews:**
```csv
# Aggregate expert scores:
Product,CNET_Score,PCMag_Score,ConsumerReports_Score
iPhone_15_Pro,9.0,8.5,8.8
Galaxy_S24,8.8,8.7,8.5

# Convert to our format (average the scores):
phone_model,brand,tier,popularity,Overall_Quality
iPhone 15 Pro,Apple,Premium,85,8.77
Galaxy S24,Samsung,Premium,72,8.67
```

---

## 🛠️ Data Preparation Tools

### **Excel/Google Sheets Formula Examples:**

#### **Calculate Averages:**
```excel
# If you have individual responses, calculate means:
=AVERAGE(B2:B10)  # Average rating for Product A
```

#### **Convert Scale (e.g., 1-5 to 1-10):**
```excel
=((A2-1)/(5-1))*(10-1)+1  # Convert 1-5 scale to 1-10
```

#### **Popularity from Market Share:**
```excel
=A2*100  # Convert 0.25 to 25 (if market share in decimals)
```

### **Python Data Cleaning:**
```python
import pandas as pd

# Load your raw data
raw_data = pd.read_csv('your_survey_export.csv')

# Rename columns to match our format
formatted_data = raw_data.rename(columns={
    'Product_Name': 'phone_model',
    'Brand_Name': 'brand',
    'Market_Segment': 'tier', 
    'Market_Share_Percent': 'popularity',
    'Camera_Rating': 'Camera_Quality',
    'Battery_Rating': 'Battery_Life'
})

# Convert scales if needed (e.g., 1-5 to 1-10)
scale_columns = ['Camera_Quality', 'Battery_Life', 'Performance']
for col in scale_columns:
    formatted_data[col] = ((formatted_data[col] - 1) / 4) * 9 + 1

# Save in our format
formatted_data.to_csv('average_brand_ratings.csv', index=False)
```

---

## ✅ Data Quality Checklist

### **Before Using Your Data:**

**Quantitative Data (`average_brand_ratings.csv`):**
- [ ] All required columns present (`phone_model`, `brand`, `tier`, `popularity`)
- [ ] Ratings on consistent scale (recommend 1-10)
- [ ] No missing values in essential columns
- [ ] Popularity values between 0-100
- [ ] At least 3 products for meaningful comparison
- [ ] Product names are unique and clear

**Qualitative Data (`qualitative_user_interviews.csv`):**
- [ ] `attribute_text` contains actual user quotes
- [ ] Each row represents one attribute mention
- [ ] User IDs are consistent across their attributes
- [ ] Date format is YYYY-MM-DD
- [ ] At least 20 participants for robust analysis
- [ ] Quotes are in natural language (not codes)

**File Format:**
- [ ] Saved as CSV (comma-separated values)
- [ ] UTF-8 encoding (handles international characters)
- [ ] Headers in first row
- [ ] No blank rows or columns
- [ ] Quotes around text containing commas

---

## 🎯 Integration Steps

### **Step 1: Prepare Your Data**
1. Export from your survey/research platform
2. Clean and format according to specifications above
3. Save as CSV files with exact names specified

### **Step 2: Replace Generated Data**  
1. Place your CSV files in the main directory
2. Your files will be automatically detected and used
3. Generated sample data will be ignored

### **Step 3: Test Integration**
1. Run `python perceptual_map_analyzer.py`
2. Open `perceptual_mapping_dashboard.html`
3. Verify your products and dimensions appear correctly

### **Step 4: Customize Dashboard** (Optional)
1. Edit the JavaScript data section in the HTML file
2. Update brand colors and tier definitions
3. Modify dimension descriptions

---

## 💡 Pro Tips

### **Data Collection Best Practices:**
- **Survey Scale:** Use 1-10 scale for better granularity than 1-5
- **Sample Size:** Minimum 50 respondents per product for reliability
- **Balanced Demographics:** Ensure representative age, geography, usage patterns
- **Consistent Wording:** Use identical questions across all products
- **Include Popularity Metric:** Market share, sales volume, or awareness scores

### **Common Mistakes to Avoid:**
- ❌ Mixing different rating scales across dimensions
- ❌ Using product codes instead of readable names
- ❌ Missing the popularity column (needed for bubble sizing)
- ❌ Inconsistent brand names (Apple vs APPLE vs apple)
- ❌ Leaving cells blank instead of using 0 or "N/A"

### **Advanced Integration:**
- **Multiple Product Categories:** Create separate CSV files for each category
- **Time Series Analysis:** Include date columns for trend analysis
- **Segmented Analysis:** Add demographic columns for filtering
- **Competitive Intelligence:** Include competitor products for benchmarking

---

## 📞 Need Help?

If you encounter issues with data formatting:

1. **Check the sample generated CSV files** for reference format
2. **Use Excel's "Save As" with CSV UTF-8** encoding
3. **Test with a small subset** of your data first
4. **Verify column names match exactly** (case-sensitive)
5. **Ensure no special characters** in product/brand names

**Your real research data will provide much more valuable insights than generated sample data!** 🎯📊

---

*Ready to transform your research into actionable perceptual maps!*