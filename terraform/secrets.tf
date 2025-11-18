resource "random_password" "rds_password" {
  length           = 20
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "quadcast_secrets" {
  name                    = "c20-quadcast-secrets"
  description             = "All credentials and secrets for the QuadCast project"
  recovery_window_in_days = 7

  tags = {
    Name        = "c20-quadcast-secrets"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

resource "aws_secretsmanager_secret_version" "quadcast_secrets" {
  secret_id = aws_secretsmanager_secret.quadcast_secrets.id
  secret_string = jsonencode({
    RDS_HOST     = aws_db_instance.postgres.address
    RDS_DB_NAME     = aws_db_instance.postgres.db_name
    RDS_PASSWORD = random_password.rds_password.result
    RDS_PORT     = tostring(aws_db_instance.postgres.port)
    RDS_USERNAME     = "quadcast_admin"
    OPENAI_API_KEY = var.openai_api_key
  })
}

