output "rds_name" {
  description = "RDS instance identifier"
  value       = aws_db_instance.postgres.identifier
}

output "rds_endpoint" {
  description = "RDS connection endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "secrets_manager_name" {
  description = "Name of the Secrets Manager secret"
  value       = aws_secretsmanager_secret.quadcast_secrets.name
}

output "secrets_manager_arn" {
  description = "ARN of the Secrets Manager secret"
  value       = aws_secretsmanager_secret.quadcast_secrets.arn
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.quadcast_data.arn
}

output "tfstate_s3_bucket_arn" {
  description = "ARN of the S3 bucket used for Terraform state"
  value       = aws_s3_bucket.terraform_state.arn
}

output "ecr_repository_url" {
  description = "URL of the ECR repository for Streamlit dashboard"
  value       = aws_ecr_repository.streamlit.repository_url
}

output "api_gateway_url" {
  description = "Base URL of the API Gateway"
  value       = aws_api_gateway_stage.dev.invoke_url
}

output "add_podcast_endpoint" {
  description = "Full URL for adding a podcast"
  value       = "${aws_api_gateway_stage.dev.invoke_url}/podcast"
}
