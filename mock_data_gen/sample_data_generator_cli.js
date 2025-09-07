#!/usr/bin/env node

/**
 * Sample Data Generator CLI
 * 
 * Generates realistic AWS and Shopify sample data for analysis
 * Based on session performance patterns with configurable options
 * 
 * Usage:
 *   npx sample-data-generator --type aws --sessions 200 --output aws_data.csv
 *   npx sample-data-generator --type shopify --sessions 200 --noise 0.15
 *   npx sample-data-generator --type both --sessions 100 --pattern curved
 */

const fs = require('fs');
const path = require('path');

// CLI argument parsing
function parseArgs() {
    const args = process.argv.slice(2);
    const options = {
        type: 'both',           // aws, shopify, or both
        sessions: 200,          // number of sessions to generate
        output: null,           // output filename (auto-generated if not provided)
        noise: 0.15,           // noise probability (0-1)
        pattern: 'curved',      // linear or curved
        inflection: 130,        // inflection point session number
        help: false
    };

    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--type':
            case '-t':
                options.type = args[++i];
                break;
            case '--sessions':
            case '-s':
                options.sessions = parseInt(args[++i]);
                break;
            case '--output':
            case '-o':
                options.output = args[++i];
                break;
            case '--noise':
            case '-n':
                options.noise = parseFloat(args[++i]);
                break;
            case '--pattern':
            case '-p':
                options.pattern = args[++i];
                break;
            case '--inflection':
            case '-i':
                options.inflection = parseInt(args[++i]);
                break;
            case '--help':
            case '-h':
                options.help = true;
                break;
            default:
                if (args[i].startsWith('-')) {
                    console.error(`Unknown option: ${args[i]}`);
                    process.exit(1);
                }
        }
    }

    return options;
}

// Display help information
function showHelp() {
    console.log(`
Sample Data Generator CLI v1.0.0

Generate realistic AWS and Shopify sample data for session analysis

USAGE:
    sample-data-generator [OPTIONS]

OPTIONS:
    -t, --type <TYPE>         Data type to generate: aws, shopify, both (default: both)
    -s, --sessions <NUM>      Number of sessions to generate (default: 200)
    -o, --output <FILE>       Output filename (auto-generated if not provided)
    -n, --noise <PROB>        Noise probability 0-1 (default: 0.15)
    -p, --pattern <PATTERN>   Success pattern: linear, curved (default: curved)
    -i, --inflection <NUM>    Inflection point session number (default: 130)
    -h, --help               Show this help message

EXAMPLES:
    # Generate both AWS and Shopify data with default settings
    sample-data-generator

    # Generate only AWS data with 100 sessions
    sample-data-generator --type aws --sessions 100

    # Generate Shopify data with custom noise level
    sample-data-generator --type shopify --noise 0.25 --output my_shopify.csv

    # Generate both datasets with linear pattern
    sample-data-generator --type both --pattern linear --inflection 150

OUTPUT:
    AWS data format:     user_id,session_id,start_timestamp,end_timestamp
    Shopify data format: user_id,session_id,success

The generator creates realistic session data with:
    - Gradual performance decline until inflection point
    - Sharp performance drop after inflection point  
    - Configurable noise injection for realistic variance
    - Consistent user IDs between AWS and Shopify datasets
`);
}

// Generate AWS sample data
function generateAWSData(options) {
    const lines = ['user_id,session_id,start_timestamp,end_timestamp'];
    const baseTimestamp = 1724515200; // Base timestamp
    
    console.log(`Generating AWS data: ${options.sessions} sessions...`);
    
    for (let i = 1; i <= options.sessions; i++) {
        const userId = `USER_${String(Math.floor(Math.random() * 9999)).padStart(4, '0')}`;
        const sessionId = `SESS_${String(i).padStart(6, '0')}`;
        
        // Session length increases by 0.2 seconds each time (1.0 to ~40+ seconds)
        const startTimestamp = baseTimestamp + (i - 1) * 60;
        const sessionLengthSeconds = 1.0 + (i - 1) * 0.2;
        const endTimestamp = startTimestamp + sessionLengthSeconds;
        
        lines.push(`${userId},${sessionId},${startTimestamp},${endTimestamp.toFixed(1)}`);
    }
    
    return lines.join('\n');
}

