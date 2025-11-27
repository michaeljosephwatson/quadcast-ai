# Terraform Infrastructure

Infrastructure-as-Code (IaC) configuration for deploying the entire podcast platform on AWS.

## Purpose

Defines and deploys all AWS resources needed for the platform:
- Lambda functions for each pipeline (add_podcast, daily_pipeline, transcribe, summarize, embeddings)
- Container registries (ECR) for Docker images
- S3 buckets for data storage
- RDS PostgreSQL database
- Athena for SQL queries on S3 data
- IAM roles and permissions
- State management backend

Enables reproducible, version-controlled infrastructure deployment.

## How It Works

Terraform files declare each AWS resource. Run `terraform apply` to create/update all infrastructure in one command.

Each resource is modular, allowing selective deployment or updates.

## Setup

### Prerequisites

- Terraform 1.0+ installed locally
- AWS CLI configured with credentials
- AWS account with appropriate permissions

### Quick Start

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform (downloads AWS provider)
terraform init

# Plan changes (see what will be created)
terraform plan

# Apply changes (create resources)
terraform apply

# Destroy resources (cleanup)
terraform destroy
```

## Key Files & Resources

### Infrastructure

- **`s3.tf`**: S3 bucket for transcripts, audio, and analysis
  - Bucket: `c20-quadcast-s3-bucket`
  - Versioning and encryption enabled
  - Object storage structure for podcast data

- **`count_episodes_lambda.tf`**: Count Episodes Lambda
  - Runtime: Python 3.11
  - Timeout: 60 seconds
  - Monitors untranscribed episodes

- **`vector_embedding_ecr.tf`**: ECR container registries
  - Image repositories for services
  - Image scanning enabled for security

- **`athena.tf`**: Athena SQL query service
  - Query transcripts and data in S3
  - Results stored back to S3

- **`backend-setup.tf`**: Terraform state management
  - S3 backend for storing state
  - DynamoDB locking for team safety
  - Consistent state across CI/CD

- **`outputs.tf`**: Output values
  - Lambda ARNs
  - S3 bucket names
  - RDS endpoint
  - Database host/port

## Lambda Functions

Each Lambda deployed with:
- Runtime: Python 3.11
- Handler: `handler.lambda_handler`
- Memory: 512 MB (typical)
- Timeout: 900 seconds (varies)
- Environment variables: Per-function config
- IAM role with minimal required permissions

Lambdas:
- `add_podcast`: Add podcasts via RSS API
- `daily_pipeline`: Daily episode ingestion from feeds
- `transcribe`: Audio transcription pipeline
- `llm_summarise`: Extract topics and speakers
- `vector_embedding`: Generate semantic embeddings
- `count_episodes`: Monitor untranscribed backlog

## RDS Database

PostgreSQL configuration:
- Engine: PostgreSQL 13+
- Instance: db.t3.micro (dev) to larger (prod)
- Storage: 20+ GB with backups
- Multi-AZ: Recommended for production
- Schema: Run `db_schema/schema.sql` after creation
- Backup retention: 7+ days

## S3 Data Structure

```
c20-quadcast-s3-bucket/
├── {podcast_name}{id}/
│   └── {episode_title}{id}/
│       ├── transcript.txt (from transcribe)
│       ├── diarized_segments.txt (speakers)
│       ├── analysis.json (topics/speakers)
│       └── embeddings.json (vector data)
└── athena-results/ (Athena query output)
```

## Environment Variables

Set per-Lambda in Terraform:

```hcl
environment = {
  RDS_HOST        = aws_db_instance.postgres.endpoint
  RDS_DB_NAME     = "quadcast"
  RDS_USERNAME    = "admin"
  RDS_PASSWORD    = data.aws_secretsmanager_secret_version.db.secret_string
  AWS_REGION      = "eu-west-2"
  OPENAI_API_KEY  = data.aws_secretsmanager_secret_version.openai.secret_string
}
```

## Deployment Workflow

### Manual Deployment

```bash
# Review plan
terraform plan

# Apply
terraform apply

# Verify
terraform show

# Get outputs
terraform output
```

### CI/CD Integration

Can automate with GitHub Actions, GitLab CI, etc:

```yaml
# Example GitHub Actions
- name: Terraform Plan
  run: terraform plan -out=tfplan

- name: Terraform Apply
  run: terraform apply tfplan
```

## State Management

### Local State (Development)

```
terraform.tfstate  # Stores resource state locally
```

Pros: Simple
Cons: Not team-friendly, risky with multiple users

### Remote State (Recommended)

```bash
# backend-setup.tf enables S3 + DynamoDB backend
terraform init  # Migrates state to S3
```

Pros: Team-safe, CI/CD friendly, state locking
Cons: Slight AWS cost

## Costs

Typical monthly estimates:

- **Lambda**: $0.20 per 1M requests + compute
- **RDS**: $20-50/month (db.t3.micro)
- **S3**: $0.023 per GB stored
- **OpenAI API**: $0.01-0.10 per 1K tokens
- **Data Transfer**: $0.09 per GB egress

**Total**: $50-500/month depending on usage

## Best Practices

1. **Use Remote State**: S3 + DynamoDB backend
2. **Plan First**: Always `terraform plan` before apply
3. **Use Workspaces**: Separate dev/staging/prod environments
4. **Tag Resources**: For cost tracking and organization
5. **Monitor Drift**: `terraform plan` regularly detects changes
6. **Backup State**: Regular S3 backups
7. **Secure Secrets**: Use AWS Secrets Manager, not hardcoded values

## Troubleshooting

### State Lock Stuck

```bash
# Force unlock (use caution)
terraform force-unlock <LOCK_ID>
```

### Drift Detected

```bash
# See what changed in AWS
terraform plan

# Update .tf files to match desired state
# Then reapply
terraform apply
```

### Lambda Timeout Issues

- Increase timeout in Lambda `.tf` file
- Check CloudWatch Logs for actual execution time
- May need to optimize function code

## Architecture Integration

Terraform resources power the entire pipeline:

```
User/Schedule
    ↓
add_podcast or daily_pipeline (Lambda)
    ↓
RDS Database (Terraform-managed)
    ↓
Transcription Workflow (Step Functions)
    ↓
transcribe_pipeline → llm_summarise → vector_embedding (Lambdas)
    ↓
S3 Storage (Terraform-managed) + RDS
    ↓
Dashboard (queries RDS)
```

## Security

- All credentials in AWS Secrets Manager (not hardcoded)
- RDS in private VPC subnet
- S3 encryption at rest enabled
- IAM roles follow least-privilege principle
- CloudWatch Logs for audit trail
- Resource tagging for compliance

## Scaling Considerations

- **More Concurrency**: Increase Lambda concurrency limits
- **Larger Database**: Change RDS instance class
- **More Storage**: Increase S3 lifecycle policies
- **Cost Optimization**: Use reserved capacity, spot instances

## Maintenance

```bash
# Regular checks
terraform plan  # Detect drift
terraform validate  # Syntax check
terraform fmt  # Format code

# Updates
terraform plan -target=aws_lambda_function.add_podcast
terraform apply -target=aws_lambda_function.add_podcast

# Full refresh
terraform refresh
```