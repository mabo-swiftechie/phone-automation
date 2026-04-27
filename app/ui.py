from __future__ import annotations
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import json
import csv
import io

from app.paths import ensure_data_dir
ensure_data_dir()

from app.database import (
    init_db,
    create_property,
    get_property,
    list_properties,
    update_property,
    delete_property,
    create_inquiry,
    get_inquiries,
    update_inquiry,
    get_config,
    set_config,
)
from app.config_manager import load_config, save_config, is_configured, DEFAULTS
from app.services.email_sender import send_email, generate_inquiry_email
from app.services.email_parser import parse_email_response
from app.services.retell import create_phone_call, create_web_call, get_call
from app.services.template_manager import (
    create_block, get_block, list_blocks, update_block, delete_block,
    create_template, get_template, list_templates, update_template, delete_template,
    set_template_blocks, get_template_blocks, generate_prompt,
    set_default_template, get_default_template, export_template, import_template,
    seed_default_template, BLOCK_TYPES, BLOCK_TYPE_LABELS,
)

st.set_page_config(page_title="AI電話自動化", page_icon="📞", layout="wide")

init_db()
seed_default_template()

if not is_configured():
    st.warning("API Keyが未設定です。設定タブから OpenAI API Key を入力してください。")

STATUS_LABEL = {
    "pending": "未対応", "email_sent": "メール送信済",
    "email_replied": "返信済", "calling": "通話中",
    "completed": "完了", "failed": "失敗",
}


def show_result(r):
    if not r or not isinstance(r, dict):
        return
    st.write(f"**空室状況**: {r.get('vacancy_status', '-')}")
    st.write(f"**外国人OK**: {r.get('foreigner_accepted', '-')}")
    st.write(f"**中国人OK**: {r.get('chinese_accepted', '-')}")
    st.write(f"**特別条件**: {r.get('special_conditions', '-')}")
    st.write(f"**月額賃料**: {r.get('monthly_rent', '-')}")
    st.write(f"**入居可能日**: {r.get('move_in_date', '-')}")
    st.write(f"**まとめ**: {r.get('summary', '-')}")


# ── サイドバー ──
tab = st.sidebar.radio(
    "メニュー",
    ["🏠 物件管理", "📧 メール確認", "📞 電話確認", "📊 結果一覧", "💬 会話テンプレート", "⚙️ 設定"],
)

st.title("AI電話自動化 — 空室確認")

