import time
from typing import Dict, Any, List
from collections import defaultdict


class APIMetrics:
    """Класс для сбора и хранения метрик API"""

    def __init__(self):
        self._request_count = 0
        self._error_count = 0
        self._response_times: List[float] = []
        self._endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'errors': 0
        })
        self._start_time = time.time()

    def record_request(self, method: str, endpoint: str, duration: float, status_code: int) -> None:
        """Запись метрик для запроса"""
        self._request_count += 1
        self._response_times.append(duration)

        # Сохраняем только последние 1000 записей
        if len(self._response_times) > 1000:
            self._response_times.pop(0)

        # Статистика по эндпоинтам
        endpoint_key = f"{method} {endpoint}"
        stats = self._endpoint_stats[endpoint_key]
        stats['count'] += 1
        stats['total_time'] += duration

        if status_code >= 400:
            self._error_count += 1
            stats['errors'] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Получение агрегированных метрик"""
        if not self._response_times:
            avg_time = 0.0
            p95 = 0.0
            p99 = 0.0
        else:
            avg_time = sum(self._response_times) / len(self._response_times)
            sorted_times = sorted(self._response_times)
            p95 = self._calculate_percentile(sorted_times, 95)
            p99 = self._calculate_percentile(sorted_times, 99)

        # Статистика по эндпоинтам
        endpoint_metrics = {}
        for endpoint, stats in self._endpoint_stats.items():
            if stats['count'] > 0:
                endpoint_metrics[endpoint] = {
                    'total_requests': stats['count'],
                    'avg_response_time': round(stats['total_time'] / stats['count'], 3),
                    'errors': stats['errors'],
                    'error_rate': round((stats['errors'] / stats['count']) * 100, 2)
                }

        return {
            "uptime_seconds": round(time.time() - self._start_time, 2),
            "total_requests": self._request_count,
            "error_requests": self._error_count,
            "success_rate": round(
                ((self._request_count - self._error_count) / self._request_count * 100)
                if self._request_count > 0 else 100.0,
                2
            ),
            "response_time": {
                "avg_seconds": round(avg_time, 3),
                "p95_seconds": round(p95, 3),
                "p99_seconds": round(p99, 3)
            },
            "endpoints": endpoint_metrics
        }

    def _calculate_percentile(self, sorted_data: List[float], percentile: int) -> float:
        """Расчет перцентиля"""
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return (lower + upper) / 2


# Глобальный экземпляр метрик
api_metrics = APIMetrics()