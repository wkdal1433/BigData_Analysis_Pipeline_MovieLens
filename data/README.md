# 데이터 디렉토리

프로젝트에서 사용하는 데이터셋 정보입니다.

## 데이터 출처

- **MovieLens 20M**: GroupLens에서 공개한 영화 평점 데이터셋
  - 다운로드: https://grouplens.org/datasets/movielens/20m/
- **TMDB API**: 영화 메타데이터 추가 수집 (장르, 인기도 등)
  - https://www.themoviedb.org/documentation/api

## 파일 구조

```
data/
├── ml-20m/          # 원본 데이터 (용량 때문에 gitignore 처리)
│   ├── ratings.csv
│   ├── movies.csv
│   └── links.csv
└── sample/          # 테스트용 샘플 (상위 1000줄)
    ├── ratings.csv
    └── movies.csv
```

## 주요 컬럼 정보

**ratings.csv**
- userId, movieId: 사용자/영화 식별자
- rating: 0.5 ~ 5.0 사이 별점
- timestamp: 유닉스 타임스탬프

**movies.csv**
- movieId, title: 영화 id랑 제목 (연도 포함)
- genres: 파이프(|)로 구분된 장르 목록

**links.csv**
- tmdbId: TMDB API 호출할 때 쓰는 id값
- imdbId: IMDB 식별자

---
*원본 ml-20m 폴더는 용량이 커서 직접 받아서 넣어야 함*
