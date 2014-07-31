import requests
import sys


def debug():
    url, *fields = sys.argv[1:]
    if fields == []:
        print("")
        print("Baseline Benchmark:")
        print("")
        benchmark(url)

    field_param = []
    for field in fields:
        field_param.append(field)
        print("")
        print(" With fields: %s" % (", ".join(field_param)))
        print("")
        benchmark(url, fields=field_param)


def benchmark(url, **kwargs):
    total_time = 0
    count = 40

    response = requests.get(url, params=kwargs).json()
    meta, results, debug = [response[x] for x in ['meta', 'results', 'debug']]

    if meta['count'] != len(results):
        print("Meta count != result length!")
        print("")

    connection = debug['connection']
    queries = connection['query']['list']

    print("Made %s queries" % (connection['query']['count']))
    print("Sorted by time:")
    print("")
    for query in sorted(queries, reverse=True, key=lambda x: float(x['time'])):
        sql = query['sql']
        if len(sql) >= 80:
            sql = sql[:80] + "..."
        print("  %s:   %s" % (query['time'], sql))
    print("")
    print("Prefetched Fields:")
    for field in debug['prefetch_fields']:
        print("  %s" % (field))
    for x in range(count):
        time = requests.get(url, params=kwargs).json().get(
            "debug")['time']['seconds']

        total_time += time
        sys.stdout.write(".")
        sys.stdout.flush()
    print("")
    print("Total time (s):  %s" % (total_time))
    print("Per request (s)  %s" % (total_time / count))
