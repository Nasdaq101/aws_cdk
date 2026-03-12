import os
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_s3 as s3,
)
from constructs import Construct

_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


class ApiStack(Stack):
    """REST API (API Gateway) backed by plotting Lambda + driver Lambda."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        plotting_fn: lambda_.Function,
        bucket: s3.Bucket,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        rest_api = apigw.LambdaRestApi(
            self,
            "PlottingApi",
            handler=plotting_fn,
            proxy=True,
            description="REST API that invokes the plotting Lambda",
        )

        # Driver Lambda lives here so it can reference rest_api.url without
        # creating a circular dependency between LambdaStack and ApiStack.
        driver_fn = lambda_.Function(
            self,
            "DriverLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(os.path.join(_ROOT, "lambdas", "driver")),
            timeout=Duration.seconds(120),
            memory_size=256,
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "PLOTTING_API_URL": rest_api.url,
            },
        )
        bucket.grant_read_write(driver_fn)

        CfnOutput(self, "ApiUrl", value=rest_api.url)
        CfnOutput(self, "DriverFunctionName", value=driver_fn.function_name)
