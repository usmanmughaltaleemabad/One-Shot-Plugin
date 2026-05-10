"""
Terraform Generator - Infrastructure as Code for multi-cloud deployment

Generates:
- Kubernetes cluster provisioning
- Cloud provider resources (AWS, GCP, Azure)
- Database provisioning (RDS, Cloud SQL, Azure Database)
- Networking (VPCs, subnets, load balancers)
- DNS and certificate management
- Auto-scaling groups
- Storage provisioning
"""

from typing import Dict, Any


class TerraformGenerator:
    """Generate Terraform infrastructure code"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_terraform_main(self, app_name: str = "app", provider: str = "aws") -> str:
        """Generate main Terraform configuration"""
        return f"""
terraform {{
  required_version = ">= 1.0"

  required_providers {{
    kubernetes = {{
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }}
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
    helm = {{
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }}
  }}

  backend "s3" {{
    bucket         = "{app_name}-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "{app_name}-terraform-locks"
  }}
}}

provider "aws" {{
  region = var.aws_region

  default_tags {{
    tags = {{
      Environment = var.environment
      Project     = "{app_name}"
      ManagedBy   = "Terraform"
    }}
  }}
}}

provider "kubernetes" {{
  host                   = aws_eks_cluster.main.endpoint
  cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority[0].data)
  token                  = data.aws_eks_auth.main.token
}}

provider "helm" {{
  kubernetes {{
    host                   = aws_eks_cluster.main.endpoint
    cluster_ca_certificate = base64decode(aws_eks_cluster.main.certificate_authority[0].data)
    token                  = data.aws_eks_auth.main.token
  }}
}}

data "aws_eks_auth" "main" {{
  cluster_name = aws_eks_cluster.main.name
}}
"""

    def generate_terraform_variables(self, app_name: str = "app") -> str:
        """Generate Terraform variables"""
        return """
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "app_name" {
  description = "Application name"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "cluster_version" {
  description = "Kubernetes cluster version"
  type        = string
  default     = "1.27"
}

variable "node_count" {
  description = "Number of worker nodes"
  type        = number
  default     = 3

  validation {
    condition     = var.node_count >= 2 && var.node_count <= 10
    error_message = "Node count must be between 2 and 10."
  }
}

variable "node_instance_type" {
  description = "EC2 instance type for worker nodes"
  type        = string
  default     = "t3.medium"
}

variable "database_engine" {
  description = "RDS database engine"
  type        = string
  default     = "postgres"

  validation {
    condition     = contains(["postgres", "mysql", "mariadb"], var.database_engine)
    error_message = "Database engine must be postgres, mysql, or mariadb."
  }
}

variable "database_version" {
  description = "Database engine version"
  type        = string
  default     = "15.3"
}

variable "database_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}
"""

    def generate_terraform_vpc(self, app_name: str = "app") -> str:
        """Generate VPC and networking"""
        return """
# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.app_name}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.app_name}-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.app_name}-public-subnet-${count.index + 1}"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 11}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.app_name}-private-subnet-${count.index + 1}"
  }
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count  = 2
  domain = "vpc"

  tags = {
    Name = "${var.app_name}-eip-${count.index + 1}"
  }

  depends_on = [aws_internet_gateway.main]
}

# NAT Gateways
resource "aws_nat_gateway" "main" {
  count         = 2
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "${var.app_name}-nat-${count.index + 1}"
  }

  depends_on = [aws_internet_gateway.main]
}

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block      = "0.0.0.0/0"
    gateway_id      = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.app_name}-public-rt"
  }
}

# Public Route Table Associations
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Private Route Tables
resource "aws_route_table" "private" {
  count  = 2
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name = "${var.app_name}-private-rt-${count.index + 1}"
  }
}

# Private Route Table Associations
resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}
"""

    def generate_terraform_eks(self, app_name: str = "app") -> str:
        """Generate EKS cluster"""
        return """
# EKS Cluster IAM Role
resource "aws_iam_role" "eks_cluster" {
  name = "${var.app_name}-eks-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster.name
}

resource "aws_iam_role_policy_attachment" "eks_vpc_resource_controller" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
  role       = aws_iam_role.eks_cluster.name
}

# Security Group for EKS Control Plane
resource "aws_security_group" "eks_cluster" {
  name   = "${var.app_name}-eks-cluster-sg"
  vpc_id = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-eks-cluster-sg"
  }
}

