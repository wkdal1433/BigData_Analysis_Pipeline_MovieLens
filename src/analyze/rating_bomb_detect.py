# -*- coding: utf-8 -*-
# 실제 MovieLens 20M 이상치 탐지 (2종): (A) 영화 평점 급락 버스트, (B) 유저 하루 도배
import pandas as pd, os
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

df = pd.read_csv(os.path.join(ml, "ratings.csv"))
df["day"] = (df["timestamp"] // 86400).astype("int32")
movies = pd.read_csv(os.path.join(ml, "movies.csv"))
print("rows:", len(df))

# ===== (A) 영화 평점 급락 버스트 =====
mv = df.groupby("movieId")["rating"].agg(movie_avg="mean", movie_cnt="count")
daily = df.groupby(["movieId", "day"])["rating"].agg(cnt="count", day_avg="mean").reset_index()
daily = daily.merge(mv, on="movieId")
daily["deviation"] = daily["movie_avg"] - daily["day_avg"]   # 평소보다 낮은 폭
daily["share"] = daily["cnt"] / daily["movie_cnt"]

# 평소 평점이 양호(>=3.3)한 영화가, 하루 30건+ 평점을 받았는데 그날만 크게 낮은 경우
A = daily[(daily["cnt"] >= 30) & (daily["movie_avg"] >= 3.3) & (daily["deviation"] >= 0.8)].copy()
A = A.merge(movies[["movieId", "title"]], on="movieId")
A["date"] = pd.to_datetime(A["day"] * 86400, unit="s").dt.date
A["score"] = A["cnt"] * A["deviation"]
A = A.sort_values("score", ascending=False)
print("\n[A. 영화 평점 급락 버스트 후보] (cnt>=30, movie_avg>=3.3, dev>=0.8) :", len(A), "건")
print(A[["title", "date", "cnt", "day_avg", "movie_avg", "deviation", "share"]].head(12).round(3).to_string(index=False))

# ===== (B) 유저 하루 도배(봇/매크로 의심) =====
ud = df.groupby(["userId", "day"]).size().reset_index(name="cnt")
topu = ud.sort_values("cnt", ascending=False).head(12)
print("\n[B. 유저 하루 평점 도배 후보] (한 유저가 하루에 매긴 평점 수 상위)")
print(topu.assign(date=pd.to_datetime(topu["day"] * 86400, unit="s").dt.date)[["userId", "date", "cnt"]].to_string(index=False))
print("  - 전체 유저 하루 평점수: 중앙값=%.0f, 95%%=%.0f, 99%%=%.0f, 최대=%d"
      % (ud["cnt"].median(), ud["cnt"].quantile(0.95), ud["cnt"].quantile(0.99), ud["cnt"].max()))

# ===== 그래프: A 최상위 후보의 일별 타임라인 =====
if len(A) > 0:
    top_id = int(A.iloc[0]["movieId"])
    top_title = A.iloc[0]["title"]
    s = df[df["movieId"] == top_id].groupby("day")["rating"].agg(cnt="count", avg="mean")
    s.index = pd.to_datetime(s.index * 86400, unit="s")
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.bar(s.index, s["cnt"], width=15, color="#C44E52", alpha=0.65, label="일별 평점 수")
    ax1.set_ylabel("일별 평점 건수", color="#C44E52")
    ax2 = ax1.twinx()
    ax2.plot(s.index, s["avg"], color="#4C72B0", marker=".", ms=3, lw=0.8)
    ax2.set_ylabel("일별 평균 평점", color="#4C72B0"); ax2.set_ylim(0.5, 5.0)
    plt.title("평점 급락 버스트 의심: %s" % top_title)
    fig.tight_layout(); fig.savefig(os.path.join(outdir, "rating_bomb_candidate.png"), dpi=120); plt.close()
    print("\nSaved rating_bomb_candidate.png (movieId=%d, '%s')" % (top_id, top_title))
