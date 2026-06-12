# MovieLens 20M & TMDB API 기반 다층적 영화 추천 및 평점 실시간 분석 파이프라인
> **2026-1 빅데이터 프로그래밍 기말 프로젝트 최종 보고서**
> **성함/학번:** 장준수 / 60201704

---

## 1. 프로젝트 개요 (Problem Definition)

본 프로젝트는 대규모 과거 데이터(Cold Data)를 기반으로 한 모델 학습과 실시간으로 유입되는 데이터(Hot Data)의 즉각적 반영을 목표로 하는 **람다 아키텍처(Lambda Architecture) 기반 통합 빅데이터 파이프라인 설계 및 검증**을 수행합니다. 

단순한 데이터 나열을 넘어, 실제 HDP Sandbox(구형 환경) 및 GCP VM 리소스 한계 속에서 발생할 수 있는 데이터 수집 제한(Rate Limit)과 버전 호환성 문제를 해결하며 프로젝트를 완수하고자 합니다.

### 핵심 분석 지표 (Metrics)
1. **저장 포맷 성능 비교**: 일반 CSV와 열 기반 Parquet 포맷의 디스크 용량 및 조회 쿼리 속도 비교
2. **장르별 평균 평점 추이**: 선호도에 따른 대중성(Horror/Comedy)과 매니아성(Film-Noir/War)의 차이 분석
3. **영화 개봉 연도별 평점 분포**: 구작 영화들의 평점 상향 분포와 특정 시기의 평가량 골짜기 형태 비교
4. **실시간 어뷰징 탐지**: 동일 영화에 대한 1점 테러 및 특정 유저의 무의미한 평점 도배 패턴 적발

---

## 2. 시스템 아키텍처 및 기술 스택 (Architecture)

| Layer | 사용 기술 | 수행 역할 (현실적 구현 전략) | 비고 |
| :--- | :--- | :--- | :--- |
| **Ingestion** | **Python (REST API)** | Rate Limit 처리 및 인기작 위주 데이터 수집 | API 호출 제한 우회 로직 포함 |
| **Storage** | **HDFS** | 대용량 CSV 및 정제된 API JSON 데이터 분산 저장 | HDP Sandbox 기반 |
| **Batch** | **Pig / Hive** | Regex SerDe를 활용한 데이터 정제 및 마스터 DW 구축 | 비정형 데이터 정규화 |
| **Serving** | **Spark (RDD & ML)** | RDD 기반 로직 검증 및 DataFrame 최적화 알고리즘 이식 | ALS 알고리즘 활용 |
| **Speed** | **Kafka + Spark Streaming** | 평점 데이터 유실 방지를 위한 12초 윈도우 기반 실시간 집계 | 고가용성 메시지 큐 구성 |

---

## 3. 세부 구현 계획 및 폴더 구조 (Implementation & Structure)

```text
BigData-Analysis-Pipeline-MovieLens/
├── README.md            
├── data/                # Sample data (Raw & Cleaned)
├── src/
│   ├── ingest/          # API Collector (w/ Rate Limit handling)
│   ├── pipeline/        # Hive Scripts, Pig Scripts, PySpark Code
│   └── analyze/         # RMSE Evaluator, Real-time Dashboard (Console)
└── infra/               # spark-submit shell scripts with dependency options
```

---

## 4. 실행 방법 (Execution Guide)

본 프로젝트의 소스코드를 실행하기 위해서는 HDP Sandbox(또는 그에 준하는 하둡 에코시스템) 및 Python 3 환경이 필요합니다.

### 4.1. 데이터 수집 (Ingestion)
윈도우 로컬 환경 또는 VM 환경에서 TMDB API를 통해 추가 메타데이터를 수집합니다.
```bash
python src/ingest/collect_tmdb.py
```
> 결과물은 `data/tmdb_movies.json` 에 적재됩니다.

### 4.2. 데이터 전처리 (Batch - Pig & Hive)
수집된 데이터와 HDFS에 적재된 `ratings.csv`를 정제하고, Hive 테이블로 변환합니다.
```bash
# 1. 결측치 제거 및 정제
pig src/pipeline/clean_data.pig

# 2. Hive DW 적재 및 포맷 성능 비교 (CSV vs Parquet)
hive -f src/pipeline/hive_dw.hql
```

### 4.3. 모델 학습 및 평가 (Serving - Spark ML)
정제된 데이터를 이용해 ALS 추천 모델을 학습하고 결과를 확인합니다.
```bash
# 모델 학습 및 추천 목록 생성
./infra/run_spark_als.sh

# 모델 성능 평가 (RMSE)
spark-submit src/analyze/evaluate_rmse.py
```

### 4.4. 실시간 스트리밍 분석 (Speed - Kafka & Spark Streaming)
Kafka로 실시간 평점 데이터를 전송하고, Spark Streaming으로 어뷰징 패턴(별점 테러)을 감지합니다.
```bash
# 1. 스트리밍 애플리케이션 실행 (터미널 1)
./infra/run_streaming.sh

# 2. 실시간 평점 시뮬레이션 및 트래픽 발생 (터미널 2)
python src/pipeline/rating_generator.py
```

---

## 5. 트러블슈팅 및 리스크 관리 (Risk Management)

- **버전 호환성 및 의존성 해결**: HDP 샌드박스의 Spark 버전과 Kafka 라이브러리 간 충돌을 방지하기 위해 전용 패키지(`org.apache.spark:spark-sql-kafka`) 명시적 로드.
- **메모리 리소스 최적화 (OOM 방지)**: GCP 리소스 한계를 고려하여 Executor 메모리를 제한하고, DataFrame 기반의 Catalyst Optimizer를 활용해 실행 계획 최적화.
- **데이터 멱등성(Idempotency) 보장**: 수집 중단 시 재시작 지점을 보장하기 위해 HDFS 기반의 체크포인트(상태 저장) 메커니즘 도입.
- **Backpressure 기반 유입량 조절**: 실시간 스트리밍 시 유입 속도가 처리 속도를 초과하지 않도록 자동 속도 조절 기능 활성화.

---

## 6. 부록: 생성형 AI 사용 내역 명시
- Claude: 로컬 환경(Windows) 제약에 따른 Parquet 디버깅(`src/analyze/bench_parquet.py`) 보조 및 분석 시각화 아이디어 제안
- Gemini: 정규식을 활용한 마크다운 내 텍스트 치환 스크립트 작성 보조 및 최종 보고서 문체 검수
