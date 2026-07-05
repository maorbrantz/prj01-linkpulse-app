#!/usr/bin/env sh
set -eu

ENDPOINT="http://localstack:4566"
REGION="${AWS_REGION:-us-east-1}"

echo "waiting for localstack"
until awslocal --endpoint-url "$ENDPOINT" sqs list-queues >/dev/null 2>&1; do
  sleep 2
done

echo "creating dynamodb table: links"
awslocal --endpoint-url "$ENDPOINT" dynamodb create-table \
  --table-name links \
  --attribute-definitions AttributeName=short_code,AttributeType=S \
  --key-schema AttributeName=short_code,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST >/dev/null 2>&1 || echo "links exists"

echo "creating dynamodb table: click_stats"
awslocal --endpoint-url "$ENDPOINT" dynamodb create-table \
  --table-name click_stats \
  --attribute-definitions AttributeName=short_code,AttributeType=S AttributeName=day,AttributeType=S \
  --key-schema AttributeName=short_code,KeyType=HASH AttributeName=day,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST >/dev/null 2>&1 || echo "click_stats exists"

echo "creating sqs dlq: clicks-dlq"
awslocal --endpoint-url "$ENDPOINT" sqs create-queue --queue-name clicks-dlq >/dev/null

DLQ_ARN=$(awslocal --endpoint-url "$ENDPOINT" sqs get-queue-attributes \
  --queue-url "$ENDPOINT/000000000000/clicks-dlq" \
  --attribute-names QueueArn --query "Attributes.QueueArn" --output text)

echo "creating sqs queue: clicks"
awslocal --endpoint-url "$ENDPOINT" sqs create-queue --queue-name clicks \
  --attributes "{\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"5\\\"}\"}" >/dev/null

echo "localstack init complete"
