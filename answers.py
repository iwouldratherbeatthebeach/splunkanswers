import requests
from lxml import html
import os

BASE_URL = "https://community.splunk.com"
OUTPUT_DIR = "splunk_answers"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def get_page_content(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.content

def parse_question_and_responses(question_url):
    response = requests.get(question_url)
    response.raise_for_status()
    tree = html.fromstring(response.content)
    
    # Extract main question content
    question_content = tree.xpath('//div[@class="lia-message-body-content"]')
    question_text = question_content[0].text_content().strip() if question_content else "No Question Content Found"
    
    # Extract responses and comments
    response_blocks = tree.xpath(
        '//div[contains(@class, "lia-message-body")]//div[@class="lia-message-body-content"] | '
        '//div[contains(@class, "lia-message-reply-body")]//div[@class="lia-message-body-content"] | '
        '//div[contains(@class, "lia-message-comment-body")]//div[@class="lia-message-body-content"]'
    )
    
    response_texts = [resp.text_content().strip() for resp in response_blocks]
    
    # Remove duplicate question content from responses
    response_texts = [resp for resp in response_texts if resp != question_text]
    
    print(f"DEBUG: Found {len(response_texts)} unique response sections.")
    
    return {
        'url': question_url,
        'question': question_text,
        'responses': response_texts
    }

def save_to_file(details, index):
    filename = f"{OUTPUT_DIR}/question_{index}.txt"
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(f"URL: {details['url']}\n\n")
        file.write("Question:\n")
        file.write(details['question'] + "\n\n")
        file.write("Responses:\n")
        for i, response in enumerate(details['responses'], 1):
            file.write(f"Response {i}:\n{response}\n\n")
    
    print(f"Saved: {filename}")

def scrape_single_page(page_number, max_questions=25):
    url = f"{BASE_URL}/t5/Find-Answers/ct-p/en-us-splunk-answers/page/{page_number}"
    try:
        page_content = get_page_content(url)
        tree = html.fromstring(page_content)
        question_links = tree.xpath('//h3[@class="message-subject"]//a/@href')
        return [BASE_URL + link for link in question_links][:max_questions]
    except Exception as e:
        print(f"Failed to scrape page {page_number}: {e}")
        return []

def scrape_splunk_answers():
    question_index = 1
    page_number = 1
    
    while True:
        print(f"Scraping page {page_number}...")
        question_links = scrape_single_page(page_number)
        
        if not question_links:
            print("No more questions found. Ending scrape.")
            break
        
        for link in question_links:
            try:
                details = parse_question_and_responses(link)
                save_to_file(details, question_index)
                question_index += 1
            except Exception as e:
                print(f"Failed to scrape question at {link}: {e}")
        
        page_number += 1  # Move to next page

if __name__ == "__main__":
    scrape_splunk_answers()
