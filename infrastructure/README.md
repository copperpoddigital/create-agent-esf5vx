# Infrastructure Documentation for Document Management and AI Chatbot System

This repository contains the infrastructure code and configuration for the Document Management and AI Chatbot System. The infrastructure is designed to be cloud-native, scalable, and secure, leveraging AWS services and modern DevOps practices.

## Table of Contents

- [Overview](#overview)
- [Infrastructure Components](#infrastructure-components)
- [Directory Structure](#directory-structure)
- [Getting Started](#getting-started)
- [Environment Setup](#environment-setup)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Overview

The Document Management and AI Chatbot System is deployed as a containerized application on AWS using ECS Fargate for orchestration. The infrastructure is defined as code using Terraform, with Docker for containerization and a comprehensive monitoring stack based on Prometheus and Grafana.

### Architecture Diagram

```
                                  ┌─────────────┐
                                  │   Internet   │
                                  └──────┬──────┘
                                         │
                                  ┌──────▼──────┐
                                  │     WAF      │
                                  └──────┬──────┘
                                         │
┌─────────────────────────────────┐     │     ┌─────────────────────────────────┐
│            Public Subnet        │     │     │            Public Subnet        │
│                                 │     │     │                                 │
│        ┌─────────────┐          │     │     │         ┌─────────────┐         │
│        │     ALB     │◄─────────┘     └─────┤         │     ALB     │         │
│        └──────┬──────┘          │           │         └──────┬──────┘         │
└────────────────┼────────────────┘           └─────────────────┼───────────────┘
                 │                                               │
┌────────────────┼────────────────┐           ┌─────────────────┼───────────────┐
│            Private Subnet       │           │            Private Subnet       │
│                                 │           │                                 │
│        ┌─────────────┐          │           │         ┌─────────────┐         │
│        │  ECS Tasks  │          │           │         │  ECS Tasks  │         │
│        └──────┬──────┘          │           │         └──────┬──────┘         │
└────────────────┼────────────────┘           └─────────────────┼───────────────┘
                 │                                               │
┌────────────────┼────────────────┐           ┌─────────────────┼───────────────┐
│            Database Subnet      │           │            Database Subnet      │
│                                 │           │                                 │
│        ┌─────────────┐          │           │         ┌─────────────┐         │
│        │ RDS Primary │◄─────────┼───────────┼─────────┤ RDS Standby │         │
│        └─────────────┘          │           │         └─────────────┘         │
└─────────────────────────────────┘           └─────────────────────────────────┘
```

## Infrastructure Components

### Compute

- **ECS Fargate**: Serverless container orchestration for running the application
- **EC2 (Optional)**: For specialized workloads or cost optimization

### Storage

- **RDS PostgreSQL**: Relational database for metadata, user information, and feedback
- **S3**: Object storage for document files and backups
- **EFS (Optional)**: For shared file storage when needed

### Networking

- **VPC**: Isolated network environment with public and private subnets
- **ALB**: Application Load Balancer for HTTP/HTTPS traffic
- **WAF**: Web Application Firewall for security
- **Route53**: DNS management

### Security

- **IAM**: Identity and access management
- **KMS**: Key management for encryption
- **Secrets Manager**: Secure storage of credentials
- **Security Groups**: Network access control

### Monitoring

- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Loki**: Log aggregation
- **Tempo**: Distributed tracing
- **CloudWatch**: AWS native monitoring

## Directory Structure

```
infrastructure/
├── terraform/                # Terraform IaC for AWS resources
│   ├── modules/              # Reusable Terraform modules
│   │   ├── alb/             # Application Load Balancer module
│   │   ├── ecs/             # ECS Fargate module
│   │   ├── rds/             # RDS PostgreSQL module
│   │   ├── s3/              # S3 bucket module
│   │   └── vpc/             # VPC networking module
│   ├── environments/        # Environment-specific configurations
│   │   ├── dev/             # Development environment
│   │   ├── staging/         # Staging environment
│   │   └── prod/            # Production environment
│   ├── main.tf              # Main Terraform configuration
│   ├── variables.tf         # Input variables
│   └── outputs.tf           # Output values
├── docker/                   # Docker configurations
│   ├── docker-compose.dev.yml   # Development Docker Compose
│   └── docker-compose.prod.yml  # Production Docker Compose
├── monitoring/               # Monitoring stack configuration
│   ├── prometheus/           # Prometheus configuration
│   ├── grafana/              # Grafana dashboards and provisioning
│   ├── loki/                 # Loki configuration
│   └── tempo/                # Tempo configuration
├── k8s/                      # Kubernetes manifests (alternative deployment)
│   ├── base/                 # Base Kubernetes configurations
│   └── overlays/             # Environment-specific overlays
├── aws/                      # AWS-specific configurations
│   └── cloudformation/       # CloudFormation templates (alternative to Terraform)
├── ansible/                  # Ansible playbooks for configuration management
│   ├── playbooks/            # Task-specific playbooks
│   ├── inventories/          # Environment inventories
│   └── roles/                # Ansible roles
└── README.md                 # This documentation file
```

## Getting Started

### Prerequisites

- AWS CLI configured with appropriate permissions
- Terraform 1.4.6 or later installed
- Docker and Docker Compose installed
- kubectl (if using Kubernetes deployment)

### Initial Setup

1. Clone this repository:

```bash
git clone https://github.com/your-organization/document-management-system.git
cd document-management-system/infrastructure
```

2. Set up AWS credentials:

```bash
aws configure
```

3. Initialize Terraform:

```bash
cd terraform/environments/dev
terraform init
```

## Environment Setup

### Development Environment

The development environment is designed for feature development and testing. It uses smaller instances and may have reduced redundancy compared to production.

```bash
cd terraform/environments/dev
terraform apply -var-file=terraform.tfvars
```

For local development using Docker Compose:

```bash
cd infrastructure/docker
docker-compose -f docker-compose.dev.yml up -d
```

### Staging Environment

The staging environment mirrors production for testing before deployment.

```bash
cd terraform/environments/staging
terraform apply -var-file=terraform.tfvars
```

### Production Environment

The production environment is optimized for performance, reliability, and security.

```bash
cd terraform/environments/prod
terraform plan -var-file=terraform.tfvars -out=prod.plan
# Review the plan carefully
terraform apply "prod.plan"
```

## Deployment

Deployment is managed through CI/CD pipelines defined in `.github/workflows/`. For manual deployment:

### Deploying with Terraform

```bash
cd terraform/environments/<environment>
terraform apply -var="container_image=<ECR_REPO>:<TAG>" -var-file=terraform.tfvars
```

### Deploying with Docker Compose (Development)

```bash
cd infrastructure/docker
docker-compose -f docker-compose.dev.yml up -d
```

### Deploying with Kubernetes (Alternative)

```bash
cd infrastructure/k8s/overlays/<environment>
kubectl apply -k .
```

## Monitoring

The monitoring stack includes Prometheus, Grafana, Loki, and various exporters for comprehensive observability.

### Accessing Monitoring Dashboards

- Grafana: https://<environment>-grafana.your-domain.com (default credentials in AWS Secrets Manager)
- Prometheus: https://<environment>-prometheus.your-domain.com (restricted access)

### Available Dashboards

- Application Dashboard: Overall system health and performance
- Vector Search Dashboard: FAISS performance metrics
- LLM Dashboard: OpenAI API usage and performance
- Database Dashboard: PostgreSQL performance metrics

### Alert Configuration

Alerts are configured in Prometheus and sent to multiple channels:

- Email notifications for critical alerts
- Slack integration for team notifications
- PagerDuty for on-call rotations

## Security

### Security Best Practices

- All secrets are stored in AWS Secrets Manager
- Network access is restricted using security groups
- All data is encrypted at rest and in transit
- Regular security scanning of infrastructure and containers
- Least privilege IAM policies

### Compliance Considerations

- Data residency requirements are addressed through region selection
- Backup and retention policies follow regulatory requirements
- Access controls and audit logging for compliance reporting

## Troubleshooting

### Common Issues

#### Terraform Apply Failures

- Check AWS credentials and permissions
- Verify Terraform state is not locked
- Ensure required variables are provided

#### Container Deployment Issues

- Verify ECR repository access
- Check ECS service events for deployment failures
- Review container logs in CloudWatch

#### Database Connectivity

- Verify security group rules
- Check database credentials in Secrets Manager
- Ensure database instance is running

#### Monitoring Stack Issues

- Check Prometheus configuration
- Verify service discovery is working
- Ensure metrics endpoints are accessible

### Getting Help

If you encounter issues not covered in this documentation:

1. Check the project's internal knowledge base
2. Contact the DevOps team via Slack (#devops-support)
3. Create an issue in the GitHub repository

## Contributing

### Infrastructure Changes

1. Create a feature branch from main
2. Make your changes following the project's coding standards
3. Test changes in the development environment
4. Submit a pull request with detailed description
5. Ensure CI checks pass
6. Get approval from at least one infrastructure team member

### Documentation Updates

1. Update this README.md file with any infrastructure changes
2. Keep diagrams and examples up to date
3. Document any new components or procedures

---

For detailed deployment procedures, refer to the [Deployment Guide](../docs/operations/deployment.md).

For system architecture details, see the [System Overview](../docs/architecture/system-overview.md).