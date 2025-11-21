resource "aws_ecr_repository" "count_episodes_ecr" {
  name = "c20-quadcast-count-episodes-ecr"

  tags = {
    Name        = "c20-quadcast-count-episodes-ecr"
    Project     = "QuadCast"
    Environment = "dev"
  }
}
