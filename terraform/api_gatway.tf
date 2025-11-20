# REST API Gateway
resource "aws_api_gateway_rest_api" "quadcast_api" {
  name        = "c20-quadcast-api-gateway"
  description = "API Gateway for QuadCast application"

  tags = {
    Name        = "c20-quadcast-api-gateway"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# /podcast resource
resource "aws_api_gateway_resource" "podcast" {
  rest_api_id = aws_api_gateway_rest_api.quadcast_api.id
  parent_id   = aws_api_gateway_rest_api.quadcast_api.root_resource_id
  path_part   = "podcast"
}

# POST method for /podcast
resource "aws_api_gateway_method" "add_podcast" {
  rest_api_id   = aws_api_gateway_rest_api.quadcast_api.id
  resource_id   = aws_api_gateway_resource.podcast.id
  http_method   = "POST"
  authorization = "NONE"
}

# Integration with Lambda
resource "aws_api_gateway_integration" "add_podcast_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.quadcast_api.id
  resource_id             = aws_api_gateway_resource.podcast.id
  http_method             = aws_api_gateway_method.add_podcast.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.add_podcast.invoke_arn
}

# Lambda permission to allow API Gateway to invoke
resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.add_podcast.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.quadcast_api.execution_arn}/*/*"
}

# Deployment
resource "aws_api_gateway_deployment" "quadcast_api" {
  rest_api_id = aws_api_gateway_rest_api.quadcast_api.id

  depends_on = [
    aws_api_gateway_integration.add_podcast_lambda
  ]

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.podcast.id,
      aws_api_gateway_method.add_podcast.id,
      aws_api_gateway_integration.add_podcast_lambda.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Stage
resource "aws_api_gateway_stage" "dev" {
  deployment_id = aws_api_gateway_deployment.quadcast_api.id
  rest_api_id   = aws_api_gateway_rest_api.quadcast_api.id
  stage_name    = "dev"

  tags = {
    Name        = "c20-quadcast-api-gateway-dev"
    Project     = "QuadCast"
    Environment = "dev"
  }
}
