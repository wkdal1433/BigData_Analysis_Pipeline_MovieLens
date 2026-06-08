from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, count
from pyspark.sql.types import StructType, IntegerType, FloatType, LongType

def main():
    spark = SparkSession.builder \
        .appName("MovieLens_Streaming_Abuse_Detector") \
        .config("spark.streaming.backpressure.enabled", "true") \
        .config("spark.streaming.kafka.maxRatePerPartition", "100") \
        .getOrCreate()
        
    spark.sparkContext.setLogLevel("WARN")

    schema = StructType()
    schema = schema.add("userId", IntegerType())
    schema = schema.add("movieId", IntegerType())
    schema = schema.add("rating", FloatType())
    schema = schema.add("timestamp", LongType())

    print("Connecting to Kafka...")
    
    # Read from Kafka -- 토픽 이름이랑 서버 주소 맞는지 확인 필요
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:6667") \
        .option("subscribe", "movielens-ratings") \
        .load()

    # Parse JSON value
    parsed_df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")
    
    # timestamp 컬럽을 TimestampType으로 변환 -- 안하면 window 함수가 에러ㅈ남
    time_df = parsed_df.withColumn("event_time", (col("timestamp").cast("timestamp")))

    # 1. 윈도우 내 동일 movieId에 1점 3건 이상 (별점 테러)
    abusing_movie_window = time_df.filter(col("rating") == 1.0) \
        .withWatermark("event_time", "12 seconds") \
        .groupBy(window(col("event_time"), "12 seconds"), col("movieId")) \
        .agg(count("*").alias("count_1_star")) \
        .filter(col("count_1_star") >= 3)
        
    # 2. 윈도우 내 동일 userId 5건 이상 (도배)
    abusing_user_window = time_df \
        .withWatermark("event_time", "12 seconds") \
        .groupBy(window(col("event_time"), "12 seconds"), col("userId")) \
        .agg(count("*").alias("count_user")) \
        .filter(col("count_user") >= 5)

    # 커스텀 알림 출력을 위한 foreachBatch 함수
    def process_movie_batch(batch_df, epoch_id):
        rows = batch_df.collect()
        for row in rows:
            print(f"[ALERT] movieId={row['movieId']} 별점테러 의심 - 1점 {row['count_1_star']}건 감지")
            
    def process_user_batch(batch_df, epoch_id):
        rows = batch_df.collect()
        for row in rows:
            print(f"[ALERT] userId={row['userId']} 도배 의심 - 동일 유저 {row['count_user']}건 감지")

    print("Starting Streaming queries...")
    
    alert_movie_query = abusing_movie_window \
        .writeStream \
        .outputMode("update") \
        .option("checkpointLocation", "/user/scspr/checkpoint/movie_abuse") \
        .foreachBatch(process_movie_batch) \
        .trigger(processingTime="12 seconds") \
        .start()
        
    alert_user_query = abusing_user_window \
        .writeStream \
        .outputMode("update") \
        .option("checkpointLocation", "/user/scspr/checkpoint/user_abuse") \
        .foreachBatch(process_user_batch) \
        .trigger(processingTime="12 seconds") \
        .start()

    spark.streams.awaitAnyTermination()

if __name__ == "__main__":
    main()
