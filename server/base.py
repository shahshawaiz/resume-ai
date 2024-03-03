import json
import os

from dotenv import dotenv_values
import fitz  # PyMuPDF

import openai
from openai import OpenAI

from pdf2docx import Converter
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

class ResumeExpert:
    def __init__(self):
        pass

    def get_text_in_pdf(self, original_pdf_path):
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

    def create_pdf(self, filename, cover_letter_text):
        #
        pdf = PDF()

        # Add a page
        pdf.add_page()

        # Set font
        pdf.set_font("Arial", size=12)

        # Add cover letter content
        pdf.multi_cell(0, 10, cover_letter_text)

        # Save the pdf with name .pdf
        pdf.output(filename)


    def replace_text_in_pdf(self, original_pdf_path, output_pdf_path, orignal_text_dict, replacements):
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

    def convert_pdf_to_doc(self, pdf_path):
        # 
        docs_path = pdf_path.replace('.pdf', '.docx')

        # convert pdf to doc
        cv = Converter(pdf_path)
        cv.convert(docs_path, start=0, end=None)
        cv.close()  

        return docs_path
                    
    def get_completion(self, message_queue, type):
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
                response_format={ "type": type }
            )

            print("OI Responseded", completion.choices)

            response = completion.choices[0].message.content            

            #
            if type == "json_object":
                
                # load json
                response = json.loads(response)
            else:
                # fix parsing issues
                response = str(response)

        except Exception as e:
            print("JSON Parsing Error!")

            return None

        return response

    def get_message_queue_cv(self, resume_text_blocks, job_ad_text):
        # init message queue
        return [
            {
                "role": "system",
                "content": """You are an expert CV writer and resume writer responsible for rewriting a given resume and generate a cover letter, with respect to a given job ad to make it more appealing to job recruiter who has posted that job ad.

Objective: 
Enhance the content of the given resume to make it more appealing and increase the probability of being shortlisted by automated HR tools and recruiters.

Input Required:
1. Resume Text Blocks: Text blocks from candidate's resume to rewrite
2. Job Ad: Job ad by the recruiter

Task Overview:
* You are tasked with rewriting sections of the resume to align them more closely with the job description.
* You are also tasked with writing a cover letter to compose a letter that is aligned with provided job description.
* The focus is on optimizing the cover letter for automated screening tools and recruiter appeal.

Rules and Guidelines:
1. Only rewrite sections which really need update. Dont make it sound so fancy
2. Maintain Key Nouns: Do not alter company names, titles, dates, or specific names.
3. Scope Limitation: Work only on the intro, experience, or skills sections.
4. Length Consistency: Ensure the original and replacement texts are of the same length.
5. Preserve Meaning: Keep the original intent and meaning of the text.
6. Retain Formatting: Do not change the format of the text.
7. Keyword Incorporation: Embed keywords from the job description in the replacement text.
8. Fix all text block where necessary.
9. Make sure important keywords are included in the replacement text where possible/necessery but usage should be consistent with orignal resume (and past experience).
10. Never lie about any experience.

Task Execution:

1. Resume Rewriting Phase:
* Create a replacement text for each block of original text.
* Integrate relevant keywords from the job description into the new text.
2. Resume Writing Phase:
* Create a cover leter based on the job description and resume text blocks.
* Integrate relevant keywords from the job description into the new text.
5. Validation:
* Verify that the resume's replacement text adheres to the specified guidelines.
* Ensure the resume's replacement text is aligned with job requirements and remains compelling.
* Verify that the cover letter aligns with job requirements and remains compelling.
6. Improvement Iteration:
* Repeat the rewriting and validation until full compliance is achieved.

Please fill the following JSON schema with the proposed replacement text for each block of original text.

```json{
    "type" : "array",
    "resume_replacement_items" : {
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
            },
        },
    },    
    "cover_letter": {
        type: "string",
        description: "Text for cover letter in proper format. And fill all the necessary details (like name, address, etc) in the cover letter."            
    }
}```""".strip()   
            },
            {
                "role": "user",
                "content": f""""Text Blocks: {resume_text_blocks}

Job Description:
{job_ad_text}""".strip()
            }
        ]   

    def get_message_queue_coverletter(self, resume_text_blocks, job_ad_text):
        # init message queue
        return [
            {
                "role": "system",
                "content": """You are an expert cover letter writer responsible for writing a cover letter provided a given job ad and text blocks of resume, to make it more appealing to job recruiter who has posted that job ad.

Objective: 
Write a coverletter to increase the probability of being shortlisted by automated HR tools and recruiters.

Input Required:
1. Resume Text Blocks: Text blocks from candidate's resume to be used as a reference for writing cover letter
2. Job Ad: Job ad by the recruiter

Task Overview:
* You are tasked with writing a cover letter to compose a letter that is aligned with provided job description.
* The focus is on optimizing the cover letter for automated screening tools and recruiter appeal.

Task Execution:
1. Writing Phase:
* Create a cover leter based on the job description and resume text blocks.
Integrate relevant keywords from the job description into the new text.
2. Validation:
* Verify that the letter aligns with job requirements and remains compelling.
3. Improvement Iteration:
* Repeat the rewriting and validation until full compliance is achieved.

Return text in proper cover letter format. And fill all the necessary details (like name, address, etc) in the cover letter.
""".strip()   
            },
            {
                "role": "user",
                "content": f""""Text Blocks: {resume_text_blocks}

Job Description:
{job_ad_text}""".strip()
            }
        ]            

    def generate(self, resume_path, job_ad_text):
        # init vars
        resume_text_blocks = {}
        response = None
        resume_path_output = None
        resume_path_docx = None
        filepath_cover = None
        cover_path_docx = None
        cover_letter = None

        # init output pdf path
        try:
            resume_path_output = resume_path.replace('.pdf', '_optimized.pdf')

            # get text block from pdf
            text_blocks = self.get_text_in_pdf(resume_path)

            # set index
            for index, text_block in enumerate(text_blocks):
                resume_text_blocks[index] = text_block
        except Exception as e:
            response = "Unable to generate optimized resume. Please try again. Code 01"
            print(e)            


        # generate optimized resume
        try:
            message_queue = self.get_message_queue_cv(resume_text_blocks, job_ad_text)            

            print("Message Queue, CV Optimization:", message_queue)

            # get completion
            response = self.get_completion(message_queue, type="json_object")
        except Exception as e:
            response = "Unable to generate optimized resume. Please try again. Code 02"
            print(e)

        # rewrite resume
        try:
            assert isinstance(response, dict)
            assert "resume_replacement_items" in response

            # get replacements
            resume_replacements = response["resume_replacement_items"]

            # replace text in pdf
            self.replace_text_in_pdf(resume_path, resume_path_output, resume_text_blocks, resume_replacements)

            # generate docs
            resume_path_docx = self.convert_pdf_to_doc(resume_path_output)
        except Exception as e:
            response = "Unable to generate optimized resume. Please try again. Code 03"

            print(e)

        # generate optimized cover
        try:
            # message_queue = self.get_message_queue_coverletter(resume_text_blocks, job_ad_text)  

            # # get completion
            # response = self.get_completion(message_queue, type="text")

            cover_letter = response["cover_letter"]
            
            print("Cover Letter Response: ", cover_letter)

            #
            filepath_cover = resume_path.replace('.pdf', '_cover.pdf')


            # create cover letter
            self.create_pdf(filepath_cover, cover_letter)        

            #
            cover_path_docx = self.convert_pdf_to_doc(filepath_cover)    
        except Exception as e:
            cover_letter = "Unable to generate optimized resume. Please try again. Code 02"
            print(e)

        resume_path_output = os.path.basename(resume_path_output)
        resume_path_docx = os.path.basename(resume_path_docx)
        filepath_cover = os.path.basename(filepath_cover)
        cover_path_docx = os.path.basename(cover_path_docx)

        return resume_path_output, resume_path_docx, filepath_cover, cover_path_docx, cover_letter

    def generate_test(self):
        # init vars
        original_pdf_path = 'server/docs/sample_2.pdf'

        #
        job_ad_text = """Pendulum is a venture-backed AI company addressing the global need to do more with less. Pendulum AI-driven supply chain solutions forecast demand, optimize supply and geolocate - continuously improving on their own. The first major investment in AI by the Bill & Melinda Gates Foundation was in Pendulum; today our technology works for customers across 10+ countries – driving profitable growth and saving lives.

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
Experience with LLMs."""

        # run test
        self.generate(original_pdf_path, job_ad_text)