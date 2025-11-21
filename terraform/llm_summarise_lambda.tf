# Security Group for Analysis Lambda
resource "aws_security_group" "analysis_lambda" {
  name        = "c20-quadcast-analysis-lambda-sg"
  description = "Security group for OpenAI Analysis Lambda function"
  vpc_id      = data.aws_vpc.c20.id

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "c20-quadcast-analysis-lambda-sg"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# Allow Analysis Lambda to access RDS
resource "aws_security_group_rule" "analysis_lambda_to_rds" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.analysis_lambda.id
  security_group_id        = aws_security_group.quadcast_rds.id
  description              = "Allow Analysis Lambda to access RDS"
}

# IAM Role for Analysis Lambda Execution
resource "aws_iam_role" "analysis_lambda" {
  name = "c20-quadcast-analysis-lambda-role"

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
    Name        = "c20-quadcast-analysis-lambda-role"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# IAM Policy for VPC Access
resource "aws_iam_role_policy_attachment" "analysis_lambda_vpc_execution" {
  role       = aws_iam_role.analysis_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# IAM Policy for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "analysis_lambda_basic_execution" {
  role       = aws_iam_role.analysis_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# IAM Policy for Secrets Manager Access (reuse existing policy)
resource "aws_iam_role_policy_attachment" "analysis_lambda_secrets_access" {
  role       = aws_iam_role.analysis_lambda.name
  policy_arn = aws_iam_policy.lambda_secrets_access.arn
}

# IAM Policy for S3 Access (read transcripts/segments, write summaries)
resource "aws_iam_policy" "analysis_lambda_s3_access" {
  name        = "c20-quadcast-analysis-lambda-s3-access"
  description = "Allow Analysis Lambda to read transcripts/segments and write summaries to S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = [
          "${aws_s3_bucket.quadcast_data.arn}/transcripts/*",
          "${aws_s3_bucket.quadcast_data.arn}/segments/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = [
          "${aws_s3_bucket.quadcast_data.arn}/summaries/*"
        ]
      }
    ]
  })

  tags = {
    Name        = "c20-quadcast-analysis-lambda-s3-access"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

resource "aws_iam_role_policy_attachment" "analysis_lambda_s3_access" {
  role       = aws_iam_role.analysis_lambda.name
  policy_arn = aws_iam_policy.analysis_lambda_s3_access.arn
}

# CloudWatch Log Group for Analysis Lambda
resource "aws_cloudwatch_log_group" "analysis_lambda" {
  name              = "/aws/lambda/c20-quadcast-analysis"
  retention_in_days = 7

  tags = {
    Name        = "c20-quadcast-analysis-logs"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# Lambda Function
resource "aws_lambda_function" "analysis" {
  function_name = "c20-quadcast-analysis"
  role          = aws_iam_role.analysis_lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.analysis_ecr.repository_url}:latest"

  timeout     = 300
  memory_size = 2048

  environment {
    variables = {
      RDS_HOST        = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_HOST"]
      RDS_DB_NAME     = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_DB_NAME"]
      RDS_USERNAME    = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_USERNAME"]
      RDS_PASSWORD    = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_PASSWORD"]
      OPENAI_API_KEY  = var.openai_api_key
      S3_BUCKET       = aws_s3_bucket.quadcast_data.id
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.analysis_lambda,
    aws_iam_role_policy_attachment.analysis_lambda_vpc_execution,
    aws_iam_role_policy_attachment.analysis_lambda_basic_execution,
    aws_iam_role_policy_attachment.analysis_lambda_secrets_access,
    aws_iam_role_policy_attachment.analysis_lambda_s3_access
  ]

  tags = {
    Name        = "c20-quadcast-analysis"
    Project     = "QuadCast"
    Environment = "dev"
  }
}