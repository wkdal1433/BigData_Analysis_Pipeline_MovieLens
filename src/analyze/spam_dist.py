# -*- coding: utf-8 -*-
# 유저 하루 평점수 분포: 대부분 1~2건 vs 극단치 2,456건/일 (도배 의심)
import pandas as pd, numpy as np, os
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

df = pd.read_csv(os.path.join(ml, "ratings.csv"), usecols=["userId", "timestamp"])
df["day"] = (df["timestamp"] // 86400).astype("int32")
ud = df.groupby(["userId", "day"]).size().values

med = np.median(ud); p99 = np.percentile(ud, 99); mx = ud.max()
print("median=%.0f  p99=%.0f  max=%d  (총 user-day=%d)" % (med, p99, mx, len(ud)))

# 로그 스케일 히스토그램 (분포의 무거운 꼬리를 보여줌)
bins = np.logspace(0, np.log10(mx), 50)
plt.figure(figsize=(10, 5))
plt.hist(ud, bins=bins, color="#55A868", edgecolor="white", linewidth=0.3)
plt.xscale("log"); plt.yscale("log")
plt.xlabel("유저가 하루에 매긴 평점 수 (로그)")
plt.ylabel("해당 (유저,일) 건수 (로그)")
plt.title("유저 하루 평점수 분포 — 대부분 1~2건, 극단치 %d건/일" % int(mx))

refs = [(med, "중앙값 %d건" % int(med), "#333333"),
        (p99, "99백분위 %d건" % int(p99), "#DD8452"),
        (mx, "최대 %d건 (도배 의심)" % int(mx), "#C44E52")]
ymax = plt.ylim()[1]
for v, lab, col in refs:
    plt.axvline(v, color=col, ls="--", lw=1.2)
    plt.text(v, ymax * 0.5, " " + lab, rotation=90, va="top", color=col, fontsize=9)

plt.tight_layout()
out = os.path.join(outdir, "user_daily_spam_dist.png")
plt.savefig(out, dpi=120); plt.close()
print("saved:", out)
