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
    aws_api_gateway_integration.add_podcast_lambda,
    aws_api_gateway_integration.trigger_workflow
  ]

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.podcast.id,
      aws_api_gateway_method.add_podcast.id,
      aws_api_gateway_integration.add_podcast_lambda.id,
      aws_api_gateway_resource.workflow.id,
      aws_api_gateway_method.trigger_workflow.id,
      aws_api_gateway_integration.trigger_workflow.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/c20-quadcast-api"
  retention_in_days = 7

  tags = {
    Name        = "c20-quadcast-api-gateway-logs"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# IAM Role for API Gateway CloudWatch Logging
resource "aws_iam_role" "api_gateway_cloudwatch" {
  name = "c20-quadcast-api-gateway-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "c20-quadcast-api-gateway-cloudwatch-role"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# Attach CloudWatch Logs policy to the role
resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch" {
  role       = aws_iam_role.api_gateway_cloudwatch.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

# API Gateway Account settings for CloudWatch
resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch.arn
}

# Stage
resource "aws_api_gateway_stage" "dev" {
  deployment_id = aws_api_gateway_deployment.quadcast_api.id
  rest_api_id   = aws_api_gateway_rest_api.quadcast_api.id
  stage_name    = "dev"

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      caller         = "$context.identity.caller"
      user           = "$context.identity.user"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  xray_tracing_enabled = true

  tags = {
    Name        = "c20-quadcast-api-gateway-dev"
    Project     = "QuadCast"
    Environment = "dev"
  }

  depends_on = [aws_api_gateway_account.main]
}

# /workflow resource
resource "aws_api_gateway_resource" "workflow" {
  rest_api_id = aws_api_gateway_rest_api.quadcast_api.id
  parent_id   = aws_api_gateway_rest_api.quadcast_api.root_resource_id
  path_part   = "workflow"
}

# POST method for /workflow to trigger Step Function
resource "aws_api_gateway_method" "trigger_workflow" {
  rest_api_id   = aws_api_gateway_rest_api.quadcast_api.id
  resource_id   = aws_api_gateway_resource.workflow.id
  http_method   = "POST"
  authorization = "NONE"
}

# IAM Role for API Gateway to invoke Step Functions
resource "aws_iam_role" "api_gateway_stepfunctions" {
  name = "c20-quadcast-api-gateway-stepfunctions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "c20-quadcast-api-gateway-stepfunctions-role"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

# IAM Policy for API Gateway to invoke Step Functions
resource "aws_iam_role_policy" "api_gateway_stepfunctions_policy" {
  name = "c20-quadcast-api-gateway-stepfunctions-policy"
  role = aws_iam_role.api_gateway_stepfunctions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "states:StartExecution"
        ]
        Resource = [
          aws_sfn_state_machine.episode_transcription_workflow.arn
        ]
      }
    ]
  })
}

# Integration with Step Functions
resource "aws_api_gateway_integration" "trigger_workflow" {
  rest_api_id             = aws_api_gateway_rest_api.quadcast_api.id
  resource_id             = aws_api_gateway_resource.workflow.id
  http_method             = aws_api_gateway_method.trigger_workflow.http_method
  integration_http_method = "POST"
  type                    = "AWS"
  uri                     = "arn:aws:apigateway:eu-west-2:states:action/StartExecution"
  credentials             = aws_iam_role.api_gateway_stepfunctions.arn

  request_templates = {
    "application/json" = jsonencode({
      stateMachineArn = aws_sfn_state_machine.episode_transcription_workflow.arn
      input           = "{}"
    })
  }
}

# Integration Response
resource "aws_api_gateway_integration_response" "trigger_workflow" {
  rest_api_id       = aws_api_gateway_rest_api.quadcast_api.id
  resource_id       = aws_api_gateway_resource.workflow.id
  http_method       = aws_api_gateway_method.trigger_workflow.http_method
  status_code       = "200"
  depends_on        = [aws_api_gateway_integration.trigger_workflow]

  response_templates = {
    "application/json" = <<-EOT
{
  "status": "success",
  "message": "Step Function workflow triggered"
}
EOT
  }
}

# Method Response
resource "aws_api_gateway_method_response" "trigger_workflow" {
  rest_api_id = aws_api_gateway_rest_api.quadcast_api.id
  resource_id = aws_api_gateway_resource.workflow.id
  http_method = aws_api_gateway_method.trigger_workflow.http_method
  status_code = "200"
}

# Method Settings for detailed CloudWatch metrics and logging
resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.quadcast_api.id
  stage_name  = aws_api_gateway_stage.dev.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled    = true
    logging_level      = "INFO"
    data_trace_enabled = true
  }
}
