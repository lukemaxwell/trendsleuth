"""Tests for web scraping utilities."""

import requests
from unittest.mock import Mock, patch

from trendsleuth.web_scraper import (
    HTMLTextExtractor,
    extract_text_from_html,
    fetch_page_text,
)


class TestHTMLTextExtractor:
    """Tests for HTMLTextExtractor."""

    def test_extracts_simple_text(self):
        """Test extracting text from simple HTML."""
        html = "<html><body><p>Hello World</p></body></html>"
        parser = HTMLTextExtractor()
        parser.feed(html)

        assert parser.get_text() == "Hello World"

    def test_skips_script_tags(self):
        """Test that script tags are skipped."""
        html = (
            "<html><body><p>Visible</p><script>alert('hidden')</script></body></html>"
        )
        parser = HTMLTextExtractor()
        parser.feed(html)

        text = parser.get_text()
        assert "Visible" in text
        assert "alert" not in text

    def test_skips_style_tags(self):
        """Test that style tags are skipped."""
        html = (
            "<html><body><p>Text</p><style>body { color: red; }</style></body></html>"
        )
        parser = HTMLTextExtractor()
        parser.feed(html)

        text = parser.get_text()
        assert "Text" in text
        assert "color" not in text

    def test_handles_multiple_paragraphs(self):
        """Test extracting text from multiple elements."""
        html = "<html><body><p>First</p><p>Second</p><p>Third</p></body></html>"
        parser = HTMLTextExtractor()
        parser.feed(html)

        text = parser.get_text()
        assert "First" in text
        assert "Second" in text
        assert "Third" in text

    def test_cleans_whitespace(self):
        """Test that whitespace is cleaned up."""
        html = "<html><body><p>Text   with    spaces</p></body></html>"
        text = extract_text_from_html(html)

        assert "Text with spaces" in text


class TestExtractTextFromHTML:
    """Tests for extract_text_from_html function."""

    def test_extracts_readable_text(self):
        """Test extracting readable text."""
        html = """
        <html>
            <head><title>Test</title></head>
            <body>
                <h1>Heading</h1>
                <p>Paragraph text</p>
                <script>console.log('skip me')</script>
            </body>
        </html>
        """

        text = extract_text_from_html(html)

        assert "Heading" in text
        assert "Paragraph text" in text
        assert "skip me" not in text

    def test_respects_max_length(self):
        """Test that max_length is respected."""
        html = "<html><body><p>" + "a" * 1000 + "</p></body></html>"

        text = extract_text_from_html(html, max_length=100)

        assert len(text) <= 100

    def test_handles_malformed_html(self):
        """Test handling of malformed HTML."""
        html = "<html><body><p>Text without closing tag</body></html>"

        text = extract_text_from_html(html)

        assert "Text without closing tag" in text

    def test_handles_empty_html(self):
        """Test handling of empty HTML."""
        text = extract_text_from_html("")

        assert text == ""


class TestFetchPageText:
    """Tests for fetch_page_text function."""

    @patch("trendsleuth.web_scraper.requests.get")
    def test_fetch_success(self, mock_get):
        """Test successful page fetch."""
        mock_response = Mock()
        mock_response.text = "<html><body><p>Test content</p></body></html>"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        text = fetch_page_text("https://example.com")

        assert "Test content" in text
        mock_get.assert_called_once()

    @patch("trendsleuth.web_scraper.requests.get")
    def test_fetch_non_html_content(self, mock_get):
        """Test that non-HTML content is skipped."""
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "application/pdf"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        text = fetch_page_text("https://example.com/doc.pdf")

        assert text is None

    @patch("trendsleuth.web_scraper.requests.get")
    def test_fetch_timeout(self, mock_get):
        """Test handling of timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")

        text = fetch_page_text("https://example.com")

        assert text is None

    @patch("trendsleuth.web_scraper.requests.get")
    def test_fetch_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")

        text = fetch_page_text("https://example.com")

        assert text is None

    @patch("trendsleuth.web_scraper.requests.get")
    def test_fetch_respects_timeout_param(self, mock_get):
        """Test that timeout parameter is passed."""
        mock_response = Mock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetch_page_text("https://example.com", timeout=20)

        # Verify timeout was passed
        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs["timeout"] == 20
