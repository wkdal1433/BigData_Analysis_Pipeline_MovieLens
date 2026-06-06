/* 
clean_data.pig
- 결측치 제거
- 평점 0.5 ~ 5.0 범위 검증
*/

-- ratings.csv 로드해서 필요한 컬럼만 뽑음
raw_data = LOAD '/user/hive/warehouse/ratings_csv' USING PigStorage(',') AS (userId:int, movieId:int, rating:float, timestamp:long);

-- 일단 userId null인거 먼저 제거
-- (movieId, rating null도 같이 처리)
filtered1 = FILTER raw_data BY userId IS NOT NULL AND movieId IS NOT NULL AND rating IS NOT NULL;

-- timestamp 컬럼 포함된 중간 결과 -- 나중에 필요할수도 있어서 남겨둠
temp_with_ts = FOREACH filtered1 GENERATE userId, movieId, rating, timestamp;

-- 평점 범위 맞는지 검사 (0.5 미만이나 5.0 초과는 이상한 데이터)
filtered2 = FILTER temp_with_ts BY rating >= 0.5 AND rating <= 5.0;

-- 필요한 컬럼만 남김
final_data = FOREACH filtered2 GENERATE userId, movieId, rating;

-- 결과 저장
STORE final_data INTO '/user/hive/warehouse/ratings_cleaned' USING PigStorage(',');
