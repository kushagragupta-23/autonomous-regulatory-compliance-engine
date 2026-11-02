import pytest
from backend.services.auto_scraper import RegulatoryScraperEngine

MOCK_TEST_HTML = """
<html>
    <body>
        <div class="notifications-feed">
            <article class="notification-item">
                <a href="/circular-tds-194r.pdf">Circular No. 22/2026: Deduction of Tax at Source under Section 194R</a>
                <span class="pub-date">01 November 2026</span>
                <p>Mandatory 10% withholding tax on benefits and perks provided in business.</p>
            </article>
            <article class="notification-item">
                <a href="/gst-notification-e-invoice.pdf">Notification No. 09/2026: E-Invoicing Mandatory Threshold</a>
                <span class="pub-date">25 October 2026</span>
                <p>CBIC mandates IRN generation for businesses crossing 5 Crore turnover.</p>
            </article>
        </div>
    </body>
</html>
"""

def test_beautifulsoup_scraper_html_parsing():
    scraper = RegulatoryScraperEngine()
    items = scraper.scrape_from_html(MOCK_TEST_HTML, authority="CBDT (Direct Taxes)")

    assert len(items) == 2
    assert "Section 194R" in items[0]["title"]
    assert items[0]["authority"] == "CBDT (Direct Taxes)"
    assert "10%" in items[0]["summary"]
    assert items[1]["url"] == "/gst-notification-e-invoice.pdf"

def test_live_scrape_pipeline():
    scraper = RegulatoryScraperEngine()
    res = scraper.run_live_scrape()

    assert res["status"] == "success"
    assert res["items_scraped"] >= 2
    assert res["engine"] == "BeautifulSoup4 HTML Parser"
    assert len(scraper.scraped_history) >= 2

