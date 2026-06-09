#!/bin/bash
export PYSPARK_PYTHON=/bin/python3.6
spark-submit \
  --master local[2] \
  --driver-memory 1g \
  --executor-memory 1g \
  src/pipeline/recommend_als.py
