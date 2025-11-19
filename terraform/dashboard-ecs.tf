resource "aws_ecs_cluster" "main" {
  name = "c20-quadcast-cluster"

  tags = {
    Name = "c20-quadcast-cluster"
    Project = "QuadCast"
    Environment = "dev"
  }
}

data "aws_ecr_image" "streamlit" {
  repository_name = aws_ecr_repository.streamlit.name
  image_tag       = "latest"
}

resource "aws_iam_role" "ecs_task_execution_role" {
  name = "c20-quadcast-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name    = "c20-quadcast-ecs-task-execution-role"
    Project = "QuadCast"
    Environment = "dev"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_task_execution_secrets_policy" {
  name = "c20-quadcast-ecs-execution-secrets-policy"
  role = aws_iam_role.ecs_task_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.quadcast_secrets.arn
      }
    ]
  })
}

resource "aws_iam_role" "ecs_task_role" {
  name = "c20-quadcast-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name    = "c20-quadcast-ecs-task-role"
    Project = "QuadCast"
    Environment = "dev"
  }
}

resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "c20-quadcast-ecs-task-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SecretsManagerAccess"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.quadcast_secrets.arn
      },
      {
        Sid    = "AthenaAccess"
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:StopQueryExecution",
          "athena:GetWorkGroup",
          "athena:BatchGetQueryExecution"
        ]
        Resource = "*" # TO DO: Specify resource after setting up Athena and Glue
      },
      {
        Sid    = "GlueAccess"
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartition",
          "glue:GetPartitions",
          "glue:BatchGetPartition"
        ]
        Resource = "*" # TO DO: Specify resource after setting up Athena and Glue
      },
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:GetBucketLocation",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.quadcast_data.arn,          
          "${aws_s3_bucket.quadcast_data.arn}/*" 
        ]
      }
    ]
  })
}


