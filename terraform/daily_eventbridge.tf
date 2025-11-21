# IAM Role for EventBridge to invoke Step Function
resource "aws_iam_role" "eventbridge_step_function_role" {
  name = "c20-quadcast-episode-transcription-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "c20-quadcast-episode-transcription-eventbridge-role"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# IAM Policy for EventBridge to execute Step Function
resource "aws_iam_role_policy" "eventbridge_step_function_policy" {
  name = "c20-quadcast-episode-transcription-eventbridge-policy"
  role = aws_iam_role.eventbridge_step_function_role.id

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
}

# EventBridge Rule to trigger Step Function on schedule
resource "aws_cloudwatch_event_rule" "episode_transcription_schedule" {
  name                = "c20-quadcast-episode-transcription-schedule"
  description         = "Trigger episode transcription Step Function on schedule"
  schedule_expression = "cron(0 0 * * ? *)" #Runs every day at midnight

  tags = {
    Name        = "c20-quadcast-episode-transcription-schedule"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# EventBridge Target to invoke Step Function
resource "aws_cloudwatch_event_target" "episode_transcription_step_function" {
  rule      = aws_cloudwatch_event_rule.episode_transcription_schedule.name
  target_id = "EpisodeTranscriptionStepFunction"
  arn       = aws_sfn_state_machine.episode_transcription_workflow.arn
  role_arn  = aws_iam_role.eventbridge_step_function_role.arn
}
