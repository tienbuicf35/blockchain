from __future__ import annotations

import base64
from html import escape
from typing import Any, Dict, List, Optional


SYMPTOM_LABELS = {
    "itch": "Ngứa",
    "bleed": "Chảy máu",
    "grow": "Tăng nhanh",
    "pain": "Đau",
    "change": "Đổi màu/hình dạng",
}


def _yes_no(value: Any) -> str:
    return "Có" if str(value).strip().lower() in {"yes", "true", "1", "có", "co"} else "Không"


def _short_hash(value: Any, length: int = 12) -> str:
    text = str(value or "")
    if not text:
        return "n/a"
    return text if len(text) <= length else f"{text[:length]}..."


def _render_list(items: Any) -> str:
    if not items:
        return '<div class="muted">Chưa có khuyến nghị chi tiết.</div>'
    return "<ul>" + "".join(f"<li>{escape(str(item))}</li>" for item in items) + "</ul>"


def _render_predictions(predictions: List[Dict[str, Any]]) -> str:
    if not predictions:
        return '<div class="empty-state">Chưa có kết quả.</div>'

    rows = []
    for item in predictions:
        rows.append(
            f"""
            <div class="row">
              <div>
                <div class="code">{escape(str(item.get("code", "")))}</div>
                <div class="label">{escape(str(item.get("label", "")))}</div>
                <div class="muted small">{escape(str(item.get("diagnosis", "")))}</div>
              </div>
              <div class="score">{float(item.get("score", 0.0)):.2%}</div>
            </div>
            """
        )
    return "\n".join(rows)


def _render_symptoms(symptoms: Optional[Dict[str, Any]]) -> str:
    if not symptoms:
        return '<div class="muted">Bạn có thể chọn Có/Không cho từng triệu chứng.</div>'
    parts = []
    for key, value in symptoms.items():
        label = SYMPTOM_LABELS.get(key, key)
        parts.append(f"<span class='chip'>{escape(label)}: {escape(_yes_no(value))}</span>")
    return "".join(parts)


def _render_chain_visual(blocks: List[Dict[str, Any]]) -> str:
    if not blocks:
        return '<div class="empty-state">Chưa có block để vẽ chuỗi.</div>'

    segments = []
    for block in blocks:
        predictions = block.get("predictions", [])
        segments.append(
            f"""
            <article class="chain-node">
              <div class="chain-node-top">
                <span class="chain-badge">#{escape(str(block.get("index", "")))}</span>
                <span class="chain-badge soft">{escape(str(block.get("source", "")))}</span>
              </div>
              <div class="chain-name">{escape(str(block.get("image_name", "")))}</div>
              <div class="chain-hash">hash {escape(_short_hash(block.get("hash")))}</div>
              <div class="chain-hash">prev {escape(_short_hash(block.get("previous_hash")))}</div>
              <div class="chain-score">{len(predictions)} kết quả</div>
            </article>
            """
        )
    return '<div class="chain-track">' + "".join(segments) + "</div>"


