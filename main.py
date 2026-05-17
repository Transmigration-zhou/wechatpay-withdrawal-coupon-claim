import os
import time
import zlib
import json
import secrets
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

BASE = "https://discount.wxpapp.wechatpay.cn"
QUERY_URL = f"{BASE}/txbbs-mall/coupon/querydailygiftcoupons"
CLAIM_URL = f"{BASE}/txbbs-mall/coupon/claimdailygiftcoupon"


def build_headers() -> dict:
    ms = int(time.time() * 1000)
    return {
        "X-Page": "pages/gift/index",
        "X-Track-Id": f"TA{secrets.token_hex(9).upper()}{ms}",
        "xweb_xhr": "1",
        "session-token": os.environ["SESSION_TOKEN"],
        "X-Module-Name": "mmpaytxbbsmp",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/132.0.0.0 Safari/537.36 "
            "MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI "
            "MiniProgramEnv/Mac MacWechat/WMPF "
            "MacWechat/3.8.7(0x13080712) "
            "UnifiedPCMacWechat(0xf2641702) XWEB/18788"
        ),
        "Content-Type": "application/json",
        "session-id": f"daily_reward-{ms}-{secrets.token_hex(5)}",
        "X-Appid": "wxdb3c0e388702f785",
        "Accept": "*/*",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://servicewechat.com/wxdb3c0e388702f785/185/page-frame.html",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }


def parse_response(resp: requests.Response) -> dict:
    """先尝试直接 JSON 解析；失败则做一次 raw deflate 再解析（应对服务端双层压缩）。"""
    try:
        return resp.json()
    except (json.JSONDecodeError, requests.exceptions.JSONDecodeError):
        inner = zlib.decompress(resp.content, -15)
        return json.loads(inner.decode("utf-8"))


def query_daily_gift() -> dict:
    resp = requests.get(QUERY_URL, headers=build_headers(), timeout=15)
    resp.raise_for_status()
    return parse_response(resp)


def claim_coupon(coupon_id: int, face_value: int, exposure_token: str) -> dict:
    payload = {
        "coupon_id": coupon_id,
        "daily_gift_type": "DGCT_PLATFORM",
        "expected_send_amount": face_value,
        "exposure_token": exposure_token,
    }
    resp = requests.post(CLAIM_URL, headers=build_headers(), json=payload, timeout=15)
    resp.raise_for_status()
    return parse_response(resp)


def main():
    logger.info("查询每日礼物券信息...")
    query = query_daily_gift()
    if query.get("errcode") != 0:
        logger.error("查询失败: errcode=%s msg=%s", query.get("errcode"), query.get("msg"))
        return

    data = query["data"]
    items = data.get("coupon_items", [])
    if not items:
        logger.warning("当前没有可领取的券")
        return

    item = items[0]
    info = item["coupon_info"]
    coupon_id = info["coupon_id"]
    face_value = info["face_value"]
    name = info.get("name", "")
    is_claimed = item.get("is_claimed", False)
    exposure_token = data.get("exposure_token", "")

    logger.info("券信息: %s coupon_id=%s face_value=%s", name, coupon_id, face_value)

    if is_claimed:
        logger.info("今日已领取，无需重复领取")
        return

    logger.info("开始领取，exposure_token=%s", exposure_token)
    result = claim_coupon(coupon_id, face_value, exposure_token)
    if result.get("errcode") == 0:
        logger.info("领券成功: %s", result)
    else:
        logger.warning("领券失败: errcode=%s msg=%s", result.get("errcode"), result.get("msg"))


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        logger.error("HTTP 错误: %s", e)
    except Exception as e:
        logger.error("未知错误: %s", e, exc_info=True)
