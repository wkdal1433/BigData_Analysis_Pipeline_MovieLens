import urllib.request
import json
import time
import os

API_KEY = os.environ.get("TMDB_API_KEY", "")  # 환경변수로 주입 (공개 repo 키 노출 방지)

def fetch_tmdb_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    links_path = os.path.join(base_dir, 'data', 'ml-20m', 'links.csv')
    output_path = os.path.join(base_dir, 'data', 'tmdb_movies.json')
    
    if not os.path.exists(links_path):
        print(f"Error: Could not find {links_path}")
        return
        
    print("Starting TMDB data collection...")
    start_time = time.time()
    
    # 전체 다 돌리면 너무 오래걸려서 샘플만 수집
    max_collect = 200
    collected_count = 0
    
    with open(links_path, 'r', encoding='utf-8') as f, \
         open(output_path, 'w', encoding='utf-8') as out_f:
        
        header = f.readline() # skip header
        for line in f:
            if collected_count >= max_collect:
                break
                
            parts = line.strip().split(',')
            if len(parts) < 3 or not parts[2]: # check if tmdbId exists
                continue
                
            movie_id = parts[0]
            tmdb_id = parts[2]
            
            url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={API_KEY}&language=en-US"
            
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    data['ml_movieId'] = movie_id # 나중에 join할때 필요
                    out_f.write(json.dumps(data) + '\n')
                    
                    if collected_count % 10 == 0:
                        print(f"Collected {collected_count} movies... Elapsed: {time.time() - start_time:.2f}s")
                    
                    collected_count += 1
            except Exception as e:
                print(f"Error on tmdbId {tmdb_id}: {e}")
                
            time.sleep(0.25) # 429에러 방지용
            
    print(f"Finished collecting {collected_count} movies.")
    print(f"Total time elapsed: {time.time() - start_time:.2f} seconds.")

if __name__ == "__main__":
    fetch_tmdb_data()