// Generate Shopify sample data
function generateShopifyData(options) {
    const lines = ['user_id,session_id,success'];
    let noiseCount = 0;
    
    console.log(`Generating Shopify data: ${options.sessions} sessions with ${options.pattern} pattern...`);
    
    for (let i = 1; i <= options.sessions; i++) {
        const userId = `USER_${String(Math.floor(Math.random() * 9999)).padStart(4, '0')}`;
        const sessionId = `SESS_${String(i).padStart(6, '0')}`;
        
        let successRate;
        
        if (i <= options.inflection) {
            // Before inflection point: high success rate with gradual decline
            if (options.pattern === 'curved') {
                // Curved decline from 99% to 55%
                const progressRatio = (i - 1) / (options.inflection - 1);
                const curveValue = 1 - Math.pow(progressRatio, 0.7);
                successRate = 0.55 + (0.99 - 0.55) * curveValue;
            } else {
                // Linear decline from 99% to 55%
                const progressRatio = (i - 1) / (options.inflection - 1);
                successRate = 0.99 - (0.99 - 0.55) * progressRatio;
            }
        } else {
            // After inflection point: sharp drop to ~5% success
            successRate = 0.05;
        }
        
        // Determine expected success based on rate
        let expectedSuccess = Math.random() < successRate ? 1 : 0;
        
        // Apply noise: flip the expected outcome with specified probability
        let finalSuccess = expectedSuccess;
        if (Math.random() < options.noise) {
            finalSuccess = expectedSuccess === 1 ? 0 : 1;
            noiseCount++;
        }
        
        lines.push(`${userId},${sessionId},${finalSuccess}`);
    }
    
    console.log(`Applied noise to ${noiseCount} sessions (${(noiseCount/options.sessions*100).toFixed(1)}%)`);
    return lines.join('\n');
}

// Generate both datasets with consistent user IDs
function generateBothData(options) {
    console.log(`Generating both AWS and Shopify data: ${options.sessions} sessions...`);
    
    const awsLines = ['user_id,session_id,start_timestamp,end_timestamp'];
    const shopifyLines = ['user_id,session_id,success'];
    const baseTimestamp = 1724515200;
    let noiseCount = 0;
    
    // Generate consistent user IDs for both datasets
    const userIds = [];
    for (let i = 1; i <= options.sessions; i++) {
        userIds.push(`USER_${String(Math.floor(Math.random() * 9999)).padStart(4, '0')}`);
    }
    
    for (let i = 1; i <= options.sessions; i++) {
        const userId = userIds[i - 1];
        const sessionId = `SESS_${String(i).padStart(6, '0')}`;
        
        // AWS data
        const startTimestamp = baseTimestamp + (i - 1) * 60;
        const sessionLengthSeconds = 1.0 + (i - 1) * 0.2;
        const endTimestamp = startTimestamp + sessionLengthSeconds;
        awsLines.push(`${userId},${sessionId},${startTimestamp},${endTimestamp.toFixed(1)}`);
        
        // Shopify data
        let successRate;
        if (i <= options.inflection) {
            if (options.pattern === 'curved') {
                const progressRatio = (i - 1) / (options.inflection - 1);
                const curveValue = 1 - Math.pow(progressRatio, 0.7);
                successRate = 0.55 + (0.99 - 0.55) * curveValue;
            } else {
                const progressRatio = (i - 1) / (options.inflection - 1);
                successRate = 0.99 - (0.99 - 0.55) * progressRatio;
            }
        } else {
            successRate = 0.05;
        }
        
        let expectedSuccess = Math.random() < successRate ? 1 : 0;
        let finalSuccess = expectedSuccess;
        if (Math.random() < options.noise) {
            finalSuccess = expectedSuccess === 1 ? 0 : 1;
            noiseCount++;
        }
        
        shopifyLines.push(`${userId},${sessionId},${finalSuccess}`);
    }
    
    console.log(`Applied noise to ${noiseCount} sessions (${(noiseCount/options.sessions*100).toFixed(1)}%)`);
    
    return {
        aws: awsLines.join('\n'),
        shopify: shopifyLines.join('\n')
    };
}

