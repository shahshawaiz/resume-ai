import json

from dotenv import dotenv_values
import fitz  # PyMuPDF

import openai
from openai import OpenAI

from pdf2docx import Converter


# 1. drop in cv
# 2. copy/paste content of job ad
# 3. generate well formatted resume/cover letter in different templates


def get_text_in_pdf(original_pdf_path):
    # Open the original PDF
    doc = fitz.open(original_pdf_path)
    
    #
    text_list = []

    #
    for page_num in range(len(doc)):
        #
        page = doc.load_page(page_num)


        # Extract text blocks
        blocks = page.get_text("dict")["blocks"]

        for block_id, block in enumerate(blocks):

            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]

                        #
                        text_list.append(text)
    #
    doc.close()

    #
    return text_list

def replace_text_in_pdf(original_pdf_path, output_pdf_path, orignal_text_dict, replacements):
    # Open the original PDF
    doc = fitz.open(original_pdf_path)
    new_doc = fitz.open()

    # Use a standard font
    standard_font = "Helvetica"

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)

        # Extract text blocks
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        # Replace text if there's a replacement provided
                        for replacement_block in replacements:
                            text_block_id = replacement_block["text_block_id"]
                            text_block = replacement_block["text_block"]

                            #
                            original = orignal_text_dict[text_block_id]
                            text_block_replacement = text_block["replacement"]

                            # Replace the text
                            text = text.replace(original, text_block_replacement)
                        # Add text to the new PDF using a standard font
                        new_page.insert_text((span["bbox"][0], span["bbox"][1]), text, fontsize=span["size"], fontname=standard_font)

    new_doc.save(output_pdf_path)
    new_doc.close()
    doc.close()

def convert_pdf_to_doc(pdf_path):
    # convert pdf to doc
    cv = Converter(pdf_path)
    cv.convert(pdf_path.replace('.pdf', '.docx'), start=0, end=None)
    cv.close()  
                
def get_completion(message_queue):
    # init client
    config = dotenv_values(".env")

    #
    client = OpenAI(api_key=config['OPENAI_API_KEY'])
    response = None

    # get completion
    try:
        completion = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=message_queue,
            response_format={ "type": "json_object" }
        )

        response = completion.choices[0].message.content

        # load json
        response = json.loads(response)

    except Exception as e:
        print(e)
        return None

    return response



# init vars
original_pdf_path = 'Resume-Shawaiz-Shah.pdf'
output_pdf_path = original_pdf_path.replace('.pdf', '_optimized.pdf')

# # define replacements
# replacements = [{
#     "original": "I have a passion for",
#     "replacement": "I absolutely love"
# },
# {
#     "original": "exact original text from resume, item 2",
#     "replacement": "optimized text from resume, , item 2"
# },
# {
#     "original": "exact original text from resume, item 3",
#     "replacement": "optimized text from resume, , item 3"
# }]  # Define your replacements here

# get text block
text_blocks = get_text_in_pdf(original_pdf_path)
text_blocks_dict = {}

#
for index, text_block in enumerate(text_blocks):
    text_blocks_dict[index] = text_block


print("text blocks", len(text_blocks))