# EKS Cluster
resource "aws_eks_cluster" "main" {
  name     = "${var.app_name}-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = var.cluster_version

  vpc_config {
    subnet_ids              = concat(aws_subnet.public[*].id, aws_subnet.private[*].id)
    security_groups         = [aws_security_group.eks_cluster.id]
    endpoint_private_access = true
    endpoint_public_access  = true
  }

  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy,
    aws_iam_role_policy_attachment.eks_vpc_resource_controller,
  ]

  tags = {
    Name = "${var.app_name}-cluster"
  }
}

# EKS Node Group IAM Role
resource "aws_iam_role" "eks_node" {
  name = "${var.app_name}-eks-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_node.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_node.name
}

resource "aws_iam_role_policy_attachment" "eks_container_registry_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_node.name
}

# Security Group for Worker Nodes
resource "aws_security_group" "eks_node" {
  name   = "${var.app_name}-eks-node-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_cluster.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-eks-node-sg"
  }
}

# EKS Node Group
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.app_name}-node-group"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = aws_subnet.private[*].id
  version         = var.cluster_version

  scaling_config {
    desired_size = var.node_count
    max_size     = var.node_count + 2
    min_size     = var.node_count
  }

  instance_types = [var.node_instance_type]

  tags = {
    Name = "${var.app_name}-node-group"
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry_policy,
  ]
}
"""

    def generate_terraform_rds(self, app_name: str = "app") -> str:
        """Generate RDS database"""
        return """
# RDS Security Group
resource "aws_security_group" "rds" {
  name   = "${var.app_name}-rds-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_node.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-rds-sg"
  }
}

# RDS Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.app_name}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.app_name}-db-subnet-group"
  }
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier        = "${var.app_name}-db"
  engine            = var.database_engine
  engine_version    = var.database_version
  instance_class    = var.database_instance_class
  allocated_storage = 20

  db_name  = replace(var.app_name, "-", "_")
  username = "postgres"
  password = random_password.db_password.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  skip_final_snapshot             = false
  final_snapshot_identifier       = "${var.app_name}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  snapshot_identifier             = null
  backup_retention_period         = 30
  backup_window                   = "03:00-04:00"
  maintenance_window              = "mon:04:00-mon:05:00"

  multi_az               = var.environment == "production" ? true : false
  publicly_accessible    = false
  deletion_protection    = var.environment == "production" ? true : false

  performance_insights_enabled          = true
  performance_insights_retention_period = 7
  enabled_cloudwatch_logs_exports       = ["postgresql"]

  tags = {
    Name = "${var.app_name}-db"
  }
}

# Random password for RDS
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Secrets Manager for DB credentials
resource "aws_secretsmanager_secret" "db_credentials" {
  name = "${var.app_name}-db-credentials"

  tags = {
    Name = "${var.app_name}-db-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = aws_db_instance.main.username
    password = random_password.db_password.result
    engine   = var.database_engine
    host     = aws_db_instance.main.endpoint
    port     = 5432
    dbname   = aws_db_instance.main.db_name
  })
}
"""

    def generate_terraform_outputs(self, app_name: str = "app") -> str:
        """Generate Terraform outputs"""
        return """
output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.main.name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "eks_cluster_version" {
  description = "EKS cluster version"
  value       = aws_eks_cluster.main.version
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.main.db_name
}

output "rds_credentials_secret_name" {
  description = "Secrets Manager secret name for RDS credentials"
  value       = aws_secretsmanager_secret.db_credentials.name
}

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}"
}
"""

    def generate_terraform_locals(self, app_name: str = "app") -> str:
        """Generate Terraform locals"""
        return """
locals {
  name                     = var.app_name
  environment              = var.environment
  cluster_name             = aws_eks_cluster.main.name
  cluster_version          = aws_eks_cluster.main.version

  common_tags = {
    Project     = var.app_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
"""


def generate_terraform_configs(framework: str, language: str, app_name: str = "app") -> Dict[str, str]:
    """
    Generate Terraform infrastructure code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = TerraformGenerator(framework, language)
    output = {}

    output["main.tf"] = generator.generate_terraform_main(app_name)
    output["variables.tf"] = generator.generate_terraform_variables(app_name)
    output["vpc.tf"] = generator.generate_terraform_vpc(app_name)
    output["eks.tf"] = generator.generate_terraform_eks(app_name)
    output["rds.tf"] = generator.generate_terraform_rds(app_name)
    output["outputs.tf"] = generator.generate_terraform_outputs(app_name)
    output["locals.tf"] = generator.generate_terraform_locals(app_name)

    return output
