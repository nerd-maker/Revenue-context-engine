# Terraform MSK (Managed Streaming for Kafka) Module
# Production-grade Kafka cluster

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Security group
resource "aws_security_group" "msk" {
  name        = "${var.environment}-revenue-context-msk"
  description = "Security group for MSK Kafka"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 9092
    to_port         = 9092
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
    description     = "Kafka plaintext from application"
  }

  ingress {
    from_port       = 9094
    to_port         = 9094
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
    description     = "Kafka TLS from application"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Environment = var.environment
  }
}

# CloudWatch log group
resource "aws_cloudwatch_log_group" "msk" {
  name              = "/aws/msk/${var.environment}-revenue-context"
  retention_in_days = 7

  tags = {
    Environment = var.environment
  }
}

# MSK Configuration
resource "aws_msk_configuration" "kafka" {
  name              = "${var.environment}-revenue-context"
  kafka_versions    = ["3.5.1"]
  server_properties = <<PROPERTIES
auto.create.topics.enable=false
default.replication.factor=3
min.insync.replicas=2
num.partitions=3
log.retention.hours=168
compression.type=snappy
PROPERTIES
}

# MSK Cluster
resource "aws_msk_cluster" "main" {
  cluster_name           = "${var.environment}-revenue-context"
  kafka_version          = "3.5.1"
  number_of_broker_nodes = 3

  broker_node_group_info {
    instance_type   = var.broker_instance_type
    client_subnets  = var.private_subnet_ids
    security_groups = [aws_security_group.msk.id]

    storage_info {
      ebs_storage_info {
        volume_size            = var.broker_volume_size
        provisioned_throughput {
          enabled           = true
          volume_throughput = 250
        }
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  configuration_info {
    arn      = aws_msk_configuration.kafka.arn
    revision = aws_msk_configuration.kafka.latest_revision
  }

  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = aws_cloudwatch_log_group.msk.name
      }
    }
  }

  open_monitoring {
    prometheus {
      jmx_exporter {
        enabled_in_broker = true
      }
      node_exporter {
        enabled_in_broker = true
      }
    }
  }

  tags = {
    Environment = var.environment
    Service     = "revenue-context-engine"
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "kafka_cpu_high" {
  alarm_name          = "${var.environment}-kafka-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CpuUser"
  namespace           = "AWS/Kafka"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Kafka CPU usage above 80%"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    "Cluster Name" = aws_msk_cluster.main.cluster_name
  }
}

resource "aws_cloudwatch_metric_alarm" "kafka_disk_high" {
  alarm_name          = "${var.environment}-kafka-disk-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "KafkaDataLogsDiskUsed"
  namespace           = "AWS/Kafka"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Kafka disk usage above 80%"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    "Cluster Name" = aws_msk_cluster.main.cluster_name
  }
}

# Outputs
output "bootstrap_brokers_tls" {
  value       = aws_msk_cluster.main.bootstrap_brokers_tls
  description = "Kafka bootstrap brokers (TLS)"
}

output "zookeeper_connect_string" {
  value       = aws_msk_cluster.main.zookeeper_connect_string
  description = "Zookeeper connection string"
}

output "cluster_arn" {
  value       = aws_msk_cluster.main.arn
  description = "MSK cluster ARN"
}
