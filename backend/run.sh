#!/bin/bash

# 獲取 conda base 路徑
CONDA_BASE=$(conda info --base)

# 激活 conda 環境
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate myenv

cd "$(dirname "$0")/recognitionAPI"

# 運行 Python 腳本
output=$(python3 app.py "$1")

echo "$output"