import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from weasyprint import HTML, CSS
import sys

BASE_URL = "https://www.anthropic.com/engineering"
OUTPUT_PDF = "anthropic_engineering_book.pdf"

def get_article_links():
    print("Fetching article links...")
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    links = []
    seen = set()
    # Find all links that look like articles
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/engineering/' in href and href != '/engineering':
            full_url = urljoin(BASE_URL, href)
            if full_url not in seen:
                links.append(full_url)
                seen.add(full_url)
    
    print(f"Found {len(links)} articles.")
    return links

def process_article(url, index):
    print(f"Processing article {index + 1}: {url}")
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract stylesheets
        stylesheets = []
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                stylesheets.append(urljoin(url, href))
        
        # Extract content
        # Try finding <article> first
        content = soup.find('article')
        if not content:
            # Fallback to main > div > div pattern if article tag is missing
            main = soup.find('main')
            if main:
                children = main.find_all(recursive=False)
                if len(children) >= 2:
                    content = children[1]
        
        if not content:
            print(f"  WARNING: Could not find content for {url}")
            return None, []

        # Fix relative URLs
        for img in content.find_all('img'):
            if img.get('src'):
                img['src'] = urljoin(url, img['src'])
            if img.get('srcset'):
                # WeasyPrint might not handle srcset well, so let's try to pick the largest src or just leave it
                # For now, let's just ensure src is absolute.
                pass
                
        for a in content.find_all('a'):
            if a.get('href'):
                a['href'] = urljoin(url, a['href'])
        
        # Extract title
        title = "Untitled Article"
        h1 = content.find('h1')
        if h1:
            title = h1.get_text().strip()
        else:
            # Try to find h1 in the page if not in content
            page_h1 = soup.find('h1')
            if page_h1:
                title = page_h1.get_text().strip()
                # Prepend h1 to content
                new_h1 = soup.new_tag('h1')
                new_h1.string = title
                content.insert(0, new_h1)

        return str(content), stylesheets, title

    except Exception as e:
        print(f"  ERROR processing {url}: {e}")
        return None, [], "Error"

def generate_book():
    links = get_article_links()
    
    articles_data = []
    all_stylesheets = set()
    
    # Process articles
    for i, link in enumerate(links):
        content, stylesheets, title = process_article(link, i)
        if content:
            all_stylesheets.update(stylesheets)
            # Create a unique ID for the article
            article_id = f"article-{i}"
            articles_data.append({
                "title": title,
                "content": content,
                "id": article_id
            })

    # Generate HTML
    
    # Cover Page
    cover_html = """
    <div style="text-align: center; page-break-after: always; display: flex; flex-direction: column; justify-content: center; height: 100vh;">
        <img src="cover.png" style="max-width: 100%; max-height: 50vh; margin-bottom: 50px;">
        <h1 style="font-size: 48px; margin-bottom: 20px;">Anthropic Engineering Blog</h1>
        <p style="font-size: 24px; color: #666;">A collection of engineering articles</p>
        <p style="margin-top: 100px; font-size: 14px; color: #999;">Generated Book</p>
    </div>
    """
    
    # Table of Contents
    toc_items = []
    for article in articles_data:
        toc_items.append(f'<li><a href="#{article["id"]}">{article["title"]}</a></li>')
    
    toc_html = f"""
    <div style="page-break-after: always;">
        <h1>Table of Contents</h1>
        <ul style="list-style-type: none; padding: 0;">
            {''.join(toc_items)}
        </ul>
    </div>
    """
    
    final_content = [cover_html, toc_html]
    
    for article in articles_data:
        # Inject ID into the first header or a wrapper div
        # We'll wrap the content in a div with the ID
        wrapped_content = f'<div id="{article["id"]}">{article["content"]}</div>'
        final_content.append(wrapped_content)
        final_content.append('<div style="page-break-after: always;"></div>')
    
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Anthropic Engineering Blog</title>
        {''.join([f'<link rel="stylesheet" href="{css}">' for css in all_stylesheets])}
        <style>
            @page {{ margin: 2cm; }}
            body {{ font-family: sans-serif; }}
            img {{ max-width: 100%; height: auto; }}
            pre {{ white-space: pre-wrap; word-wrap: break-word; background: #f5f5f5; padding: 10px; }}
            code {{ word-break: break-all; }}
            a {{ text-decoration: none; color: #000; }}
            a:hover {{ text-decoration: underline; }}
            ul li {{ margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        </style>
    </head>
    <body>
        {''.join(final_content)}
    </body>
    </html>
    """
    
    # Save HTML for debugging
    with open("book.html", "w") as f:
        f.write(full_html)
    
    print("Generating PDF...")
    HTML(string=full_html, base_url=BASE_URL).write_pdf(OUTPUT_PDF)
    print(f"PDF generated: {OUTPUT_PDF}")

if __name__ == "__main__":
    generate_book()
