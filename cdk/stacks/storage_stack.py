from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
)
from aws_cdk.aws_lambda_event_sources import S3EventSource
from constructs import Construct
import os

_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


class StorageStack(Stack):
    """S3 bucket (TestBucket), DynamoDB table with GSI ByMaxSize, and size-tracking Lambda with S3 trigger."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.bucket = s3.Bucket(
            self,
            "TestBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        self.table = dynamodb.Table(
            self,
            "SizeHistoryTable",
            partition_key=dynamodb.Attribute(
                name="bucket_name",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # GSI used by plotting lambda to find the global max total_size.
        self.table.add_global_secondary_index(
            index_name="ByMaxSize",
            partition_key=dynamodb.Attribute(
                name="gsi_pk",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="total_size",
                type=dynamodb.AttributeType.NUMBER,
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        CfnOutput(self, "BucketName", value=self.bucket.bucket_name)
        CfnOutput(self, "TableName", value=self.table.table_name)

        # Size-tracking Lambda + S3 trigger (same stack as bucket to avoid cyclic dependency)
        self.size_tracking_fn = lambda_.Function(
            self,
            "SizeTrackingLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(os.path.join(_ROOT, "lambdas", "size_tracking")),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={"TABLE_NAME": self.table.table_name},
        )
        self.bucket.grant_read(self.size_tracking_fn)
        self.table.grant_write_data(self.size_tracking_fn)
        self.size_tracking_fn.add_event_source(
            S3EventSource(
                self.bucket,
                events=[s3.EventType.OBJECT_CREATED, s3.EventType.OBJECT_REMOVED],
            )
        )
        CfnOutput(self, "SizeTrackingFunctionName", value=self.size_tracking_fn.function_name)