// Write data to file
function writeToFile(data, filename, type) {
    try {
        fs.writeFileSync(filename, data);
        const lines = data.split('\n').length - 1; // Subtract header
        console.log(`✅ ${type} data written to: ${filename} (${lines} records)`);
        return true;
    } catch (error) {
        console.error(`❌ Error writing ${type} data:`, error.message);
        return false;
    }
}

// Generate auto filename
function generateFilename(type, options) {
    const timestamp = new Date().toISOString().slice(0, 10);
    const sessions = options.sessions;
    const noise = Math.round(options.noise * 100);
    
    if (type === 'aws') {
        return `aws_sample_data_${sessions}s_${timestamp}.csv`;
    } else if (type === 'shopify') {
        return `shopify_sample_data_${sessions}s_n${noise}_${timestamp}.csv`;
    }
    return null;
}

// Main execution
function main() {
    const options = parseArgs();
    
    if (options.help) {
        showHelp();
        return;
    }
    
    // Validate options
    if (!['aws', 'shopify', 'both'].includes(options.type)) {
        console.error('Error: --type must be aws, shopify, or both');
        process.exit(1);
    }
    
    if (options.sessions < 1 || options.sessions > 10000) {
        console.error('Error: --sessions must be between 1 and 10000');
        process.exit(1);
    }
    
    if (options.noise < 0 || options.noise > 1) {
        console.error('Error: --noise must be between 0 and 1');
        process.exit(1);
    }
    
    if (!['linear', 'curved'].includes(options.pattern)) {
        console.error('Error: --pattern must be linear or curved');
        process.exit(1);
    }
    
    console.log(`🚀 Sample Data Generator v1.0.0`);
    console.log(`📊 Configuration:`);
    console.log(`   Type: ${options.type}`);
    console.log(`   Sessions: ${options.sessions}`);
    console.log(`   Pattern: ${options.pattern}`);
    console.log(`   Inflection point: ${options.inflection}`);
    console.log(`   Noise probability: ${options.noise}`);
    console.log('');
    
    const startTime = Date.now();
    let success = true;
    
    if (options.type === 'aws') {
        const data = generateAWSData(options);
        const filename = options.output || generateFilename('aws', options);
        success = writeToFile(data, filename, 'AWS');
        
    } else if (options.type === 'shopify') {
        const data = generateShopifyData(options);
        const filename = options.output || generateFilename('shopify', options);
        success = writeToFile(data, filename, 'Shopify');
        
    } else if (options.type === 'both') {
        const data = generateBothData(options);
        
        // Write AWS data
        const awsFilename = options.output ? 
            options.output.replace(/\.csv$/, '_aws.csv') : 
            generateFilename('aws', options);
        success = writeToFile(data.aws, awsFilename, 'AWS') && success;
        
        // Write Shopify data  
        const shopifyFilename = options.output ?
            options.output.replace(/\.csv$/, '_shopify.csv') :
            generateFilename('shopify', options);
        success = writeToFile(data.shopify, shopifyFilename, 'Shopify') && success;
    }
    
    const duration = Date.now() - startTime;
    console.log('');
    
    if (success) {
        console.log(`✅ Generation completed successfully in ${duration}ms`);
        console.log(`📈 Data shows realistic session performance pattern:`);
        console.log(`   - High success rates (99% → 55%) until session ${options.inflection}`);
        console.log(`   - Sharp performance drop (5% success) after inflection point`);
        console.log(`   - ${Math.round(options.noise * 100)}% realistic noise injection`);
    } else {
        console.log(`❌ Generation failed after ${duration}ms`);
        process.exit(1);
    }
}

// Run if called directly
if (require.main === module) {
    main();
}

module.exports = {
    generateAWSData,
    generateShopifyData, 
    generateBothData,
    parseArgs,
    main
};