resource "aws_ecr_repository" "vector_embedding" {
  name = "c20-quadcast-vector_embedding-ecr"

  tags = {
    Name    = "c20-quadcast-vector_embedding-ecr"
    Project = "QuadCast"
    Environment = "dev"
  }
}
