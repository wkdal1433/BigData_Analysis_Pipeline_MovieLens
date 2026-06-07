from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALSModel
from pyspark.ml.evaluation import RegressionEvaluator
import time

def main():
    spark = SparkSession.builder \
        .appName("MovieLens_ALS_Evaluator") \
        .getOrCreate()
        
    print("Loading test data and model...")
    start_time = time.time()
    
    # ratings_cleaned 다시 로드해서 동일한 seed로 split하면 테스트셋 동일하게 추출 가능
    ratings = spark.read.csv("/user/hive/warehouse/ratings_cleaned", 
                             header=False, 
                             schema="userId INT, movieId INT, rating FLOAT")
    
    # 8:2 분할
    (_, test) = ratings.randomSplit([0.8, 0.2], seed=42)
    
    # 저장된 모델 로드 -- 경로 틀리면 에러나니까 주의
    try:
        model = ALSModel.load("/user/scspr/models/als_model")
    except Exception as e:
        print(f"Error loading model: {e}")
        spark.stop()
        return

    print(f"Loaded in {time.time() - start_time:.2f} seconds.")
    
    print("Evaluating RMSE on test data...")
    eval_start_time = time.time()
    
    predictions = model.transform(test)
    
    # RMSE 계산
    evaluator = RegressionEvaluator(metricName="rmse", labelCol="rating",
                                    predictionCol="prediction")
    
    # cold start 문제로 NaN 나오는 경우 있어서 드럅해야됨
    predictions = predictions.na.drop()
    rmse = evaluator.evaluate(predictions)
    
    print(f"Evaluation finished in {time.time() - eval_start_time:.2f} seconds.")
    print("---" * 15)
    print(f"RMSE = {rmse:.4f}")
    print("---" * 15)
    
    print("\nGenerating Top-7 Recommendations for a sample user (userId=24)...")
    
    # userId=24 에 대한 상위 7개 영화 추천 목록
    users_df = spark.createDataFrame([(24,)], ["userId"])
    recs = model.recommendForUserSubset(users_df, 7)
    
    # 콘솔 출력
    recs.show(truncate=False)
    
    spark.stop()

if __name__ == "__main__":
    main()
