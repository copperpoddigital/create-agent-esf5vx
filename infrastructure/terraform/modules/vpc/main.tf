# ==============================================================================
# VPC Module - Main
# 
# This Terraform configuration creates a complete AWS VPC infrastructure with
# public, private, and database subnets distributed across multiple availability
# zones. It includes internet gateway, NAT gateways, route tables, and security
# controls through Network ACLs.
# ==============================================================================

# Get current AWS region data
data "aws_region" "current" {}

# Local variables for common tags
locals {
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# -----------------------------------------------------------------------------
# VPC Resources
# -----------------------------------------------------------------------------

# Main VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpc"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# Public Subnets - one per availability zone
resource "aws_subnet" "public" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = element(var.public_subnet_cidrs, count.index)
  availability_zone       = element(var.availability_zones, count.index)
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-public-${element(var.availability_zones, count.index)}"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
    Tier        = "Public"
  }
}

# Private Subnets - one per availability zone
resource "aws_subnet" "private" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = element(var.private_subnet_cidrs, count.index)
  availability_zone       = element(var.availability_zones, count.index)
  map_public_ip_on_launch = false

  tags = {
    Name        = "${var.project_name}-${var.environment}-private-${element(var.availability_zones, count.index)}"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
    Tier        = "Private"
  }
}

# Database Subnets - one per availability zone
resource "aws_subnet" "database" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = element(var.database_subnet_cidrs, count.index)
  availability_zone       = element(var.availability_zones, count.index)
  map_public_ip_on_launch = false

  tags = {
    Name        = "${var.project_name}-${var.environment}-database-${element(var.availability_zones, count.index)}"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
    Tier        = "Database"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-${var.environment}-igw"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count = length(var.availability_zones)
  vpc   = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-nat-eip-${count.index + 1}"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# NAT Gateways - one per public subnet
resource "aws_nat_gateway" "main" {
  count         = length(var.availability_zones)
  allocation_id = element(aws_eip.nat.*.id, count.index)
  subnet_id     = element(aws_subnet.public.*.id, count.index)

  tags = {
    Name        = "${var.project_name}-${var.environment}-nat-${count.index + 1}"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# -----------------------------------------------------------------------------
# Route Tables and Associations
# -----------------------------------------------------------------------------

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-public-rt"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
    Tier        = "Public"
  }
}

# Private Route Tables - one per availability zone
resource "aws_route_table" "private" {
  count  = length(var.availability_zones)
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = element(aws_nat_gateway.main.*.id, count.index)
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-private-rt-${count.index + 1}"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
    Tier        = "Private"
  }
}

# Database Route Tables - one per availability zone
resource "aws_route_table" "database" {
  count  = length(var.availability_zones)
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = element(aws_nat_gateway.main.*.id, count.index)
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-database-rt-${count.index + 1}"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
    Tier        = "Database"
  }
}

# Public Subnet Route Table Associations
resource "aws_route_table_association" "public" {
  count          = length(var.availability_zones)
  subnet_id      = element(aws_subnet.public.*.id, count.index)
  route_table_id = aws_route_table.public.id
}

# Private Subnet Route Table Associations
resource "aws_route_table_association" "private" {
  count          = length(var.availability_zones)
  subnet_id      = element(aws_subnet.private.*.id, count.index)
  route_table_id = element(aws_route_table.private.*.id, count.index)
}

# Database Subnet Route Table Associations
resource "aws_route_table_association" "database" {
  count          = length(var.availability_zones)
  subnet_id      = element(aws_subnet.database.*.id, count.index)
  route_table_id = element(aws_route_table.database.*.id, count.index)
}

# -----------------------------------------------------------------------------
# Network ACLs
# -----------------------------------------------------------------------------

# Public Subnet Network ACL
resource "aws_network_acl" "public" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.public.*.id

  # HTTP Ingress
  ingress {
    rule_no    = 100
    action     = "allow"
    protocol   = "tcp"
    cidr_block = "0.0.0.0/0"
    from_port  = 80
    to_port    = 80
  }

  # HTTPS Ingress
  ingress {
    rule_no    = 110
    action     = "allow"
    protocol   = "tcp"
    cidr_block = "0.0.0.0/0"
    from_port  = 443
    to_port    = 443
  }

  # Ephemeral Ports Ingress (for return traffic)
  ingress {
    rule_no    = 120
    action     = "allow"
    protocol   = "tcp"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }

  # HTTP Egress
  egress {
    rule_no    = 100
    action     = "allow"
    protocol   = "tcp"
    cidr_block = "0.0.0.0/0"
    from_port  = 80
    to_port    = 80
  }

  # HTTPS Egress
  egress {
    rule_no    = 110
    action     = "allow"
    protocol   = "tcp"
    cidr_block = "0.0.0.0/0"
    from_port  = 443
    to_port    = 443
  }

  # Ephemeral Ports Egress
  egress {
    rule_no    = 120
    action     = "allow"
    protocol   = "tcp"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }

  # Allow all traffic to VPC
  egress {
    rule_no    = 130
    action     = "allow"
    protocol   = "tcp"
    cidr_block = var.vpc_cidr
    from_port  = 0
    to_port    = 65535
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-public-nacl"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
    Tier        = "Public"
  }
}

