from __future__ import annotations
import uuid
from datetime import datetime, timedelta
import random
from app.database import (
    create_property, list_properties, delete_property,
    create_inquiry, get_inquiries, update_inquiry,
    get_property, update_property,
    create_call_record,
)
from app.database import _get_conn


# 6 typical scenarios for real estate vacancy inquiries
DEMO_PROPERTIES = [
    {
        "name": "グランメゾン東京南青山",
        "address": "東京都港区南青山3-8-40",
        "phone_number": "03-1234-5678",
        "email_address": "info@grandmaison-aoyama.example.com",
        "management_company": "青山住販株式会社",
        "property_url": "https://suumo.jp/chintai/g_maison_aoyama/",
        "scenario": "A",
        "description": "空室あり・外国人OK",
    },
    {
        "name": "サンシティ恵比寿",
        "address": "東京都渋谷区恵比寿2-15-8",
        "phone_number": "03-2345-6789",
        "email_address": "ebisu@suncity-re.example.com",
        "management_company": "恵比寿不動産管理",
        "property_url": "https://suumo.jp/chintai/suncity_ebisu/",
        "scenario": "B",
        "description": "空室あり・外国人NG",
    },
    {
        "name": "パークハウス新宿",
        "address": "東京都新宿区西新宿6-12-1",
        "phone_number": "03-3456-7890",
        "email_address": "shinjuku@parkhouse.example.com",
        "management_company": "三井不動産レジデンシャル",
        "property_url": "https://suumo.jp/chintai/park_shinjuku/",
        "scenario": "C",
        "description": "空室なし（満室）",
    },
    {
        "name": "ロイヤルハイツ池袋",
        "address": "東京都豊島区南池袋1-22-5",
        "phone_number": "03-4567-8901",
        "email_address": "ikebukuro@royalhi.example.com",
        "management_company": "池袋管理サービス",
        "property_url": "https://homes.co.jp/chintai/royal_ikebukuro/",
        "scenario": "D",
        "description": "条件付き（保証会社必須・中国人不可）",
    },
    {
        "name": "コープ野村世田谷",
        "address": "東京都世田谷区三軒茶屋2-10-3",
        "phone_number": "03-5678-9012",
        "email_address": "",
        "management_company": "野村不動産パートナーズ",
        "property_url": "https://suumo.jp/chintai/coop_setagaya/",
        "scenario": "E",
        "description": "留守電・不通",
    },
    {
        "name": "メゾン・ド・上野",
        "address": "東京都台東区上野6-3-15",
        "phone_number": "03-6789-0123",
        "email_address": "ueno@maisond.example.com",
        "management_company": "上野ハウジング",
        "property_url": "https://athome.jp/chintai/maison_ueno/",
        "scenario": "F",
        "description": "曖昧回答（要確認）",
    },
    {
        "name": "ヴィラ代々木",
        "address": "東京都渋谷区代々木1-5-12",
        "phone_number": "03-7890-1234",
        "email_address": "yoyogi@villa-re.example.com",
        "management_company": "代々木不動産",
        "property_url": "https://suumo.jp/chintai/villa_yoyogi/",
        "scenario": "A2",
        "description": "空室あり・外国人OK・詳細条件付き",
    },
    {
        "name": "ハイツ練馬",
        "address": "東京都練馬区豊玉北5-8-2",
        "phone_number": "03-8901-2345",
        "email_address": "",
        "management_company": "練馬不動産管理",
        "property_url": "",
        "scenario": "C2",
        "description": "空室なし・次期入居可能",
    },
]


