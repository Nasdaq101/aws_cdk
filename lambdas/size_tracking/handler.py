
# Part 2: Size-tracking Lambda.
# Triggered by S3 events (object create, update, delete) in TestBucket.
# Computes total size and object count of the bucket and writes to S3-object-size-history.


import os
from datetime import datetime, timezone
from typing import Tuple
import boto3

TABLE_NAME = os.environ.get("TABLE_NAME", "S3-object-size-history")

# Returns (total_size_bytes, object_count).
def get_bucket_total_size(s3_client, bucket: str) -> Tuple[int, int]:
    total_size = 0
    count = 0
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents") or []:
            total_size += obj.get("Size", 0)
            count += 1
    return total_size, count


def lambda_handler(event, context):
    s3 = boto3.client("s3")
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(TABLE_NAME)

    # Determine which bucket triggered (from event)
    bucket = None
    for record in event.get("Records", []):
        if record.get("eventSource") == "aws:s3":
            bucket = record["s3"]["bucket"]["name"]
            break
    if not bucket:
        return {"statusCode": 400, "body": "No S3 bucket in event"}

    total_size, object_count = get_bucket_total_size(s3, bucket)
    ts = datetime.now(timezone.utc).isoformat()

    item = {
        "bucket_name": bucket,
        "timestamp": ts,
        "total_size": total_size,
        "object_count": object_count,
        "gsi_pk": "GLOBAL",
    }
    # total_size is both an attribute and the GSI sort key; DynamoDB uses the attribute
    table.put_item(Item=item)

    return {
        "statusCode": 200,
        "bucket": bucket,
        "total_size": total_size,
        "object_count": object_count,
        "timestamp": ts,
    }
