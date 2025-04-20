import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import random
import re
import os

# List of restaurant websites to scrape
restaurant_urls = [
    {"name": "Bresca", "url": "https://www.jainshikanji.com/menu/"},
    {"name": "Quay", "url": "https://www.quay.com.au/menu/"}
]

# Fixed function to extract menu items and prices
def extract_menu_items(soup):
    # Look for common menu item patterns
    menu_items = []
    
    # Strategy 1: Look for divs or sections with menu-related class or id
    menu_sections = soup.find_all(['div', 'section'], class_=lambda c: c and ('menu' in c.lower() if c else False))
    menu_sections += soup.find_all(['div', 'section'], id=lambda i: i and ('menu' in i.lower() if i else False))
    
    # Strategy 2: Look for menu item patterns - often items have prices nearby
    price_patterns = r'\$\d+(?:\.\d{2})?'  # matches $XX or $XX.XX
    
    # Find all paragraphs or list items that might contain menu items with prices
    potential_items = soup.find_all(['p', 'li', 'div'], string=re.compile(price_patterns))
    
    # Extract menu item text and prices
    for item in potential_items:
        item_text = item.get_text().strip()
        # Extract price using regex
        prices = re.findall(price_patterns, item_text)
        
        if prices:
            # Remove prices from item text to get just the item description
            item_clean = item_text
            for price in prices:
                item_clean = item_clean.replace(price, '').strip()
            
            menu_items.append({
                "item": item_clean,
                "price": prices[0] if prices else "Not found", 
                "description": item_text,
                # Look for dietary indicators
                "vegetarian": any(v in item_text.lower() for v in ["vegetarian", "veg", "plant-based", "meatless"]),
                "vegan": "vegan" in item_text.lower(),
                "gluten_free": any(g in item_text.lower() for g in ["gluten-free", "gluten free", "gf"]),
                "spicy": any(s in item_text.lower() for s in ["spicy", "hot", "chili"])
            })
    
    # If we still don't have many menu items, try a more aggressive approach
    if len(menu_items) < 5:
        # Look for menu headings
        menu_headings = soup.find_all(['h2', 'h3', 'h4'], string=re.compile(r'menu|appetizer|entree|dessert|starter|main', re.I))
        
        for heading in menu_headings:
            # Get the next elements after each heading
            next_elements = heading.find_next_siblings(['p', 'div', 'li', 'span'])
            for elem in next_elements[:10]:  # Limit to 10 items after each heading
                item_text = elem.get_text().strip()
                prices = re.findall(price_patterns, item_text)
                if prices:
                    item_clean = item_text
                    for price in prices:
                        item_clean = item_clean.replace(price, '').strip()
                    
                    menu_items.append({
                        "item": item_clean,
                        "price": prices[0],
                        "description": item_text,
                        "section": heading.get_text().strip(),
                        "vegetarian": any(v in item_text.lower() for v in ["vegetarian", "veg", "plant-based", "meatless"]),
                        "vegan": "vegan" in item_text.lower(),
                        "gluten_free": any(g in item_text.lower() for g in ["gluten-free", "gluten free", "gf"]),
                        "spicy": any(s in item_text.lower() for s in ["spicy", "hot", "chili"])
                    })
    
    # Manual section parsing for pages with structured menu layout
    menu_divs = soup.find_all('div', class_=lambda c: c and ('menu' in c.lower() if c else False))
    for menu_div in menu_divs:
        # Try to find menu sections and items within
        section_headings = menu_div.find_all(['h2', 'h3', 'h4'])
        for section in section_headings:
            section_name = section.get_text().strip()
            # Get all potential menu items after this section heading
            items = section.find_next_siblings(['p', 'div', 'li'])
            for item_elem in items[:15]:  # Limit to 15 items per section
                item_text = item_elem.get_text().strip()
                prices = re.findall(price_patterns, item_text)
                
                # Skip to next section heading if we encounter one
                if item_elem.name in ['h2', 'h3', 'h4']:
                    break
                    
                if prices:
                    item_clean = item_text
                    for price in prices:
                        item_clean = item_clean.replace(price, '').strip()
                    
                    menu_items.append({
                        "item": item_clean,
                        "price": prices[0],
                        "description": item_text,
                        "section": section_name,
                        "vegetarian": any(v in item_text.lower() for v in ["vegetarian", "veg", "plant-based", "meatless"]),
                        "vegan": "vegan" in item_text.lower(),
                        "gluten_free": any(g in item_text.lower() for g in ["gluten-free", "gluten free", "gf"]),
                        "spicy": any(s in item_text.lower() for s in ["spicy", "hot", "chili"])
                    })
    
    return menu_items

