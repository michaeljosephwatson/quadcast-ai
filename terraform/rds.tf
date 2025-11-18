data "aws_vpc" "c20" {
  filter {
    name   = "tag:Name"
    values = ["c20-VPC"]
  }
}

data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.c20.id]
  }

  # Filter for subnets with "public" in the name
  filter {
    name   = "tag:Name"
    values = ["*public*"]
  }
}

resource "aws_db_subnet_group" "quadcast_rds" {
  name       = "c20-quadcast-rds-subnet-group"
  subnet_ids = data.aws_subnets.public.ids

  tags = {
    Name        = "c20-quadcast-rds-subnet-group"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

resource "aws_security_group" "quadcast_rds" {
  name        = "c20-quadcast-rds-sg"
  description = "Security group for QuadCast PostgreSQL RDS"
  vpc_id      = data.aws_vpc.c20.id

  ingress {
    description = "PostgreSQL from anywhere"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "c20-quadcast-rds-sg"
    Project     = "QuadCast"
    Environment = "dev"
  }
}

resource "aws_db_instance" "postgres" {
  identifier        = "c20-quadcast-rds"
  engine            = "postgres"
  engine_version    = "17.6"
  instance_class    = "db.t3.micro"
  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = "quadcast_db"
  username = "quadcast_admin"
  password = random_password.rds_password.result

  db_subnet_group_name   = aws_db_subnet_group.quadcast_rds.name
  vpc_security_group_ids = [aws_security_group.quadcast_rds.id]
  publicly_accessible    = true

  backup_retention_period = 7

  skip_final_snapshot       = false
  final_snapshot_identifier = "c20-quadcast-rds-final-snapshot"

  auto_minor_version_upgrade      = true
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  tags = {
    Name        = "c20-quadcast-rds"
    Project     = "QuadCast"
    Environment = "dev"
  }
}