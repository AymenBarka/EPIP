# Cache Policy

| Policy | Limit | Eviction order |
| --- | --- | --- |
| LRU | Required | Least recently accessed |
| FIFO | Required | Earliest insertion |
| Fixed Size | Required | Earliest insertion |
| Ring Buffer | Required | Earliest insertion |
| Time Window | Required duration | Explicit logical timestamp |
| Manual | Caller controlled | Explicit clear |
| Disabled | Zero retained | No insertion |
| Unbounded | None | No automatic eviction |

Bounded policies validate a strictly positive maximum. Automatic cleanup runs
on insertion; manual cleanup never runs implicitly.
