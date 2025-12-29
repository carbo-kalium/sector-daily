# GitHub Setup & Deployment Guide

## Quick Start: Push to GitHub

```bash
cd /home/chinmay/projects/tradeselect/sector-daily

# Initialize Git (if not already done)
git init
git add .
git commit -m "Initial commit: Sector Intelligence Daily blog"

# Create and push to GitHub
git branch -M main
git remote add origin https://github.com/carbo-kalium/sector-daily.git
git push -u origin main
```

## Enable GitHub Pages

1. Go to your repo: https://github.com/carbo-kalium/sector-daily
2. Click **Settings** → **Pages** (left sidebar)
3. Under "Build and deployment":
   - Source: **GitHub Actions**
4. Save changes

Your blog will be live at: `https://carbo-kalium.github.io/sector-daily/`

## Custom Domain Setup (Namecheap)

### 1. Buy your domain (e.g., `sector-intel.com`)

### 2. Configure DNS at Namecheap

Go to Namecheap Dashboard → Domain List → Manage → Advanced DNS:

Add these records:

| Type  | Host | Value                      | TTL  |
|-------|------|----------------------------|------|
| A     | @    | 185.199.108.153            | Auto |
| A     | @    | 185.199.109.153            | Auto |
| A     | @    | 185.199.110.153            | Auto |
| A     | @    | 185.199.111.153            | Auto |
| CNAME | www  | carbo-kalium.github.io     | Auto |

### 3. Update GitHub Pages Settings

1. Go to repo **Settings** → **Pages**
2. Under "Custom domain", enter: `sector-intel.com`
3. Check "Enforce HTTPS" (after DNS propagates, ~24 hours)

### 4. Update `_config.yml`

```yaml
url: "https://sector-intel.com"
baseurl: ""
```

Commit and push the change.

## SEO & Monetization

### Google Search Console
1. Visit https://search.google.com/search-console
2. Add property: `https://sector-intel.com`
3. Verify via DNS TXT record or HTML file
4. Submit sitemap: `https://sector-intel.com/sitemap.xml`

### Google AdSense
1. Apply at https://www.google.com/adsense
2. Add AdSense code to `_includes/head.html` (create if needed)
3. Wait for approval (~1-2 weeks)
4. Place ad units in templates

### Analytics
Add to `_config.yml`:
```yaml
google_analytics: UA-XXXXXXXXX-X
```

## Daily Operation

- **Automatic**: Pipeline runs daily at 8 AM UTC via GitHub Actions
- **Manual trigger**: Go to Actions tab → "Daily Sector Intelligence Pipeline" → "Run workflow"
- **View logs**: Actions tab shows fetch status for each run

## Troubleshooting

**If workflow fails:**
- Check Actions logs for errors
- Verify RSS sources are accessible
- Ensure GitHub Pages is enabled

**If posts don't appear:**
- Wait 2-3 minutes for Pages deployment
- Check workflow completed successfully
- Clear browser cache

## Future Enhancements

- Add email newsletter signup (Mailchimp/ConvertKit)
- Social sharing buttons on posts
- Related articles section
- Historical charts/trends
- Mobile app version
