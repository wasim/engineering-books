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
        
        # Add a title header if it's missing from the article body (sometimes it's in the hero section)
        # Check if h1 exists in content
        if not content.find('h1'):
            # Try to find h1 in the page
            h1 = soup.find('h1')
            if h1:
                # Prepend h1 to content
                new_h1 = soup.new_tag('h1')
                new_h1.string = h1.get_text()
                content.insert(0, new_h1)

        return str(content), stylesheets

    except Exception as e:
        print(f"  ERROR processing {url}: {e}")
        return None, []

def generate_book():
    links = get_article_links()
    
    all_content = []
    all_stylesheets = set()
    
    # Add a cover page
    cover_html = """
    <div style="text-align: center; margin-top: 200px;">
        <h1 style="font-size: 48px;">Anthropic Engineering Blog</h1>
        <p style="font-size: 24px;">A collection of engineering articles</p>
        <p style="margin-top: 100px;">Generated Book</p>
    </div>
    <div style="page-break-after: always;"></div>
    """
    all_content.append(cover_html)
    
    for i, link in enumerate(links):
        content, stylesheets = process_article(link, i)
        if content:
            all_stylesheets.update(stylesheets)
            all_content.append(content)
            all_content.append('<div style="page-break-after: always;"></div>')
    
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Anthropic Engineering Blog</title>
        {''.join([f'<link rel="stylesheet" href="{css}">' for css in all_stylesheets])}
        <style>
            body {{ font-family: sans-serif; }}
            img {{ max-width: 100%; height: auto; }}
            pre {{ white-space: pre-wrap; word-wrap: break-word; background: #f5f5f5; padding: 10px; }}
            /* Ensure code blocks don't overflow */
            code {{ word-break: break-all; }}
        </style>
    </head>
    <body>
        {''.join(all_content)}
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
