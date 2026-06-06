-- hive_dw.hql
-- CSV랑 Parquet 테이블 둘다 만들어서 속도비교 해볼려고

CREATE DATABASE IF NOT EXISTS movielens;
USE movielens;

-- 1. CSV 테이블 생성
CREATE EXTERNAL TABLE IF NOT EXISTS ratings_csv (
    userId INT,
    movieId INT,
    rating FLOAT,
    timestamp BIGINT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/ratings_csv'
TBLPROPERTIES("skip.header.line.count"="1");

-- 2. Parquet 테이블 생성
CREATE TABLE IF NOT EXISTS ratings_parquet (
    userId INT,
    movieId INT,
    rating FLOAT,
    timestamp BIGINT
)
STORED AS PARQUET;

-- 3. CSV -> Parquet 변환해서 넣기
INSERT OVERWRITE TABLE ratings_parquet
SELECT * FROM ratings_csv;

-- 4. 아래 쿼리로 속도차이 직접 비교해봄
-- [테스트 1] 전체 데이터 카운트
-- CSV:
-- SELECT COUNT(*) FROM ratings_csv;
-- Parquet:
-- SELECT COUNT(*) FROM ratings_parquet;

-- [테스트 2] 영화별 평균 평점 계산 (Top 10)
-- CSV:
-- SELECT movieId, AVG(rating) as avg_rating FROM ratings_csv GROUP BY movieId ORDER BY avg_rating DESC LIMIT 10;
-- Parquet:
-- SELECT movieId, AVG(rating) as avg_rating FROM ratings_parquet GROUP BY movieId ORDER BY avg_rating DESC LIMIT 10;
