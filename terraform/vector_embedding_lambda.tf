# IAM Role for Vector Embedding Lambda Execution
resource "aws_iam_role" "vector_embedding_lambda" {
  name = "c20-quadcast-vector-embedding-lambda-role"

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
    Name        = "c20-quadcast-vector-embedding-lambda-role"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# IAM Policy for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "vector_embedding_lambda_basic_execution" {
  role       = aws_iam_role.vector_embedding_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# IAM Policy for Secrets Manager Access
resource "aws_iam_role_policy_attachment" "vector_embedding_lambda_secrets_access" {
  role       = aws_iam_role.vector_embedding_lambda.name
  policy_arn = aws_iam_policy.lambda_secrets_access.arn
}

# IAM Policy for S3 Access (read transcripts only)
resource "aws_iam_policy" "vector_embedding_lambda_s3_access" {
  name        = "c20-quadcast-vector-embedding-lambda-s3-access"
  description = "Allow Vector Embedding Lambda to read transcripts from S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = [
          "${aws_s3_bucket.quadcast_data.arn}/transcripts/*"
        ]
      }
    ]
  })

  tags = {
    Name        = "c20-quadcast-vector-embedding-lambda-s3-access"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

resource "aws_iam_role_policy_attachment" "vector_embedding_lambda_s3_access" {
  role       = aws_iam_role.vector_embedding_lambda.name
  policy_arn = aws_iam_policy.vector_embedding_lambda_s3_access.arn
}

# CloudWatch Log Group for Vector Embedding Lambda
resource "aws_cloudwatch_log_group" "vector_embedding_lambda" {
  name              = "/aws/lambda/c20-quadcast-vector-embedding"
  retention_in_days = 7

  tags = {
    Name        = "c20-quadcast-vector-embedding-logs"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# Lambda Function
resource "aws_lambda_function" "vector_embedding" {
  function_name = "c20-quadcast-vector-embedding"
  role          = aws_iam_role.vector_embedding_lambda.arn
  package_type  = "Image"
  image_uri = "${aws_ecr_repository.vector_embedding.repository_url}:latest"

  timeout     = 900
  memory_size = 10240

  environment {
    variables = {
      RDS_HOST         = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_HOST"]
      RDS_DB_NAME      = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_DB_NAME"]
      RDS_USERNAME     = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_USERNAME"]
      RDS_PASSWORD     = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_PASSWORD"]
      RDS_PORT         = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_PORT"]
      S3_BUCKET       = aws_s3_bucket.quadcast_data.id
      OPENAI_API_KEY  = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["OPENAI_API_KEY"]
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.vector_embedding_lambda,
    aws_iam_role_policy_attachment.vector_embedding_lambda_basic_execution,
    aws_iam_role_policy_attachment.vector_embedding_lambda_secrets_access,
    aws_iam_role_policy_attachment.vector_embedding_lambda_s3_access
  ]

  tags = {
    Name        = "c20-quadcast-vector-embedding"
    Project     = "QuadCast"
    Environment = "dev"
  }
}