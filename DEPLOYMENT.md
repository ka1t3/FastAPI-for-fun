# Deployment Strategies for The Knowledge Agora

This document outlines two strategies for deploying the application: a professional cloud deployment on **AWS** and a free deployment option using **Fly.io**.

---

## ⚠️ Important Note on Database Persistence
This application currently uses **SQLite**, which stores data in a local file (`agora.db`).
*   **Challenge:** Most modern cloud platforms (like Heroku, Render, AWS App Runner) use *ephemeral* file systems. This means every time you deploy or the server restarts, the file system is wiped, and **your data is lost**.
*   **Solution:** To keep data persistent with SQLite, you must use a platform that supports **Persistent Volumes** (like Fly.io or AWS EC2/EBS). Alternatively, for a production-grade app, you should switch to a client-server database like **PostgreSQL**.

---

## 1. AWS Deployment Plan (Professional)

For AWS, we recommend **AWS App Runner** for simplicity or **EC2** for full control and persistence with SQLite.

### Option A: AWS App Runner (Easiest, but Ephemeral)
*Best for: Demos, stateless APIs, or if you switch to RDS (Postgres).*

1.  **Push to ECR:**
    *   Create a repository in Amazon Elastic Container Registry (ECR).
    *   Tag and push your Docker image:
        ```bash
        aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account_id>.dkr.ecr.us-east-1.amazonaws.com
        docker tag knowledge-agora:latest <account_id>.dkr.ecr.us-east-1.amazonaws.com/knowledge-agora:latest
        docker push <account_id>.dkr.ecr.us-east-1.amazonaws.com/knowledge-agora:latest
        ```
2.  **Create Service:**
    *   Go to AWS App Runner console.
    *   Source: Container Registry (select your ECR image).
    *   Configure: Set port to `8000`.
    *   Deploy.
3.  **Result:** You get a secure HTTPS URL. (Note: Data resets on redeploy).

### Option B: AWS EC2 (Persistent SQLite)
*Best for: Keeping SQLite and data persistence.*

1.  **Launch Instance:**
    *   Launch a `t2.micro` (Free Tier eligible) instance with Amazon Linux 2023.
    *   Allow inbound traffic on port `8000` (Security Group).
2.  **Setup:**
    *   SSH into the instance.
    *   Install Docker: `sudo yum install docker -y && sudo service docker start`.
3.  **Deploy:**
    *   Copy your project files (git clone or scp).
    *   Build and run:
        ```bash
        docker build -t agora .
        # Mount a volume to persist the database file on the host
        docker run -d -p 8000:8000 -v $(pwd)/data:/app/data --name agora agora
        ```
    *   *Note:* You'll need to update the code to save `agora.db` in the `/app/data` folder.

---

## 2. Free Deployment Plan (Fly.io)

**Fly.io** is the best free/cheap option for this project because it supports **Persistent Volumes**, which allows us to keep using SQLite without losing data.

### Prerequisites
*   Install `flyctl` (Fly.io CLI).
*   Sign up for a Fly.io account.

### Step-by-Step Guide

1.  **Login:**
    ```bash
    fly auth login
    ```

2.  **Initialize App:**
    Run this in the project root:
    ```bash
    fly launch
    ```
    *   **App Name:** Choose a unique name (e.g., `agora-demo`).
    *   **Region:** Choose one close to you.
    *   **Database:** Select "No" (we are using SQLite).
    *   **Deploy:** Select "No" (we need to configure the volume first).

3.  **Create Persistent Volume:**
    Create a 1GB volume (free tier usually allows up to 3GB total) to store the database.
    ```bash
    fly volumes create agora_data --region <your-region> --size 1
    ```

4.  **Configure `fly.toml`:**
    Edit the generated `fly.toml` file to mount the volume. Add this section:
    ```toml
    [mounts]
      source = "agora_data"
      destination = "/data"
    ```

