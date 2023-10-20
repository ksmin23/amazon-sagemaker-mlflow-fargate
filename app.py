# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os

import aws_cdk as cdk

from cdk_stacks import (
  VpcStack,
  S3Stack,
  RDSStack,
  ECSFargateStack
)


AWS_ENV = cdk.Environment(
  account=os.environ["CDK_DEFAULT_ACCOUNT"],
  region=os.environ["CDK_DEFAULT_REGION"]
)

app = cdk.App()

vpc_stack = VpcStack(app, "MLflowVpcStack",
    env=AWS_ENV)

s3_stack = S3Stack(app, "MLflowS3Stack",
  env=AWS_ENV
)
s3_stack.add_dependency(vpc_stack)

rds_stack = RDSStack(app, "MLflowRDSStack",
  vpc_stack.vpc,
  env=AWS_ENV
)
rds_stack.add_dependency(s3_stack)

ecs_fargate_stack = ECSFargateStack(app, "MLflowECSFargateStack",
  vpc_stack.vpc,
  s3_stack.artifact_bucket,
  rds_stack.database,
  rds_stack.db_name,
  rds_stack.db_username,
  rds_stack.db_password_secret,
  env=AWS_ENV
)
ecs_fargate_stack.add_dependency(rds_stack)

app.synth()