def _email_reply_body(scenario: str, prop_name: str, company: str) -> str:
    replies = {
        "A": f"""{company} ご担当者様

お問い合わせいただき、誠にありがとうございます。
「{prop_name}」の空室状況についてお知らせいたします。

現在、1部屋空室がございます。
・1K 52,000円/月
・外国人の方の入居も問題なく承っております。
・敷金1ヶ月、礼金1ヶ月
・入居可能時期：即入居可

ご不明な点がございましたら、お気軽にお問い合わせください。
よろしくお願いいたします。
""",
        "B": f"""{company} ご担当者様

お問い合わせありがとうございます。
「{prop_name}」につきまして、現在空室がございます。

1LDK 85,000円/月 が空室となっております。
ただし、誠に恐れ入りますが、当物件は日本国籍の方のみとしていただいております。
外国人の方の入居はお断りさせていただいております。

ご了承いただけますようお願い申し上げます。
""",
        "C": f"""{company} ご担当者様

お問い合わせいただきありがとうございます。
「{prop_name}」につきまして、現在満室となっております。

次の空室予定は未定ですが、キャンセル待ちが可能です。
キャンセルが出次第ご連絡いたしますが、よろしいでしょうか。

申し訳ございませんが、今しばらくお待ちいただけますと幸いです。
""",
        "D": f"""{company} ご担当者様

お問い合わせありがとうございます。
「{prop_name}」につきまして、現在2部屋空室がございます。

空室状況：
・1K 68,000円/月
・1LDK 95,000円/月

入居条件：
・保証会社（株式会社日本保証）の利用が必須となります（初回保証料：家賃の50%）
・外国人の方の入居は可能ですが、中国籍の方につきましては、現状お断りさせていただいております。その他の国籍の方は問題ございません。
・敷金1ヶ月、礼金なし
・入居可能時期：来月1日より

ご検討いただけますと幸いです。よろしくお願いいたします。
""",
        "F": f"""{company} ご担当者様

お問い合わせいただきありがとうございます。
「{prop_name}」の空室状況についてですが、現在確認しております。

しばらくお時間をいただけますでしょうか。
管理会社へ確認後、改めてご連絡させていただきます。

恐れ入りますが、2-3日ほどお待ちいただけますでしょうか。
""",
        "A2": f"""{company} ご担当者様

お問い合わせいただきありがとうございます。
「{prop_name}」につきまして、空室がございます。

空室状況：
・2LDK 120,000円/月（5階 South facing）
・外国人の方の入居も歓迎しております

入居条件：
・敷金2ヶ月、礼金1ヶ月
・保証会社利用可（任意）
・ペット不可
・駐車場別途15,000円/月
・入居可能時期：来月中旬以降

ご見学も可能ですので、ご希望の日時をお知らせください。
""",
        "C2": f"""{company} ご担当者様

お問い合わせありがとうございます。
「{prop_name}」は現在満室となっております。

次回の空室予定は3ヶ月後（7月末）を予定しております。
退去予定者の都合により変動する可能性がございます。

外国人の方の入居は可能です。ご興味がございましたら、
改めてお問い合わせいただけますと幸いです。
""",
    }
    return replies.get(scenario, replies["F"])