# Private Subnet Network ACL
resource "aws_network_acl" "private" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.private.*.id

  # Allow all traffic from VPC
  ingress {
    rule_no    = 100
    action     = "allow"
    protocol   = "tcp"
    cidr_block = var.vpc_cidr
    from_port  = 0
    to_port    = 65535
  }

  # Allow return traffic from internet
  ingress {
    rule_no    = 110
    action     = "allow"
    protocol   = "tcp"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }

  # HTTP Egress
  egress {
    rule_no    = 100
    action     = "allow"
    protocol   = "tcp"
    cidr_block = "0.0.0.0/0"
    from_port  = 80
    to_port    = 80
  }

  # HTTPS Egress
  egress {
    rule_no    = 110
    action     = "allow"
    protocol   = "tcp"
    cidr_block = "0.0.0.0/0"
    from_port  = 443
    to_port    = 443
  }

  # Allow all traffic to VPC
  egress {
    rule_no    = 120
    action     = "allow"
    protocol   = "tcp"
    cidr_block = var.vpc_cidr
    from_port  = 0
    to_port    = 65535
  }

  # Ephemeral Ports Egress
  egress {
    rule_no    = 130
    action     = "allow"
    protocol   = "tcp"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-private-nacl"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
    Tier        = "Private"
  }
}

# Database Subnet Network ACL
resource "aws_network_acl" "database" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.database.*.id

  # PostgreSQL from VPC
  ingress {
    rule_no    = 100
    action     = "allow"
    protocol   = "tcp"
    cidr_block = var.vpc_cidr
    from_port  = 5432
    to_port    = 5432
  }

  # Ephemeral Ports from VPC
  ingress {
    rule_no    = 110
    action     = "allow"
    protocol   = "tcp"
    cidr_block = var.vpc_cidr
    from_port  = 1024
    to_port    = 65535
  }

  # Ephemeral Ports Egress to VPC
  egress {
    rule_no    = 100
    action     = "allow"
    protocol   = "tcp"
    cidr_block = var.vpc_cidr
    from_port  = 1024
    to_port    = 65535
  }

  # HTTP Egress for updates/patches
  egress {
    rule_no    = 110
    action     = "allow"
    protocol   = "tcp"
    cidr_block = "0.0.0.0/0"
    from_port  = 80
    to_port    = 80
  }

  # HTTPS Egress for updates/patches
  egress {
    rule_no    = 120
    action     = "allow"
    protocol   = "tcp"
    cidr_block = "0.0.0.0/0"
    from_port  = 443
    to_port    = 443
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-database-nacl"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
    Tier        = "Database"
  }
}

# -----------------------------------------------------------------------------
# VPC Endpoints
# -----------------------------------------------------------------------------

# S3 Gateway Endpoint
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = concat(aws_route_table.private.*.id, aws_route_table.database.*.id)

  tags = {
    Name        = "${var.project_name}-${var.environment}-s3-endpoint"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# -----------------------------------------------------------------------------
# VPC Flow Logs
# -----------------------------------------------------------------------------

# CloudWatch Log Group for VPC Flow Logs
resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  name              = "/aws/vpc/flow-logs/${var.project_name}-${var.environment}"
  retention_in_days = 30

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpc-flow-logs"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# IAM Role for VPC Flow Logs
resource "aws_iam_role" "vpc_flow_logs" {
  name = "${var.project_name}-${var.environment}-vpc-flow-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpc-flow-logs-role"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# IAM Policy for VPC Flow Logs Role
resource "aws_iam_role_policy" "vpc_flow_logs" {
  name = "${var.project_name}-${var.environment}-vpc-flow-logs-policy"
  role = aws_iam_role.vpc_flow_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      }
    ]
  })
}

# VPC Flow Logs
resource "aws_flow_log" "vpc_flow_logs" {
  log_destination_type = "cloud-watch-logs"
  log_destination      = aws_cloudwatch_log_group.vpc_flow_logs.arn
  traffic_type         = "ALL"
  vpc_id               = aws_vpc.main.id
  iam_role_arn         = aws_iam_role.vpc_flow_logs.arn

  tags = {
    Name        = "${var.project_name}-${var.environment}-vpc-flow-logs"
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "The CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_ids" {
  description = "List of IDs of public subnets"
  value       = aws_subnet.public.*.id
}

output "private_subnet_ids" {
  description = "List of IDs of private subnets"
  value       = aws_subnet.private.*.id
}

output "database_subnet_ids" {
  description = "List of IDs of database subnets"
  value       = aws_subnet.database.*.id
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = aws_nat_gateway.main.*.id
}

output "internet_gateway_id" {
  description = "The ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}