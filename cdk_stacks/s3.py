#!/usr/bin/env python3
import aws_cdk as cdk

from aws_cdk import (
  Stack,
  CfnParameter,
  CfnOutput,
  Aws,

  aws_s3 as s3,
)

from constructs import Construct


class S3Stack(Stack):

  def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # ==============================
    # ======= CFN PARAMETERS =======
    # ==============================
    project_name_param = CfnParameter(scope=self, id="ProjectName", type="String", default="mlflow")
    bucket_name = f"{project_name_param.value_as_string}-artifacts-{Aws.ACCOUNT_ID}"

    # ==================================================
    # ================= S3 BUCKET ======================
    # ==================================================
    self.artifact_bucket = s3.Bucket(
      scope=self,
      id="ARTIFACTBUCKET",
      bucket_name=bucket_name,
      public_read_access=False,
    )

    CfnOutput(
      scope=self,
      id="ArtifactBucketName",
      value=self.artifact_bucket.bucket_name,
      export_name=f"{self.stack_name}-ArtifactBucketName"
    )