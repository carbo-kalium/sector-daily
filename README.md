# 📊 Sector Intelligence Daily

> **Free daily market intelligence blog** covering 11 major sectors with curated news from 10+ trusted financial sources.

[![Daily Updates](https://img.shields.io/badge/updates-daily%20at%208AM%20UTC-blue)](https://github.com/carbo-kalium/sector-daily/actions)
[![GitHub Pages](https://img.shields.io/badge/blog-live-success)](https://carbo-kalium.github.io/sector-daily/)

## 🎯 What is this?

An **automated financial news aggregator** that:
- ✅ Fetches from 10+ free RSS sources (CNBC, Bloomberg, Yahoo Finance, etc.)
- ✅ Classifies articles into 11 SPDR ETF-aligned sectors using keyword + company matching
- ✅ Generates SEO-optimized daily blog posts in Markdown
- ✅ Publishes automatically to GitHub Pages every morning
- ✅ Ready for custom domain + monetization

## 🚀 Live Blog

**View at:** https://carbo-kalium.github.io/sector-daily/

## 📈 Sectors Covered

| Sector | ETF | Examples |
|--------|-----|----------|
| Energy | XLE | Exxon, Chevron, oil prices |
| Materials | XLB | Mining, metals, chemicals |
| Industrials | XLI | Boeing, airlines, logistics |
| Consumer Discretionary | XLY | Amazon, Tesla, retail |
| Consumer Staples | XLP | Walmart, Coca-Cola, P&G |
| Health Care | XLV | Pfizer, UnitedHealth, biotech |
| Financials | XLF | JPMorgan, banks, Fed policy |
| Information Technology | XLK | Apple, Microsoft, Nvidia, AI |
| Communication Services | XLC | Meta, Google, Netflix |
| Utilities | XLU | Power, renewables, utilities |
| Real Estate | XLRE | REITs, commercial property |

## 🛠️ Local Development

```bash
# Setup
python -m venv sectors
source sectors/bin/activate
pip install -r requirements.txt
pip install -e .

# Run pipeline
sector-intel run --date $(date +%Y-%m-%d)

# Output: output/YYYY-MM-DD/*.md
```

## 📝 Configuration

- **RSS sources:** `config/rss_sources.yml` (10 sources)
- **Sector rules:** `config/sectors.yml` (keywords + companies per sector)
- **Template:** `templates/sector_daily.md.j2` (SEO-optimized Markdown)

## 🤖 Automation

Daily updates via **GitHub Actions**:
- Runs at **8:00 AM UTC** every day
- Fetches latest news, classifies, deduplicates
- Commits new posts to `output/YYYY-MM-DD/`
- Deploys to GitHub Pages automatically

## 📖 Setup Guide

See [SETUP.md](SETUP.md) for:
- Pushing to GitHub
- Enabling GitHub Pages
- Custom domain setup (Namecheap)
- SEO & monetization (Google AdSense)

## 🎨 Features

✨ **SEO Optimized**
- Catchy titles: "Energy Sector Daily Brief: Top Market News & Analysis"
- Meta descriptions with keywords
- Open Graph tags for social sharing
- Auto-generated sitemaps

✨ **Clean Formatting**
- Numbered headlines
- Blockquote excerpts
- Source attribution with timestamps
- Navigation links between sectors

✨ **Production Ready**
- Persistent dedup (7-day memory)
- Error handling for failed sources
- Logging for monitoring
- Extensible architecture

## 💰 Monetization Ready

Blog is designed for:
- Google AdSense integration
- Affiliate links
- Sponsored content
- Premium newsletter tiers

## 📊 Tech Stack

- **Python 3.12**
- **Feedparser** (RSS parsing)
- **Jinja2** (templating)
- **Jekyll** (static site generation)
- **GitHub Actions** (CI/CD)
- **GitHub Pages** (hosting)

## 📜 License

Content sourced from public RSS feeds. Original aggregation and classification logic is open source.

## 🤝 Contributing

Ideas for enhancements:
- More RSS sources
- Better sector keywords
- UI/UX improvements
- Analytics dashboard

---

**Built by:** [carbo-kalium](https://github.com/carbo-kalium)  
**Live at:** https://carbo-kalium.github.io/sector-daily/
# Trigger deployment
