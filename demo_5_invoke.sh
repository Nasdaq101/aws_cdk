#!/bin/bash
# Demo Step 5: Invoke the driver Lambda, then show DynamoDB contents and S3 plot URL.
set -e

REGION="${CDK_DEFAULT_REGION:-us-east-1}"
OUTPUT_FILE="/tmp/driver_output.json"

echo "Fetching resource names from stack outputs..."

DRIVER_FN=$(aws cloudformation describe-stacks \
  --stack-name ApiStack \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='DriverFunctionName'].OutputValue" \
  --output text)

TABLE_NAME=$(aws cloudformation describe-stacks \
  --stack-name StorageStack \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='TableName'].OutputValue" \
  --output text)

BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name StorageStack \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" \
  --output text)

API_URL=$(aws cloudformation describe-stacks \
  --stack-name ApiStack \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text)

echo "  Driver: $DRIVER_FN"
echo "  Table:  $TABLE_NAME"
echo "  Bucket: $BUCKET_NAME"
echo "  API:    $API_URL"
echo ""
echo "Invoking driver Lambda..."
aws lambda invoke \
  --function-name "$DRIVER_FN" \
  --region "$REGION" \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  "$OUTPUT_FILE"

echo "Response:"
cat "$OUTPUT_FILE"
echo ""
echo "Recent DynamoDB items:"
aws dynamodb scan \
  --table-name "$TABLE_NAME" \
  --region "$REGION" \
  --max-items 10 \
  --query "Items[*].{bucket:bucket_name.S,ts:timestamp.S,size:total_size.N,count:object_count.N}" \
  --output table

echo ""
PLOT_URL=$(aws s3 presign "s3://$BUCKET_NAME/plot" --region "$REGION" --expires-in 300 2>/dev/null || echo "(plot not yet generated)")
echo "Plot URL (5 min): $PLOT_URL"
