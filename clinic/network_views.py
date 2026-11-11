import json

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from . import services
from .models import ChainBlock


def _check_token(request):
    return request.headers.get("X-Internal-Token", "") == settings.INTERNAL_SYNC_TOKEN


@require_GET
def network_height(request):
    if not _check_token(request):
        return JsonResponse({"error": "forbidden"}, status=403)
    return JsonResponse({
        "node_id": settings.NODE_ID,
        "height": services.local_height(),
        "last_hash": services.local_last_hash(),
    })


@csrf_exempt
@require_http_methods(["GET", "POST"])
def network_blocks(request):
    if not _check_token(request):
        return JsonResponse({"error": "forbidden"}, status=403)

    if request.method == "GET":
        try:
            from_index = int(request.GET.get("from", "0"))
        except ValueError:
            return JsonResponse({"error": "from must be integer"}, status=400)
        qs = ChainBlock.objects.filter(index__gte=from_index).order_by("index")
        blocks = [
            {
                "index": b.index,
                "prev_hash": b.prev_hash,
                "type": b.type,
                "timestamp": b.timestamp,
                "content_hash": b.content_hash,
                "payload": b.payload,
                "hash": b.hash,
            }
            for b in qs
        ]
        return JsonResponse({"blocks": blocks})

    # POST
    import json
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "bad json"}, status=400)

    ok, err = services.validate_incoming_block(data)
    if not ok:
        return JsonResponse({"ok": False, "error": err}, status=400)

    services.add_block_from_dict(data)
    return JsonResponse({"ok": True, "index": data["index"]})
