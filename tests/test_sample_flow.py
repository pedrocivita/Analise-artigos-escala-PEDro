"""No-key sample flow and Gemini request shape.

The tests use a fake key string and assert it never appears in URLs, errors,
rendered page text, or log records.
"""

from __future__ import annotations

import logging
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import pedro  # noqa: E402
import requests  # noqa: E402


FAKE_KEY = "unit-test-gemini-key-9f3a"


class SampleResultTests(unittest.TestCase):
    def test_eleven_criteria_yes_no_and_total(self) -> None:
        sample = pedro.load_sample_result()
        criteria = sample["criteria"]
        self.assertEqual(len(criteria), 11)
        numbers = [item["number"] for item in criteria]
        self.assertEqual(numbers, list(range(1, 12)))
        for item in criteria:
            self.assertIn(item["answer"], {"Sim", "Não"})
            self.assertTrue(item["justification"].strip())
            self.assertTrue(item["name"].strip())
        self.assertFalse(criteria[0]["scored"])
        self.assertTrue(all(item["scored"] for item in criteria[1:]))
        self.assertEqual(pedro.scored_total(sample), 8)
        self.assertEqual(sample["total"], 8)
        self.assertEqual(pedro.reliability_label(8), "Alta")

        rendered = pedro.render_sample_markdown(sample)
        for item in criteria:
            self.assertIn(f"**{item['number']}. {item['name']}:** {item['answer']}", rendered)
            self.assertIn(item["justification"], rendered)
        self.assertIn("### Pontuação Final PEDro: 8/10", rendered)
        self.assertIn("### Nível de Confiabilidade: Alta", rendered)
        self.assertNotIn(FAKE_KEY, rendered)

    def test_sample_pdf_is_the_cited_rct(self) -> None:
        import PyPDF2

        self.assertTrue(pedro.SAMPLE_PDF_PATH.is_file())
        reader = PyPDF2.PdfReader(str(pedro.SAMPLE_PDF_PATH))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        flat = " ".join(text.split())
        self.assertIn("Creative Commons", flat)
        self.assertIn("e0193358", flat.replace(" ", ""))
        self.assertIn("Intention-to-treat", flat)
        self.assertIn("allocation concealment", flat)


class GeminiRequestTests(unittest.TestCase):
    def test_model_and_key_placement(self) -> None:
        self.assertEqual(pedro.GEMINI_MODEL, "gemini-3.8-flash")
        self.assertNotIn("gemini-1.5", pedro.GEMINI_URL)
        self.assertNotIn(FAKE_KEY, pedro.GEMINI_URL)
        self.assertNotIn("key=", pedro.GEMINI_URL)
        headers = pedro.gemini_headers(FAKE_KEY)
        self.assertEqual(headers["x-goog-api-key"], FAKE_KEY)
        body = pedro.gemini_payload("texto do artigo")
        encoded = str(body)
        self.assertNotIn(FAKE_KEY, encoded)
        self.assertEqual(body["generationConfig"]["thinkingConfig"]["thinkingLevel"], "low")

    def test_http_error_hides_body_and_key(self) -> None:
        class Response:
            status_code = 400
            text = f"body includes {FAKE_KEY} and prompt echo"
            url = f"https://example.invalid/?key={FAKE_KEY}"

            def raise_for_status(self) -> None:
                raise requests.HTTPError(f"400 for url {self.url}", response=self)

            def json(self):
                raise AssertionError("error body must not be parsed")

        with mock.patch("pedro.requests.post", return_value=Response()):
            result = pedro.analyze_article("artigo", FAKE_KEY)

        self.assertIsNone(result.text)
        self.assertIsNotNone(result.error)
        assert result.error is not None
        self.assertIn("status 400", result.error)
        self.assertNotIn(FAKE_KEY, result.error)
        self.assertNotIn("body includes", result.error)

    def test_success_skips_thought_parts(self) -> None:
        class Response:
            status_code = 200
            text = FAKE_KEY

            def raise_for_status(self) -> None:
                return None

            def json(self):
                return {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {"text": f"thought {FAKE_KEY}", "thought": True},
                                    {"text": "análise visível"},
                                ]
                            }
                        }
                    ]
                }

        with mock.patch("pedro.requests.post", return_value=Response()) as posted:
            result = pedro.analyze_article("artigo", FAKE_KEY)

        self.assertEqual(result.text, "análise visível")
        self.assertIsNone(result.error)
        url = posted.call_args.args[0]
        headers = posted.call_args.kwargs["headers"]
        payload = posted.call_args.kwargs["json"]
        self.assertNotIn(FAKE_KEY, url)
        self.assertEqual(headers["x-goog-api-key"], FAKE_KEY)
        self.assertNotIn(FAKE_KEY, str(payload))


