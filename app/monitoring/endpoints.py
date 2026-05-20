from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from .models import api_metrics

router = APIRouter(tags=["Monitoring"])


@router.get("/health", summary="Health check")
async def health_check():
    """Проверка здоровья приложения"""
    return {
        "status": "healthy",
        "service": "1CRoutingAPI"
    }


@router.get("/metrics", summary="Метрики API")
async def get_metrics():
    """Получение метрик производительности API"""
    return api_metrics.get_metrics()


# @router.get("/dashboard", response_class=HTMLResponse, summary="Dashboard мониторинга")
# async def metrics_dashboard():
#     """HTML дашборд для мониторинга в реальном времени"""

#     metrics = api_metrics.get_metrics()

#     html_content = f"""
# <!DOCTYPE html>
# <html lang="ru">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>1CRoutingAPI - Мониторинг</title>
#     <style>
#         * {{
#             margin: 0;
#             padding: 0;
#             box-sizing: border-box;
#         }}

#         body {{
#             font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
#             background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#             min-height: 100vh;
#             padding: 20px;
#         }}

#         .container {{
#             max-width: 1200px;
#             margin: 0 auto;
#         }}

#         .header {{
#             text-align: center;
#             color: white;
#             margin-bottom: 30px;
#         }}

#         .header h1 {{
#             font-size: 2.5rem;
#             margin-bottom: 10px;
#             text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
#         }}

#         .header p {{
#             font-size: 1.1rem;
#             opacity: 0.9;
#         }}

#         .dashboard {{
#             display: flex;
#             flex-direction: column;
#             gap: 20px;
#             margin-bottom: 30px;
#         }}

#         .card {{
#             width: 100%;
#             background: white;
#             border-radius: 15px;
#             padding: 25px;
#             box-shadow: 0 10px 30px rgba(0,0,0,0.2);
#             transition: transform 0.3s ease;
#         }}

#         .card:hover {{
#             transform: translateY(-5px);
#         }}

#         .card h2 {{
#             color: #333;
#             margin-bottom: 15px;
#             font-size: 1.3rem;
#             border-bottom: 2px solid #667eea;
#             padding-bottom: 10px;
#         }}

#         .metric {{
#             display: flex;
#             justify-content: between;
#             align-items: center;
#             margin-bottom: 12px;
#             padding: 10px;
#             background: #f8f9fa;
#             border-radius: 8px;
#         }}

#         .metric-label {{
#             font-weight: 600;
#             color: #555;
#             flex: 1;
#         }}
#         .kaifariki {{
#             display: flex;
#             gap: 20px;
#             width: 100%;
#             justify-content: space-between;
#         }}
#         .metric-value {{
#             font-weight: bold;
#             color: #667eea;
#             font-size: 1.1rem;
#         }}

#         .success {{
#             color: #28a745 !important;
#         }}

#         .warning {{
#             color: #ffc107 !important;
#         }}

#         .danger {{
#             color: #dc3545 !important;
#         }}

#         .endpoint-list {{
#             max-height: 400px;
#             overflow-y: auto;
#         }}

#         .endpoint-item {{
#             background: #f8f9fa;
#             margin-bottom: 8px;
#             padding: 12px;
#             border-radius: 8px;
#             border-left: 4px solid #667eea;
#         }}

#         .endpoint-method {{
#             display: inline-block;
#             background: #667eea;
#             color: white;
#             padding: 2px 8px;
#             border-radius: 4px;
#             font-size: 0.8rem;
#             margin-right: 10px;
#         }}

#         .refresh-btn {{
#             background: #fff;
#             color: #667eea;
#             border: none;
#             padding: 12px 24px;
#             border-radius: 25px;
#             font-size: 1rem;
#             font-weight: 600;
#             cursor: pointer;
#             transition: all 0.3s ease;
#             box-shadow: 0 4px 15px rgba(0,0,0,0.2);
#         }}

#         .refresh-btn:hover {{
#             background: #667eea;
#             color: white;
#             transform: translateY(-2px);
#         }}

