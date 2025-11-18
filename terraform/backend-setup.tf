resource "aws_s3_bucket" "terraform_state" {
  bucket = "c20-quadcast-terraform-state"

  lifecycle {
    ignore_changes = all
  }
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "c20-quadcast-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  lifecycle {
    ignore_changes = all
  }
}