class NoKeySampleUiTests(unittest.TestCase):
    def test_sample_button_without_key(self) -> None:
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30)
        app.run()
        self._assert_clean(app)

        sample = self._button(app, "Testar com uma amostra")
        sample.click()
        app.run()
        self._assert_clean(app)

        main_text = "\n".join(block.value for block in app.markdown)
        info_text = "\n".join(block.value for block in app.info)
        self.assertIn("### Pontuação Final PEDro: 8/10", main_text)
        self.assertIn("### Nível de Confiabilidade: Alta", main_text)
        for number in range(1, 12):
            self.assertIn(f"**{number}.", main_text)
        self.assertIn("sem chamada à API", info_text)
        self.assertNotIn(FAKE_KEY, main_text + info_text)

    def test_secret_key_is_used_without_rendering_it(self) -> None:
        from streamlit.runtime.secrets import secrets_singleton
        from streamlit.testing.v1 import AppTest

        secrets_path = ROOT / ".streamlit" / "secrets.toml"
        self.assertFalse(secrets_path.exists())
        secrets_path.write_text(
            f'GEMINI_API_KEY = "{FAKE_KEY}"\n',
            encoding="utf-8",
        )
        records: list[str] = []

        class Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record.getMessage())

        handler = Capture(level=logging.INFO)
        root_logger = logging.getLogger()
        previous_level = root_logger.level
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
        try:
            secrets_singleton._reset()
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30)
            app.run()
            visible = self._visible_text(app)
            self.assertIn("segredos do app", visible)
            self.assertNotIn(FAKE_KEY, visible)
            self.assertEqual(app.session_state["gemini_api_key"], "")
            leaked = [line for line in records if FAKE_KEY in line]
            self.assertEqual(leaked, [])
        finally:
            root_logger.removeHandler(handler)
            root_logger.setLevel(previous_level)
            secrets_singleton._reset()
            os.environ.pop("GEMINI_API_KEY", None)
            secrets_path.unlink(missing_ok=True)

    def test_sidebar_key_is_not_rendered_or_logged(self) -> None:
        from streamlit.testing.v1 import AppTest

        records: list[str] = []

        class Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record.getMessage())

        handler = Capture(level=logging.INFO)
        root_logger = logging.getLogger()
        previous_level = root_logger.level
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
        try:
            app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30)
            app.run()
            app.sidebar.text_input[0].set_value(FAKE_KEY)
            app.run()
            analyze = self._button(app, "Analisar Artigo")
            analyze.click()
            app.run()
        finally:
            root_logger.removeHandler(handler)
            root_logger.setLevel(previous_level)

        self.assertEqual(app.session_state["gemini_api_key"], FAKE_KEY)
        visible = self._visible_text(app)
        self.assertNotIn(FAKE_KEY, visible)
        leaked = [line for line in records if FAKE_KEY in line]
        self.assertEqual(leaked, [])
        warnings = "\n".join(block.value for block in app.warning)
        self.assertIn("PDF", warnings)

    def _button(self, app, label: str):
        matches = [button for button in app.sidebar.button if button.label == label]
        self.assertEqual(len(matches), 1, msg=f"missing button {label}")
        return matches[0]

    def _visible_text(self, app) -> str:
        chunks: list[str] = []
        for collection in (
            app.markdown,
            app.info,
            app.warning,
            app.error,
            app.success,
            app.caption,
            app.title,
            app.header,
            app.exception,
        ):
            for block in collection:
                value = getattr(block, "value", "")
                chunks.append(str(value))
        sidebar = app.sidebar
        for collection in (sidebar.markdown, sidebar.caption, sidebar.info, sidebar.error):
            for block in collection:
                chunks.append(str(getattr(block, "value", "")))
        return "\n".join(chunks)

    def _assert_clean(self, app) -> None:
        self.assertEqual(list(app.exception), [])
        error_text = "\n".join(block.value for block in app.error)
        self.assertNotIn("secrets", error_text.lower())
        self.assertEqual(error_text, "")


if __name__ == "__main__":
    unittest.main()
