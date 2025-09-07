# Sample Data Generator CLI

A command-line tool to generate realistic AWS and Shopify sample data for session analysis, featuring configurable performance patterns and noise injection.

## Features

- **Dual Dataset Generation**: Create AWS session logs and Shopify success/failure data
- **Realistic Patterns**: Configurable curved or linear performance decline patterns
- **Noise Injection**: Add realistic variance with configurable noise probability
- **Inflection Points**: Simulate performance cliffs at specified session numbers
- **Consistent Data**: Matching user IDs between AWS and Shopify datasets
- **Flexible Output**: Custom filenames or auto-generated timestamped files

## Installation

### Global Installation
```bash
npm install -g sample-data-generator
```

### Local Installation
```bash
git clone https://github.com/yourusername/sample-data-generator.git
cd sample-data-generator
npm install
chmod +x index.js
```

### Direct Usage (No Installation)
```bash
npx sample-data-generator [options]
```

## Quick Start

```bash
# Generate both AWS and Shopify data with defaults
sample-data-generator

# Generate 100 sessions of AWS data only
sample-data-generator --type aws --sessions 100

# Generate Shopify data with custom noise and output filename
sample-data-generator --type shopify --noise 0.25 --output my_data.csv
```

## Usage

```
sample-data-generator [OPTIONS]

OPTIONS:
    -t, --type <TYPE>         Data type: aws, shopify, both (default: both)
    -s, --sessions <NUM>      Number of sessions (default: 200)
    -o, --output <FILE>       Output filename (auto-generated if not provided)
    -n, --noise <PROB>        Noise probability 0-1 (default: 0.15)
    -p, --pattern <PATTERN>   Pattern: linear, curved (default: curved)
    -i, --inflection <NUM>    Inflection point session (default: 130)
    -h, --help               Show help
```

## Data Patterns

### AWS Session Data
- **Format**: `user_id,session_id,start_timestamp,end_timestamp`
- **Pattern**: Session duration increases linearly (1.0s + 0.2s per session)
- **Timestamps**: Unix timestamps with 60-second intervals

### Shopify Success Data
- **Format**: `user_id,session_id,success`
- **Pattern**: Success rate starts at 99%, declines to 55%, then drops to 5%
- **Curved Pattern**: Exponential decay for realistic user behavior
- **Linear Pattern**: Straight-line decline for simplified analysis

## Examples

### Basic Usage
```bash
# Generate default datasets (200 sessions each)
sample-data-generator

# Output:
# aws_sample_data_200s_2025-01-22.csv
# shopify_sample_data_200s_n15_2025-01-22.csv
```

### AWS Data Only
```bash
sample-data-generator --type aws --sessions 500 --output aws_large.csv

# Generates: aws_large.csv with 500 session records
```

### Custom Shopify Configuration
```bash
sample-data-generator \
  --type shopify \
  --sessions 300 \
  --noise 0.10 \
  --pattern linear \
  --inflection 200

# Generates: Shopify data with linear decline, 10% noise, inflection at session 200
```

### Matched Datasets
```bash
sample-data-generator \
  --type both \
  --sessions 150 \
  --output matched_data.csv

# Generates:
# matched_data_aws.csv
# matched_data_shopify.csv
# (with consistent user IDs between datasets)
```

## Output Format

### AWS Sample Data
```csv
user_id,session_id,start_timestamp,end_timestamp
USER_1234,SESS_000001,1724515200,1724515201.0
USER_5678,SESS_000002,1724515260,1724515261.2
USER_9012,SESS_000003,1724515320,1724515321.4
```

### Shopify Sample Data
```csv
user_id,session_id,success
USER_1234,SESS_000001,1
USER_5678,SESS_000002,1
USER_9012,SESS_000003,0
```

## Data Analysis Use Cases

This tool generates data perfect for:

- **Session Length Analysis**: Correlate session duration with success rates
- **Inflection Point Detection**: Find where user patience drops dramatically
- **Performance Testing**: Simulate realistic user behavior patterns
- **Algorithm Development**: Test smoothing and trend detection algorithms
- **Visualization Development**: Create charts showing user engagement patterns

## Pattern Details

### Curved Pattern (Default)
- Mimics real user behavior with exponential decay
- Steeper decline initially, flattening over time
- More realistic for user patience analysis

### Linear Pattern
- Straight-line decline from start to inflection
- Simpler for mathematical analysis
- Easier to predict and model

### Noise Injection
- Randomly flips expected success/failure outcomes
- Default 15% noise creates realistic variance
- Adjustable from 0% (perfect pattern) to 100% (random)

## Integration Examples

### With Pandas (Python)
```python
import pandas as pd

# Load generated data
aws_df = pd.read_csv('aws_sample_data_200s_2025-01-22.csv')
shopify_df = pd.read_csv('shopify_sample_data_200s_n15_2025-01-22.csv')

# Calculate session duration
aws_df['duration'] = aws_df['end_timestamp'] - aws_df['start_timestamp']

# Join datasets
merged = aws_df.merge(shopify_df, on=['user_id', 'session_id'])
```

### With R
```r
# Load generated data
aws_data <- read.csv("aws_sample_data_200s_2025-01-22.csv")
shopify_data <- read.csv("shopify_sample_data_200s_n15_2025-01-22.csv")

# Calculate duration and merge
aws_data$duration <- aws_data$end_timestamp - aws_data$start_timestamp
merged_data <- merge(aws_data, shopify_data, by = c("user_id", "session_id"))
```

## Development

### Local Development
```bash
git clone https://github.com/yourusername/sample-data-generator.git
cd sample-data-generator
npm install

# Run locally
node index.js --help

# Test with different options
node index.js --type both --sessions 50 --noise 0.1
```

### Testing
```bash
# Run basic functionality test
npm test

# Manual testing
./index.js --sessions 10 --type both
ls -la *.csv
```

## Configuration Files

You can create a `.samplerc` file for default settings:

```json
{
  "sessions": 200,
  "noise": 0.15,
  "pattern": "curved",
  "inflection": 130,
  "type": "both"
}
```

## Troubleshooting

### Permission Denied
```bash
chmod +x index.js
```

### Module Not Found
```bash
npm install
```

### Large File Generation
For large datasets (>10,000 sessions), generation may take several seconds. Progress indicators show current status.

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Changelog

### v1.0.0
- Initial release
- AWS and Shopify data generation
- Curved and linear patterns
- Configurable noise injection
- CLI interface with full options