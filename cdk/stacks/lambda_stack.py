import os
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_lambda as lambda_,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
)
import aws_cdk.aws_lambda_python_alpha as lambda_python
from constructs import Construct


_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


class LambdaStack(Stack):
    """Plotting Lambda, matplotlib Layer (size-tracking Lambda lives in StorageStack)."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        bucket: s3.Bucket,
        table: dynamodb.Table,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        matplotlib_layer = lambda_python.PythonLayerVersion(
            self,
            "MatplotlibLayer",
            entry=os.path.join(_ROOT, "layers", "matplotlib"),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="matplotlib for plotting lambda",
        )

        # ── plotting Lambda ───────────────────────────────────────────────────
        self.plotting_fn = lambda_.Function(
            self,
            "PlottingLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(os.path.join(_ROOT, "lambdas", "plotting")),
            timeout=Duration.seconds(60),
            memory_size=512,
            layers=[matplotlib_layer],
            environment={
                "TABLE_NAME": table.table_name,
                "BUCKET_NAME": bucket.bucket_name,
            },
        )
        table.grant_read_data(self.plotting_fn)
        bucket.grant_put(self.plotting_fn)

        CfnOutput(self, "PlottingFunctionName", value=self.plotting_fn.function_name)
