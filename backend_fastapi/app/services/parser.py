from bs4 import BeautifulSoup
from typing import List, Optional
from app.models.article import Article

class HTMLParser:
    """Parse HTML content to extract articles"""
    
    def parse_section(self, html: str, section: str, date: str) -> List[Article]:
        """Parse articles from HTML with enhanced selectors"""
        soup = BeautifulSoup(html, 'html.parser')
        articles = []

        selectors = [
            'article.story',
            'article[class*="story"]',
            '.story.box',
            '.story',
            'article',
            '.box.story',
            '.story-list article',
            'div[class*="story"]',
            '.article-box',
            '[data-story-id]'
        ]

        for selector in selectors:
            elements = soup.select(selector)
            
            if not elements:
                continue

            for el in elements:
                title_el = el.select_one(
                    'h2 a, .story__title a, h3 a, .story__link, '
                    'a.story__link, [class*="title"] a, h2, h3'
                )
                
                summary_el = el.select_one(
                    '.story__excerpt, .story__text, .excerpt, '
                    '[class*="excerpt"], p, .description'
                )

                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                url = title_el.get('href') if title_el.name == 'a' else None
                
                if not url:
                    link = el.find('a')
                    url = link.get('href') if link else None
                
                summary = summary_el.get_text(strip=True) if summary_el else ''

                if not title or not url:
                    continue

                if any(a.title == title for a in articles):
                    continue

                raw_image = self._resolve_image_url(el)
                image_url = None

                if raw_image:
                    if raw_image.startswith('//'):
                        image_url = f"https:{raw_image}"
                    elif raw_image.startswith('http'):
                        image_url = raw_image
                    else:
                        image_url = f"https://www.dawn.com{raw_image}"

                article_url = url if url.startswith('http') else f"https://www.dawn.com{url}"

                article = Article(
                    title=title,
                    url=article_url,
                    summary=summary,
                    section=section,
                    date=date,
                    imageUrl=image_url
                )
                articles.append(article)

            if articles:
                break

        return articles
    
    def _resolve_image_url(self, article_soup) -> Optional[str]:
        img = article_soup.find('img')
        picture = article_soup.find('picture')

        if img:
            for attr in ['data-src', 'data-original', 'data-lazy-src']:
                url = img.get(attr)
                if url and not url.startswith('data:image'):
                    return url

            srcset = img.get('srcset')
            if srcset:
                first = srcset.split(',')[0].strip().split(' ')[0]
                if not first.startswith('data:image'):
                    return first

        if picture:
            source = picture.find('source')
            if source:
                srcset = source.get('srcset')
                if srcset:
                    first = srcset.split(',')[0].strip().split(' ')[0]
                    return first

        if img:
            url = img.get('src')
            if url and not url.startswith('data:image'):
                return url

        return None