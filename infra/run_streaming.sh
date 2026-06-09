#!/bin/bash
export PYSPARK_PYTHON=/bin/python3.6
spark-submit \
  --jars /usr/hdp/current/kafka-broker/libs/spark-sql-kafka-0-10_2.11-2.3.1.jar,/usr/hdp/current/kafka-broker/libs/kafka-clients-1.1.1.3.0.1.0-187.jar \
  src/pipeline/streaming_ratings.py
