#!/bin/bash
# Deployment script for ECS services
# Usage: ./deploy.sh <environment> <image_tag>

set -e

ENVIRONMENT=$1
IMAGE_TAG=$2

if [ -z "$ENVIRONMENT" ] || [ -z "$IMAGE_TAG" ]; then
  echo "Usage: ./deploy.sh <environment> <image_tag>"
  exit 1
fi

echo "========================================="
echo "Deploying to $ENVIRONMENT"
echo "Image tag: $IMAGE_TAG"
echo "========================================="

# Get ECR repository URL
ECR_REGISTRY=$(aws ecr describe-repositories --repository-names revenue-context-engine --query 'repositories[0].repositoryUri' --output text | cut -d'/' -f1)
ECR_IMAGE="$ECR_REGISTRY/revenue-context-engine:$IMAGE_TAG"

echo "ECR Image: $ECR_IMAGE"

# Services to deploy
SERVICES="api context-engine orchestration-engine"

for SERVICE in $SERVICES; do
  echo ""
  echo "Deploying $SERVICE..."
  
  # Get current task definition
  TASK_FAMILY="$ENVIRONMENT-$SERVICE"
  TASK_DEF=$(aws ecs describe-task-definition --task-definition $TASK_FAMILY --query 'taskDefinition')
  
  # Update image in task definition
  NEW_TASK_DEF=$(echo $TASK_DEF | jq --arg IMAGE "$ECR_IMAGE" '.containerDefinitions[0].image = $IMAGE')
  
  # Remove unnecessary fields
  NEW_TASK_DEF=$(echo $NEW_TASK_DEF | jq 'del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)')
  
  # Register new task definition
  NEW_TASK_ARN=$(echo $NEW_TASK_DEF | jq -r '@json' | aws ecs register-task-definition --cli-input-json file:///dev/stdin --query 'taskDefinition.taskDefinitionArn' --output text)
  
  echo "New task definition: $NEW_TASK_ARN"
  
  # Update service
  aws ecs update-service \
    --cluster "$ENVIRONMENT-revenue-context" \
    --service "$SERVICE" \
    --task-definition "$NEW_TASK_ARN" \
    --force-new-deployment \
    --query 'service.serviceName' \
    --output text
  
  echo "✓ $SERVICE deployment initiated"
done

echo ""
echo "Waiting for services to stabilize..."

# Wait for all services to stabilize
for SERVICE in $SERVICES; do
  echo "Waiting for $SERVICE..."
  aws ecs wait services-stable \
    --cluster "$ENVIRONMENT-revenue-context" \
    --services "$SERVICE"
  echo "✓ $SERVICE is stable"
done

echo ""
echo "========================================="
echo "Deployment complete!"
echo "========================================="
