FROM public.ecr.aws/lambda/python:3.13

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt

COPY extract_episodes.py ${LAMBDA_TASK_ROOT}
COPY transform_episodes.py ${LAMBDA_TASK_ROOT}
COPY load_episodes.py ${LAMBDA_TASK_ROOT}
COPY handler.py ${LAMBDA_TASK_ROOT}

CMD ["handler.lambda_handler"]