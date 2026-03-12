
# Part 3: Plotting Lambda.
# Triggered via REST API. Queries S3-object-size-history (query only, no scan),
# plots TestBucket size over last 10 seconds and a horizontal line for max size any bucket has ever had. Saves plot as object 'plot' in TestBucket.


import os
import io
from datetime import datetime, timezone, timedelta
import boto3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

TABLE_NAME = os.environ.get("TABLE_NAME", "S3-object-size-history")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "testbucket-yunfei-cs6620")  


# Query items for bucket in the last 10 seconds (query, no scan)
def query_last_10_seconds(table, bucket: str):
    now = datetime.now(timezone.utc)
    start = (now - timedelta(seconds=10)).isoformat()
    end = now.isoformat()
    response = table.query(
        KeyConditionExpression="bucket_name = :b AND #t BETWEEN :t1 AND :t2",
        ExpressionAttributeNames={"#t": "timestamp"},
        ExpressionAttributeValues={":b": bucket, ":t1": start, ":t2": end},
    )
    return response.get("Items", [])


def query_global_max_size(table):
    """Query GSI ByMaxSize for the single largest total_size (any bucket)."""
    response = table.query(
        IndexName="ByMaxSize",
        KeyConditionExpression="gsi_pk = :pk",
        ExpressionAttributeValues={":pk": "GLOBAL"},
        Limit=1,
        ScanIndexForward=False,
    )
    items = response.get("Items", [])
    return int(items[0]["total_size"]) if items else 0


def lambda_handler(event, context):
    dynamodb = boto3.resource("dynamodb")
    s3 = boto3.client("s3")
    table = dynamodb.Table(TABLE_NAME)

    items = query_last_10_seconds(table, BUCKET_NAME)
    max_size_ever = query_global_max_size(table)

    timestamps = [datetime.fromisoformat(i["timestamp"].replace("Z", "+00:00")) for i in items]
    sizes = [int(i["total_size"]) for i in items]
    # Sort by time for plot
    if timestamps:
        sorted_pairs = sorted(zip(timestamps, sizes))
        timestamps = [p[0] for p in sorted_pairs]
        sizes = [p[1] for p in sorted_pairs]

    fig, ax1 = plt.subplots(figsize=(10, 6))
    if timestamps and sizes:
        ax1.plot(timestamps, sizes, "b.-", label=f"{BUCKET_NAME} size (last 10s)", color="blue")
        ax1.set_xlabel("Timestamp")
        ax1.set_ylabel("Size (bytes) — last 10s", color="blue")
        ax1.tick_params(axis="y", labelcolor="blue")
        ax1.set_ylim(0, max(sizes) * 1.2 if max(sizes) > 0 else 50)
    ax2 = ax1.twinx()
    ax2.axhline(y=max_size_ever, color="red", linestyle="--", linewidth=2, label="Max size (any bucket, all time)")
    ax2.set_ylabel("Global max (bytes)", color="red")
    ax2.tick_params(axis="y", labelcolor="red")
    ax2.set_ylim(0, max_size_ever * 1.1 if max_size_ever > 0 else 100)
    ax1.set_title("S3 Bucket Size Over Time (Last 10s) vs Global Max")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100)
    plt.close()
    buf.seek(0)

    s3.put_object(Bucket=BUCKET_NAME, Key="plot", Body=buf.getvalue(), ContentType="image/png")

    # REST API response (for API Gateway Lambda proxy integration)
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"message": "Plot saved to s3://' + BUCKET_NAME + '/plot"}',
    }
