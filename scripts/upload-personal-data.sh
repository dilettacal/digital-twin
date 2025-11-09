#!/bin/bash
set -e

# Get stage from command line argument or default to 'dev'
STAGE=${1:-dev}

# Configuration
BUCKET_NAME="digital-twin-data-${STAGE}"
REGION="eu-central-1"

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

# Upload skills.yml
if [ -f "$DATA_DIR/skills.yml" ]; then
    aws s3 cp "$DATA_DIR/skills.yml" "s3://$BUCKET_NAME/skills.yml"
    echo "✅ Uploaded skills.yml"
else
    echo "⚠️  Warning: skills.yml not found"
fi

# Upload education.yml
if [ -f "$DATA_DIR/education.yml" ]; then
    aws s3 cp "$DATA_DIR/education.yml" "s3://$BUCKET_NAME/education.yml"
    echo "✅ Uploaded education.yml"
else
    echo "⚠️  Warning: education.yml not found"
fi

# Upload experience.yml
if [ -f "$DATA_DIR/experience.yml" ]; then
    aws s3 cp "$DATA_DIR/experience.yml" "s3://$BUCKET_NAME/experience.yml"
    echo "✅ Uploaded experience.yml"
else
    echo "⚠️  Warning: experience.yml not found"
fi

# Upload qna.yml
if [ -f "$DATA_DIR/qna.yml" ]; then
    aws s3 cp "$DATA_DIR/qna.yml" "s3://$BUCKET_NAME/qna.yml"
    echo "✅ Uploaded qna.yml"
else
    echo "⚠️  Warning: qna.yml not found"
fi

# Upload sources.json
if [ -f "$DATA_DIR/sources.json" ]; then
    aws s3 cp "$DATA_DIR/sources.json" "s3://$BUCKET_NAME/sources.json"
    echo "✅ Uploaded sources.json"
else
    echo "⚠️  Warning: sources.json not found"
fi

# Upload resume.md (optional)
if [ -f "$DATA_DIR/resume.md" ]; then
    aws s3 cp "$DATA_DIR/resume.md" "s3://$BUCKET_NAME/resume.md"
    echo "✅ Uploaded resume.md"
else
    echo "ℹ️  Info: resume.md not found (optional file)"
fi

# Upload prompts directory
if [ -d "$DATA_DIR/prompts" ]; then
    aws s3 sync "$DATA_DIR/prompts/" "s3://$BUCKET_NAME/prompts/" --delete
    echo "✅ Uploaded prompts/ directory"
else
    echo "⚠️  Warning: prompts/ directory not found"
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
