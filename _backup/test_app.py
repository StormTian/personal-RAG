import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess

from app import CandidateScore, RerankerBackend, TinyRAG


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
    (root / "hr" / "expense_policy.md").write_text(
        "# 内部差旅报销制度\n\n员工完成出差后，应在 7 个自然日内提交报销单。\n",
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

    visitor_source = root / "ops" / "_visitor_policy.txt"
    visitor_source.write_text(
        "访客接待制度\n\n外部访客来访需要至少提前 1 天在前台系统中登记。\n",
        encoding="utf-8",
    )
    subprocess.run(
        [
            "textutil",
            "-convert",
            "doc",
            str(visitor_source),
            "-output",
            str(root / "ops" / "visitor_policy.doc"),
        ],
        check=True,
        capture_output=True,
    )
    visitor_source.unlink()

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


class TinyRAGTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = TemporaryDirectory()
        cls.library_dir = build_sample_library(Path(cls.temp_dir.name) / "library")
        cls.rag = TinyRAG(cls.library_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp_dir.cleanup()

    def test_can_list_documents_from_library(self) -> None:
        sources = {item["source"] for item in self.rag.list_documents()}
        self.assertIn("product/product_overview.md", sources)
        self.assertIn("hr/leave_policy.docx", sources)
        self.assertIn("ops/visitor_policy.doc", sources)
        self.assertIn("pdf/visitor_guide.pdf", sources)

    def test_can_answer_sso_question(self) -> None:
        response = self.rag.answer("企业版支持 SSO 吗？")
        joined = "\n".join(response.answer_lines)
        self.assertIn("SSO", joined)
        self.assertTrue(any(hit.chunk.source == "product/product_overview.md" for hit in response.hits))

    def test_can_answer_trial_question(self) -> None:
        response = self.rag.answer("免费试用多久？")
        joined = "\n".join(response.answer_lines)
        self.assertIn("14 天免费试用", joined)

    def test_can_answer_docx_question(self) -> None:
        response = self.rag.answer("年假申请至少要提前多久提交？")
        joined = "\n".join(response.answer_lines)
        self.assertIn("2 个工作日", joined)

    def test_can_answer_doc_question(self) -> None:
        response = self.rag.answer("访客来访要提前多久登记？")
        joined = "\n".join(response.answer_lines)
        self.assertIn("1 天", joined)

    def test_can_answer_pdf_question(self) -> None:
        response = self.rag.answer("How many hours in advance must guests register?")
        joined = "\n".join(response.answer_lines)
        self.assertIn("24 hours", joined)

    def test_failed_reload_keeps_previous_index(self) -> None:
        original_stats = self.rag.stats()

        with TemporaryDirectory() as tmp_dir:
            with self.assertRaises(FileNotFoundError):
                self.rag.reload(Path(tmp_dir))

        reloaded_stats = self.rag.stats()
        self.assertEqual(reloaded_stats["chunks"], original_stats["chunks"])
        self.assertEqual(reloaded_stats["documents"], original_stats["documents"])
        self.assertEqual(reloaded_stats["library_dir"], original_stats["library_dir"])

    def test_custom_reranker_backend_can_override_ranking(self) -> None:
        class PreferVisitorReranker(RerankerBackend):
            name = "test-reranker"
            strategy = "test-rerank"

            def rerank(self, query, snapshot, candidates):
                ranked = []
                for candidate in candidates:
                    bonus = 1.0 if snapshot.chunks[candidate.index].source.endswith("visitor_policy.doc") else 0.0
                    ranked.append(
                        CandidateScore(
                            index=candidate.index,
                            retrieve_score=candidate.retrieve_score,
                            lexical_score=candidate.lexical_score,
                            title_score=candidate.title_score,
                            rerank_score=bonus + candidate.retrieve_score * 0.01,
                            llm_score=bonus,
                        )
                    )
                ranked.sort(key=lambda item: item.rerank_score, reverse=True)
                return ranked

        rag = TinyRAG(self.library_dir, reranker_backend=PreferVisitorReranker())
        hit = rag.search("访客来访要提前多久登记？", top_k=1)[0]
        self.assertEqual(hit.chunk.source, "ops/visitor_policy.doc")
        self.assertEqual(hit.llm_score, 1.0)


if __name__ == "__main__":
    unittest.main()
