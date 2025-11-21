# IAM Role for Lambda Execution
resource "aws_iam_role" "count_episodes_lambda" {
  name = "c20-quadcast-count-episodes-lambda-role"

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
    Name        = "c20-quadcast-count-episodes-lambda-role"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# IAM Policy for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "count_episodes_lambda_basic_execution" {
  role       = aws_iam_role.count_episodes_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# IAM Policy for Secrets Manager Access
resource "aws_iam_role_policy_attachment" "count_episodes_lambda_secrets_access" {
  role       = aws_iam_role.count_episodes_lambda.name
  policy_arn = aws_iam_policy.lambda_secrets_access.arn
}

# IAM Policy for ECR Image Pull
resource "aws_iam_role_policy" "count_episodes_lambda_ecr_access" {
  name = "c20-quadcast-count-episodes-lambda-ecr-access"
  role = aws_iam_role.count_episodes_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability"
        ]
        Resource = aws_ecr_repository.count_episodes_ecr.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "count_episodes_lambda" {
  name              = "/aws/lambda/c20-quadcast-count-episodes"
  retention_in_days = 7

  tags = {
    Name        = "c20-quadcast-count-episodes-logs"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# Lambda Function
resource "aws_lambda_function" "count_episodes" {
  function_name = "c20-quadcast-count-episodes"
  role          = aws_iam_role.count_episodes_lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.count_episodes_ecr.repository_url}:latest"

  timeout     = 60
  memory_size = 256

  environment {
    variables = {
      USE_SECRETS_MANAGER = "false"
      RDS_HOST            = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_HOST"]
      RDS_DB_NAME         = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_DB_NAME"]
      RDS_USERNAME        = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_USERNAME"]
      RDS_PASSWORD        = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_PASSWORD"]
      RDS_PORT            = jsondecode(data.aws_secretsmanager_secret_version.quadcast_secrets.secret_string)["RDS_PORT"]
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.count_episodes_lambda,
    aws_iam_role_policy_attachment.count_episodes_lambda_basic_execution,
    aws_iam_role_policy_attachment.count_episodes_lambda_secrets_access
  ]

  tags = {
    Name        = "c20-quadcast-count-episodes"
    Project     = "QuadCast"
    Environment = "dev"
  }
}
