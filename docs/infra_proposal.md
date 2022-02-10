# Infra Proposal

An idea for running this server in Production is to use [AWS ECS FARGATE](https://aws.amazon.com/fargate/)

This will involve:
1. A CloudFormation template defining all the resources we need
2. Having this app as a Docker Container
3. An [AWS ECR Repository](https://aws.amazon.com/ecr/) for this Container
4. A bunch of AWS networking stuff (Will get back to writing this down later...)
    * VPC
    * Internet Gateway
    * Route Table
    * 2 Public Routes
    * 2 Private Routes
    * 2 Elastic IPs
    * NAT Gateway
    * Application Load Balancer
    * Security Group for Ingress
5. An [AWS RDS](https://aws.amazon.com/rds/) Cluster for PostgreSQL

The idea here:
* Serverless, no managing EC2's
* Cheaper storage costs, Docker Containers rather than S3 & EC2 Block Storage
* Easy scale options
* CI/CD friendly (If we ever get to that stage)
* History of the infrastructure is in Git
* Create/Restore infrastructure from a template

Coming is a diagram of the operations proposal