"""Fail-closed subscription and host admission, independent of model output."""

from datetime import datetime, timezone
import math
from pathlib import Path
import shutil
import subprocess
import sys
import json
import re
from zoneinfo import ZoneInfo

from .contracts import Rejected, parse


def utcnow():
    return datetime.now(timezone.utc)


def timestamp(value):
    if isinstance(value, bool):
        raise Rejected("INVALID_TIME")
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc)
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise Rejected("INVALID_TIME")
    return result


def quota_limit(config):
    policy = config.get("owner_quota_exception")
    if policy is None:
        return 35
    if (
        policy.get("scope") != "functional_poc"
        or policy.get("authorized_by") != "owner"
        or timestamp(policy["expires_at"]) <= utcnow()
    ):
        raise Rejected("QUOTA_EXCEPTION_INVALID_OR_EXPIRED")
    limit = policy.get("limit_percent")
    if type(limit) is not int or not 0 < limit <= 100:
        raise Rejected("QUOTA_EXCEPTION_INVALID")
    return limit


def check_quota(readings, now=None, required=("five_hour", "seven_day"), limit=35):
    now = now or utcnow()
    scopes = {r["scope"]: r for r in readings}
    evidence = []
    if not required:
        raise Rejected("QUOTA_POLICY_MISSING")
    for scope in required:
        if scope not in scopes:
            raise Rejected("QUOTA_MISSING_WINDOW")
        r = scopes[scope]
        percent = r.get("percent")
        if isinstance(percent, bool) or not isinstance(percent, (int, float)) or not math.isfinite(percent):
            raise Rejected("QUOTA_INVALID")
        if not 0 <= percent < limit:
            raise Rejected("QUOTA_THRESHOLD")
        age = (now - timestamp(r["observed_at"])).total_seconds()
        if not 0 <= age <= 300 or timestamp(r["resets_at"]) <= now:
            raise Rejected("QUOTA_STALE")
        evidence.append({k: r[k] for k in ("scope", "percent", "observed_at", "resets_at")})
    return evidence


def collect(command, limit=35):
    try:
        r = subprocess.run(command, capture_output=True, timeout=40, check=True)
        return check_quota(parse(r.stdout)["readings"], limit=limit)
    except Rejected:
        raise
    except (OSError, subprocess.SubprocessError, KeyError, ValueError, TypeError):
        raise Rejected("QUOTA_UNAVAILABLE") from None


def capacity(root, probe, *, integrating=True):
    now = utcnow()
    mem = dict(line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
    used = 1 - int(mem["MemAvailable"].split()[0]) / int(mem["MemTotal"].split()[0])
    disk = shutil.disk_usage(root)
    if disk.free / disk.total < 0.15:
        raise Rejected("HOST_DISK")
    if not probe:
        raise Rejected("GLOBAL_CAPACITY_UNKNOWN")
    try:
        r = subprocess.run(probe, capture_output=True, check=True, timeout=15)
        data = parse(r.stdout)
        if type(data.get("business_hours")) is not bool:
            raise Rejected("HOUSE_WINDOW_UNKNOWN")
        business = data["business_hours"]
        if used > (0.90 if business else 0.95):
            raise Rejected("HOST_MEMORY")
        if not 0 <= (utcnow() - timestamp(data["observed_at"])).total_seconds() <= 60:
            raise Rejected("CAPACITY_STALE")
        live = data["live_workers"]
        limit = data["worker_limit"]
        if type(live) is not int or type(limit) is not int or live < 0 or limit < 1:
            raise Rejected("GLOBAL_CAPACITY_INVALID")
        if integrating and live >= limit:
            raise Rejected("GLOBAL_CAPACITY_FULL")
    except Rejected:
        raise
    except (OSError, subprocess.SubprocessError, KeyError, ValueError, TypeError):
        raise Rejected("GLOBAL_CAPACITY_UNKNOWN") from None
    return {
        "observed_at": now.isoformat(),
        "memory_used": used,
        "disk_free_fraction": disk.free / disk.total,
        "live_workers": live,
        "worker_limit": limit,
        "admission_profile": "integrating_worker" if integrating else "tool_free_data_producer",
    }


def house_capacity(infra_root):
    """Read the canonical local window and Orca all-run accounting without prompts."""
    root = Path(infra_root)
    from .containment import control_env

    policy = json.loads((root / "config/esteira-janela.json").read_text())
    local = utcnow().astimezone(ZoneInfo(policy["fuso"]))
    holiday = any(h["data"] == local.date().isoformat() for h in policy["feriados"])
    business = (
        not holiday
        and local.isoweekday() in policy["dias_uteis"]
        and policy["inicio"] <= local.strftime("%H:%M") < policy["fim"]
    )
    if business:
        limit = policy["capacidade_comercial"]
    else:
        text = (root / "deploy/gitea-runner/docker-compose.yml").read_text()
        match = re.search(r"\$\{RUNNER_CAPACITY:-(\d+)\}", text)
        if not match:
            raise Rejected("HOUSE_WINDOW_UNKNOWN")
        limit = int(match[1])
    result = subprocess.run(
        ["orca-ide", "orchestration", "worker-list", "--json"], capture_output=True, check=True, timeout=15
    )
    data = parse(result.stdout, 1048576)["result"]
    if data["scope"]["source"] != "all":
        raise Rejected("CAPACITY_NOT_GLOBAL")
    live = data["counts"]["active"]
    units = subprocess.run(
        [
            "systemctl",
            "--user",
            "list-units",
            "ensemble-poc-*.service",
            "--state=running",
            "--no-legend",
            "--plain",
            "--no-pager",
        ],
        capture_output=True,
        check=True,
        timeout=10,
        env=control_env(),
    )
    # Count local POC units conservatively in addition to supervised Orca workers.
    live += len(units.stdout.splitlines())
    containers = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, check=True, timeout=10)
    return {
        "observed_at": utcnow().isoformat(),
        "live_workers": live,
        "worker_limit": limit,
        "live_task_containers": len(containers.stdout.splitlines()),
        "business_hours": business,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(house_capacity(sys.argv[1])))
    except Exception:
        print("CAPACITY_UNAVAILABLE", file=sys.stderr)
        raise SystemExit(1)
