import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess

from app import TinyRAG
from web_app import (
    STATIC_DIR,
    build_answer_payload,
    build_library_payload,
    load_asset,
    parse_top_k,
    reload_library,
)


def build_sample_library(root: Path) -> Path:
    (root / "product").mkdir(parents=True, exist_ok=True)
    (root / "billing").mkdir(parents=True, exist_ok=True)
    (root / "hr").mkdir(parents=True, exist_ok=True)
    (root / "ops").mkdir(parents=True, exist_ok=True)
    (root / "pdf").mkdir(parents=True, exist_ok=True)

    (root / "product" / "product_overview.md").write_text(
        "# 星云知识库产品概览\n\n"
        "企业版支持 SSO（SAML 2.0）单点登录、审计日志、组织架构同步。\n\n"
        "所有新注册团队都可以获得 14 天免费试用。\n",
        encoding="utf-8",
    )
    (root / "billing" / "billing_policy.md").write_text(
        "# 计费与套餐说明\n\n免费试用结束后，系统不会自动扣费。\n",
        encoding="utf-8",
    )

    leave_source = root / "hr" / "_leave_policy.txt"
    leave_source.write_text(
        "请假申请制度\n\n员工申请年假时，至少需要提前 2 个工作日提交审批。\n",
        encoding="utf-8",
    )
    subprocess.run(
        [
            "textutil",
            "-convert",
            "docx",
            str(leave_source),
            "-output",
            str(root / "hr" / "leave_policy.docx"),
        ],
        check=True,
        capture_output=True,
    )
    leave_source.unlink()

    pdf_source = root / "pdf" / "_pdf_policy.txt"
    pdf_source.write_text(
        "PDF onboarding guide\n\nGuests must register 24 hours in advance.\n",
        encoding="utf-8",
    )
    pdf_result = subprocess.run(
        ["cupsfilter", str(pdf_source)],
        check=True,
        capture_output=True,
    )
    (root / "pdf" / "visitor_guide.pdf").write_bytes(pdf_result.stdout)
    pdf_source.unlink()

    return root


class WebAppTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = TemporaryDirectory()
        cls.library_dir = build_sample_library(Path(cls.temp_dir.name) / "library")
        cls.rag = TinyRAG(cls.library_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()

    def test_index_page_loads(self) -> None:
        payload = load_asset(STATIC_DIR / "index.html").decode("utf-8")
        self.assertIn("Tiny RAG Demo", payload)
        self.assertIn("文档库", payload)

    def test_parse_top_k_clamps_value(self) -> None:
        self.assertEqual(parse_top_k("99"), 8)
        self.assertEqual(parse_top_k("0"), 1)

    def test_library_payload_contains_files(self) -> None:
        payload = build_library_payload(self.rag)
        self.assertEqual(payload["status"], "ok")
        self.assertGreaterEqual(payload["documents"], 1)
        self.assertTrue(any(item["source"].endswith(".docx") for item in payload["files"]))
        self.assertTrue(any(item["source"].endswith(".pdf") for item in payload["files"]))
        self.assertIn("embedding_backend", payload)
        self.assertIn("reranker_backend", payload)
        self.assertIn("rerank_strategy", payload)

    def test_ask_endpoint_answers_question(self) -> None:
        status, data = build_answer_payload(self.rag, "企业版支持 SSO 吗？", "3")
        self.assertEqual(status, 200)
        self.assertEqual(data["query"], "企业版支持 SSO 吗？")
        self.assertTrue(any("SSO" in line for line in data["answer_lines"]))
        self.assertGreaterEqual(len(data["hits"]), 1)

    def test_ask_endpoint_validates_empty_query(self) -> None:
        status, data = build_answer_payload(self.rag, "   ", "3")
        self.assertEqual(status, 400)
        self.assertEqual(data["error"], "请输入问题。")

    def test_reload_endpoint_rebuilds_library(self) -> None:
        status, data = reload_library(self.rag)
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "ok")
        self.assertGreater(data["chunks"], 0)

    def test_failed_reload_preserves_last_good_snapshot(self) -> None:
        original = self.rag.stats()
        with TemporaryDirectory() as tmp_dir:
            status, data = reload_library(self.rag, Path(tmp_dir))

        self.assertEqual(status, 500)
        self.assertIn("error", data)
        self.assertEqual(self.rag.stats()["chunks"], original["chunks"])


if __name__ == "__main__":
    unittest.main()