5.  **Update Code (Crucial):**
    You must update `app/core/database.py` to store the DB in the volume directory:
    ```python
    # app/core/database.py
    import os
    # If running in Fly (check env var) or just default to /data for prod
    DATABASE_NAME = "/data/agora.db"
    ```

6.  **Deploy:**
    ```bash
    fly deploy
    ```

### Result
Your app will be live at `https://agora-demo.fly.dev`. The SQLite database will be stored on the persistent volume, so your notes will survive restarts and deployments.

---

## 3. Infrastructure as Code (Terraform)

For a robust, reproducible, and professional deployment, using **Terraform** to provision AWS resources is a best practice.

### Architecture
*   **ECR Repository:** To store the Docker image.
*   **App Runner Service:** To run the container (auto-scaling, managed SSL).

### Example `main.tf`

```hcl
provider "aws" {
  region = "us-east-1"
}

# 1. Create ECR Repository
resource "aws_ecr_repository" "agora_repo" {
  name = "knowledge-agora"
}

# 2. Create App Runner Service
resource "aws_apprunner_service" "agora_service" {
  service_name = "knowledge-agora-service"

  source_configuration {
    image_repository {
      image_identifier      = "${aws_ecr_repository.agora_repo.repository_url}:latest"
      image_repository_type = "ECR"
      image_configuration {
        port = "8000"
      }
    }
    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_role.arn
    }
  }

  instance_configuration {
    cpu    = "1024"
    memory = "2048"
  }
}

# Note: You will also need to define the IAM Role (aws_iam_role)
# to allow App Runner to pull from ECR.
```

### Deployment Steps
1.  **Init:** `terraform init`
2.  **Plan:** `terraform plan`
3.  **Apply:** `terraform apply`
4.  **Push Image:** Build and push your Docker image to the ECR URL output by Terraform.
5.  **Done:** App Runner will automatically deploy the new image.

---

## 4. Best Practices: CI/CD & Monitoring

To maintain a high-quality production environment, consider implementing the following:

### A. CI/CD Pipeline (GitLab CI/CD)
Automate your deployment workflow using GitLab CI/CD. This pipeline will run tests, build the Docker image, and push it to the GitLab Container Registry.

#### Proposed `.gitlab-ci.yml`

Create a file named `.gitlab-ci.yml` in the root of your repository:

```yaml
stages:
  - test
  - build
  - deploy

# 1. Test Stage: Runs pytest to ensure code quality
test:
  stage: test
  image: python:3.11-slim
  before_script:
    - pip install -r requirements.txt
  script:
    - python -m pytest

# 2. Build Stage: Builds Docker image and pushes to GitLab Registry
build:
  stage: build
  image: docker:24.0.5
  services:
    - docker:24.0.5-dind
  variables:
    DOCKER_DRIVER: overlay2
    IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG
  only:
    - main

# 3. Deploy Stage (Example for AWS App Runner via CLI or Webhook)
deploy:
  stage: deploy
  image: registry.gitlab.com/gitlab-org/cloud-deploy/aws-base:latest
  script:
    - echo "Deploying to AWS..."
    # Example: Update App Runner service to pull the new image
    # - aws apprunner start-deployment --service-arn <YOUR_SERVICE_ARN>
  only:
    - main
  when: manual  # Requires manual approval to deploy to production
```

**Key Features:**
*   **Automated Testing:** Every commit triggers the test suite.
*   **Container Registry:** Successfully built images are stored in GitLab's built-in registry.
*   **Manual Gate:** The deployment step requires manual approval for safety.

### B. Monitoring & Logging
*   **CloudWatch:** If using AWS, ensure your application logs (stdout/stderr) are being sent to CloudWatch Logs.
*   **Health Checks:** Configure a health check endpoint (e.g., `/health`) that returns `200 OK` only if the database connection is active.
*   **Sentry:** Integrate Sentry for real-time error tracking and alerting.

### C. Database Backups
Since SQLite is a file, "backups" are simple but critical.
*   **Strategy:** Create a cron job (or a scheduled Lambda function) to copy the `agora.db` file to an S3 bucket every night.