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

output "transcribe_ecr_repository_url" {
  description = "URL of the Transcribe ECR repository"
  value       = aws_ecr_repository.transcribe_ecr.repository_url
}

output "transcribe_lambda_function_name" {
  description = "Name of the Transcribe Lambda function"
  value       = aws_lambda_function.transcribe.function_name
}

output "transcribe_lambda_arn" {
  description = "ARN of the Transcribe Lambda function"
  value       = aws_lambda_function.transcribe.arn
}
output "api_gateway_url" {
  description = "Base URL of the API Gateway"
  value       = aws_api_gateway_stage.dev.invoke_url
}

output "add_podcast_endpoint" {
  description = "Full URL for adding a podcast"
  value       = "${aws_api_gateway_stage.dev.invoke_url}/podcast"
}

output "glue_database_name" {
  description = "Name of the Glue catalog database"
  value       = aws_glue_catalog_database.quadcast.name
}

output "glue_crawler_name" {
  description = "Name of the Glue crawler"
  value       = aws_glue_crawler.quadcast_transcripts.name
}

output "athena_workgroup_name" {
  description = "Name of the Athena workgroup"
  value       = aws_athena_workgroup.quadcast.name
}

output "athena_results_bucket" {
  description = "S3 bucket for Athena query results"
  value       = aws_s3_bucket.athena_results.bucket
}

output "analysis_ecr_repository_url" {
  description = "URL of the Analysis ECR repository"
  value       = aws_ecr_repository.analysis_ecr.repository_url
}

output "analysis_lambda_function_name" {
  description = "Name of the Analysis Lambda function"
  value       = aws_lambda_function.analysis.function_name
}

output "analysis_lambda_arn" {
  description = "ARN of the Analysis Lambda function"
  value       = aws_lambda_function.analysis.arn
}

output "vector_embedding_ecr_repository_url" {
  description = "URL of the Vector Embedding ECR repository"
  value       = aws_ecr_repository.vector_embedding.repository_url
}

output "vector_embedding_lambda_function_name" {
  description = "Name of the Vector Embedding Lambda function"
  value       = aws_lambda_function.vector_embedding.function_name
}

output "vector_embedding_lambda_arn" {
  description = "ARN of the Vector Embedding Lambda function"
  value       = aws_lambda_function.vector_embedding.arn
}