#         .footer {{
#             text-align: center;
#             color: white;
#             margin-top: 30px;
#             opacity: 0.8;
#         }}
#     </style>
# </head>
# <body>
# <div class="container">
#     <div class="header">
#         <h1>🚀 1CRoutingAPI Мониторинг</h1>
#         <p>Дашборд в реальном времени</p>
#     </div>

#     <div class="dashboard">

#         <div class="kaifariki">
#             <!-- Карточка общей статистики -->
#             <div class="card">
#                 <h2>📊 Общая статистика</h2>
#                 <div class="metric">
#                     <span class="metric-label">Аптайм:</span>
#                     <span class="metric-value">{metrics['uptime_seconds']} сек</span>
#                 </div>
#                 <div class="metric">
#                     <span class="metric-label">Всего запросов:</span>
#                     <span class="metric-value">{metrics['total_requests']}</span>
#                 </div>
#                 <div class="metric">
#                     <span class="metric-label">Ошибки:</span>
#                     <span class="metric-value danger">{metrics['error_requests']}</span>
#                 </div>
#                 <div class="metric">
#                     <span class="metric-label">Успешность:</span>
#                     <span class="metric-value success">{metrics['success_rate']}%</span>
#                 </div>
#             </div>

#             <!-- Карточка времени ответа -->
#             <div class="card">
#                 <h2>⏱️ Время ответа</h2>
#                 <div class="metric">
#                     <span class="metric-label">Среднее:</span>
#                     <span class="metric-value">{metrics['response_time']['avg_seconds']} сек</span>
#                 </div>
#                 <div class="metric">
#                     <span class="metric-label">P95:</span>
#                     <span class="metric-value">{metrics['response_time']['p95_seconds']} сек</span>
#                 </div>
#                 <div class="metric">
#                     <span class="metric-label">P99:</span>
#                     <span class="metric-value">{metrics['response_time']['p99_seconds']} сек</span>
#                 </div>
#             </div>
#         </div>
#         <!-- Карточка эндпоинтов -->
#         <div class="card">
#             <h2>🔗 Эндпоинты</h2>
#             <div class="endpoint-list">
#                 {"".join([
#                 f'''
#                 <div class="endpoint-item">
#                     <span class="endpoint-method">{endpoint.split(' ')[0]}</span>
#                     <strong>{endpoint.split(' ')[1]}</strong>
#                     <div style="margin-top: 5px; font-size: 0.9rem;">
#                         📈 {stats['total_requests']} запросов |
#                         ⏱️ {stats['avg_response_time']} сек |
#                         ❌ {stats['error_rate']}% ошибок
#                     </div>
#                 </div>
#                 '''
#                 # Сортируем эндпоинты по количеству запросов (от большего к меньшему)
#                 for endpoint, stats in sorted(
#                     metrics['endpoints'].items(), 
#                     key=lambda x: x[1]['total_requests'], 
#                     reverse=True
#                 )
#                 ]) if metrics['endpoints'] else '<p>Нет данных об эндпоинтах</p>'}
#             </div>
#         </div>
#     </div>
#     <div style="text-align: center;">
#         <button class="refresh-btn" onclick="location.reload()">🔄 Обновить дашборд</button>
#     </div>

#     <div class="footer">
#         <p>1CRoutingAPI Monitoring Dashboard | Обновлено: <span id="timestamp">{__import__('datetime').datetime.now().strftime('%H:%M:%S')}</span></p>
#     </div>
# </div>

# //
# <script>
#     //    // Авто-обновление каждые 10 секунд
#     //    setTimeout(() => {{
#     //        location.reload();
#     //    }}, 10000);
#     //
#     //    // Обновление времени
#     //    function updateTimestamp() {{
#     //        const now = new Date();
#     //        document.getElementById('timestamp').textContent =
#     //            now.getHours().toString().padStart(2, '0') + ':' +
#     //            now.getMinutes().toString().padStart(2, '0') + ':' +
#     //            now.getSeconds().toString().padStart(2, '0');
#     //    }}
#     //    setInterval(updateTimestamp, 1000);
#     //
# </script>
# </body>
# </html>
#     """

#     return HTMLResponse(content=html_content)