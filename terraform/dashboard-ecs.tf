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
        Resource = "*"
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
        Resource = "*"
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
        Resource = "*"
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "streamlit" {
  name              = "/ecs/c20-quadcast-streamlit"
  retention_in_days = 7

  tags = {
    Name    = "c20-quadcast-streamlit-logs"
    Project = "QuadCast"
  }
}

resource "aws_security_group" "ecs_tasks" {
  name        = "c20-quadcast-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = data.aws_vpc.c20.id

  ingress {
    description = "Streamlit port"
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "c20-quadcast-ecs-tasks-sg"
    Project = "QuadCast"
    Environment = "dev"
  }
}

resource "aws_security_group_rule" "rds_from_ecs" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.ecs_tasks.id
  security_group_id        = aws_security_group.quadcast_rds.id
  description              = "Allow ECS tasks to connect to RDS"
}

resource "aws_ecs_task_definition" "streamlit" {
  family                   = "c20-quadcast-streamlit"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "streamlit"
      image = "${aws_ecr_repository.streamlit.repository_url}@${data.aws_ecr_image.streamlit.image_digest}"

      portMappings = [
        {
          containerPort = 8501
          hostPort      = 8501
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "AWS_DEFAULT_REGION"
          value = "eu-west-2"
        }
      ]

      secrets = [
        {
          name      = "RDS_HOST"
          valueFrom = "${aws_secretsmanager_secret.quadcast_secrets.arn}:RDS_HOST::"
        },
        {
          name      = "RDS_PORT"
          valueFrom = "${aws_secretsmanager_secret.quadcast_secrets.arn}:RDS_PORT::"
        },
        {
          name      = "RDS_DB_NAME"
          valueFrom = "${aws_secretsmanager_secret.quadcast_secrets.arn}:RDS_DB_NAME::"
        },
        {
          name      = "RDS_USERNAME"
          valueFrom = "${aws_secretsmanager_secret.quadcast_secrets.arn}:RDS_USERNAME::"
        },
        {
          name      = "RDS_PASSWORD"
          valueFrom = "${aws_secretsmanager_secret.quadcast_secrets.arn}:RDS_PASSWORD::"
        },
        {
          name      = "OPENAI_API_KEY"
          valueFrom = "${aws_secretsmanager_secret.quadcast_secrets.arn}:OPENAI_API_KEY::"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.streamlit.name
          "awslogs-region"        = "eu-west-2"
          "awslogs-stream-prefix" = "ecs"
        }
      }

      essential = true
    }
  ])

  tags = {
    Name    = "c20-quadcast-streamlit-task"
    Project = "QuadCast"
    Environment = "dev"
  }
}

resource "aws_ecs_service" "streamlit" {
  name            = "c20-quadcast-streamlit-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.streamlit.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  force_new_deployment = true

  network_configuration {
    subnets          = data.aws_subnets.public.ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  tags = {
    Name    = "c20-quadcast-streamlit-service"
    Project = "QuadCast"
    Environment = "dev"
  }
}