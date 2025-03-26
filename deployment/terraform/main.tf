terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC Configuration
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "midcoast-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true

  tags = {
    Environment = var.environment
    Project     = "midcoast"
  }
}

# EKS Cluster
module "eks" {
  source = "terraform-aws-modules/eks/aws"

  cluster_name    = "midcoast-cluster"
  cluster_version = "1.21"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_private_access = true
  cluster_endpoint_public_access  = true

  # Node groups
  eks_managed_node_groups = {
    main = {
      desired_size = 2
      max_size     = 4
      min_size     = 1

      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
    }
  }

  tags = {
    Environment = var.environment
    Project     = "midcoast"
  }
}

# RDS Database
module "db" {
  source = "terraform-aws-modules/rds/aws"

  identifier = "midcoast-db"

  engine            = "postgres"
  engine_version    = "13.4"
  instance_class    = "db.t3.medium"
  allocated_storage = 20

  db_name  = "midcoast"
  username = var.db_username
  password = var.db_password
  port     = "5432"

  vpc_security_group_ids = [aws_security_group.rds.id]
  subnet_ids             = module.vpc.private_subnets

  family = "postgres13"

  major_engine_version = "13"

  tags = {
    Environment = var.environment
    Project     = "midcoast"
  }
}

# ElastiCache Redis
module "redis" {
  source = "terraform-aws-modules/elasticache/aws"

  cluster_id           = "midcoast-redis"
  engine              = "redis"
  node_type           = "cache.t3.micro"
  num_cache_nodes     = 1
  parameter_group_family = "redis6.x"
  port                = 6379

  subnet_ids          = module.vpc.private_subnets
  security_group_ids  = [aws_security_group.redis.id]

  tags = {
    Environment = var.environment
    Project     = "midcoast"
  }
}

# MSK (Kafka)
resource "aws_msk_cluster" "midcoast" {
  cluster_name           = "midcoast-kafka"
  kafka_version          = "2.8.1"
  number_of_broker_nodes = 2

  broker_node_group_info {
    instance_type   = "kafka.t3.small"
    client_subnets  = module.vpc.private_subnets
    security_groups = [aws_security_group.kafka.id]
  }

  encryption_info {
    encryption_at_rest_kms_key_arn = aws_kms_key.kafka.arn
  }

  tags = {
    Environment = var.environment
    Project     = "midcoast"
  }
}

# Security Groups
resource "aws_security_group" "rds" {
  name        = "midcoast-rds"
  description = "Security group for RDS"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
  }
}

resource "aws_security_group" "redis" {
  name        = "midcoast-redis"
  description = "Security group for Redis"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
  }
}

resource "aws_security_group" "kafka" {
  name        = "midcoast-kafka"
  description = "Security group for Kafka"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 9092
    to_port         = 9092
    protocol        = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
  }
}

# KMS Key for Kafka
resource "aws_kms_key" "kafka" {
  description = "KMS key for Kafka encryption"
  
  tags = {
    Environment = var.environment
    Project     = "midcoast"
  }
}

# Route53 DNS
resource "aws_route53_zone" "main" {
  name = var.domain_name

  tags = {
    Environment = var.environment
    Project     = "midcoast"
  }
}

# ACM Certificate
resource "aws_acm_certificate" "main" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  tags = {
    Environment = var.environment
    Project     = "midcoast"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# S3 Bucket for Assets
resource "aws_s3_bucket" "assets" {
  bucket = "midcoast-assets-${var.environment}"
  acl    = "private"

  versioning {
    enabled = true
  }

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  tags = {
    Environment = var.environment
    Project     = "midcoast"
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "app" {
  name              = "/midcoast/app"
  retention_in_days = 30

  tags = {
    Environment = var.environment
    Project     = "midcoast"
  }
}

# Outputs
output "eks_cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "db_endpoint" {
  description = "RDS instance endpoint"
  value       = module.db.db_instance_endpoint
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.redis.redis_endpoint
}

output "kafka_brokers" {
  description = "Kafka broker endpoints"
  value       = aws_msk_cluster.midcoast.bootstrap_brokers
}
