from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError

@api_view(['GET'])
def return_one(request):
    return Response({"result": 1})

@api_view(['GET'])
def return_two(request):
    return Response({"result": 2})

@api_view(['GET'])
def sum_numbers(request):
    # Get query parameters 'a' and 'b' from the request URL
    try:
        a = int(request.query_params.get('a', 0))
        b = int(request.query_params.get('b', 0))
        return Response({"result": a + b})
    except (ValueError, TypeError):
        return Response({"error": "Invalid or missing parameters. Please provide integers 'a' and 'b'."}, status=400)

def db_health_check(request):
    try:
        # Attempt to connect to the default database
        connection = connections['default']
        connection.ensure_connection()
        return JsonResponse({"status": "success", "message": "Database connection successful!"}, status=200)
    except OperationalError as e:
        return JsonResponse({"status": "error", "message": "Database connection failed!", "error": str(e)}, status=500)

def index(request):
    return render(request, 'api/index.html')