def _call_result(scenario: str) -> dict:
    results = {
        "A": {
            "vacancy_status": "空室あり（1K 52,000円）",
            "foreigner_accepted": "可",
            "chinese_accepted": "可",
            "special_conditions": "敷金1ヶ月、礼金1ヶ月、即入居可",
            "monthly_rent": "¥52,000",
            "move_in_date": "即入居可",
            "summary": "空室あり。外国人・中国人入居可能。1K 52,000円。敷礼金各1ヶ月。",
        },
        "B": {
            "vacancy_status": "空室あり（1LDK 85,000円）",
            "foreigner_accepted": "不可",
            "chinese_accepted": "不可",
            "special_conditions": "日本国籍の方のみ",
            "monthly_rent": "¥85,000",
            "move_in_date": "即入居可",
            "summary": "空室あり。外国人入居不可（日本国籍のみ）。1LDK 85,000円。",
        },
        "C": {
            "vacancy_status": "満室（空室なし）",
            "foreigner_accepted": "不明",
            "chinese_accepted": "不明",
            "special_conditions": "キャンセル待ち可能",
            "monthly_rent": "-",
            "move_in_date": "未定",
            "summary": "現在満室。次期空室予定なし。キャンセル待ち受付可。",
        },
        "D": {
            "vacancy_status": "空室あり（1K 68,000円 / 1LDK 95,000円）",
            "foreigner_accepted": "条件付き可",
            "chinese_accepted": "不可",
            "special_conditions": "保証会社必須（初回50%）、敷金1ヶ月、礼金なし",
            "monthly_rent": "¥68,000〜¥95,000",
            "move_in_date": "来月1日〜",
            "summary": "2部屋空室あり。外国人OKだが中国人不可。保証会社利用必須。",
        },
        "E": {
            "vacancy_status": "不明（不通）",
            "foreigner_accepted": "不明",
            "chinese_accepted": "不明",
            "special_conditions": "留守電対応",
            "monthly_rent": "-",
            "move_in_date": "-",
            "summary": "電話不通・留守電。再架電が必要。",
        },
        "F": {
            "vacancy_status": "確認中",
            "foreigner_accepted": "未確認",
            "chinese_accepted": "未確認",
            "special_conditions": "管理会社確認中、2-3日後に回答予定",
            "monthly_rent": "-",
            "move_in_date": "-",
            "summary": "回答曖昧。管理会社確認中。再確認が必要。",
        },
        "A2": {
            "vacancy_status": "空室あり（2LDK 120,000円）",
            "foreigner_accepted": "可",
            "chinese_accepted": "可",
            "special_conditions": "敷金2ヶ月、礼金1ヶ月、ペット不可、駐車場別途15,000円",
            "monthly_rent": "¥120,000",
            "move_in_date": "来月中旬以降",
            "summary": "2LDK空室あり。外国人歓迎。敷金2・礼金1。ペット不可。",
        },
        "C2": {
            "vacancy_status": "満室（3ヶ月後に空室予定）",
            "foreigner_accepted": "可",
            "chinese_accepted": "可",
            "special_conditions": "7月末に退去予定あり",
            "monthly_rent": "-",
            "move_in_date": "7月末〜",
            "summary": "現在満室。7月末に空室予定。外国人OK。",
        },
    }
    return results.get(scenario, results["F"])


def _call_transcript(scenario: str, prop_name: str) -> str:
    transcripts = {
        "A": f"""AI: お世話になっております。{prop_name}についてお伺いしたくお電話いたしました。現在、空室はございますでしょうか。
相手: はい、1部屋空いてますよ。
AI: ありがとうございます。外国人の方の入居は可能でしょうか。
相手: はい、問題ないですよ。
AI: 敷金や礼金の条件をお教えいただけますでしょうか。
相手: 敷金1ヶ月、礼金1ヶ月です。家賃は52,000円ですぐ入れます。
AI: 承知いたしました。本日はお忙しい中、ご対応いただき誠にありがとうございました。失礼いたします。
""",
        "D": f"""AI: お世話になっております。{prop_name}について空室確認のお電話です。空室はございますでしょうか。
相手: はい、2部屋空いてます。1Kが68,000円で1LDKが95,000円です。
AI: 外国人の方の入居は可能でしょうか。
相手: 外国人は基本OKですが、中国籍の方は申し訳ないですけどお断りしてます。
AI: 中国籍の方は不可とのこと、承知いたしました。入居条件についてお伺いしてもよろしいでしょうか。
相手: 保証会社の利用が必須です。日本保証ってところにお願いしてます。あと敷金1ヶ月で礼金はなし。来月1日から入れます。
AI: 承知いたしました。本日はお忙しい中、ご対応いただき誠にありがとうございました。失礼いたします。
""",
        "E": f"""AI: お世話になっております。{prop_name}についてお伺いしたくお電話いたしました。
（留守電：ピーっ）
AI: 空室確認のお電話でした。{prop_name}についてお伺いしたくお電話いたしました。またかけ直します。失礼いたします。
""",
    }
    return transcripts.get(scenario, "")


