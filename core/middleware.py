import time
import logging

logger = logging.getLogger(__name__)

class RequestTimingMiddleware:
  def __int__(self, get_response):
    self.get_response = get_response

  def __call__(self, request):
    start = time.perf_counter()
    response = self.get_response(request)
    duration = time.perf_counter() - start

    if duration > 1.0:
      logger.warning(
        "SLOW REQUEST: %s %s → %dms (status=%d)",
        request.method,
        request.path,
        int(duration * 1000),
        response.status_code
      )
    response['X-Response-Time'] = f'{duration * 1000:.1f}ms'
    return response
