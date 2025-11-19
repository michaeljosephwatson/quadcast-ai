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







