from __future__ import annotations
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.config_manager import load_config


def send_email(
    to_address: str,
    subject: str,
    body: str,
) -> bool:
    """Gmail SMTP経由でメールを送信する"""
    cfg = load_config()
    gmail_addr = cfg["gmail_address"]
    app_password = cfg["gmail_app_password"]

    if not gmail_addr or not app_password:
        raise ValueError("Gmail設定が未完了です。設定画面で入力してください。")

    msg = MIMEMultipart()
    msg["From"] = gmail_addr
    msg["To"] = to_address
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_addr, app_password)
        server.send_message(msg)

    return True


def generate_inquiry_email(
    property_name: str,
    management_company: Optional[str] = None,
) -> dict:
    """AIで問い合わせメールを生成する"""
    cfg = load_config()
    company = cfg.get("company_name", "〇〇不動産")
    person = cfg.get("contact_person", "担当者")

    mgmt = f"{management_company} " if management_company else ""

    subject = f"【空室確認】{property_name}についてのお問い合わせ（{company}）"

    body = f"""{mgmt}ご担当者様

お世話になっております。
{company}の{person}と申します。

{property_name}について、以下の点をお伺いしたくご連絡いたしました。

1. 現在、空室はございますでしょうか。
2. 外国籍の方（特に中国籍）の入居は可能でしょうか。
3. 入居にあたり特別な条件（敷金・礼金・保証会社の利用など）はございますでしょうか。
4. 月額賃料と入居可能時期をお教えいただけますでしょうか。

お忙しいところ恐縮ですが、ご返答いただけますと幸いです。
何かご不明な点がございましたら、お気軽にお問い合わせください。

よろしくお願い申し上げます。

{company}
{person}
"""

    return {"subject": subject, "body": body}
