set -e
./create_lambda_image.sh
./push_lambda_image_to_aws.sh
aws lambda update-function-code --function-name c20-quadcast-analysis --image-uri 129033205317.dkr.ecr.eu-west-2.amazonaws.com/c20-quadcast-analysis-ecr:latest
