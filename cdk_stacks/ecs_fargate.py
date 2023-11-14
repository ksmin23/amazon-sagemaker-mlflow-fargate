#!/usr/bin/env python3
import urllib

import aws_cdk as cdk

from aws_cdk import (
  Stack,
  CfnOutput,
  Aws,
  Duration,

  aws_ec2 as ec2,
  aws_ecs as ecs,
  aws_ecr as ecr,
  aws_ecr_assets as ecr_assets,
  aws_iam as iam,
  aws_ecs_patterns as ecs_patterns,
)

from constructs import Construct


class ECSFargateStack(Stack):

  def __init__(self, scope: Construct, construct_id: str,
    vpc, artifact_bucket, database,
    db_name, username, db_password_secret,
    **kwargs) -> None:

    super().__init__(scope, construct_id, **kwargs)

    # ==================================================
    # ================= IAM ROLE =======================
    # ==================================================
    role = iam.Role(
      scope=self,
      id="TASKROLE",
      assumed_by=iam.ServicePrincipal(service="ecs-tasks.amazonaws.com"),
    )
    role.add_managed_policy(
      iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
    )
    role.add_managed_policy(
      iam.ManagedPolicy.from_aws_managed_policy_name("AmazonECS_FullAccess")
    )

    # ==================================================
    # =============== FARGATE SERVICE ==================
    # ==================================================
    cluster_name = self.node.try_get_context('ecs_cluster_name') or "mlflow"
    cluster = ecs.Cluster(
      scope=self, id="CLUSTER", cluster_name=cluster_name, vpc=vpc
    )

    task_definition = ecs.FargateTaskDefinition(
      scope=self,
      id="MLflow",
      task_role=role,
      cpu=4 * 1024,
      memory_limit_mib=8 * 1024
    )

    container = task_definition.add_container(
      id="Container",
      image=ecs.ContainerImage.from_asset(directory="container"),
      environment={
        "BUCKET": f"s3://{artifact_bucket.bucket_name}",
        "HOST": database.db_instance_endpoint_address,
        "PORT": database.db_instance_endpoint_port,
        "DATABASE": db_name,
        "USERNAME": username
      },
      secrets={"PASSWORD": ecs.Secret.from_secrets_manager(db_password_secret)},
      logging=ecs.LogDriver.aws_logs(stream_prefix="mlflow"),
    )
    port_mapping = ecs.PortMapping(
      container_port=5000, host_port=5000, protocol=ecs.Protocol.TCP
    )
    container.add_port_mappings(port_mapping)

    service_name = self.node.try_get_context('ecs_service_name') or "mlflow"
    fargate_service = ecs_patterns.NetworkLoadBalancedFargateService(
      scope=self,
      id="MLFLOW",
      service_name=service_name,
      cluster=cluster,
      task_definition=task_definition,
    )

    # Setup security group
    fargate_service.service.connections.security_groups[0].add_ingress_rule(
      peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
      connection=ec2.Port.tcp(5000),
      description="Allow inbound from VPC for mlflow",
    )

    # Setup autoscaling policy
    scaling = fargate_service.service.auto_scale_task_count(max_capacity=2)
    scaling.scale_on_cpu_utilization(
      id="AUTOSCALING",
      target_utilization_percent=70,
      scale_in_cooldown=Duration.seconds(60),
      scale_out_cooldown=Duration.seconds(60),
    )

    CfnOutput(
      scope=self,
      id="LoadBalancerDNS",
      value=fargate_service.load_balancer.load_balancer_dns_name,
      export_name=f'{self.stack_name}-LoadBalancerDNS'
    )
