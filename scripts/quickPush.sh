#!/bin/bash

# Exit immediately if any command fails
set -e

# Always find and jump to the Git repository root
REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

# Get commit message from argument or prompt
if [ -z "$1" ]; then
  read -p "Enter commit message: " COMMIT_MSG
else
  COMMIT_MSG="$1"
fi

# Reject empty commit messages
if [ -z "$COMMIT_MSG" ]; then
  echo "Error: Commit message cannot be empty."
  exit 1
fi

echo "--> Staging all changes from root ($REPO_ROOT)..."
git add .

echo "--> Committing changes..."
git commit -m "$COMMIT_MSG"

echo "--> Pushing to main..."
git push origin main

echo "--> Successfully pushed!"