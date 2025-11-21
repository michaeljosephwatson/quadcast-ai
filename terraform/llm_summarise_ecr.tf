# ECR Repository for OpenAI Analysis Lambda
resource "aws_ecr_repository" "analysis_ecr" {
  name = "c20-quadcast-analysis-ecr"

  tags = {
    Name        = "c20-quadcast-analysis-ecr"
    Project     = "QuadCast"
    Environment = "dev"
  }
}