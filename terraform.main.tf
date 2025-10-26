# terraform/main.tf
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }
  backend "s3" {
    bucket         = "ymera-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "terraform-lock"
  }
}

provider "aws" {
  region = var.aws_region
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  token                  = data.aws_eks_cluster_auth.cluster.token
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    token                  = data.aws_eks_cluster_auth.cluster.token
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "ymera-enterprise"
  cluster_version = "1.27"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access = true

  eks_managed_node_groups = {
    compute = {
      min_size     = 3
      max_size     = 10
      desired_size = 3

      instance_types = ["m6i.large", "m6i.xlarge"]
      capacity_type  = "ON_DEMAND"

      labels = {
        node-type = "compute-optimized"
      }

      taints = [{
        key    = "dedicated"
        value  = "ymera"
        effect = "NO_SCHEDULE"
      }]

      tags = {
        Environment = "production"
      }
    }

    memory = {
      min_size     = 2
      max_size     = 6
      desired_size = 2

      instance_types = ["r6i.large", "r6i.xlarge"]
      capacity_type  = "ON_DEMAND"

      labels = {
        node-type = "memory-optimized"
      }

      tags = {
        Environment = "production"
      }
    }
  }

  node_security_group_additional_rules = {
    ingress_https = {
      description = "HTTPS from everywhere"
      protocol    = "tcp"
      from_port   = 443
      to_port     = 443
      type        = "ingress"
      cidr_blocks = ["0.0.0.0/0"]
    }

    ingress_istio = {
      description = "Istio ports"
      protocol    = "tcp"
      from_port   = 15017
      to_port     = 15017
      type        = "ingress"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  tags = {
    Environment = "production"
    Application = "ymera-enterprise"
  }
}

# VPC
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "ymera-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-west-2a", "us-west-2b", "us-west-2c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = false
  enable_dns_hostnames = true

  tags = {
    Environment = "production"
    Application = "ymera-enterprise"
  }
}

# RDS PostgreSQL
module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "ymera-db"

  engine               = "postgresql"
  engine_version       = "15.3"
  instance_class       = "db.m6i.large"
  allocated_storage    = 100
  max_allocated_storage = 500

  db_name  = "ymera"
  username = var.db_username
  password = var.db_password
  port     = 5432

  multi_az               = true
  vpc_security_group_ids = [module.rds_security_group.security_group_id]
  subnet_ids             = module.vpc.private_subnets

  maintenance_window = "Mon:03:00-Mon:04:00"
  backup_window      = "02:00-03:00"
  backup_retention_period = 35

  performance_insights_enabled = true

  create_db_subnet_group    = true
  create_db_parameter_group = true
  create_db_option_group    = true

  parameters = [
    {
      name  = "autovacuum"
      value = 1
    },
    {
      name  = "client_encoding"
      value = "utf8"
    }
  ]

  tags = {
    Environment = "production"
    Application = "ymera-enterprise"
  }
}

# Elasticache Redis
module "redis" {
  source  = "terraform-aws-modules/elasticache/aws"
  version = "~> 4.0"

  cluster_id           = "ymera-redis"
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = "cache.m6g.large"
  num_cache_nodes      = 3
  parameter_group_name = "default.redis7"

  subnet_ids             = module.vpc.private_subnets
  vpc_security_group_ids = [module.redis_security_group.security_group_id]

  maintenance_window = "mon:03:00-mon:04:00"
  snapshot_window   = "02:00-03:00"

  tags = {
    Environment = "production"
    Application = "ymera-enterprise"
  }
}

# MSK Kafka
module "msk" {
  source  = "terraform-aws-modules/msk/aws"
  version = "~> 4.0"

  cluster_name = "ymera-kafka"

  kafka_version    = "3.4.0"
  number_of_broker_nodes = 3
  broker_node_instance_type = "kafka.m5.large"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  security_groups = [module.kafka_security_group.security_group_id]

  configuration_server_properties = {
    "auto.create.topics.enable" = "false"
    "delete.topic.enable"       = "true"
    "log.retention.hours"       = "168"
  }

  cloudwatch_logs_enabled = true

  tags = {
    Environment = "production"
    Application = "ymera-enterprise"
  }
}

# Security Groups
module "rds_security_group" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"

  name        = "ymera-rds-sg"
  description = "Security group for RDS database"
  vpc_id      = module.vpc.vpc_id

  ingress_with_source_security_group_id = [
    {
      rule                     = "postgresql-tcp"
      source_security_group_id = module.eks.node_security_group_id
    }
  ]

  egress_rules = ["all-all"]
}

module "redis_security_group" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"

  name        = "ymera-redis-sg"
  description = "Security group for Redis"
  vpc_id      = module.vpc.vpc_id

  ingress_with_source_security_group_id = [
    {
      rule                     = "redis-tcp"
      source_security_group_id = module.eks.node_security_group_id
    }
  ]

  egress_rules = ["all-all"]
}

module "kafka_security_group" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.0"

  name        = "ymera-kafka-sg"
  description = "Security group for Kafka"
  vpc_id      = module.vpc.vpc_id

  ingress_with_source_security_group_id = [
    {
      rule                     = "kafka-tcp"
      source_security_group_id = module.eks.node_security_group_id
    }
  ]

  egress_rules = ["all-all"]
}

# IAM Roles
resource "aws_iam_role" "ymera_enterprise_role" {
  name = "ymera-enterprise-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRoleWithWebIdentity"
        Effect = "Allow"
        Principal = {
          Federated = module.eks.oidc_provider_arn
        }
        Condition = {
          StringEquals = {
            "${module.eks.oidc_provider}:sub" = "system:serviceaccount:ymera-enterprise:ymera-service-account"
          }
        }
      }
    ]
  })

  tags = {
    Environment = "production"
    Application = "ymera-enterprise"
  }
}

resource "aws_iam_role_policy_attachment" "ymera_s3_access" {
  role       = aws_iam_role.ymera_enterprise_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "ymera_rds_access" {
  role       = aws_iam_role.ymera_enterprise_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonRDSFullAccess"
}

resource "aws_iam_role_policy_attachment" "ymera_cloudwatch_access" {
  role       = aws_iam_role.ymera_enterprise_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchFullAccess"
}

# Outputs
output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_certificate_authority_data" {
  description = "EKS cluster CA certificate"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = module.rds.db_instance_address
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.redis.redis_endpoint
}

output "kafka_bootstrap_brokers" {
  description = "Kafka bootstrap brokers"
  value       = module.msk.bootstrap_brokers
  sensitive   = true
}