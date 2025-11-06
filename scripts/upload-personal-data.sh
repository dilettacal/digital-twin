#!/bin/bash
set -e

# Get stage from command line argument or default to 'dev'
STAGE=${1:-dev}

# Configuration
BUCKET_NAME="digital-twin-data-${STAGE}"
REGION="eu-west-1"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the digital-twin directory (parent of scripts directory)
TWIN_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$TWIN_DIR/backend/data"

echo "🔐 Uploading personal data to S3 for stage: $STAGE..."
echo "📦 Target bucket: $BUCKET_NAME"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ Error: AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Create S3 bucket if it doesn't exist
echo "📦 Checking if S3 bucket exists..."
if ! aws s3 ls "s3://$BUCKET_NAME" 2>/dev/null; then
    echo "Creating S3 bucket: $BUCKET_NAME"
    aws s3 mb "s3://$BUCKET_NAME" --region "$REGION"
    
    # Enable server-side encryption
    aws s3api put-bucket-encryption \
        --bucket "$BUCKET_NAME" \
        --server-side-encryption-configuration '{
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        }'
    
    echo "✅ Bucket created with encryption enabled"
else
    echo "✅ Bucket already exists"
fi

# Upload files
echo "📤 Uploading files..."

# Upload summary.txt
if [ -f "$DATA_DIR/summary.txt" ]; then
    aws s3 cp "$DATA_DIR/summary.txt" "s3://$BUCKET_NAME/summary.txt"
    echo "✅ Uploaded summary.txt"
else
    echo "⚠️  Warning: summary.txt not found"
fi

# Upload linkedin.pdf
if [ -f "$DATA_DIR/linkedin.pdf" ]; then
    aws s3 cp "$DATA_DIR/linkedin.pdf" "s3://$BUCKET_NAME/linkedin.pdf"
    echo "✅ Uploaded linkedin.pdf"
else
    echo "⚠️  Warning: linkedin.pdf not found"
fi

# Upload facts.json
if [ -f "$DATA_DIR/facts.json" ]; then
    aws s3 cp "$DATA_DIR/facts.json" "s3://$BUCKET_NAME/facts.json"
    echo "✅ Uploaded facts.json"
else
    echo "⚠️  Warning: facts.json not found"
fi

# Upload style.txt
if [ -f "$DATA_DIR/style.txt" ]; then
    aws s3 cp "$DATA_DIR/style.txt" "s3://$BUCKET_NAME/style.txt"
    echo "✅ Uploaded style.txt"
else
    echo "⚠️  Warning: style.txt not found"
fi

# Upload me.txt (optional)
if [ -f "$DATA_DIR/me.txt" ]; then
    aws s3 cp "$DATA_DIR/me.txt" "s3://$BUCKET_NAME/me.txt"
    echo "✅ Uploaded me.txt"
else
    echo "ℹ️  Info: me.txt not found (optional file)"
fi

echo ""
echo "🎉 Personal data upload complete!"
echo "📋 Files uploaded to: s3://$BUCKET_NAME"
echo ""
echo "💡 Next steps:"
echo "   1. Update your Lambda environment variable: PERSONAL_DATA_BUCKET=$BUCKET_NAME"
echo "   2. Deploy your Lambda function for stage: $STAGE"
echo "   3. Your Lambda will now read data from S3 instead of local files"
echo ""
echo "🔄 Usage examples (run from digital-twin/ directory):"
echo "   ./scripts/upload-personal-data.sh dev     # Upload to digital-twin-data-dev"
echo "   ./scripts/upload-personal-data.sh test    # Upload to digital-twin-data-test"
echo "   ./scripts/upload-personal-data.sh prod    # Upload to digital-twin-data-prod"
echo ""
echo "🔄 To update files later, just run this script again with the same stage!"
