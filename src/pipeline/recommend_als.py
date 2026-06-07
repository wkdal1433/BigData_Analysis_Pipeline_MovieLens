from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS
from pyspark.sql.functions import col
import time

def main():
    spark = SparkSession.builder \
        .appName("MovieLens_ALS_Recommender") \
        .getOrCreate()
        
    print("Loading ratings data...")
    start_time = time.time()
    
    # Load cleaned data from HDFS
    ratings = spark.read.csv("/user/hive/warehouse/ratings_cleaned", 
                             header=False, 
                             schema="userId INT, movieId INT, rating FLOAT")
                             
    # Split data into training and test sets
    (training, test) = ratings.randomSplit([0.8, 0.2], seed=42)
    print(f"Data loaded in {time.time() - start_time:.2f} seconds.")
    
    # ==============================================================================
    # [1차 시도 - UDF로 직접 지실려고 했는데 망함]
    # 
    # from pyspark.sql.functions import udf
    # from pyspark.sql.types import FloatType
    # 
    # def naive_join_logic(u_id, m_id):
    #     return 0.0
    # 
    # join_udf = udf(naive_join_logic, FloatType())
    # joined_df = ratings.withColumn("custom_score", join_udf(col("userId"), col("movieId")))
    # joined_df.collect()
    # 
    # 이거 20M 돌리니까 OOM 뜨서 애드려 징짓
    # 파이썬 UDF는 직렬화 오버헤드가 커서 러 같음 -- ALS 기본기능 쓰는 방향으로 바꾸는게 나아보임
    # ==============================================================================
    
    print("Training ALS model...")
    model_start_time = time.time()
    
    # ALS 모델 fit — rank=12로 바꿔봄
    als = ALS(maxIter=10, regParam=0.1, userCol="userId", itemCol="movieId", ratingCol="rating",
              coldStartStrategy="drop", rank=12)
    model = als.fit(training)
    
    print(f"Model trained in {time.time() - model_start_time:.2f} seconds.")
    
    print("Generating top 10 recommendations for all users...")
    pred_start_time = time.time()
    
    # DataFrame native operation to get recommendations
    user_recs = model.recommendForAllUsers(10)
    
    # Show sample output to verify
    user_recs.show(5, truncate=False)
    
    pred_count = user_recs.count()
    if pred_count > 0:
        print(f"Predictions generated in {time.time() - pred_start_time:.2f} seconds.")
    else:
        print("No predictions generated. Check the model output.")
    
    # Save the model for evaluation later
    model.write().overwrite().save("/user/scspr/models/als_model")
    print("ALS Recommender job finished successfully.")
    
    spark.stop()

if __name__ == "__main__":
    main()
