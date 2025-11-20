import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from .models import api_metrics


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware для сбора метрик"""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Записываем метрики для успешных запросов
            api_metrics.record_request(
                method=request.method,
                endpoint=request.url.path,
                duration=duration,
                status_code=response.status_code
            )

            # Добавляем header с временем выполнения
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            return response

        except Exception as e:
            duration = time.time() - start_time
            # Записываем метрики для ошибок
            api_metrics.record_request(
                method=request.method,
                endpoint=request.url.path,
                duration=duration,
                status_code=500
            )
            raise e