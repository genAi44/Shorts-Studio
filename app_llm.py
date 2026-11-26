"""LLM provider/router routes (/api/llm/*), split from app.py and registered there as a blueprint."""
from flask import Blueprint, jsonify, request

from app_helpers import body, err
from pipeline import llm_providers, llm_router

bp = Blueprint("llm", __name__)


@bp.get("/api/llm/providers")
def get_llm_providers():
    """قائمة المزوّدين المسجلين وحالتهم والنماذج المتاحة من كل مزوّد."""
    provs = llm_providers.get_all_providers()
    out = {}
    for pid, p in provs.items():
        out[pid] = {
            "id": p.id,
            "name": p.name,
            "configured": p.is_configured(),
            "supports_auto_mode": p.supports_auto_mode,
            "auto_mode_info": p.auto_mode_info(),
            "models": p.list_models(),
        }
    return jsonify(out)


@bp.get("/api/llm/health")
def get_llm_health():
    """فحص صحة اتصال واستجابة المزوّدين (Health Check)."""
    provs = llm_providers.get_all_providers()
    res = {}
    for pid, p in provs.items():
        res[pid] = p.health_check()
    return jsonify(res)


@bp.get("/api/llm/config")
def get_llm_config():
    """استرجاع إعدادات النماذج والأدوار الحالية."""
    router = llm_router.get_router()
    return jsonify({
        "roles": router.get_all_role_configs(),
        "available_roles": llm_router.ROLES,
    })


@bp.post("/api/llm/config")
def update_llm_config():
    """تحديث مزوّد ونموذج كل دور من واجهة المستخدم."""
    b = body()
    router = llm_router.get_router()
    if "roles" in b and isinstance(b["roles"], dict):
        for role, c in b["roles"].items():
            if isinstance(c, dict):
                router.update_role_config(
                    role=role,
                    provider=c.get("provider", "freellmapi"),
                    model=c.get("model"),
                    fallback_chain=c.get("fallback_chain"),
                )
    elif "role" in b:
        router.update_role_config(
            role=b["role"],
            provider=b.get("provider", "freellmapi"),
            model=b.get("model"),
            fallback_chain=b.get("fallback_chain"),
        )
    else:
        return err("بيانات الإعدادات غير صالحة.")
    return jsonify({"status": "updated", "roles": router.get_all_role_configs()})


@bp.get("/api/llm/logs")
def get_llm_logs():
    """سجل استدعاءات النماذج والتحويل الاحتياطي والتوكنز."""
    limit = int(request.args.get("limit", 50))
    router = llm_router.get_router()
    return jsonify({"logs": router.get_logs(limit)})


@bp.post("/api/llm/test-call")
def test_llm_call():
    """اختبار تجريبي فوري لمزوّد ونموذج محدد."""
    b = body()
    provider_id = b.get("provider", "freellmapi")
    model = b.get("model")
    prompt = b.get("prompt", "أجب كـ JSON فقط بمفتاح reply: {\"reply\": \"مرحباً، الاتصال ناجح!\"}")
    try:
        p = llm_providers.get_provider(provider_id)
        resp = p.complete(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.2,
            json_mode=True,
            timeout=30,
        )
        return jsonify({
            "status": "success",
            "content": resp.content,
            "provider": resp.provider,
            "model": resp.model,
            "usage": resp.usage.to_dict(),
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 502
