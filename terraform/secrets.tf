resource "random_password" "rds_password" {
  length           = 20
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "quadcast_secrets" {
  name                    = "c20-quadcast-secrets"
  description             = "All credentials and secrets for the Quadcast project"
  recovery_window_in_days = 7

  tags = {
    Name        = "c20-quadcast-secrets"
    Project     = "Quadcast"
    Environment = "dev"
  }
}