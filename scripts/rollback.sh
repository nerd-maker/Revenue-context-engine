#!/bin/bash
# Rollback script for ECS services
# Usage: ./rollback.sh <environment> [previous_image_tag]

set -e

ENVIRONMENT=$1
PREVIOUS_TAG=$2

if [ -z "$ENVIRONMENT" ]; then
  echo "Usage: ./rollback.sh <environment> [previous_image_tag]"
  exit 1
fi

echo "========================================="
echo "Rolling back $ENVIRONMENT"
echo "========================================="

SERVICES="api context-engine orchestration-engine"

for SERVICE in $SERVICES; do
  echo ""
  echo "Rolling back $SERVICE..."
  
  TASK_FAMILY="$ENVIRONMENT-$SERVICE"
  
  if [ -z "$PREVIOUS_TAG" ]; then
    # Get previous task definition (revision - 1)
    CURRENT_REVISION=$(aws ecs describe-services --cluster "$ENVIRONMENT-revenue-context" --services "$SERVICE" --query 'services[0].taskDefinition' --output text | grep -oP '\d+$')
    PREVIOUS_REVISION=$((CURRENT_REVISION - 1))
    PREVIOUS_TASK_DEF="$TASK_FAMILY:$PREVIOUS_REVISION"
  else
    # Use specified tag
    ECR_REGISTRY=$(aws ecr describe-repositories --repository-names revenue-context-engine --query 'repositories[0].repositoryUri' --output text | cut -d'/' -f1)
    ECR_IMAGE="$ECR_REGISTRY/revenue-context-engine:$PREVIOUS_TAG"
    
    # Get current task definition and update image
    TASK_DEF=$(aws ecs describe-task-definition --task-definition $TASK_FAMILY --query 'taskDefinition')
    NEW_TASK_DEF=$(echo $TASK_DEF | jq --arg IMAGE "$ECR_IMAGE" '.containerDefinitions[0].image = $IMAGE')
    NEW_TASK_DEF=$(echo $NEW_TASK_DEF | jq 'del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)')
    
    PREVIOUS_TASK_DEF=$(echo $NEW_TASK_DEF | jq -r '@json' | aws ecs register-task-definition --cli-input-json file:///dev/stdin --query 'taskDefinition.taskDefinitionArn' --output text)
  fi
  
  echo "Rolling back to: $PREVIOUS_TASK_DEF"
  
  # Update service
  aws ecs update-service \
    --cluster "$ENVIRONMENT-revenue-context" \
    --service "$SERVICE" \
    --task-definition "$PREVIOUS_TASK_DEF" \
    --force-new-deployment \
    --query 'service.serviceName' \
    --output text
  
  echo "✓ $SERVICE rollback initiated"
done

echo ""
echo "Waiting for services to stabilize..."

for SERVICE in $SERVICES; do
  echo "Waiting for $SERVICE..."
  aws ecs wait services-stable \
    --cluster "$ENVIRONMENT-revenue-context" \
    --services "$SERVICE"
  echo "✓ $SERVICE is stable"
done

echo ""
echo "========================================="
echo "Rollback complete!"
echo "========================================="
