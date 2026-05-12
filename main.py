import asyncio
import json
import os
import re
import logging

import asyncssh
import httpx
from dotenv import load_dotenv

load_dotenv()

# ── 配置 ──────────────────────────────────────────────────────────────────────
API_URL = os.environ["API_URL"]
API_USER = os.environ["API_USER"]
API_PASS = os.environ["API_PASS"]

SSH_HOST = os.environ["SSH_HOST"]
SSH_USER = os.environ["SSH_USER"]
SSH_PASS = os.environ["SSH_PASS"]
SSH_CONNECT_TIMEOUT = 10  # 秒

VERSION_FILE = "/home/zheshi/Documents/z_lift/src/_version.py"
MITSUBISHI_PATTERN = re.compile(r'__version__\s*=\s*"(0\.5\.\d+)"')

MAX_CONCURRENT = 50  # 最大并发 SSH 连接数

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


# ── 获取设备列表 ──────────────────────────────────────────────────────────────
async def fetch_device_list() -> list[dict]:
    """通过 HTTP API 获取代理设备列表，返回 [{name, remote_port, status}, ...]"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(API_URL, auth=(API_USER, API_PASS), timeout=30)
        resp.raise_for_status()
    data = resp.json()
    devices = []
    for proxy in data.get("proxies", []):
        conf = proxy.get("conf")
        remote_port = conf.get("remote_port") if conf else None
        if remote_port is None:
            continue
        devices.append({
            "name": proxy.get("name", ""),
            "port": remote_port,
            "status": proxy.get("status", "unknown"),
        })
    log.info("从 API 获取到 %d 个有效设备", len(devices))
    return devices


# ── 单台设备 SSH 检查 ─────────────────────────────────────────────────────────
async def check_device(sem: asyncio.Semaphore, device: dict) -> dict | None:
    """
    SSH 连接设备，读取版本文件。
    如果版本匹配 0.5.*，返回设备信息；否则返回 None。
    """
    port = device["port"]
    name = device["name"]

    async with sem:
        try:
            async with asyncssh.connect(
                SSH_HOST,
                port=port,
                username=SSH_USER,
                password=SSH_PASS,
                known_hosts=None,
                connect_timeout=SSH_CONNECT_TIMEOUT,
            ) as conn:
                result = await asyncio.wait_for(
                    conn.run(f"cat {VERSION_FILE}", check=False),
                    timeout=SSH_CONNECT_TIMEOUT,
                )
                output = result.stdout.strip() if result.stdout else ""

                match = MITSUBISHI_PATTERN.search(output)
                if match:
                    version = match.group(1)
                    log.info("[三菱] %s (port=%d) version=%s", name, port, version)
                    return {
                        "name": name,
                        "port": port,
                        "version": version,
                    }
                else:
                    log.debug("[跳过] %s (port=%d) 版本不匹配: %s", name, port, output)
                    return None

        except Exception as exc:
            log.debug("[跳过] %s (port=%d) 连接/读取失败: %s", name, port, exc)
            return None


# ── 主流程 ────────────────────────────────────────────────────────────────────
async def main() -> str:
    devices = await fetch_device_list()

    sem = asyncio.Semaphore(MAX_CONCURRENT)
    tasks = [check_device(sem, d) for d in devices]
    results = await asyncio.gather(*tasks)

    mitsubishi_devices = [r for r in results if r is not None]
    mitsubishi_devices.sort(key=lambda d: d["port"])

    output = {
        "total_devices": len(devices),
        "mitsubishi_count": len(mitsubishi_devices),
        "mitsubishi_devices": mitsubishi_devices,
    }

    json_str = json.dumps(output, ensure_ascii=False, indent=2)
    print(json_str)
    return json_str


if __name__ == "__main__":
    asyncio.run(main())