# Function to extract contact information and hours
def extract_contact_info(soup, url):
    contact_info = {
        "address": "Not found",
        "phone": "Not found",
        "email": "Not found",
        "hours": "Not found"
    }
    
    # Look for address using common patterns
    address_patterns = ['address', 'location', 'find us', 'directions']
    phone_patterns = ['phone', 'call', 'tel', 'contact']
    hours_patterns = ['hours', 'open', 'opening', 'time']
    
    # Check for structured data (JSON-LD)
    script_tags = soup.find_all('script', type='application/ld+json')
    for script in script_tags:
        try:
            data = json.loads(script.string)
            # Check if it's a local business or restaurant schema
            if isinstance(data, dict):
                if "@type" in data and data["@type"] in ["Restaurant", "LocalBusiness"]:
                    if "address" in data:
                        address_data = data["address"]
                        contact_info["address"] = f"{address_data.get('streetAddress', '')}, {address_data.get('addressLocality', '')}, {address_data.get('addressRegion', '')} {address_data.get('postalCode', '')}"
                    if "telephone" in data:
                        contact_info["phone"] = data["telephone"]
                    if "openingHoursSpecification" in data:
                        hours_data = data["openingHoursSpecification"]
                        hours_text = []
                        for hours in hours_data if isinstance(hours_data, list) else [hours_data]:
                            day = hours.get("dayOfWeek", "")
                            opens = hours.get("opens", "")
                            closes = hours.get("closes", "")
                            hours_text.append(f"{day}: {opens}-{closes}")
                        contact_info["hours"] = ", ".join(hours_text)
            # Handle graphs
            if isinstance(data, dict) and "@graph" in data:
                for item in data["@graph"]:
                    if item.get("@type") in ["Restaurant", "LocalBusiness"]:
                        if "address" in item:
                            address_data = item["address"]
                            contact_info["address"] = f"{address_data.get('streetAddress', '')}, {address_data.get('addressLocality', '')}, {address_data.get('addressRegion', '')} {address_data.get('postalCode', '')}"
                        if "telephone" in item:
                            contact_info["phone"] = item["telephone"]
                        if "openingHoursSpecification" in item:
                            hours_data = item["openingHoursSpecification"]
                            hours_text = []
                            for hours in hours_data if isinstance(hours_data, list) else [hours_data]:
                                day = hours.get("dayOfWeek", "")
                                opens = hours.get("opens", "")
                                closes = hours.get("closes", "")
                                hours_text.append(f"{day}: {opens}-{closes}")
                            contact_info["hours"] = ", ".join(hours_text)
        except:
            continue
    
    # If structured data didn't work, try other methods
    if contact_info["address"] == "Not found":
        # Look for address in paragraphs, spans, or divs
        for pattern in address_patterns:
            address_elements = soup.find_all(['p', 'span', 'div'], string=re.compile(pattern, re.I))
            for element in address_elements:
                # Look for text that might be an address (contains digits and street-related words)
                text = element.get_text().strip()
                if re.search(r'\d+.*(?:street|st\.|avenue|ave\.|road|rd\.|blvd|boulevard)', text, re.I):
                    contact_info["address"] = text
                    break
    
    # Look for phone numbers
    if contact_info["phone"] == "Not found":
        phone_regex = r'(?:\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
        for pattern in phone_patterns:
            phone_elements = soup.find_all(['p', 'span', 'div', 'a'], string=re.compile(pattern, re.I))
            for element in phone_elements:
                matches = re.search(phone_regex, element.get_text())
                if matches:
                    contact_info["phone"] = matches.group(0)
                    break
        
        # Also check for tel: links
        tel_links = soup.find_all('a', href=re.compile(r'^tel:'))
        if tel_links and len(tel_links) > 0:
            contact_info["phone"] = tel_links[0]['href'].replace('tel:', '')
    
    # Look for email
    email_links = soup.find_all('a', href=re.compile(r'^mailto:'))
    if email_links and len(email_links) > 0:
        contact_info["email"] = email_links[0]['href'].replace('mailto:', '')
    
    # Look for hours
    if contact_info["hours"] == "Not found":
        for pattern in hours_patterns:
            hours_elements = soup.find_all(['p', 'div', 'span'], string=re.compile(pattern, re.I))
            for element in hours_elements:
                # Check if the text contains day names (likely hours)
                text = element.get_text().strip()
                if re.search(r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', text, re.I):
                    contact_info["hours"] = text
                    break
    
    return contact_info

# Function to scrape restaurant data
def scrape_restaurant(restaurant_dict):
    name = restaurant_dict["name"]
    url = restaurant_dict["url"]
    print(f"Scraping {name} at {url}...")
    
    try:
        # Set headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Send a GET request to the restaurant website
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract restaurant metadata
            title = soup.title.string if soup.title else "No title found"
            
            # Extract menu items
            menu_items = extract_menu_items(soup)
            
            # Extract contact information
            contact_info = extract_contact_info(soup, url)
            
            # Calculate price range
            prices = [float(item["price"].replace("$", "")) for item in menu_items 
                     if item["price"] != "Not found" and "$" in item["price"]]
            
            min_price = min(prices) if prices else 0
            max_price = max(prices) if prices else 0
            
            # Compile restaurant data
            restaurant_data = {
                "name": name,
                "url": url,
                "title": title,
                "menu_items": menu_items,
                "contact_info": contact_info,
                "dietary_options": {
                    "vegetarian_count": sum(1 for item in menu_items if item.get("vegetarian", False)),
                    "vegan_count": sum(1 for item in menu_items if item.get("vegan", False)),
                    "gluten_free_count": sum(1 for item in menu_items if item.get("gluten_free", False)),
                    "spicy_count": sum(1 for item in menu_items if item.get("spicy", False))
                },
                "item_count": len(menu_items),
                "price_range": {
                    "min": min_price,
                    "max": max_price
                }
            }
            
            return restaurant_data
        else:
            return {"name": name, "url": url, "error": f"Failed to fetch page: Status code {response.status_code}"}
    
    except Exception as e:
        return {"name": name, "url": url, "error": f"Exception: {str(e)}"}

# Scrape data from all restaurants
results = []
for restaurant in restaurant_urls:
    data = scrape_restaurant(restaurant)
    results.append(data)
    # Be respectful with delay between requests
    time.sleep(random.uniform(2, 4))

# Display basic results summary
summary = []
for restaurant in results:
    if "error" in restaurant:
        summary.append({
            "name": restaurant["name"],
            "url": restaurant["url"],
            "status": "Error",
            "error": restaurant["error"]
        })
    else:
        summary.append({
            "name": restaurant["name"],
            "url": restaurant["url"],
            "status": "Success",
            "menu_items_found": restaurant["item_count"],
            "price_range": f"${restaurant['price_range']['min']} - ${restaurant['price_range']['max']}" if restaurant['price_range']['max'] > 0 else "Not found",
            "vegetarian_items": restaurant["dietary_options"]["vegetarian_count"],
            "contact_info": "✓" if restaurant["contact_info"]["address"] != "Not found" or restaurant["contact_info"]["phone"] != "Not found" else "✗"
        })

# Display summary table
summary_df = pd.DataFrame(summary)
print(summary_df)

# Save the data to JSON
if not os.path.exists('data'):
    os.makedirs('data')

# Save the restaurant data
with open('data/restaurant_data.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nSaved restaurant data to data/restaurant_data.json")

# Print detailed sample of first restaurant with menu items
print("\nDetailed sample of first restaurant's menu items:")
for restaurant in results:
    if "menu_items" in restaurant and len(restaurant["menu_items"]) > 0:
        print(f"\n{restaurant['name']} Menu Sample:")
        sample_items = restaurant["menu_items"][:3] if len(restaurant["menu_items"]) > 3 else restaurant["menu_items"]
        for i, item in enumerate(sample_items):
            print(f"{i+1}. {item.get('item', 'Unnamed item')}")
            print(f"   Price: {item.get('price', 'Not found')}")
            print(f"   Dietary: {'Vegetarian ' if item.get('vegetarian', False) else ''}{'Vegan ' if item.get('vegan', False) else ''}{'Gluten-free ' if item.get('gluten_free', False) else ''}{'Spicy' if item.get('spicy', False) else 'None specified'}")
        
        print(f"\n{restaurant['name']} Contact Information:")
        for key, value in restaurant["contact_info"].items():
            print(f"- {key.capitalize()}: {value}")
        print(f"Total Menu Items: {restaurant['item_count']}")
        print(f"Price Range: ${restaurant['price_range']['min']} - ${restaurant['price_range']['max']}" if restaurant['price_range']['max'] > 0 else "Price Range: Not found")
        print(f"Dietary Options:")
        print(f"- Vegetarian Items: {restaurant['dietary_options']['vegetarian_count']}")
        print(f"- Vegan Items: {restaurant['dietary_options']['vegan_count']}")
        print(f"- Gluten-free Items: {restaurant['dietary_options']['gluten_free_count']}")
        print(f"- Spicy Items: {restaurant['dietary_options']['spicy_count']}")
        break