# S3 Bucket for QuadCast
resource "aws_s3_bucket" "quadcast_data" {
  bucket = "c20-quadcast-data-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name        = "c20-quadcast-data"
    Project     = "QuadCast"
    Environment = "dev"
  }
}


# Enable versioning for data protection
resource "aws_s3_bucket_versioning" "quadcast_data" {
  bucket = aws_s3_bucket.quadcast_data.id

  versioning_configuration {
    status = "Enabled"
  }
}


# IAM role for Lambda to access S3
resource "aws_iam_role" "lambda_s3_role" {
  name = "c20-quadcast-lambda-s3-role"

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
    Name        = "c20-quadcast-lambda-s3-role"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# IAM policy for Lambda to read/write S3 objects
resource "aws_iam_role_policy" "lambda_s3_policy" {
  name = "c20-quadcast-lambda-s3-policy"
  role = aws_iam_role.lambda_s3_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
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

# Data source to get current AWS account ID
data "aws_caller_identity" "current" {}
