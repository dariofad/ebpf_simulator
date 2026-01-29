import redis
import csv
import sys

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
ZSET_KEY = 'simulation:0'

signals = {
    "TIME": 0,
    "PANGLE": 1,
    "AF": 2,
    "CMODE": 3,
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
        i = 0
        writer.writerow(["cycle", "pangle", "af", "cmode"])
        for member, _ in all_records:
            print(member)
            record = list(map(float, member.split(",")))
            record[0] = int(record[0])
            writer.writerow(record)
            i += 1
    except redis.exceptions.ConnectionError as e:
        print(f"Error connecting to Redis: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'r' in locals():
            r.close()
            print("\nRedis connection closed.")
