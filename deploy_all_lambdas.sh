#!/bin/bash

# Script to deploy all Lambda functions
set -e

echo "======================================"
echo "Deploying All Lambda Functions"
echo "======================================"
echo ""

# Array of Lambda directories with bash_scripts
LAMBDA_DIRS=(
  "add_podcast"
  "count_episodes"
  "daily_pipeline"
  "llm_summarise"
  "transcribe_pipeline"
  "vector_embedding"
)

# Track success/failure
SUCCESSFUL=()
FAILED=()

# Deploy each Lambda
for LAMBDA_DIR in "${LAMBDA_DIRS[@]}"; do
  echo "--------------------------------------"
  echo "Deploying: $LAMBDA_DIR"
  echo "--------------------------------------"

  SCRIPT_PATH="$LAMBDA_DIR/bash_scripts/update_lambda_on_aws.sh"

  if [ -f "$SCRIPT_PATH" ]; then
    # Change to the bash_scripts directory and run the script
    cd "$LAMBDA_DIR/bash_scripts"

    if ./update_lambda_on_aws.sh; then
      echo "✓ $LAMBDA_DIR deployed successfully"
      SUCCESSFUL+=("$LAMBDA_DIR")
    else
      echo "✗ $LAMBDA_DIR deployment failed"
      FAILED+=("$LAMBDA_DIR")
    fi

    # Return to project root
    cd ../..
  else
    echo "✗ Script not found: $SCRIPT_PATH"
    FAILED+=("$LAMBDA_DIR")
  fi

  echo ""
done

# Deploy Dashboard
echo "--------------------------------------"
echo "Deploying: Dashboard (Streamlit on ECS)"
echo "--------------------------------------"

DASHBOARD_ECR_SCRIPT="dashboard/bash_scripts/upload_image_to_ecr.sh"
DASHBOARD_ECS_SCRIPT="dashboard/bash_scripts/update_ecs_service.sh"

if [ -f "$DASHBOARD_ECR_SCRIPT" ] && [ -f "$DASHBOARD_ECS_SCRIPT" ]; then
  # Build and push to ECR
  if bash "$DASHBOARD_ECR_SCRIPT"; then
    echo "✓ Dashboard image pushed to ECR successfully"

    # Update ECS service
    if bash "$DASHBOARD_ECS_SCRIPT"; then
      echo "✓ Dashboard ECS service updated successfully"
      SUCCESSFUL+=("Dashboard")
    else
      echo "✗ Dashboard ECS service update failed"
      FAILED+=("Dashboard")
    fi
  else
    echo "✗ Dashboard ECR upload failed"
    FAILED+=("Dashboard")
  fi
else
  echo "✗ Dashboard scripts not found"
  [ ! -f "$DASHBOARD_ECR_SCRIPT" ] && echo "  Missing: $DASHBOARD_ECR_SCRIPT"
  [ ! -f "$DASHBOARD_ECS_SCRIPT" ] && echo "  Missing: $DASHBOARD_ECS_SCRIPT"
  FAILED+=("Dashboard")
fi

echo ""

# Summary
echo "======================================"
echo "Deployment Summary"
echo "======================================"
echo "Successful (${#SUCCESSFUL[@]}): ${SUCCESSFUL[*]}"
echo "Failed (${#FAILED[@]}): ${FAILED[*]}"
echo ""

if [ ${#FAILED[@]} -eq 0 ]; then
  echo "✓ All deployments (Lambdas + Dashboard) completed successfully!"
  exit 0
else
  echo "✗ Some deployments failed"
  exit 1
fi