# init message queue
message_queue = [
    {
        "role": "system",
        "content": """You are an expert CV writer responsible for rewriting a given resume with respect to a given job ad to make it more appealing to job recruiter who has posted that job ad.

Objective: 
Enhance the content of the given resume to make it more appealing and increase the probability of being shortlisted by automated HR tools and recruiters.

Input Required:
1. Resume Text Blocks: Text blocks from candidate's resume to rewrite
1. Job Ad: Job ad by the recruiter

Task Overview:
* You are tasked with rewriting sections of the resume to align them more closely with the job description.
* The focus is on optimizing the resume for automated screening tools and recruiter appeal.


Rules and Guidelines:
1. Only rewrite sections which really need update. Dont make it sound so fancy
2. Maintain Key Nouns: Do not alter company names, titles, dates, or specific names.
3. Scope Limitation: Work only on the intro, experience, or skills sections.
4. Length Consistency: Ensure the original and replacement texts are of the same length.
5. Preserve Meaning: Keep the original intent and meaning of the text.
6. Retain Formatting: Do not change the format of the text.
7. Keyword Incorporation: Embed keywords from the job description in the replacement text.
8. Fix all text block where necessary.

Task Execution:

1. Rewriting Phase:
* Create a replacement text for each block of original text.
Integrate relevant keywords from the job description into the new text.
2. Validation:
* Verify that the replacement text adheres to the specified guidelines.
* Ensure the replacement text is aligned with job requirements and remains compelling.
3. Improvement Iteration:
* Repeat the rewriting and validation until full compliance is achieved.

Expected Output Format:
```json{
    "type" : "array",
    "items" : {
        "type" : "object",
        "properties" : {
            "text_block_id": {
                type: "number",
                description: "Index of the text block in the resume"
            },
            "text_block": {
                "type": "object",
                "properties": {
                    "original" : {
                        "type" : "str",
                        "description" : "Original text block as provided by user"
                    },
                    "replacement" : {
                        "type" : "str",
                        "description" : "Optimized text block for the resume."
                    }                
                }
            }
        }
    }
}```""".strip()   
    },
    {
        "role": "user",
        "content": f""""Text Blocks: {text_blocks_dict}

Job Description:
Pendulum is a venture-backed AI company addressing the global need to do more with less. Pendulum AI-driven supply chain solutions forecast demand, optimize supply and geolocate - continuously improving on their own. The first major investment in AI by the Bill & Melinda Gates Foundation was in Pendulum; today our technology works for customers across 10+ countries – driving profitable growth and saving lives.

The Pendulum team works across Europe, North America and Africa. We believe in recruiting the best talent in the world, regardless of location. This role will be remote with the freedom to choose how and when to work. Our remote team has been executing at the highest level for a decade. You will have access to your choice of hardware and a travel budget to interact with the distributed team in person. Pendulum has a rigorously horizontal culture that values diversity of every kind.

Pendulum Systems is looking for a highly motivated and detail oriented Machine Learning Engineer to join our team.

As an ML Engineer at Pendulum, you will have the opportunity to push the boundaries of the field in AI+supply chains, by building, designing and deploying cutting-edge machine learning solutions. You will work on problems that bring a direct impact to saving lives and enabling governments to do more with less. The problems we address need careful transformation of state-of-the-art machine learning techniques to enable robust performance when deployed in the real world.

What We Will Do Together

Gather and preprocess large datasets to be used for training machine learning models. This work may involve cleaning data, handling missing values, and transforming data into suitable formats for analysis.
Identify and create relevant features from the raw data to improve the performance of machine learning algorithms.
Design and develop machine learning models/architectures and algorithms based on project requirements. This work includes for instance selecting appropriate algorithms, tuning hyperparameters, and optimizing for performance and efficiency.
Work closely with the engineering team to deploy machine learning models into production, ensuring they are scalable, reliable, and maintainable. 
Collaborate with a highly diverse and completely remote team.
Document and publish your work at high-impact machine learning conferences.

What You Will Need

Masters or Doctorate degree in computer science, electrical engineering, computer engineering, mathematics, or another related field.
Solid programming experience in Python. Proficiency in popular machine learning libraries/frameworks like, PyTorch, scikit-learn, etc.
Strong understanding of machine learning algorithms, data structures, and statistics. Experience with deep learning algorithms and frameworks is a plus.
Knowledge of software engineering principles, version control systems (e.g., Git), and best practices in software development.
Problem-solving skills and the ability to think critically about complex technical challenges.
Solid communication skills and collaboration experience
Curiosity about new things.

Definite Plus Points

Publication or contributions to top-tier ML venues
Proficiency in mathematical optimization
Experience with LLMs.""".strip()
    }
]


# get completion
response = get_completion(message_queue)

print("response", response)	

# assert response is dict
assert isinstance(response, dict)
assert "items" in response

# get replacements
replacements = response["items"]

# replace text in pdf
replace_text_in_pdf(original_pdf_path, output_pdf_path, text_blocks_dict, replacements)

#
convert_pdf_to_doc(output_pdf_path)