# -*- coding: utf-8 -*-
# 실제 MovieLens 20M 으로 장르별/연도별 평점 분석 + 그래프 (진짜 데이터)
import pandas as pd, os, time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
try:
    plt.rcParams["font.family"] = "Malgun Gothic"
except Exception:
    pass
plt.rcParams["axes.unicode_minus"] = False

base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
ml = os.path.join(base, "data", "ml-20m")
outdir = os.path.join(base, "reports", "figures")
os.makedirs(outdir, exist_ok=True)

t = time.time()
ratings = pd.read_csv(os.path.join(ml, "ratings.csv"), usecols=["movieId", "rating"])
movies = pd.read_csv(os.path.join(ml, "movies.csv"))
print("loaded: ratings=%d, movies=%d (%.1fs)" % (len(ratings), len(movies), time.time()-t))

# 영화별 합계/건수로 먼저 축약 (메모리 절약, 정확)
per_movie = ratings.groupby("movieId")["rating"].agg(rsum="sum", rcnt="count").reset_index()

# 제목에서 개봉연도 추출
movies["year"] = movies["title"].str.extract(r"\((\d{4})\)").astype("float")

# ---------- 분석 1: 장르별 평균 평점 ----------
mm = per_movie.merge(movies[["movieId", "genres"]], on="movieId")
mm["genres"] = mm["genres"].str.split("|")
ex = mm.explode("genres")
ex = ex[ex["genres"] != "(no genres listed)"]
g = ex.groupby("genres").agg(rsum=("rsum", "sum"), rcnt=("rcnt", "sum"))
g["avg"] = g["rsum"] / g["rcnt"]
g = g.sort_values("avg", ascending=False)
print("\n[장르별 평균 평점 (rating 수 기준 가중)]")
print(g[["avg", "rcnt"]].round(3).to_string())

plt.figure(figsize=(9, 5))
plt.barh(g.index[::-1], g["avg"][::-1], color="#4C72B0")
plt.xlabel("평균 평점"); plt.title("장르별 평균 평점 (MovieLens 20M)")
plt.xlim(3.0, 4.0); plt.tight_layout()
plt.savefig(os.path.join(outdir, "genre_avg_rating.png"), dpi=120); plt.close()

# ---------- 분석 2: 개봉 연도별 평균 평점 추이 ----------
ym = per_movie.merge(movies[["movieId", "year"]], on="movieId").dropna(subset=["year"])
ym = ym[(ym["year"] >= 1920) & (ym["year"] <= 2015)]
yr = ym.groupby("year").agg(rsum=("rsum", "sum"), rcnt=("rcnt", "sum"))
yr["avg"] = yr["rsum"] / yr["rcnt"]
print("\n[연도별 평균 평점 - 10년 단위 요약]")
dec = yr.copy(); dec.index = (dec.index // 10 * 10).astype(int)
decade = dec.groupby(level=0).agg(rsum=("rsum", "sum"), rcnt=("rcnt", "sum"))
decade["avg"] = decade["rsum"] / decade["rcnt"]
print(decade[["avg", "rcnt"]].round(3).to_string())

plt.figure(figsize=(9, 5))
plt.plot(yr.index, yr["avg"], color="#C44E52")
plt.xlabel("개봉 연도"); plt.ylabel("평균 평점")
plt.title("개봉 연도별 평균 평점 추이 (MovieLens 20M)")
plt.grid(alpha=0.3); plt.tight_layout()
plt.savefig(os.path.join(outdir, "year_avg_rating.png"), dpi=120); plt.close()

# ---------- 분석 3: 연도별 평가량(인기) ----------
plt.figure(figsize=(9, 5))
plt.bar(yr.index, yr["rcnt"], color="#55A868")
plt.xlabel("개봉 연도"); plt.ylabel("평점 건수")
plt.title("개봉 연도별 누적 평점 건수 (MovieLens 20M)")
plt.tight_layout()
plt.savefig(os.path.join(outdir, "year_rating_volume.png"), dpi=120); plt.close()

print("\nSaved figures to:", outdir)
print(os.listdir(outdir))
