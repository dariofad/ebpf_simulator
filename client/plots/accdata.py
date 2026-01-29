import redis
import csv
import sys

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
ZSET_KEY = 'simulation:0'

signals = {
    "TIME": 0,
    "DREL": 1,
    "AEGO": 2,
    "VEGO": 3,
    "VREL": 4,
    "DLEAD": 5,
    "APOS": 6,    
}

if len(sys.argv) > 1:
    fname = sys.argv[1]
    print(f"fname: {fname}")
else:
    print("You must provide the name of the csv file to save the data")

with open(fname, mode='w+', newline='') as file:
    writer = csv.writer(file)
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
        print(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        all_records = r.zrange(ZSET_KEY, 0, -1, withscores=True)
        trajectory = []
        phi = []
        ow_drel = []
        real_drel = []
        i = 0
        writer.writerow(["cycle", "real_drel", "ow_drel", "phi"])
        for member, _ in all_records:
            record = list(map(float, member.split(",")))
            trajectory.append(record)
            ow_drel.append(record[signals["DREL"]])                
            real_drel.append(record[signals["DLEAD"]] - (record[signals["APOS"]] +10))
            phi.append(real_drel[-1] - 1.4 * record[signals["VEGO"]])
            writer.writerow([i, real_drel[i], ow_drel[i], phi[i]])
            i += 1
            
    except redis.exceptions.ConnectionError as e:
        print(f"Error connecting to Redis: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'r' in locals():
            r.close()
            print("\nRedis connection closed.")
