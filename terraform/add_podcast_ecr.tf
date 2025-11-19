resource "aws_ecr_repository" "add_podcast_ecr" {
  name = "c20-quadcast-add-podcast-ecr"

  tags = {
    Name    = "c20-quadcast-add-podcast-ecr"
    Project = "QuadCast"
    Environment = "dev"
  }
}
