terraform {
  backend "s3" {
    bucket         = "c20-quadcast-terraform-state"
    key            = "terraform.tfstate"
    region         = "eu-west-2"
    dynamodb_table = "c20-quadcast-terraform-locks"
  }
}