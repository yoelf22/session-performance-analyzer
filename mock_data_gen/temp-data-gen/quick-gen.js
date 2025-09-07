// Minimal data generator
function generateQuickData(sessions = 100) {
    const aws = ['user_id,session_id,start_timestamp,end_timestamp'];
    const shopify = ['user_id,session_id,success'];
    
    for (let i = 1; i <= sessions; i++) {
        const userId = `USER_${String(Math.floor(Math.random() * 9999)).padStart(4, '0')}`;
        const sessionId = `SESS_${String(i).padStart(6, '0')}`;
        
        // AWS data
        const startTime = 1724515200 + (i - 1) * 60;
        const duration = 1.0 + (i - 1) * 0.2;
        aws.push(`${userId},${sessionId},${startTime},${startTime + duration}`);
        
        // Shopify data - success rate pattern
        let successRate = i <= 70 ? 0.99 - (i-1) * 0.006 : 0.05;
        const success = Math.random() < successRate ? 1 : 0;
        shopify.push(`${userId},${sessionId},${success}`);
    }
    
    require('fs').writeFileSync('aws_quick.csv', aws.join('\n'));
    require('fs').writeFileSync('shopify_quick.csv', shopify.join('\n'));
    console.log(`Generated ${sessions} sessions in aws_quick.csv and shopify_quick.csv`);
}

generateQuickData(100);
