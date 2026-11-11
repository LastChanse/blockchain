import json
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings


@csrf_exempt
@require_POST
def sync_user(request):
    token = request.headers.get("X-Internal-Token", "")
    if token != settings.INTERNAL_SYNC_TOKEN:
        return JsonResponse({"error": "forbidden"}, status=403)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "bad json"}, status=400)

    username = (data.get("username") or "").strip()
    password_hash = data.get("password_hash") or ""
    if not username or not password_hash:
        return JsonResponse({"error": "username and password_hash required"}, status=400)

    user, created = User.objects.get_or_create(
        username=username,
        defaults={"password": password_hash},
    )
    if not created:
        # Обновляем хеш, если пользователь уже был (идемпотентность)
        user.password = password_hash
        user.save(update_fields=["password"])

    return JsonResponse({"ok": True, "created": created, "username": username})