def _render_ledger_details(blocks: List[Dict[str, Any]]) -> str:
    if not blocks:
        return '<div class="empty-state">Chưa có block nào trong ledger.</div>'

    details = []
    for block in blocks:
        pred_lines = []
        for item in block.get("predictions", []):
            pred_lines.append(
                f"<span class='pill'>{escape(str(item.get('code', '')))} {float(item.get('score', 0.0)):.2%}</span>"
            )
        details.append(
            f"""
            <details class="ledger-details">
              <summary>
                <span class="summary-left">
                  <span class="ledger-title">#{escape(str(block.get("index", "")))} - {escape(str(block.get("image_name", "")))}</span>
                  <span class="ledger-meta">{escape(str(block.get("timestamp", "")))} | {escape(str(block.get("source", "")))} | top-k {escape(str(block.get("top_k", "")))}</span>
                </span>
                <span class="ledger-score">{len(block.get("predictions", []))} kết quả</span>
              </summary>
              <div class="ledger-detail-grid">
                <div><span class="detail-label">Record ID</span><div class="detail-value mono">{escape(str(block.get("record_id", "")))}</div></div>
                <div><span class="detail-label">Off-chain ref</span><div class="detail-value mono">{escape(str(block.get("offchain_record_id", "")))}</div></div>
                <div><span class="detail-label">Image SHA-256</span><div class="detail-value mono">{escape(str(block.get("image_sha256", "")))}</div></div>
                <div><span class="detail-label">Payload hash</span><div class="detail-value mono">{escape(str(block.get("payload_hash", "")))}</div></div>
                <div><span class="detail-label">Block hash</span><div class="detail-value mono">{escape(str(block.get("hash", "")))}</div></div>
                <div><span class="detail-label">Previous hash</span><div class="detail-value mono">{escape(str(block.get("previous_hash", "")))}</div></div>
                <div><span class="detail-label">Signature</span><div class="detail-value mono">{escape(str(block.get("signature", "")))}</div></div>
                <div><span class="detail-label">Writer</span><div class="detail-value mono">{escape(str(block.get("writer_address", "")))}</div></div>
                <div><span class="detail-label">Tx hash</span><div class="detail-value mono">{escape(str(block.get("tx_hash", "")))}</div></div>
                <div><span class="detail-label">Storage</span><div class="detail-value">{escape(str(block.get("storage", "")))}</div></div>
                <div><span class="detail-label">Model dir</span><div class="detail-value">{escape(str(block.get("model_dir", "")))}</div></div>
                <div><span class="detail-label">Top K</span><div class="detail-value">{escape(str(block.get("top_k", "")))}</div></div>
              </div>
              <div class="ledger-preds">{''.join(pred_lines) if pred_lines else '<span class="pill">Không có prediction</span>'}</div>
            </details>
            """
        )
    return "\n".join(details)


