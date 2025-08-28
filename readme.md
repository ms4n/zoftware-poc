# Zoftware POC - Capterra Scraper

## Challenge: Bypassing Sophisticated Anti-Bot Protection

### Blocker #1: Cloudflare Enterprise Protection

**Problem**: Capterra uses advanced Cloudflare protection that blocked all automation attempts

- Simple `curl` requests → "Attention Required! | Cloudflare"
- Playwright + stealth techniques → 403 Forbidden
- Rotating proxies + user-agents → Still blocked
- Even browser-like headers failed

**Evidence**: `curl -H "User-Agent: Mozilla/..." https://www.capterra.in/directory` returned Cloudflare block page

**Root Cause**: Sophisticated detection beyond User-Agent checks:

- TLS fingerprinting
- JavaScript challenges requiring execution
- Browser behavior pattern analysis
- Missing "human" browser characteristics

### Blocker #2: Framework Architecture Conflicts

**Problem**: Mixed async/sync code and incorrect status checking

- Scrapy's HTTP response showed 403, but `undetected-chromedriver` navigation was actually working
- Base spider had async methods conflicting with synchronous approach

### Solution: `undetected-chromedriver`

**Breakthrough**: Replaced Playwright with `undetected-chromedriver`

- **Result**: Complete Cloudflare bypass ✅
- Successfully scraped 50+ products across 2 pages
- Perfect data extraction: names, links, logos, categories, pagination

**Key Insight**: Enterprise anti-bot protection requires tools specifically designed for evasion, not just stealth layers on standard automation.

### Blocker #3: Headless Mode Detection

**Problem**: Cloudflare applies stricter detection for headless browsers

- **Headful mode** (visible browser): ✅ Complete bypass
- **Headless mode**: ❌ "Attention Required! | Cloudflare"

**Solution**: Production deployment requires headful mode for Capterra

## Final Success Metrics

- ✅ 999 categories discovered
- ✅ Random sampling working
- ✅ 50 products scraped from "Speech Analytics" category
- ✅ Pagination across multiple pages
- ✅ Complete data extraction pipeline
- ✅ Confirmed headful mode requirement for production
- ✅ Configurable proxy support for scale
