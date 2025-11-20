# S3 Bucket for Athena Query Results
resource "aws_s3_bucket" "athena_results" {
  bucket = "c20-quadcast-athena-results"

  tags = {
    Name        = "c20-quadcast-athena-results"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# S3 Bucket Lifecycle Configuration for Athena Results
resource "aws_s3_bucket_lifecycle_configuration" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id

  rule {
    id     = "delete-old-query-results"
    status = "Enabled"

    expiration {
      days = 7
    }
  }
}

# Athena Workgroup
resource "aws_athena_workgroup" "quadcast" {
  name        = "c20-quadcast-workgroup"
  description = "Workgroup for QuadCast transcript queries"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.bucket}/query-results/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }

    engine_version {
      selected_engine_version = "AUTO"
    }
  }

  tags = {
    Name        = "c20-quadcast-athena-workgroup"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# CloudWatch Log Group for Athena Queries
resource "aws_cloudwatch_log_group" "athena" {
  name              = "/aws/athena/c20-quadcast"
  retention_in_days = 7

  tags = {
    Name        = "c20-quadcast-athena-logs"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# IAM Role for Athena
resource "aws_iam_role" "athena" {
  name = "c20-quadcast-athena-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "athena.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "c20-quadcast-athena-role"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# IAM Policy for Athena S3 Access
resource "aws_iam_role_policy" "athena_s3_access" {
  name = "c20-quadcast-athena-s3-access"
  role = aws_iam_role.athena.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.quadcast_data.arn,
          "${aws_s3_bucket.quadcast_data.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.athena_results.arn,
          "${aws_s3_bucket.athena_results.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetTable",
          "glue:GetPartitions",
          "glue:GetTables"
        ]
        Resource = [
          "arn:aws:glue:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:catalog",
          "arn:aws:glue:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:database/${aws_glue_catalog_database.quadcast.name}",
          "arn:aws:glue:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:table/${aws_glue_catalog_database.quadcast.name}/*"
        ]
      }
    ]
  })
}

