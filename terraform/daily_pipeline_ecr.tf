resource "aws_ecr_repository" "daily_pipeline_ecr" {
  name = "c20-quadcast-daily-pipeline-ecr"

  tags = {
    Name    = "c20-quadcast-daily-pipeline-ecr"
    Project = "QuadCast"
    Environment = "dev"
  }
}
