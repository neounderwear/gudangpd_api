from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache

@never_cache
def health_check(request):
    """
    Health check endpoint for monitoring.
    Checks database connection and returns system status.
    """
    status = 200
    db_status = "healthy"
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        status = 503
    
    # Build response
    data = {
        "status": "healthy" if status == 200 else "unhealthy",
        "components": {
            "database": db_status
        },
        "version": "1.0.0"
    }
    
    return JsonResponse(data, status=status)