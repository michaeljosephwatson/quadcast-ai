resource "aws_ecr_repository" "streamlit" {
  name = "c20-quadcast-streamlit-ecr"

  tags = {
    Name    = "c20-quadcast-streamlit-ecr"
    Project = "QuadCast"
    Environment = "dev"
  }
}