def render_homepage(
    *,
    predictions: Optional[List[Dict[str, Any]]] = None,
    screen: Optional[Dict[str, Any]] = None,
    uploaded_image: Optional[bytes] = None,
    uploaded_mime_type: str = "image/jpeg",
    model_dir: Optional[str] = None,
    top_k: int = 3,
    ledger_blocks: Optional[List[Dict[str, Any]]] = None,
    ledger_validation: Optional[Dict[str, Any]] = None,
    ledger_summary: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> str:
    preview_html = ""
    if uploaded_image:
        encoded = base64.b64encode(uploaded_image).decode("ascii")
        preview_html = f'<img class="preview" src="data:{escape(uploaded_mime_type)};base64,{encoded}" alt="Ảnh da đã tải lên" />'

    predictions_html = _render_predictions(predictions or [])
    screen_html = ""
    if screen:
        screen_html = f"""
        <section class="result-card">
          <div class="card-kicker">Chẩn đoán gợi ý</div>
          <div class="status status-{escape(str(screen.get("priority", "monitor")))}">{escape(str(screen.get("priority", ""))).upper()}</div>
          <div class="risk risk-{escape(str(screen.get("risk_level", "low")))}">Mức độ nguy hiểm: {escape(str(screen.get("risk_level", ""))).upper()}</div>
          <div class="big">{escape(str(screen.get("diagnosis_summary", screen.get("predicted_label", ""))))}</div>
          <div class="muted">{escape(str(screen.get("condition_overview", "")))}</div>
          <div class="metric-grid">
            <div><span>Độ tin cậy</span><strong>{float(screen.get("confidence", 0.0)):.2%}</strong></div>
            <div><span>Điểm cảnh báo</span><strong>{float(screen.get("red_flag_score", 0.0)):.2%}</strong></div>
          </div>
          <div class="notice">{escape(str(screen.get("risk_reason", "")))} {escape(str(screen.get("recommendation", "")))}</div>
          <div class="advice-grid">
            <div>
              <h3>Lời khuyên</h3>
              {_render_list(screen.get("care_advice"))}
            </div>
            <div>
              <h3>Dấu hiệu cần đi khám</h3>
              {_render_list(screen.get("warning_signs"))}
            </div>
          </div>
          <div class="disclaimer">{escape(str(screen.get("medical_disclaimer", "")))}</div>
          <div class="symptoms">{_render_symptoms(screen.get("symptoms"))}</div>
          <h3>Top kết quả</h3>
          <div class="result-list">{predictions_html}</div>
        </section>
        """

    ledger_html = ""
    if ledger_blocks is not None:
        validation = ledger_validation or {"valid": False, "length": 0}
        summary = ledger_summary or {}
        head_hash = _short_hash(ledger_blocks[-1].get("hash")) if ledger_blocks else "n/a"
        validation_text = "Hợp lệ" if validation.get("valid") else "Không hợp lệ"
        validation_class = "ledger-good" if validation.get("valid") else "ledger-bad"
        backend = escape(str(summary.get("backend", "hybrid-local")))
        onchain_length = int(summary.get("onchain_length", validation.get("length", 0)))
        offchain_length = int(summary.get("offchain_length", 0))
        ledger_html = f"""
        <section class="result-card">
          <div class="card-kicker">Hybrid blockchain</div>
          <div class="big">Sổ cái on-chain / off-chain</div>
          <div class="muted">Ảnh và payload nặng được lưu Off-chain trên IPFS; Hash, bệnh án tóm tắt và metadata kiểm chứng được neo On-chain để minh bạch, chống sửa đổi và làm bằng chứng xác thực cho chẩn đoán từ xa.</div>
          <div class="muted">Backend: <span class="mono">{backend}</span></div>
          <div class="muted">Trạng thái: <span class="{validation_class}">{escape(validation_text)}</span> | On-chain: {onchain_length} | Off-chain: {offchain_length}</div>
          <div class="muted">Head hash: <span class="mono">{escape(head_hash)}</span></div>
          <div class="ledger-links">
            <a class="ledger-link" href="/ledger/ui">Xem sổ cái</a>
            <a class="ledger-link" href="/ledger/validate">Kiểm tra chuỗi</a>
            <a class="ledger-link" href="/ledger/export.json">Xuất JSON</a>
          </div>
          {_render_chain_visual(ledger_blocks[-5:][::-1])}
        </section>
        """

    error_html = f'<div class="error">{escape(error)}</div>' if error else ""
    model_html = escape(model_dir or "mô hình local")

    return f"""
    <!doctype html>
    <html lang="vi">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Ứng dụng sàng lọc bệnh da liễu</title>
      <style>
        :root {{
          --paper: #f7f8fb;
          --panel: #ffffff;
          --ink: #132238;
          --ink-soft: #53657a;
          --line: rgba(19, 34, 56, 0.14);
          --accent: #b45309;
          --accent-2: #1d4e89;
          --accent-3: #0f766e;
          --danger: #9f1239;
          --warn: #92400e;
          --shadow: 0 14px 40px rgba(19, 34, 56, 0.10);
        }}
        * {{ box-sizing: border-box; }}
        body {{
          margin: 0;
          font-family: Inter, "Segoe UI", Roboto, Arial, sans-serif;
          color: var(--ink);
          background: linear-gradient(160deg, #f7f8fb, #eef3f8);
        }}
        .wrap {{ max-width: 1280px; margin: 0 auto; padding: 28px 22px 42px; }}
        .hero, .card, .result-card {{
          background: var(--panel);
          border: 1px solid var(--line);
          border-radius: 8px;
          box-shadow: var(--shadow);
        }}
        .hero {{ padding: 26px; }}
        .hero-grid {{ display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(300px, 0.75fr); gap: 18px; }}
        .eyebrow {{ color: var(--accent-2); font-size: 12px; letter-spacing: 0; text-transform: uppercase; font-weight: 800; }}
        h1 {{ margin: 10px 0 0; font-size: clamp(34px, 5vw, 58px); line-height: 1; letter-spacing: 0; }}
        h2 {{ margin: 0 0 10px; font-size: 22px; }}
        h3 {{ margin: 18px 0 8px; font-size: 16px; }}
        p, .muted {{ color: var(--ink-soft); line-height: 1.65; }}
        .hero p {{ max-width: 780px; margin: 14px 0 0; }}
        .hero-panel {{ padding: 18px; border-radius: 8px; background: #132238; color: #f7fafc; }}
        .hero-panel .muted {{ color: rgba(247, 250, 252, 0.78); }}
        .workflow {{ display: grid; gap: 10px; margin-top: 14px; }}
        .workflow-step {{ padding: 12px 14px; border-radius: 8px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12); }}
        .workflow-step strong {{ display: block; margin-bottom: 4px; }}
        .meta-row, .ledger-links, .symptoms, .ledger-preds {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .meta-row {{ margin-top: 18px; }}
        .chip, .pill, .ledger-link {{
          display: inline-flex; align-items: center; padding: 8px 10px; border-radius: 999px;
          background: rgba(19, 34, 56, 0.05); border: 1px solid rgba(19, 34, 56, 0.10);
          color: var(--ink-soft); font-size: 13px; font-weight: 700; text-decoration: none;
        }}
        .grid {{ display: grid; grid-template-columns: 390px 1fr; gap: 18px; margin-top: 18px; align-items: start; }}
        .card, .result-card {{ padding: 22px; }}
        .form {{ display: grid; gap: 14px; margin-top: 14px; }}
        label {{ display: block; margin-bottom: 6px; font-size: 14px; color: var(--ink-soft); font-weight: 700; }}
        input, select {{
          width: 100%; padding: 12px 14px; border-radius: 8px; border: 1px solid var(--line);
          background: #fff; color: var(--ink); outline: none; font: inherit;
        }}
        .btn {{ padding: 13px 16px; border-radius: 8px; border: 0; font-weight: 800; background: var(--accent-2); color: white; cursor: pointer; }}
        .preview {{ width: 100%; max-height: 360px; object-fit: contain; border-radius: 8px; background: #fff; border: 1px solid var(--line); margin-bottom: 16px; }}
        .row {{ display: flex; justify-content: space-between; gap: 16px; padding: 12px 0; border-top: 1px solid rgba(19,34,56,0.10); }}
        .row:first-child {{ border-top: 0; }}
        .code, .card-kicker, .detail-label, .ledger-title {{ color: var(--accent-2); font-weight: 800; }}
        .card-kicker, .detail-label {{ letter-spacing: 0; text-transform: uppercase; font-size: 12px; }}
        .label {{ font-size: 16px; font-weight: 800; margin-top: 4px; }}
        .score, .ledger-score, .chain-score, .ledger-good {{ color: var(--accent-3); font-weight: 800; }}
        .big {{ font-size: 24px; font-weight: 800; margin-top: 6px; }}
        .status, .risk {{ display: inline-flex; margin: 8px 10px 12px 0; padding: 8px 12px; border-radius: 999px; font-weight: 800; }}
        .status-urgent, .risk-high {{ background: rgba(255, 105, 122, 0.16); color: var(--danger); }}
        .status-review, .risk-moderate {{ background: rgba(255, 193, 92, 0.18); color: var(--warn); }}
        .status-monitor, .risk-low {{ background: rgba(71, 209, 140, 0.18); color: #065f46; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin: 14px 0; }}
        .metric-grid div {{ border: 1px solid var(--line); border-radius: 8px; padding: 12px; background: #f9fbfd; }}
        .metric-grid span {{ display: block; color: var(--ink-soft); font-size: 13px; }}
        .metric-grid strong {{ display: block; margin-top: 4px; font-size: 20px; }}
        .notice, .disclaimer, .error {{ margin-top: 12px; padding: 12px 14px; border-radius: 8px; border: 1px solid rgba(180, 83, 9, 0.20); background: rgba(180, 83, 9, 0.08); color: #7c2d12; line-height: 1.55; }}
        .disclaimer {{ color: var(--ink-soft); background: #f9fbfd; border-color: var(--line); }}
        .advice-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }}
        ul {{ margin: 0; padding-left: 20px; color: var(--ink-soft); line-height: 1.6; }}
        .empty-state {{ padding: 16px; border: 1px dashed rgba(19,34,56,0.18); border-radius: 8px; color: var(--ink-soft); background: #f9fbfd; }}
        .small {{ font-size: 13px; }}
        .mono {{ font-family: "Cascadia Mono", Consolas, "Courier New", monospace; font-size: 12px; word-break: break-all; }}
        .ledger-bad {{ color: var(--danger); font-weight: 800; }}
        .chain-track {{ display: grid; gap: 10px; margin-top: 14px; }}
        .chain-node, .ledger-details {{ padding: 14px 16px; border-radius: 8px; background: #f9fbfd; border: 1px solid var(--line); }}
        .chain-node-top {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }}
        .chain-badge {{ display: inline-flex; padding: 6px 10px; border-radius: 999px; background: rgba(29, 78, 137, 0.12); color: var(--accent-2); font-size: 12px; font-weight: 800; }}
        .chain-badge.soft {{ background: rgba(15, 118, 110, 0.12); color: var(--accent-3); }}
        .chain-name {{ font-weight: 800; margin-bottom: 6px; }}
        .chain-hash, .ledger-meta, .detail-value {{ color: var(--ink-soft); word-break: break-all; line-height: 1.5; }}
        .ledger-details {{ margin-top: 14px; padding: 0; overflow: hidden; }}
        .ledger-details summary {{ list-style: none; cursor: pointer; display: flex; justify-content: space-between; gap: 16px; align-items: center; padding: 14px 16px; }}
        .ledger-details summary::-webkit-details-marker {{ display: none; }}
        .summary-left {{ display: grid; gap: 6px; }}
        .ledger-detail-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; padding: 0 16px 16px; }}
        @media (max-width: 960px) {{
          .hero-grid, .grid, .advice-grid, .metric-grid {{ grid-template-columns: 1fr; }}
          .wrap {{ padding: 18px; }}
          .ledger-detail-grid {{ grid-template-columns: 1fr; }}
        }}
      </style>
    </head>
    <body>
      <div class="wrap">
        <section class="hero">
          <div class="hero-grid">
            <div>
              <div class="eyebrow">Skin Screening Studio</div>
              <h1>Sàng lọc ảnh da liễu kèm triệu chứng</h1>
              <p>Dựa trên mô hình local và checklist nhanh, kết quả không chỉ là nhãn lớp mà còn có chẩn đoán gợi ý, mức ưu tiên xem lại và lời khuyên chăm sóc ban đầu. Lịch sử dự đoán được quản lý bằng Blockchain Hybrid: ảnh nặng lưu Off-chain trên IPFS, còn Hash và bệnh án tóm tắt được neo On-chain để chống sửa đổi và hỗ trợ truy xuất xác thực.</p>
              <div class="meta-row">
                <span class="chip">{model_html}</span>
                <span class="chip">8 nhóm bệnh da</span>
                <span class="chip">Ảnh + triệu chứng</span>
              </div>
            </div>
            <aside class="hero-panel">
              <h2>Quy trình</h2>
              <div class="muted">Luồng kiểm tra nhanh, tập trung vào dấu hiệu cần ưu tiên khám.</div>
              <div class="workflow">
                <div class="workflow-step"><strong>1. Tải ảnh</strong><span>Chọn ảnh tổn thương da cần kiểm tra.</span></div>
                <div class="workflow-step"><strong>2. Đánh dấu triệu chứng</strong><span>Nhập nhanh Có/Không cho các dấu hiệu quan trọng.</span></div>
                <div class="workflow-step"><strong>3. Nhận lời khuyên</strong><span>Hệ thống đưa ra risk level, dấu hiệu cảnh báo và khuyến nghị tiếp theo.</span></div>
              </div>
            </aside>
          </div>
        </section>

        <main class="grid">
          <section class="card">
            <h2>Biểu mẫu sàng lọc</h2>
            <form class="form" action="/screen-ui" method="post" enctype="multipart/form-data">
              <div><label for="file">Ảnh đầu vào</label><input id="file" name="file" type="file" accept="image/*" required /></div>
              <div><label for="itch">Ngứa</label><select id="itch" name="itch"><option value="no">Không</option><option value="yes">Có</option></select></div>
              <div><label for="bleed">Chảy máu</label><select id="bleed" name="bleed"><option value="no">Không</option><option value="yes">Có</option></select></div>
              <div><label for="grow">Tăng nhanh</label><select id="grow" name="grow"><option value="no">Không</option><option value="yes">Có</option></select></div>
              <div><label for="pain">Đau</label><select id="pain" name="pain"><option value="no">Không</option><option value="yes">Có</option></select></div>
              <div><label for="change">Thay đổi màu/hình</label><select id="change" name="change"><option value="no">Không</option><option value="yes">Có</option></select></div>
              <div><label for="top_k">Top K</label><input id="top_k" name="top_k" type="number" min="1" max="8" value="{int(top_k)}" /></div>
              <button class="btn" type="submit">Chạy sàng lọc</button>
            </form>
            {error_html}
          </section>

          <section class="card">
            <h2>Kết quả hiện tại</h2>
            {preview_html}
            {screen_html if screen_html else '<div class="empty-state">Tải ảnh lên và chạy sàng lọc để xem kết quả.</div>'}
          </section>
          {ledger_html}
        </main>
      </div>
    </body>
    </html>
    """


def render_ledger_page(
    *,
    blocks: Optional[List[Dict[str, Any]]] = None,
    validation: Optional[Dict[str, Any]] = None,
) -> str:
    blocks = blocks or []
    validation = validation or {"valid": False, "length": 0}
    valid_text = "Hợp lệ" if validation.get("valid") else "Không hợp lệ"
    valid_class = "good" if validation.get("valid") else "bad"
    broken_index = validation.get("broken_index", -1)
    reason = validation.get("reason", "")
    head_hash = _short_hash(blocks[-1].get("hash")) if blocks else "n/a"
    tail_hash = _short_hash(blocks[0].get("hash")) if blocks else "n/a"

    return f"""
    <!doctype html>
    <html lang="vi">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Lịch sử ledger</title>
      <style>
        body {{ margin: 0; font-family: Inter, "Segoe UI", Roboto, Arial, sans-serif; color: #132238; background: linear-gradient(160deg, #f7f8fb, #eef3f8); }}
        .wrap {{ max-width: 1240px; margin: 0 auto; padding: 28px 20px 40px; }}
        .hero, .card {{ background: #fff; border: 1px solid rgba(19,34,56,0.14); border-radius: 8px; box-shadow: 0 14px 40px rgba(19,34,56,0.10); }}
        .hero, .card {{ padding: 24px; }}
        h1 {{ margin: 0; font-size: clamp(30px, 4vw, 48px); letter-spacing: 0; }}
        .muted, .ledger-meta, .detail-value, .chain-hash {{ color: #53657a; line-height: 1.6; word-break: break-all; }}
        .stats {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 18px; }}
        .stat-card, .chain-node, .ledger-details {{ border: 1px solid rgba(19,34,56,0.14); border-radius: 8px; background: #f9fbfd; }}
        .stat-card {{ padding: 14px 16px; }}
        .stat-label, .detail-label {{ color: #1d4e89; font-size: 12px; text-transform: uppercase; font-weight: 800; }}
        .stat-value {{ margin-top: 6px; font-size: 20px; font-weight: 800; word-break: break-all; }}
        .actions, .status, .ledger-preds {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 16px; }}
        .btn {{ display: inline-block; text-decoration: none; border-radius: 8px; padding: 12px 16px; color: white; background: #1d4e89; font-weight: 800; }}
        .btn.secondary, .pill {{ background: rgba(19,34,56,0.06); color: #132238; border: 1px solid rgba(19,34,56,0.12); }}
        .pill {{ display: inline-flex; padding: 8px 12px; border-radius: 999px; }}
        .pill.good {{ color: #065f46; }} .pill.bad {{ color: #9f1239; }}
        .warning {{ margin-top: 12px; padding: 12px 14px; border-radius: 8px; border: 1px solid rgba(180,83,9,0.20); background: rgba(180,83,9,0.08); color: #7c2d12; }}
        .stack, .chain-track {{ display: grid; gap: 14px; margin-top: 18px; }}
        .section-title {{ font-size: 18px; font-weight: 800; margin-bottom: 10px; }}
        .chain-node {{ padding: 14px 16px; }}
        .chain-node-top {{ display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; align-items: center; }}
        .chain-badge {{ display: inline-flex; padding: 6px 10px; border-radius: 999px; background: rgba(29,78,137,0.12); color: #1d4e89; font-size: 12px; font-weight: 800; }}
        .chain-badge.soft {{ background: rgba(15,118,110,0.12); color: #0f766e; }}
        .chain-name {{ font-weight: 800; font-size: 15px; }}
        .chain-score, .ledger-score {{ color: #0f766e; font-weight: 800; }}
        .ledger-details {{ margin-top: 14px; overflow: hidden; }}
        .ledger-details summary {{ list-style: none; cursor: pointer; display: flex; justify-content: space-between; gap: 16px; align-items: center; padding: 14px 16px; }}
        .ledger-details summary::-webkit-details-marker {{ display: none; }}
        .summary-left {{ display: grid; gap: 6px; }}
        .ledger-detail-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; padding: 0 16px 16px; }}
        .ledger-title {{ color: #1d4e89; font-weight: 800; }}
        .mono {{ font-family: "Cascadia Mono", Consolas, "Courier New", monospace; }}
        .empty-state {{ border: 1px dashed rgba(19,34,56,0.18); border-radius: 8px; padding: 24px; color: #53657a; background: #f9fbfd; }}
        @media (max-width: 900px) {{ .stats, .ledger-detail-grid {{ grid-template-columns: 1fr; }} .ledger-details summary {{ align-items: flex-start; flex-direction: column; }} }}
      </style>
    </head>
    <body>
      <div class="wrap">
        <section class="hero">
          <h1>Toàn bộ lịch sử dự đoán</h1>
          <div class="muted">Trang này hiển thị block On-chain kèm payload Off-chain/IPFS, trạng thái kiểm tra chuỗi, chữ ký wallet và bằng chứng hash cho từng kết quả sàng lọc.</div>
          <div class="stats">
            <div class="stat-card"><div class="stat-label">Trạng thái</div><div class="stat-value">{valid_text}</div></div>
            <div class="stat-card"><div class="stat-label">Hash đầu chuỗi</div><div class="stat-value mono">{escape(head_hash)}</div></div>
            <div class="stat-card"><div class="stat-label">Hash cuối chuỗi</div><div class="stat-value mono">{escape(tail_hash)}</div></div>
          </div>
          <div class="actions">
            <a class="btn secondary" href="/">Về trang chính</a>
            <a class="btn" href="/ledger/export.json">Xuất JSON</a>
            <a class="btn" href="/ledger/export.csv">Xuất CSV</a>
          </div>
          <div class="status">
            <span class="pill {valid_class}">Chuỗi {valid_text}</span>
            <span class="pill">Tổng block: {int(validation.get("length", 0))}</span>
            <span class="pill">Chỉ số lỗi: {int(broken_index) if broken_index is not None else -1}</span>
          </div>
          {f'<div class="warning">Lý do: {escape(str(reason))}</div>' if reason else ""}
        </section>

        <div class="stack">
          <section class="card">
            <div class="section-title">Danh sách block</div>
            {_render_chain_visual(blocks[::-1])}
          </section>
          <section class="card">
            <div class="section-title">Chi tiết block</div>
            {_render_ledger_details(blocks[::-1])}
          </section>
        </div>
      </div>
    </body>
    </html>
    """
