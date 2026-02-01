provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  name = "revenue-context-vpc"
  cidr = var.vpc_cidr
  azs = var.azs
  public_subnets = var.public_subnets
  private_subnets = var.private_subnets
  enable_nat_gateway = true
}

module "rds" {
  source = "terraform-aws-modules/rds/aws"
  identifier = "revenue-context-db"
  engine = "postgres"
  engine_version = "15.4"
  instance_class = var.rds_instance_class
  allocated_storage = 100
  storage_encrypted = true
  multi_az = true
  db_subnet_group_name = module.vpc.database_subnet_group
  vpc_security_group_ids = [module.vpc.default_security_group_id]
  username = var.db_username
  password = var.db_password
  db_name = var.db_name
  publicly_accessible = false
  backup_retention_period = 35
  deletion_protection = true
}

module "redis" {
  source = "terraform-aws-modules/elasticache/aws"
  name = "revenue-context-redis"
  engine = "redis"
  node_type = var.redis_node_type
  num_cache_nodes = 2
  cluster_mode = true
  subnet_group_name = module.vpc.database_subnet_group
  vpc_security_group_ids = [module.vpc.default_security_group_id]
}

module "msk" {
  source = "terraform-aws-modules/msk-kafka-cluster/aws"
  cluster_name = "revenue-context-msk"
  kafka_version = "3.6.0"
  number_of_broker_nodes = 3
  broker_node_instance_type = var.msk_instance_type
  client_subnets = module.vpc.private_subnets
  security_groups = [module.vpc.default_security_group_id]
}

module "ecs" {
  source = "terraform-aws-modules/ecs/aws"
  cluster_name = "revenue-context-ecs"
  vpc_id = module.vpc.vpc_id
  subnets = module.vpc.private_subnets
}

module "alb" {
  source = "terraform-aws-modules/alb/aws"
  name = "revenue-context-alb"
  vpc_id = module.vpc.vpc_id
  subnets = module.vpc.public_subnets
  security_groups = [module.vpc.default_security_group_id]
  enable_https = true
  certificate_arn = var.acm_certificate_arn
}

resource "aws_s3_bucket" "audit_logs" {
  bucket = "revenue-context-audit-logs"
  lifecycle {
    prevent_destroy = true
    transition {
      days          = 30
      storage_class = "GLACIER"
    }
    expiration {
      days = 2555 # 7 years
    }
  }
}
