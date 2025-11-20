# IAM Role for Transcribe Lambda Execution
resource "aws_iam_role" "transcribe_lambda" {
  name = "c20-quadcast-transcribe-lambda-role"

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
    Name        = "c20-quadcast-transcribe-lambda-role"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# IAM Policy for VPC Access
resource "aws_iam_role_policy_attachment" "transcribe_lambda_vpc_execution" {
  role       = aws_iam_role.transcribe_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# IAM Policy for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "transcribe_lambda_basic_execution" {
  role       = aws_iam_role.transcribe_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# IAM Policy for Secrets Manager Access
resource "aws_iam_role_policy_attachment" "transcribe_lambda_secrets_access" {
  role       = aws_iam_role.transcribe_lambda.name
  policy_arn = aws_iam_policy.lambda_secrets_access.arn
}

# IAM Policy for S3 Access
resource "aws_iam_policy" "transcribe_lambda_s3_access" {
  name        = "c20-quadcast-transcribe-lambda-s3-access"
  description = "Allow Transcribe Lambda to read/write S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
            aws_s3_bucket.quadcast_data.arn,
            "${aws_s3_bucket.quadcast_data.arn}/*"
        ]
      }
    ]
  })

  tags = {
    Name        = "c20-quadcast-transcribe-lambda-s3-access"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

resource "aws_iam_role_policy_attachment" "transcribe_lambda_s3_access" {
  role       = aws_iam_role.transcribe_lambda.name
  policy_arn = aws_iam_policy.transcribe_lambda_s3_access.arn
}

# CloudWatch Log Group for Transcribe Lambda
resource "aws_cloudwatch_log_group" "transcribe_lambda" {
  name              = "/aws/lambda/c20-quadcast-transcribe"
  retention_in_days = 7

  tags = {
    Name        = "c20-quadcast-transcribe-logs"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# Lambda Function
resource "aws_lambda_function" "transcribe" {
  function_name = "c20-quadcast-transcribe"
  role          = aws_iam_role.transcribe_lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.transcribe_ecr.repository_url}:latest"

  timeout     = 900
  memory_size = 10240

  environment {
  variables = {
    USE_SECRETS_MANAGER = "false"
    S3_BUCKET           = "c20-quadcast-s3-bucket"
    RDS_HOST            = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_HOST"]
    RDS_DB_NAME         = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_DB_NAME"]
    RDS_USERNAME        = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_USERNAME"]
    RDS_PASSWORD        = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_PASSWORD"]
    RDS_PORT            = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_PORT"]
    OPENAI_API_KEY      = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["OPENAI_API_KEY"]
  }
}

  depends_on = [
    aws_cloudwatch_log_group.transcribe_lambda,
    aws_iam_role_policy_attachment.transcribe_lambda_basic_execution,
    aws_iam_role_policy_attachment.transcribe_lambda_secrets_access,
    aws_iam_role_policy_attachment.transcribe_lambda_s3_access
  ]

  tags = {
    Name        = "c20-quadcast-transcribe"
    Project     = "QuadCast"
    Environment = "dev"
  }
}