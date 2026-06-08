from kafka import KafkaProducer
import csv
import json
import time
import random
import os

def main():
    print("Starting Kafka Rating Generator...")
    
    # 여기서 에러나길래 api_version 명시해야됨
    producer = KafkaProducer(
        bootstrap_servers=['localhost:6667'],
        api_version=(0, 10, 2),
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    topic_name = 'movielens-ratings'
    csv_path = r'C:\Users\scspr\WorkSpace\for_school\BigData-Analysis-Pipeline-MovieLens\data\ml-20m\ratings.csv'
    
    # ratings.csv 로드해서 스트리밍 시뮬레이션용 샘플 추출
    samples = []
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # skip header
            for _ in range(5000):
                try:
                    row = next(reader)
                    uid = int(row[0])
                    mid = int(row[1])
                    r = float(row[2])
                    ts = int(row[3])
                    samples.append({
                        'userId': uid,
                        'movieId': mid,
                        'rating': r,
                        'timestamp': ts
                    })
                except StopIteration:
                    break
    else:
        print("Warning: ratings.csv not found. Using dummy data.")
        # 파일 없으면 일단 더미 데이터라도 넣어놔야 에러 안남
        samples = [{'userId': 1, 'movieId': 1, 'rating': 4.0, 'timestamp': int(time.time())}]
                
    count = 0
    abusing_movieId = 99999
    abusing_userIds = [99901, 99902, 99903, 99904, 99905]
    
    try:
        while True:
            # 가끔 어뷰징(별점 테러 및 도배) 트래픽 발생
            if count > 0 and count % 30 == 0:
                print(f"--- 어뷰징 트래픽 발생 (별점테러 및 도배) ---")
                
                # 1) 별점테러: 여러 유저가 특정 영화(99999)에 1.0점 부여 (5건)
                for uid in abusing_userIds:
                    producer.send(topic_name, value={
                        'userId': uid,
                        'movieId': abusing_movieId,
                        'rating': 1.0,
                        'timestamp': int(time.time())
                    })
                
                # 2) 도배: 동일 유저(99901)가 짧은 시간 내에 여러 평점 부여 (5건)
                for i in range(5):
                    producer.send(topic_name, value={
                        'userId': 99901,
                        'movieId': 1000 + i,
                        'rating': 3.0,
                        'timestamp': int(time.time())
                    })
                
            # 정상 트래픽
            data = random.choice(samples)
            data['timestamp'] = int(time.time())
            producer.send(topic_name, value=data)
            
            if count % 10 == 0:
                print(f"Sent {count} messages...")
            
            count += 1
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("Stopping generator...")
    finally:
        producer.close()

if __name__ == "__main__":
    main()
