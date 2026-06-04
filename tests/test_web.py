import unittest

from app.web import render_homepage, render_ledger_page


class WebRenderTest(unittest.TestCase):
    def test_homepage_contains_screening_form(self) -> None:
        html = render_homepage(
            screen={
                "predicted_label": "U hắc tố da",
                "diagnosis_summary": "Nghi ngờ u hắc tố da",
                "condition_overview": "Cần đánh giá sớm.",
                "care_advice": ["Khám da liễu sớm."],
                "warning_signs": ["Thay đổi nhanh."],
                "medical_disclaimer": "Kết quả chỉ hỗ trợ sàng lọc.",
                "confidence": 0.91,
                "red_flag_score": 0.4,
                "priority": "urgent",
                "risk_level": "high",
                "risk_reason": "Cần ưu tiên xem lại sớm.",
                "recommendation": "Cần ưu tiên xem lại sớm.",
                "symptoms": {"itch": "yes", "bleed": "no"},
                "predictions": [
                    {
                        "code": "MEL",
                        "label": "U hắc tố da",
                        "score": 0.91,
                        "diagnosis": "Nghi ngờ u hắc tố da",
                    },
                ],
            }
        )
        self.assertIn('action="/screen-ui"', html)
        self.assertIn("Sàng lọc ảnh da liễu kèm triệu chứng", html)
        self.assertIn("status-urgent", html)
        self.assertIn("Mức độ nguy hiểm", html)
        self.assertIn("Nghi ngờ u hắc tố da", html)
        self.assertIn("Lời khuyên", html)
        self.assertIn("Dấu hiệu cần đi khám", html)

    def test_homepage_contains_ledger_section(self) -> None:
        html = render_homepage(
            ledger_blocks=[
                {
                    "index": 0,
                    "timestamp": "2026-04-29T00:00:00Z",
                    "source": "test",
                    "image_name": "a.jpg",
                    "image_sha256": "abc",
                    "model_dir": "local-model",
                    "top_k": 3,
                    "predictions": [{"code": "MEL", "label": "U hắc tố da", "score": 0.91}],
                    "previous_hash": "0" * 64,
                    "hash": "1" * 64,
                    "signature": "2" * 64,
                }
            ],
            ledger_validation={"valid": True, "length": 1},
        )
        self.assertIn("Hybrid blockchain", html)
        self.assertIn("Sổ cái on-chain / off-chain", html)
        self.assertIn("IPFS", html)
        self.assertIn("bệnh án tóm tắt", html)
        self.assertIn("/ledger/ui", html)
        self.assertIn("Hợp lệ", html)
        self.assertIn("Head hash", html)
        self.assertIn("chain-node", html)

    def test_ledger_page_contains_details(self) -> None:
        html = render_ledger_page(
            blocks=[
                {
                    "index": 0,
                    "timestamp": "2026-04-29T00:00:00Z",
                    "source": "test",
                    "image_name": "a.jpg",
                    "image_sha256": "abc",
                    "model_dir": "local-model",
                    "top_k": 3,
                    "predictions": [{"code": "MEL", "label": "U hắc tố da", "score": 0.91}],
                    "previous_hash": "0" * 64,
                    "hash": "1" * 64,
                    "signature": "2" * 64,
                }
            ],
            validation={"valid": True, "length": 1},
        )
        self.assertIn("Toàn bộ lịch sử dự đoán", html)
        self.assertIn("Chi tiết block", html)
        self.assertIn("Image SHA-256", html)
        self.assertIn("Off-chain/IPFS", html)
        self.assertIn("ledger-details", html)


if __name__ == "__main__":
    unittest.main()
