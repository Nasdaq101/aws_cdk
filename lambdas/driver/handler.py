# Part 4: Driver Lambda
# Creates/updates/deletes objects in TestBucket with sleeps, then invokes the plotting API.
# Invoke manually from AWS Console.

import os
import time
import boto3
import urllib.request
import urllib.error

BUCKET_NAME = os.environ.get("BUCKET_NAME", "testbucket-yunfei-cs6620")
PLOTTING_API_URL = os.environ.get("PLOTTING_API_URL", "")


def lambda_handler(event, context):
    s3 = boto3.client("s3")
    sleep_sec = 3

    # Delete previous plot so bucket starts ~empty; else sizes stay ~33KB (plot size)
    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key="plot")
    except Exception:
        pass
    time.sleep(1)

    # Create assignment1.txt — "Empty Assignment 1" (19 bytes)
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key="assignment1.txt",
        Body=b"Empty Assignment 1",
        ContentType="text/plain",
    )
    time.sleep(sleep_sec)

    # Update assignment1.txt — "Empty Assignment 2222222222" (28 bytes)
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key="assignment1.txt",
        Body=b"Empty Assignment 2222222222",
        ContentType="text/plain",
    )
    time.sleep(sleep_sec)

    # Delete assignment1.txt (size 0)
    s3.delete_object(Bucket=BUCKET_NAME, Key="assignment1.txt")
    time.sleep(sleep_sec)

    # Create assignment2.txt — "33" (2 bytes)
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key="assignment2.txt",
        Body=b"33",
        ContentType="text/plain",
    )
    time.sleep(sleep_sec)

    # Call plotting Lambda REST API
    if not PLOTTING_API_URL:
        return {
            "statusCode": 200,
            "body": "Driver finished. Set PLOTTING_API_URL to call plotting API.",
        }
    try:
        req = urllib.request.Request(PLOTTING_API_URL, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
        return {"statusCode": 200, "body": body}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode() if e.fp else str(e)
        return {
            "statusCode": e.code,
            "body": f"Plotting API error {e.code}: {err_body}. Check plotting-lambda CloudWatch logs.",
        }
