"""
ViewTurbo 自动签到脚本
每隔 20 秒自动签到一次，自动登录刷新 token
"""

import hashlib
import json
import random
import time
import logging
from datetime import datetime
from pathlib import Path

import requests

# ============ 配置 ============
EMAIL = "49399316@qq.com"
PASSWORD = "iamagod"
RANDOM_INTERVALS = [15, 26]  # 随机签到间隔（秒）
API_BASE = "https://api.viewturbo.com"
# ==============================

# 日志配置
log_file = Path(__file__).parent / "checkin.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def login() -> str:
    """登录获取 token"""
    url = f"{API_BASE}/appuser/reglogin?platform=web&cur_version=0.0.0&lang=hk"
    payload = {"email": EMAIL, "password": md5(PASSWORD)}
    resp = requests.post(url, json=payload, timeout=15)
    data = resp.json()
    if data.get("code") == 0:
        token = data["data"]["token"]
        log.info("登录成功, token: %s...%s", token[:6], token[-4:])
        return token
    else:
        raise Exception(f"登录失败: {data.get('msg')}")


def checkin(token: str) -> dict:
    """执行签到"""
    url = (
        f"{API_BASE}/appuser/checkin"
        f"?platform=web&cur_version=0.0.0&token={token}"
        f"&deviceinfo=&lang=hk&code=Others"
    )
    resp = requests.post(url, timeout=15)
    return resp.json()


def main():
    log.info("=" * 50)
    log.info("ViewTurbo 自动签到启动 (随机间隔 %s 秒)", RANDOM_INTERVALS)
    log.info("=" * 50)

    token = None

    while True:
        try:
            # 确保 token 有效
            if not token:
                token = login()

            # 执行签到
            result = checkin(token)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if result.get("code") == 0:
                d = result.get("data", {})
                log.info(
                    "[%s] 签到成功! 连续 %d 天, 奖励: %s",
                    now,
                    d.get("consecutive", 0),
                    d.get("reward_display", "unknown"),
                )
            elif result.get("code") == 7:
                # token 过期，重新登录
                log.warning("[%s] Token 过期，重新登录...", now)
                token = login()
                # 用新 token 重试签到
                result = checkin(token)
                if result.get("code") == 0:
                    d = result.get("data", {})
                    log.info(
                        "[%s] 签到成功! 连续 %d 天, 奖励: %s",
                        now,
                        d.get("consecutive", 0),
                        d.get("reward_display", "unknown"),
                    )
                else:
                    log.warning("[%s] 重试签到返回: %s", now, result.get("msg"))
            else:
                log.warning("[%s] 签到返回异常: %s", now, json.dumps(result, ensure_ascii=False))

        except requests.exceptions.RequestException as e:
            log.error("网络错误: %s", e)
        except Exception as e:
            log.error("发生错误: %s", e)

        # 随机等待下次签到
        interval = random.choice(RANDOM_INTERVALS)
        log.info("下次签到将在 %d 秒后", interval)
        time.sleep(interval)


if __name__ == "__main__":
    main()
