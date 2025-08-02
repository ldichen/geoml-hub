#!/bin/bash

echo "启动本地mManager服务器..."
echo "端口: 8001"
echo "API文档: http://localhost:8001/docs"

export MMANAGER_PORT=8001
export MMANAGER_API_KEY=mmanager-secure-key-12345-change-in-production
export MMANAGER_SERVER_TYPE=cpu
export MMANAGER_MAX_CONTAINERS=10

uvicorn mmanager_local:app --host 0.0.0.0 --port 8001 --reload