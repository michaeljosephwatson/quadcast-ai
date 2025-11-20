# IAM Role for Step Function Execution
resource "aws_iam_role" "step_function_role" {
  name = "c20-quadcast-episode-transcription-step-function-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "c20-quadcast-episode-transcription-step-function-role"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# IAM Policy to allow Step Function to invoke Lambda
resource "aws_iam_role_policy" "step_function_lambda_policy" {
  name = "c20-quadcast-episode-transcription-step-function-lambda-policy"
  role = aws_iam_role.step_function_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.daily_pipeline.arn
      }
    ]
  })
}

# Step Function Definition
resource "aws_sfn_state_machine" "episode_transcription_workflow" {
  name       = "c20-quadcast-episode-transcription-workflow"
  role_arn   = aws_iam_role.step_function_role.arn
  definition = jsonencode({
    Comment = "Episode transcription workflow triggered after daily pipeline"
    StartAt = "RunDailyPipeline"
    States = {
      RunDailyPipeline = {
        Type     = "Task"
        Resource = aws_lambda_function.daily_pipeline.arn
        End      = true
      }
    }
  })

  tags = {
    Name        = "c20-quadcast-episode-transcription-workflow"
    Project     = "QuadCast"
    Environment = "dev"
  }
}
