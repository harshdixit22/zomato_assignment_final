import requests
from bs4 import BeautifulSoup
import re
import json

def extract_menu_items(soup):
    menu_items = []
    # Enhanced price pattern with context awareness
    price_pattern = r'(?:price|₹|Rs\.?)\s*([\d,]+)'
    
    menu_sections = soup.find_all('section', class_='product-area')
    
    for section in menu_sections:
        category_header = section.find('h2')
        if not category_header:
            continue
            
        category = category_header.get_text(strip=True).replace('Top Rated - ', '')
        items = section.find_all('div', class_=['strip', 'item_version_2', 'list_home'])
        
        for item in items:
            try:
                # Item name extraction
                name_tag = item.find('h3') or item.find('h4') or item.find('strong')
                name = name_tag.get_text(strip=True) if name_tag else 'Unnamed Item'
                
                # Price detection with multiple fallbacks
                price = None
                
                # 1. Check explicit price elements
                price_tag = item.find('li', text=re.compile(r'price', re.I))
                if not price_tag:
                    price_tag = item.find('span', class_=re.compile(r'price', re.I))
                
                # 2. Search all text in item for price pattern
                if not price_tag:
                    full_text = item.get_text()
                    price_match = re.search(price_pattern, full_text, re.IGNORECASE)
                    if price_match:
                        price = f'₹{price_match.group(1)}'
                
                # 3. Format extracted price
                if price_tag:
                    price_text = price_tag.get_text(strip=True)
                    price_match = re.search(price_pattern, price_text, re.IGNORECASE)
                    if price_match:
                        price = f'₹{price_match.group(1)}'
                
                # Image extraction with multiple fallbacks
                img = item.find('img')
                image_url = (
                    img.get('data-src', '') or 
                    img.get('src', '') or 
                    img.get('data-lazy', '')
                )
                if image_url.startswith('//'):
                    image_url = f'https:{image_url}'
                
                menu_items.append({
                    'item': name,
                    'price': price or 'Price not found',
                    'category': category,
                    'image_url': image_url,
                    'full_card_text': item.get_text(strip=True, separator=' ')  # For debugging
                })
                
            except Exception as e:
                continue
    
    return menu_items

def improved_extract_contact_info(soup):
    contact_info = {}
    
    # Address extraction
    address_section = soup.find('div', id='collapse_4')
    if address_section:
        contact_info['addresses'] = [
            li.get_text(strip=True) 
            for li in address_section.find_all('li')
        ]
    
    # Phone number extraction
    phone_section = soup.find('div', class_='contacts')
    if phone_section:
        contact_info['phones'] = list(set(
            re.findall(r'\+?\d[\d\s-]{7,}', phone_section.get_text())
        ))
    
    # Email extraction
    contact_info['emails'] = [
        a['href'].replace('mailto:', '') 
        for a in soup.select('a[href^="mailto:"]')
    ]
    
    return contact_info

def scrape_tundaykababi():
    url = 'https://www.tundaykababi.com/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        return {
            'menu': extract_menu_items(soup),
            'contact_info': improved_extract_contact_info(soup),
            'success': True
        }
        
    except Exception as e:
        return {'error': str(e), 'success': False}

if __name__ == '__main__':
    result = scrape_tundaykababi()
    
    if result.get('success'):
        with open('tundaykababi_data.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Successfully scraped {len(result['menu'])} menu items")
        print("Sample items:")
        for item in result['menu'][:3]:
            print(f"{item['item']}: {item['price']}")
    else:
        print(f"Scraping failed: {result.get('error')}")