def seed_demo_data() -> dict:
    now = datetime.now()
    results = {"properties": 0, "emails": 0, "calls": 0}

    for i, dp in enumerate(DEMO_PROPERTIES):
        sent_at = (now - timedelta(days=random.randint(3, 14))).isoformat()
        prop = create_property({
            "name": dp["name"],
            "address": dp["address"],
            "phone_number": dp["phone_number"],
            "email_address": dp["email_address"],
            "management_company": dp["management_company"],
            "property_url": dp["property_url"],
        })
        results["properties"] += 1

        scenario = dp["scenario"]

        if dp["email_address"]:
            email_body = f"""
件名：{dp['name']}の空室確認について

{dp['management_company']} ご担当者様

お世話になっております。
{dp['name']}の空室状況についてお伺いいたします。

以下の点についてお教えいただけますでしょうか：
1. 現在空室はございますか
2. 外国人の方の入居は可能でしょうか
3. 特別な条件（敷金・礼金・保証会社等）はございますか

お忙しいところ恐縮ですが、ご返答いただけますと幸いです。
よろしくお願いいたします。
"""
            create_inquiry({
                "property_id": prop["id"],
                "type": "email",
                "status": "sent",
                "content": email_body,
                "sent_at": sent_at,
            })

            if scenario in ("A", "B", "C", "D", "F", "A2", "C2"):
                reply_body = _email_reply_body(scenario, dp["name"], dp["management_company"])
                replied_at = (now - timedelta(days=random.randint(1, 3))).isoformat()
                call_result = _call_result(scenario)
                create_inquiry({
                    "property_id": prop["id"],
                    "type": "email",
                    "status": "replied",
                    "content": email_body,
                    "response": reply_body,
                    "result_json": call_result,
                    "sent_at": sent_at,
                    "replied_at": replied_at,
                })
                update_property(prop["id"], {"status": "completed"})
                results["emails"] += 1

            elif scenario == "E":
                update_property(prop["id"], {"status": "email_sent"})
                results["emails"] += 1

        if scenario in ("A", "B", "D", "E", "A2"):
            call_sent_at = (now - timedelta(days=random.randint(0, 2))).isoformat()
            retell_call_id = f"demo_call_{uuid.uuid4().hex[:12]}"
            call_res = _call_result(scenario)

            create_inquiry({
                "property_id": prop["id"],
                "type": "call",
                "status": "completed" if scenario != "E" else "failed",
                "retell_call_id": retell_call_id,
                "response": _call_transcript(scenario, dp["name"]),
                "result_json": call_res,
                "sent_at": call_sent_at,
            })

            create_call_record({
                "property_id": prop["id"],
                "retell_call_id": retell_call_id,
                "call_status": "ended" if scenario != "E" else "failed",
                "duration_seconds": random.randint(60, 240) if scenario != "E" else 0,
                "transcript": _call_transcript(scenario, dp["name"]),
                "vacancy_status": call_res.get("vacancy_status", ""),
                "foreigner_accepted": call_res.get("foreigner_accepted", "") != "不可",
                "chinese_accepted": call_res.get("chinese_accepted", "") not in ("不可", "未確認"),
                "special_conditions": call_res.get("special_conditions", ""),
            })

            results["calls"] += 1

    return results


def clear_demo_data() -> int:
    conn = _get_conn()
    conn.execute("DELETE FROM template_blocks")
    conn.execute("DELETE FROM conversation_blocks WHERE is_system = 0")
    conn.execute("DELETE FROM conversation_templates")
    conn.execute("DELETE FROM inquiries")
    conn.execute("DELETE FROM call_records")
    conn.execute("DELETE FROM properties")
    conn.execute("DELETE FROM config WHERE key = 'default_template_id'")
    conn.commit()
    conn.close()
    return 0


def get_demo_stats() -> dict:
    props = list_properties()
    inquiries = get_inquiries()
    return {
        "properties": len(props),
        "inquiries": len(inquiries),
        "scenarios": {
            "completed": len([p for p in props if p["status"] == "completed"]),
            "email_sent": len([p for p in props if p["status"] == "email_sent"]),
            "calling": len([p for p in props if p["status"] == "calling"]),
            "pending": len([p for p in props if p["status"] == "pending"]),
            "failed": len([p for p in props if p["status"] == "failed"]),
        },
    }
