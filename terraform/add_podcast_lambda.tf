# Data source to fetch secrets
data "aws_secretsmanager_secret_version" "quadcast_secrets" {
  secret_id = aws_secretsmanager_secret.quadcast_secrets.id
}

# Security Group for Add Podcast Lambda
resource "aws_security_group" "add_podcast_lambda" {
  name        = "c20-quadcast-add-podcast-lambda-sg"
  description = "Security group for Add Podcast Lambda function"
  vpc_id      = data.aws_vpc.c20.id

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "c20-quadcast-add-podcast-lambda-sg"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# Allow Lambda to access RDS
resource "aws_security_group_rule" "lambda_to_rds" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.add_podcast_lambda.id
  security_group_id        = aws_security_group.quadcast_rds.id
  description              = "Allow Lambda to access RDS"
}

# IAM Role for Lambda Execution
resource "aws_iam_role" "add_podcast_lambda" {
  name = "c20-quadcast-add-podcast-lambda-role"

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
    Name        = "c20-quadcast-add-podcast-lambda-role"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# IAM Policy for VPC Access
resource "aws_iam_role_policy_attachment" "lambda_vpc_execution" {
  role       = aws_iam_role.add_podcast_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# IAM Policy for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.add_podcast_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# IAM Policy for Secrets Manager Access
resource "aws_iam_policy" "lambda_secrets_access" {
  name        = "c20-quadcast-lambda-secrets-access"
  description = "Allow Lambda to read QuadCast secrets from Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = aws_secretsmanager_secret.quadcast_secrets.arn
      }
    ]
  })

  tags = {
    Name        = "c20-quadcast-lambda-secrets-access"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_secrets_access" {
  role       = aws_iam_role.add_podcast_lambda.name
  policy_arn = aws_iam_policy.lambda_secrets_access.arn
}


# IAM Policy for Step Function Invocation
resource "aws_iam_policy" "lambda_stepfunctions_execution" {
  name        = "c20-quadcast-lambda-stepfunctions-execution"
  description = "Allow Lambda to invoke the episode transcription Step Function"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "states:StartExecution"
        ]
        Resource = aws_sfn_state_machine.episode_transcription_workflow.arn
      }
    ]
  })

  tags = {
    Name        = "c20-quadcast-lambda-stepfunctions-execution"
    Project     = "QuadCast"
    Environment = "dev"
  }
}


resource "aws_iam_role_policy_attachment" "lambda_stepfunctions_execution" {
  role       = aws_iam_role.add_podcast_lambda.name
  policy_arn = aws_iam_policy.lambda_stepfunctions_execution.arn
}


# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "add_podcast_lambda" {
  name              = "/aws/lambda/c20-quadcast-add-podcast"
  retention_in_days = 7

  tags = {
    Name        = "c20-quadcast-add-podcast-logs"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# Lambda Function
resource "aws_lambda_function" "add_podcast" {
  function_name = "c20-quadcast-add-podcast"
  role          = aws_iam_role.add_podcast_lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.add_podcast_ecr.repository_url}:latest"

  timeout     = 500
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
    aws_cloudwatch_log_group.add_podcast_lambda,
    aws_iam_role_policy_attachment.lambda_vpc_execution,
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy_attachment.lambda_secrets_access,
    aws_iam_role_policy_attachment.lambda_stepfunctions_execution  # ADD THIS LINE
  ]

  tags = {
    Name        = "c20-quadcast-add-podcast"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

