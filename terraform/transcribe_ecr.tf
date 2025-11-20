resource "aws_ecr_repository" "transcribe_ecr" {
  name = "c20-quadcast-transcribe-ecr"

  tags = {
    Name        = "c20-quadcast-transcribe-ecr"
    Project     = "QuadCast"
    Environment = "dev"
  }
}