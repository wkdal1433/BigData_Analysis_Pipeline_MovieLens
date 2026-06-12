# -*- coding: utf-8 -*-
# 실제 MovieLens 20M ratings.csv 로 CSV vs Parquet 용량/조회속도 진짜 측정
import pandas as pd, pyarrow.parquet as pq, os, time

repo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
base = os.path.join(repo, "data", "ml-20m")
csv = os.path.join(base, "ratings.csv")
pqf = os.path.join(base, "ratings.parquet")

csv_size = os.path.getsize(csv)
print("CSV size       : %.1f MB" % (csv_size/1e6))

t = time.time()
df = pd.read_csv(csv)
print("read_csv(full) : %.2fs, rows=%d, cols=%s" % (time.time()-t, len(df), list(df.columns)))

t = time.time()
df.to_parquet(pqf, engine="pyarrow", compression="snappy", index=False)
print("write parquet  : %.2fs" % (time.time()-t))

pq_size = os.path.getsize(pqf)
print("Parquet size   : %.1f MB" % (pq_size/1e6))
print("SIZE REDUCTION : %.1f%%" % ((1 - pq_size/csv_size)*100))
print("-"*40)

# 분석 쿼리: 영화별 평균 평점 Top-10 (집계). CSV=전체 reparse vs Parquet=컬럼 프로젝션
t = time.time()
d2 = pd.read_csv(csv, usecols=["movieId", "rating"])
_ = d2.groupby("movieId")["rating"].mean().sort_values(ascending=False).head(10)
csv_q = time.time()-t
print("CSV query      : %.2fs (read 2 cols + groupby)" % csv_q)

t = time.time()
d3 = pd.read_parquet(pqf, columns=["movieId", "rating"], engine="pyarrow")
top = d3.groupby("movieId")["rating"].mean().sort_values(ascending=False).head(10)
pq_q = time.time()-t
print("Parquet query  : %.2fs (columnar read + groupby)" % pq_q)
print("SPEEDUP        : %.1fx" % (csv_q/pq_q))
print("-"*40)
print("Top-10 movieId by avg rating (real):")
print(top.to_string())