# ═══════════════════════════════════════════════
# タブ1: 物件管理（一覧・追加・編集）
# ═══════════════════════════════════════════════
if tab == "🏠 物件管理":
    st.header("物件管理")

    # ── 新規登録 ──
    with st.expander("＋ 新規物件登録", expanded=False):
        with st.form("add_property"):
            c1, c2 = st.columns(2)
            with c1:
                p_name = st.text_input("物件名 *")
                p_address = st.text_input("住所")
                p_phone = st.text_input("電話番号")
            with c2:
                p_email = st.text_input("メールアドレス")
                p_company = st.text_input("管理会社名")
                p_url = st.text_input("物件URL")
            if st.form_submit_button("登録", type="primary"):
                if not p_name:
                    st.error("物件名は必須です")
                else:
                    create_property({
                        "name": p_name, "address": p_address,
                        "phone_number": p_phone, "email_address": p_email,
                        "management_company": p_company, "property_url": p_url,
                    })
                    st.success(f"登録完了: {p_name}")
                    st.rerun()

    # ── 物件一覧 ──
    properties = list_properties()
    if not properties:
        st.info("物件が登録されていません。上の「＋ 新規物件登録」から追加してください。")
    else:
        for p in properties:
            sl = STATUS_LABEL.get(p["status"], p["status"])
            with st.expander(f"[{sl}] {p['name']}"):
                with st.form(f"edit_{p['id']}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        e_name = st.text_input("物件名", value=p.get("name", ""), key=f"en_{p['id']}")
                        e_addr = st.text_input("住所", value=p.get("address", ""), key=f"ea_{p['id']}")
                        e_phone = st.text_input("電話番号", value=p.get("phone_number", ""), key=f"ep_{p['id']}")
                    with c2:
                        e_email = st.text_input("メール", value=p.get("email_address", ""), key=f"ee_{p['id']}")
                        e_comp = st.text_input("管理会社", value=p.get("management_company", ""), key=f"ec_{p['id']}")
                        e_url = st.text_input("物件URL", value=p.get("property_url", ""), key=f"eu_{p['id']}")
                    st.caption(f"登録日: {p['created_at'][:10]}  |  状態: {sl}")

                    c_save, c_del, c_reset = st.columns(3)
                    with c_save:
                        if st.form_submit_button("保存", type="primary"):
                            update_property(p["id"], {
                                "name": e_name, "address": e_addr,
                                "phone_number": e_phone, "email_address": e_email,
                                "management_company": e_comp, "property_url": e_url,
                            })
                            st.success("更新しました")
                            st.rerun()
                    with c_del:
                        if st.form_submit_button("削除"):
                            delete_property(p["id"])
                            st.rerun()
                    with c_reset:
                        if st.form_submit_button("状態リセット"):
                            update_property(p["id"], {"status": "pending"})
                            st.rerun()

# ═══════════════════════════════════════════════
# タブ2: メール確認（生成→送信→返信解析）
# ═══════════════════════════════════════════════
elif tab == "📧 メール確認":
    st.header("メール確認")

    properties = list_properties()
    emailable = [p for p in properties if p.get("email_address")]
    if not emailable:
        st.info("メールアドレスが登録された物件がありません。先に物件管理で登録してください。")
    else:
        opts = {f"{p['name']} ({p['email_address']})": p for p in emailable}
        sel = st.selectbox("物件を選択", list(opts.keys()))

        if sel:
            prop = opts[sel]
            st.write(f"**管理会社**: {prop.get('management_company', '-')}")

            # Step 1: メール生成
            if st.button("AIメール生成", type="primary"):
                email = generate_inquiry_email(prop["name"], prop.get("management_company"))
                st.session_state["email_subject"] = email["subject"]
                st.session_state["email_body"] = email["body"]

            # Step 2: 編集・送信
            if "email_subject" in st.session_state:
                subject = st.text_input("件名", value=st.session_state["email_subject"])
                body = st.text_area("本文", value=st.session_state["email_body"], height=300)
                if st.button("📧 送信する"):
                    try:
                        send_email(prop["email_address"], subject, body)
                        create_inquiry({
                            "property_id": prop["id"], "type": "email",
                            "status": "sent", "content": body,
                            "sent_at": datetime.now().isoformat(),
                        })
                        update_property(prop["id"], {"status": "email_sent"})
                        st.success(f"{prop['email_address']} に送信しました！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"送信エラー: {e}")

    # ── 返信登録・解析 ──
    st.divider()
    st.subheader("返信登録・AI解析")
    inquiries = get_inquiries()
    sent_emails = [i for i in inquiries if i["type"] == "email" and i["status"] == "sent"]

    if not sent_emails:
        st.info("送信済みメールがありません。")
    else:
        email_opts = {
            f"{i.get('content', '')[:40]}... ({i['sent_at'][:10]})": i for i in sent_emails
        }
        sel_email = st.selectbox("返信対象のメール", list(email_opts.keys()))
        if sel_email:
            inq = email_opts[sel_email]
            prop = get_property(inq["property_id"])
            reply_text = st.text_area("返信内容を貼り付け", height=200)
            if st.button("AI解析して保存") and reply_text:
                try:
                    result = parse_email_response(
                        inq.get("content", ""), reply_text,
                        prop["name"] if prop else "",
                    )
                    update_inquiry(inq["id"], {
                        "status": "replied", "response": reply_text,
                        "result_json": result, "replied_at": datetime.now().isoformat(),
                    })
                    update_property(inq["property_id"], {"status": "completed"})
                    st.success("解析完了！結果を保存しました")
                    show_result(result)
                except Exception as e:
                    st.error(f"解析エラー: {e}")

# ═══════════════════════════════════════════════
# タブ3: 電話確認（Web Call→通話→結果取得）
# ═══════════════════════════════════════════════
elif tab == "📞 電話確認":
    st.header("電話確認（Retell AI）")

    cfg = load_config()
    if not cfg.get("retell_api_key"):
        st.warning("設定画面でRetell AI API Keyを入力してください。")
    else:
        properties = list_properties()

        # ── 通話履歴 ──
        st.subheader("通話履歴")
        all_calls = []
        for p in properties:
            for i in get_inquiries(p["id"]):
                if i["type"] == "call":
                    all_calls.append({**i, "property_name": p["name"], "property_id": p["id"]})

        if all_calls:
            for ci in reversed(all_calls):
                result = ci.get("result_json")
                label = STATUS_LABEL.get(ci.get("status", ""), ci.get("status", ""))
                st.write(f"**[{label}]** {ci['property_name']} — {ci.get('sent_at', '')[:16]}")
                if result and isinstance(result, dict):
                    show_result(result)
                else:
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("結果を取得", key=f"fetch_{ci['id']}", type="primary"):
                            with st.spinner("Retell AIから取得中..."):
                                try:
                                    cd = get_call(ci["retell_call_id"])
                                    analysis = cd.get("call_analysis", {})
                                    custom = analysis.get("custom_analysis_data", {})
                                    cs = cd.get("call_status", "")
                                    if custom:
                                        update_inquiry(ci["id"], {
                                            "status": "completed" if cs == "ended" else cs,
                                            "result_json": custom,
                                            "response": analysis.get("call_summary", ""),
                                        })
                                        if cs == "ended":
                                            update_property(ci["property_id"], {"status": "completed"})
                                        st.success("結果を保存しました！")
                                        st.rerun()
                                    else:
                                        st.warning(f"通話状態: {cs} — 通話が終わっていないか結果がありません")
                                except Exception as e:
                                    st.error(f"エラー: {e}")
                    with c2:
                        if st.button("リセット", key=f"rst_{ci['id']}"):
                            update_property(ci["property_id"], {"status": "pending"})
                            st.rerun()
                st.divider()
        else:
            st.info("通話履歴がありません。")

        # ── 新規発信 ──
        st.divider()
        st.subheader("新規発信")
        callable_props = [p for p in properties if p["status"] in ("pending", "email_sent", "retry", "calling")]

        if not callable_props:
            st.info("発信可能な物件がありません。物件管理で登録してください。")
        else:
            opts = {p["name"]: p for p in callable_props}
            sel = st.selectbox("物件を選択", list(opts.keys()))

            if sel:
                prop = opts[sel]
                if prop.get("phone_number"):
                    st.write(f"**電話番号**: {prop['phone_number']}")

                if st.button("🌐 Web Call 開始", type="primary"):
                    with st.spinner("Retell AIに接続中..."):
                        try:
                            res = create_web_call(prop["name"], prop["id"])
                            call_id = res.get("call_id")
                            token = res.get("access_token")
                            create_inquiry({
                                "property_id": prop["id"], "type": "call",
                                "status": "calling", "retell_call_id": call_id,
                                "sent_at": datetime.now().isoformat(),
                            })
                            update_property(prop["id"], {"status": "calling"})
                            st.session_state["last_call_id"] = call_id
                            st.session_state["web_call_token"] = token
                            st.rerun()
                        except Exception as e:
                            st.error(f"エラー: {e}")

                # 通話ウィジェット
                if "web_call_token" in st.session_state and st.session_state["web_call_token"]:
                    st.info("マイクを許可して「Start 通話」→ AIと会話 → 「Stop 通話」→ 上部「結果を取得」")
                    token = st.session_state["web_call_token"]
                    components.html(f"""
                    <html>
                    <head>
                    <style>
                        body {{margin:0;font-family:sans-serif;text-align:center;padding:20px}}
                        #s {{font-size:18px;margin:10px 0;color:#333}}
                        button {{padding:12px 40px;font-size:18px;border:none;border-radius:8px;cursor:pointer;margin:5px}}
                        .go {{background:#0066ff;color:#fff}} .no {{background:#cc0000;color:#fff}}
                    </style></head>
                    <body>
                    <div id="s">準備完了</div>
                    <button class="go" id="startBtn">Start 通話</button>
                    <button class="no" id="stopBtn" style="display:none">Stop 通話</button>
                    <script type="module">
                    import {{ RetellWebClient }} from "https://cdn.jsdelivr.net/npm/retell-client-js-sdk@2.0.7/+esm";
                    let r;
                    const s=document.getElementById('s');
                    document.getElementById('startBtn').onclick=async()=>{{
                        s.textContent='接続中...';
                        try{{
                            r=new RetellWebClient();
                            r.on('call_started',()=>{{s.textContent='通話中...';document.getElementById('stopBtn').style.display='inline-block'}});
                            r.on('call_ended',()=>{{s.textContent='通話終了 — 上の「結果を取得」を押してください';document.getElementById('stopBtn').style.display='none'}});
                            r.on('error',(e)=>{{s.textContent='エラー:'+e}});
                            await r.startCall({{accessToken:"{token}"}});
                        }}catch(e){{s.textContent='エラー:'+e.message}}
                    }};
                    document.getElementById('stopBtn').onclick=async()=>{{if(r)await r.stopCall()}};
                    </script></body></html>
                    """, height=150)

# ═══════════════════════════════════════════════
# タブ4: 会話テンプレート
# ═══════════════════════════════════════════════
elif tab == "💬 会話テンプレート":
    st.header("会話テンプレート管理")

    t1, t2, t3 = st.tabs(["ブロック管理", "テンプレート管理", "物件割り当て"])

    # ── ブロック管理 ──
    with t1:
        st.subheader("ブロック（積木）一覧")

        with st.expander("＋ 新規ブロック"):
            with st.form("add_block"):
                b_name = st.text_input("ブロック名 *")
                b_type = st.selectbox("タイプ", BLOCK_TYPES, format_func=lambda x: BLOCK_TYPE_LABELS.get(x, x))
                b_desc = st.text_input("説明")
                b_content = st.text_area("内容（話術テキスト）*", height=200)
                if st.form_submit_button("登録", type="primary"):
                    if b_name and b_content:
                        create_block({"name": b_name, "type": b_type, "content": b_content, "description": b_desc})
                        st.success(f"登録完了: {b_name}")
                        st.rerun()
                    else:
                        st.error("ブロック名と内容は必須です")

        for b in list_blocks():
            type_label = BLOCK_TYPE_LABELS.get(b["type"], b["type"])
            with st.expander(f"[{type_label}] {b['name']}{' 🔒' if b['is_system'] else ''}"):
                with st.form(f"edit_block_{b['id']}"):
                    eb_name = st.text_input("ブロック名", value=b["name"], key=f"bn_{b['id']}")
                    eb_type = st.selectbox("タイプ", BLOCK_TYPES, index=BLOCK_TYPES.index(b["type"]),
                                           format_func=lambda x: BLOCK_TYPE_LABELS.get(x, x), key=f"bt_{b['id']}")
                    eb_desc = st.text_input("説明", value=b.get("description", ""), key=f"bd_{b['id']}")
                    eb_content = st.text_area("内容", value=b["content"], height=200, key=f"bc_{b['id']}")
                    c_save, c_del = st.columns(2)
                    with c_save:
                        if st.form_submit_button("保存", type="primary"):
                            update_block(b["id"], {"name": eb_name, "type": eb_type, "description": eb_desc, "content": eb_content})
                            st.success("更新しました")
                            st.rerun()
                    with c_del:
                        if not b["is_system"]:
                            if st.form_submit_button("削除"):
                                delete_block(b["id"])
                                st.rerun()

    # ── テンプレート管理 ──
    with t2:
        st.subheader("テンプレート一覧")

        with st.expander("＋ 新規テンプレート"):
            with st.form("add_template"):
                t_name = st.text_input("テンプレート名 *")
                t_desc = st.text_input("説明")
                if st.form_submit_button("登録", type="primary"):
                    if t_name:
                        create_template({"name": t_name, "description": t_desc})
                        st.success(f"登録完了: {t_name}")
                        st.rerun()

        default_id = get_default_template()

        for tmpl in list_templates():
            is_default = default_id and tmpl["id"] == default_id
            label = f"{'★ ' if is_default else ''}{tmpl['name']}"

            with st.expander(label):
                with st.form(f"edit_tmpl_{tmpl['id']}"):
                    et_name = st.text_input("テンプレート名", value=tmpl["name"], key=f"tn_{tmpl['id']}")
                    et_desc = st.text_input("説明", value=tmpl.get("description", ""), key=f"td_{tmpl['id']}")
                    if st.form_submit_button("保存"):
                        update_template(tmpl["id"], {"name": et_name, "description": et_desc})
                        st.rerun()

                if not is_default:
                    if st.button("デフォルトに設定", key=f"default_{tmpl['id']}"):
                        set_default_template(tmpl["id"])
                        st.rerun()

                # ブロック構成
                st.write("---")
                st.write("**ブロック構成（順序）**")
                current_blocks = get_template_blocks(tmpl["id"])
                all_blocks = list_blocks()

                if current_blocks:
                    for i, cb in enumerate(current_blocks):
                        type_l = BLOCK_TYPE_LABELS.get(cb["type"], cb["type"])
                        st.write(f"{i+1}. [{type_l}] {cb['name']}")

                # 順序変更
                block_opts = {f"{BLOCK_TYPE_LABELS.get(b['type'],'')} - {b['name']}": b["id"] for b in all_blocks}
                selected_blocks = st.multiselect(
                    "ブロックを選択（順序どおり）",
                    list(block_opts.keys()),
                    default=[f"{BLOCK_TYPE_LABELS.get(cb['type'],'')} - {cb['name']}" for cb in current_blocks],
                    key=f"ms_{tmpl['id']}",
                )
                if st.button("順序を更新", key=f"reorder_{tmpl['id']}"):
                    ordered_ids = [block_opts[s] for s in selected_blocks]
                    set_template_blocks(tmpl["id"], ordered_ids)
                    st.success("更新しました")
                    st.rerun()

                # プレビュー
                st.write("---")
                if st.button("プレビュー", key=f"preview_{tmpl['id']}"):
                    prompt = generate_prompt(tmpl["id"])
                    st.text_area("生成されるプロンプト", value=prompt, height=300, key=f"pv_{tmpl['id']}")

                # エクスポート
                exp_data = export_template(tmpl["id"])
                st.download_button(
                    "JSON エクスポート",
                    json.dumps(exp_data, ensure_ascii=False, indent=2),
                    file_name=f"template_{tmpl['name']}.json",
                    mime="application/json",
                    key=f"exp_{tmpl['id']}",
                )

                # 削除
                if not is_default:
                    if st.button("テンプレート削除", key=f"del_tmpl_{tmpl['id']}"):
                        delete_template(tmpl["id"])
                        st.rerun()

        # インポート
        st.divider()
        uploaded = st.file_uploader("JSON インポート", type=["json"])
        if uploaded:
            try:
                data = json.loads(uploaded.read().decode("utf-8"))
                t = import_template(data)
                st.success(f"インポート完了: {t['name']}")
                st.rerun()
            except Exception as e:
                st.error(f"エラー: {e}")

    # ── 物件割り当て ──
    with t3:
        st.subheader("物件にテンプレートを割り当て")
        properties = list_properties()
        tmpls = list_templates()
        tmpl_opts = {"デフォルトを使用": None}
        tmpl_opts.update({t["name"]: t["id"] for t in tmpls})

        if not properties:
            st.info("物件が登録されていません。")
        else:
            for p in properties:
                current_tid = p.get("template_id")
                current_name = "デフォルトを使用"
                for t in tmpls:
                    if t["id"] == current_tid:
                        current_name = t["name"]

                sel = st.selectbox(
                    p["name"],
                    list(tmpl_opts.keys()),
                    index=list(tmpl_opts.keys()).index(current_name) if current_name in tmpl_opts else 0,
                    key=f"assign_{p['id']}",
                )
                new_tid = tmpl_opts.get(sel)
                if new_tid != current_tid:
                    update_property(p["id"], {"template_id": new_tid})

# ═══════════════════════════════════════════════
# タブ5: 結果一覧
# ═══════════════════════════════════════════════
elif tab == "📊 結果一覧":
    st.header("結果一覧")

    properties = list_properties()
    if not properties:
        st.info("物件が登録されていません。")
    else:
        # サマリー
        counts = {}
        for p in properties:
            s = p["status"]
            counts[s] = counts.get(s, 0) + 1
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("全件", len(properties))
        c2.metric("未対応", counts.get("pending", 0))
        c3.metric("確認中", counts.get("email_sent", 0) + counts.get("calling", 0))
        c4.metric("完了", counts.get("completed", 0) + counts.get("email_replied", 0))

        st.divider()

        for p in properties:
            inqs = get_inquiries(p["id"])
            results = [i for i in inqs if i.get("result_json")]
            sl = STATUS_LABEL.get(p["status"], p["status"])

            with st.expander(f"[{sl}] {p['name']} — {p.get('management_company', '')}"):
                c_a, c_b = st.columns(2)
                with c_a:
                    st.write(f"**住所**: {p.get('address', '-')}")
                    st.write(f"**電話**: {p.get('phone_number', '-')}")
                    st.write(f"**メール**: {p.get('email_address', '-')}")
                with c_b:
                    if results:
                        show_result(results[-1]["result_json"])
                    else:
                        st.info("まだ結果がありません")

        # CSV出力
        st.divider()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["物件名", "住所", "管理会社", "ステータス", "空室", "外国人OK", "中国人OK", "条件", "賃料", "まとめ"])
        for p in properties:
            result = {}
            for i in get_inquiries(p["id"]):
                if i.get("result_json") and isinstance(i["result_json"], dict):
                    result = i["result_json"]
            writer.writerow([
                p["name"], p.get("address", ""), p.get("management_company", ""),
                STATUS_LABEL.get(p["status"], p["status"]),
                result.get("vacancy_status", ""), result.get("foreigner_accepted", ""),
                result.get("chinese_accepted", ""), result.get("special_conditions", ""),
                result.get("monthly_rent", ""), result.get("summary", ""),
            ])
        st.download_button(
            "CSV ダウンロード", output.getvalue(),
            file_name=f"results_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv",
        )

# ═══════════════════════════════════════════════
# タブ5: 設定
# ═══════════════════════════════════════════════
elif tab == "⚙️ 設定":
    st.header("設定")

    cfg = load_config()
    with st.form("settings"):
        st.subheader("OpenAI")
        cfg["openai_api_key"] = st.text_input("OpenAI API Key", value=cfg["openai_api_key"], type="password")

        st.subheader("Gmail（メール確認用）")
        cfg["gmail_address"] = st.text_input("Gmailアドレス", value=cfg["gmail_address"])
        cfg["gmail_app_password"] = st.text_input(
            "Gmailアプリパスワード", value=cfg["gmail_app_password"], type="password",
            help="Googleアカウント → セキュリティ → 2段階認証 → アプリパスワード",
        )

        st.subheader("Retell AI（電話確認用）")
        cfg["retell_api_key"] = st.text_input("Retell API Key", value=cfg["retell_api_key"], type="password")
        cfg["retell_agent_id"] = st.text_input("Retell Agent ID", value=cfg["retell_agent_id"])

        st.subheader("会社情報（メール署名用）")
        cfg["company_name"] = st.text_input("会社名", value=cfg["company_name"])
        cfg["contact_person"] = st.text_input("担当者名", value=cfg["contact_person"])

        if st.form_submit_button("保存", type="primary"):
            save_config(cfg)
            st.success("設定を保存しました！")
