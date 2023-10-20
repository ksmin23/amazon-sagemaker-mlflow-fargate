#!/usr/bin/env python3
import aws_cdk as cdk

from aws_cdk import (
  Stack,
  CfnOutput,
  Aws,
  RemovalPolicy,

  aws_ec2 as ec2,
  aws_rds as rds,
  aws_secretsmanager as sm,
)

from constructs import Construct


class RDSStack(Stack):

  def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
    super().__init__(scope, construct_id, **kwargs)

    db_name = "mlflowdb"
    port = 3306
    username = "master"

    # ==================================================
    # ================== SECRET ========================
    # ==================================================
    db_password_secret = sm.Secret(
      scope=self,
      id="DBSECRET",
      secret_name="dbPassword",
      generate_secret_string=sm.SecretStringGenerator(
        password_length=20, exclude_punctuation=True
      ),
    )

    # # ==================================================
    # # ================== DATABASE  =====================
    # # ==================================================
    # Creates a security group for AWS RDS
    sg_rds = ec2.SecurityGroup(
      scope=self, id="SGRDS", vpc=vpc, security_group_name="sg_rds"
    )
    # Adds an ingress rule which allows resources in the VPC's CIDR to access the database.
    sg_rds.add_ingress_rule(
      peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
      connection=ec2.Port.tcp(port),
      description="Allow inbound from VPC for mlflow"
    )

    sg_rds.add_ingress_rule(
      peer=sg_rds,
      connection=ec2.Port.all_tcp(),
      description="Allow inbound from RDS itself"
    )

    self.database = rds.DatabaseInstance(
      scope=self,
      id="MYSQL",
      database_name=db_name,
      port=port,
      credentials=rds.Credentials.from_username(
        username=username, password=db_password_secret.secret_value
      ),
      engine=rds.DatabaseInstanceEngine.mysql(
        version=rds.MysqlEngineVersion.VER_8_0_34
      ),
      instance_type=ec2.InstanceType.of(
        ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.SMALL
      ),
      vpc=vpc,
      security_groups=[sg_rds],
      vpc_subnets=ec2.SubnetSelection(
        subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
      ),
      # multi_az=True,
      removal_policy=RemovalPolicy.DESTROY,
      deletion_protection=False,
    )

    self.db_name = db_name
    self.db_username = username
    self.db_password_secret = db_password_secret

    CfnOutput(self, "DatabaseName", value=self.db_name,
      export_name=f"{self.stack_name}-DatabaseName")

    CfnOutput(self, "DBUserName", value=self.db_username,
      export_name=f"{self.stack_name}-DBUserName")

    CfnOutput(self, "DBPasswordSecret", value=self.db_password_secret.secret_name,
      export_name=f"{self.stack_name}-DBPasswordSecret")
