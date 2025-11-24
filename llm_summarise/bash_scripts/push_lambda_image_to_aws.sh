aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 129033205317.dkr.ecr.eu-west-2.amazonaws.com

docker tag c20-quadcast-analysis-ecr:latest 129033205317.dkr.ecr.eu-west-2.amazonaws.com/c20-quadcast-analysis-ecr:latest

docker push 129033205317.dkr.ecr.eu-west-2.amazonaws.com/c20-quadcast-analysis-ecr:latest
