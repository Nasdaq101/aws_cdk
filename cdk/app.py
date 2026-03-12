#!/usr/bin/env python3
import os
import aws_cdk as cdk

from stacks.storage_stack import StorageStack
from stacks.lambda_stack import LambdaStack
from stacks.api_stack import ApiStack

app = cdk.App()

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
)

# Stack 1: S3 bucket + DynamoDB table (foundational storage layer)
storage_stack = StorageStack(app, "StorageStack", env=env)

# Stack 2: size-tracking Lambda, plotting Lambda, matplotlib layer, S3 trigger
lambda_stack = LambdaStack(
    app,
    "LambdaStack",
    bucket=storage_stack.bucket,
    table=storage_stack.table,
    env=env,
)

# Stack 3: REST API Gateway + driver Lambda
api_stack = ApiStack(
    app,
    "ApiStack",
    plotting_fn=lambda_stack.plotting_fn,
    bucket=storage_stack.bucket,
    env=env,
)

app.synth()
