docker build --platform linux/amd64 --no-cache -t c20-quadcast-streamlit-ecr:latest ../

aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 129033205317.dkr.ecr.eu-west-2.amazonaws.com

docker tag c20-quadcast-streamlit-ecr:latest 129033205317.dkr.ecr.eu-west-2.amazonaws.com/c20-quadcast-streamlit-ecr:latest

docker push 129033205317.dkr.ecr.eu-west-2.amazonaws.com/c20-quadcast-streamlit-ecr:latest
