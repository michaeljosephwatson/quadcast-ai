# Glue Database for QuadCast
resource "aws_glue_catalog_database" "quadcast" {
  name        = "c20_quadcast_db"
  description = "Glue catalog database for QuadCast transcripts"

  tags = {
    Name        = "c20-quadcast-glue-database"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# IAM Role for Glue Crawler
resource "aws_iam_role" "glue_crawler" {
  name = "c20-quadcast-glue-crawler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "c20-quadcast-glue-crawler-role"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# Attach AWS Managed Policy for Glue Service
resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_crawler.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# Custom Policy for S3 Access
resource "aws_iam_role_policy" "glue_s3_access" {
  name = "c20-quadcast-glue-s3-access"
  role = aws_iam_role.glue_crawler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.quadcast_data.arn,
          "${aws_s3_bucket.quadcast_data.arn}/*"
        ]
      }
    ]
  })
}

# CloudWatch Log Group for Glue Crawler
resource "aws_cloudwatch_log_group" "glue_crawler" {
  name              = "/aws/glue/crawler/c20-quadcast-transcripts"
  retention_in_days = 7

  tags = {
    Name        = "c20-quadcast-glue-crawler-logs"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# Glue Crawler for Transcripts
resource "aws_glue_crawler" "quadcast_transcripts" {
  name          = "c20-quadcast-transcripts-crawler"
  database_name = aws_glue_catalog_database.quadcast.name
  role          = aws_iam_role.glue_crawler.arn
  description   = "Crawler for QuadCast podcast transcripts in S3"

  s3_target {
    path = "s3://${aws_s3_bucket.quadcast_data.bucket}/transcripts/"
  }

  s3_target {
    path = "s3://${aws_s3_bucket.quadcast_data.bucket}/segments/"
  }

  s3_target {
    path = "s3://${aws_s3_bucket.quadcast_data.bucket}/summaries/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
  })

  tags = {
    Name        = "c20-quadcast-transcripts-crawler"
    Project     = "QuadCast"
    Environment = "dev"
  }

  depends_on = [
    aws_iam_role_policy_attachment.glue_service,
    aws_iam_role_policy.glue_s3_access
  ]
}

# EventBridge Rule to trigger Glue Crawler daily
resource "aws_cloudwatch_event_rule" "glue_crawler_schedule" {
  name                = "c20-quadcast-glue-crawler-schedule"
  description         = "Trigger Glue crawler daily to update catalog"
  schedule_expression = "cron(0 2 * * ? *)" # Run at 2 AM UTC daily

  tags = {
    Name        = "c20-quadcast-glue-crawler-schedule"
    Project     = "QuadCast"
    Environment = "dev"
  }
}
