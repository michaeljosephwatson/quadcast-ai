# Security Group for Daily Pipeline Lambda
resource "aws_security_group" "daily_pipeline_lambda" {
  name        = "c20-quadcast-daily-pipeline-lambda-sg"
  description = "Security group for Daily Pipeline Lambda function"
  vpc_id      = data.aws_vpc.c20.id

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "c20-quadcast-daily-pipeline-lambda-sg"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# Allow Lambda to access RDS
resource "aws_security_group_rule" "daily_pipeline_lambda_to_rds" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.daily_pipeline_lambda.id
  security_group_id        = aws_security_group.quadcast_rds.id
  description              = "Allow Daily Pipeline Lambda to access RDS"
}

# IAM Role for Lambda Execution
resource "aws_iam_role" "daily_pipeline_lambda" {
  name = "c20-quadcast-daily-pipeline-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "c20-quadcast-daily-pipeline-lambda-role"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# IAM Policy for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "daily_pipeline_lambda_basic_execution" {
  role       = aws_iam_role.daily_pipeline_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "daily_pipeline_lambda" {
  name              = "/aws/lambda/c20-quadcast-daily-pipeline"
  retention_in_days = 7

  tags = {
    Name        = "c20-quadcast-daily-pipeline-logs"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# Lambda Function
resource "aws_lambda_function" "daily_pipeline" {
  function_name = "c20-quadcast-daily-pipeline"
  role          = aws_iam_role.daily_pipeline_lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.daily_pipeline_ecr.repository_url}:latest"

  timeout     = 900
  memory_size = 512

  environment {
    variables = {
      RDS_HOST     = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_HOST"]
      RDS_DB_NAME  = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_DB_NAME"]
      RDS_USERNAME = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_USERNAME"]
      RDS_PASSWORD = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_PASSWORD"]
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.daily_pipeline_lambda,
    aws_iam_role_policy_attachment.daily_pipeline_lambda_basic_execution
  ]

  tags = {
    Name        = "c20-quadcast-daily-pipeline"
    Project     = "QuadCast"
    Environment = "dev"
  }
}
