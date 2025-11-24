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
  image_uri     = "${aws_ecr_repository.vector_embedding_ecr.repository_url}:latest"

  timeout     = 900
  memory_size = 10240

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda_sg.id]
  }

  environment {
    variables = {
      DB_HOST         = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_HOST"]
      DB_NAME         = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_DB_NAME"]
      DB_USER         = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_USERNAME"]
      DB_PASSWORD     = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_PASSWORD"]
      DB_PORT         = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_PORT"]
      S3_BUCKET       = "c20-quadcast-s3-bucket"
      AWS_REGION      = "eu-west-2"
      OPENAI_API_KEY  = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["OPENAI_API_KEY"]
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.vector_embedding_lambda,
    aws_iam_role_policy_attachment.vector_embedding_lambda_vpc_execution,
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

# ECR Repository for Vector Embedding Lambda
resource "aws_ecr_repository" "vector_embedding_ecr" {
  name                 = "c20-quadcast-vector-embedding"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = false
  }

  tags = {
    Name        = "c20-quadcast-vector-embedding-ecr"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# CloudWatch Event Rule to trigger Vector Embedding Lambda
resource "aws_cloudwatch_event_rule" "vector_embedding_trigger" {
  name                = "c20-quadcast-vector-embedding-trigger"
  description         = "Trigger vector embedding lambda every 5 minutes"
  schedule_expression = "rate(5 minutes)"

  tags = {
    Name        = "c20-quadcast-vector-embedding-trigger"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# CloudWatch Event Target
resource "aws_cloudwatch_event_target" "vector_embedding_lambda" {
  rule      = aws_cloudwatch_event_rule.vector_embedding_trigger.name
  target_id = "VectorEmbeddingLambda"
  arn       = aws_lambda_function.vector_embedding.arn
}

# Lambda Permission for CloudWatch Events
resource "aws_lambda_permission" "allow_cloudwatch_vector_embedding" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.vector_embedding.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.vector_embedding_trigger.arn
}
