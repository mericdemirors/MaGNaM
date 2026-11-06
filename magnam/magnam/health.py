from django.http import JsonResponse


def ping_check(request):
    return JsonResponse({"status": "ok"})
