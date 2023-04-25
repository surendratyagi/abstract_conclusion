import PyPDF2
import spacy
import re
import csv
import os
from collections import Counter
from heapq import nlargest
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTTextContainer, LTTextLineHorizontal

import sys


# Get the paths of the two directories from the command line arguments
pdf_folder = sys.argv[1]
csv_path = sys.argv[2]
'''
# Get the paths of the two directories from the command line arguments
pdf_folder = sys.argv[1]
csv_path = sys.argv[2]


# Define the path to the folder containing the PDF files
pdf_folder = 'C:\\Users\\1001 SURENDRA TYAGI\\Downloads\\mchine learning papers\\MATLAB'

# Define the path to the output CSV file
csv_path = 'C:\\Users\\1001 SURENDRA TYAGI\\Downloads\\mchine learning papers\\MATLAB\\Summary_data.csv'
'''
# Initialize an empty list to store the data
data = []

def get_title(pdf_path):
    # Initialize variables
    highest_font_size = 0
    highest_font_text = ''

    # Extract text from first page of PDF
    for page_layout in extract_pages(pdf_path, page_numbers=[0]):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    '''if not isinstance(text_line, LTChar):'''
                    if isinstance(text_line, LTTextLineHorizontal):
                        font_size = 0
                        text = ''
                        for character in text_line:
                            if isinstance(character, LTChar):
                                font_size = character.size
                                text += character.get_text()
                        if font_size == highest_font_size:
                            highest_font_size = font_size
                            highest_font_text += text
                        elif font_size > highest_font_size:
                            highest_font_size = font_size
                            highest_font_text = text

    # Return highest font text
    return highest_font_text

# Loop through each PDF file in the folder
for filename in os.listdir(pdf_folder):
    # Check if the file is a PDF file
    if filename.endswith('.pdf'):
        # Define the path to the PDF file
        pdf_path = os.path.join(pdf_folder, filename)
        title = ''
        title = get_title(pdf_path)

        # Open the PDF file in read-binary mode
        with open(pdf_path, 'rb') as f:
            # Create a PDF reader object
            reader = PyPDF2.PdfReader(f)
            #reader.decrypt('')
            
            # Get the total number of pages in the PDF document
            num_pages = len(reader.pages)
            
            # Initialize an empty string to store the extracted text
            text = ''
            
            # Loop through each page of the PDF document
            for i in range(num_pages):
                # Get the current page
                page = reader.pages[i]
                
                # Extract the text from the current page
                page_text = page.extract_text()
                
                # Add the extracted text to the overall text string
                text += page_text
        
        # Load the English language model
        if len(text)>= 2000000:
            continue
        nlp = spacy.load('en_core_web_sm')
        nlp.max_length = 2000000  # or any other larger value depending on your input text

        
        # Parse the text using the NLP model
        doc = nlp(text)
        
        # Extract the title
        # Initialize variables
        highest_font_size = 0
        highest_font_text = ''

        # Search for the "Abstract" section in the PDF file
        found_abstract = False
        for page_num in range(num_pages):
            page = reader.pages[page_num]
            text = page.extract_text()
            # Clean up the extracted text
            text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            text = re.sub('\s+', ' ', text).strip()
            if "abstract" in text.lower():
                # Found the "abstract" section
                found_abstract = True
                # Extract the text between the "Conclusion" section and the "References" section
                abstract_index = text.lower().find("abstract")
                if "introduction" in text.lower():
                    introduction_index = text.lower().find("introduction")
                    abstract_text = text[abstract_index + len("abstract"):introduction_index].strip()
                else:
                    abstract_text = text[abstract_index + len("abstract"):].strip()
                break 
        

        # Search for the "Conclusion" section in the PDF file
        found_conclusion = False
        for page_num in range(num_pages):
            page = reader.pages[num_pages-(page_num+1)]
            text = page.extract_text()
            # Clean up the extracted text
            text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            text = re.sub('\s+', ' ', text).strip()
            if "conclusion" in text.lower():
                # Found the "Conclusion" section
                found_conclusion = True
                # Extract the text between the "Conclusion" section and the "References" section
                conclusion_index = text.lower().find("conclusion")
                if "references" in text.lower():
                    reference_index = text.lower().find("references")
                    conclusion_text = text[conclusion_index + len("conclusion"):reference_index].strip()
                else:
                    conclusion_text = text[conclusion_index + len("conclusion"):].strip()
                break

                
        # If no title is found based on font size, try to extract it using a regular expression
        if not title:
            # Define a regular expression pattern to match titles
            title_pattern = re.compile(r'^\s*([\w\d\s\-\,\(\)\:\;]+)[\n\r\f\v]+={2,}')

            # Search for the pattern in the text
            match = title_pattern.search(text)

            # If a match is found, extract the title
            if match:
                title = match.group(1).strip()

        # If no title is found, use the PDF file name
        if not title:
            title = os.path.splitext(os.path.basename(pdf_path))[0]

        # Extract the abstract and conclusion
        abstract = ''
        conclusion = ''

        if found_abstract:
            abstract = abstract_text
        else:
            abstract = None
            
        if not abstract:
            for sent in doc.sents:
                for token in sent:
                    if 'abstract' in token.lower_:
                        abstract = sent.text
                        break


        if found_conclusion:
            conclusion = conclusion_text
        else:
            conclusion = None
        if not conclusion:
            for sent in reversed(list(doc.sents)):
                for token in sent:
                    if 'conclusion' in token.lower_:
                        conclusion = sent.text
                        break

        # Get the most frequent words in the document
        word_freq = Counter([token.text for token in doc if not token.is_stop and not token.is_punct])
        max_freq = max(word_freq.values())
        
        # Calculate the importance score for each sentence
        sent_scores = []
        for sent in doc.sents:
            score = sum([word_freq[token.text] / max_freq for token in sent if not token.is_stop and not token.is_punct])
            # Check if score is zero to avoid dividing by zero error
            if score != 0:
                sent_scores.append((sent, score))
        # Get the top 3 most important sentences
        top_sents = nlargest(3, sent_scores, key=lambda x: x[1])
        top_sents = [sent[0].text.strip() for sent in top_sents]
    
        # Add the extracted data to the list #'top_sentences': top_sents
        data.append({
            'file_name': filename,
            'title': title,
            'abstract': abstract,
            'conclusion': conclusion
            })
        
#Write the data to a CSV file
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    # Define the column names
    #fieldnames = ['file_name', 'title', 'abstract', 'conclusion', 'top_sentences']
    fieldnames = ['file_name', 'title', 'abstract', 'conclusion']
    # Create a CSV writer object
    writer = csv.DictWriter(f, fieldnames=fieldnames)

    # Write the header row
    writer.writeheader()

    # Write the data rows
    for row in data:
        writer.writerow(row)

print('Done')

