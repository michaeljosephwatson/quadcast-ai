variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
  default = ""
}

# Data sources for account and region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}