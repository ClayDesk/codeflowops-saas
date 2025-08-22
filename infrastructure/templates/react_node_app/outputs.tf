# React Node App Template Outputs

output "application_url" {
  description = "Public URL of the deployed application"
  value       = "http://${aws_lb.main.dns_name}"
}

output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "load_balancer_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.main.arn
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = aws_ecs_service.app.name
}

output "database_endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "database_port" {
  description = "Database port"
  value       = aws_db_instance.main.port
}

output "database_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "security_group_alb" {
  description = "ALB security group ID"
  value       = aws_security_group.alb.id
}

output "security_group_ecs" {
  description = "ECS security group ID"
  value       = aws_security_group.ecs.id
}

output "security_group_rds" {
  description = "RDS security group ID"
  value       = aws_security_group.rds.id
}

output "ecs_execution_role_arn" {
  description = "ECS execution role ARN"
  value       = aws_iam_role.ecs_execution.arn
}

output "ecs_task_role_arn" {
  description = "ECS task role ARN"
  value       = aws_iam_role.ecs_task.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.app.name
}

# Deployment information
output "deployment_info" {
  description = "Comprehensive deployment information"
  value = {
    project_name      = var.project_name
    environment       = var.environment
    region           = var.aws_region
    application_url  = "http://${aws_lb.main.dns_name}"
    ecs_cluster      = aws_ecs_cluster.main.name
    ecs_service      = aws_ecs_service.app.name
    database_endpoint = aws_db_instance.main.endpoint
    vpc_id           = aws_vpc.main.id
    load_balancer    = aws_lb.main.dns_name
    log_group        = aws_cloudwatch_log_group.app.name
  }
  sensitive = true
}

# Database connection info (sensitive)
output "database_connection" {
  description = "Database connection information"
  value = {
    host     = aws_db_instance.main.endpoint
    port     = aws_db_instance.main.port
    database = aws_db_instance.main.db_name
    username = aws_db_instance.main.username
    password = random_password.db_password.result
  }
  sensitive = true
}
