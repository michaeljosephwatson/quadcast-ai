# S3 Bucket for QuadCast
resource "aws_s3_bucket" "quadcast_data" {
  bucket = "c20-quadcast-s3-bucket"

  tags = {
    Name        = "c20-quadcast-s3-bucket"
    Project     = "QuadCast"
    Environment = "dev"
  }
}