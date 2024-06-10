from flask import Flask, request, render_template 
from flask_bootstrap import Bootstrap
from PyPDF2 import PdfReader, PdfWriter
import pdfplumber
import spacy
from collections import Counter
import random

# Creating app
app = Flask(__name__)
Bootstrap(app)

# Load English tokenizer, tagger, parser, NER, and word vectors
nlp = spacy.load("en_core_web_sm")

# def generate_mcqs(text, num_questions=5):
#     # text = clean_text(text)
#     if text is None:
#         return []

#     # Process the text with spaCy
#     doc = nlp(text)

#     # Extract sentences from the text
#     sentences = [sent.text for sent in doc.sents]

#     # Ensure that the number of questions does not exceed the number of sentences
#     num_questions = min(num_questions, len(sentences))

#     # Randomly select sentences to form questions
#     selected_sentences = random.sample(sentences, num_questions)

#     # Initialize list to store generated MCQs
#     mcqs = []

#     # Generate MCQs for each selected sentence
#     for sentence in selected_sentences:
#         # Process the sentence with spaCy
#         sent_doc = nlp(sentence)

#         # Extract entities (nouns) from the sentence
#         nouns = [token.text for token in sent_doc if token.pos_ == "NOUN"]

#         # Ensure there are enough nouns to generate MCQs
#         if len(nouns) < 2:
#             continue

#         # Count the occurrence of each noun
#         noun_counts = Counter(nouns)

#         # Select the most common noun as the subject of the question
#         if noun_counts:
#             subject = noun_counts.most_common(1)[0][0]

#             # Generate the question stem
#             question_stem = sentence.replace(subject, "______")

#             # Generate answer choices
#             answer_choices = [subject]

#             # Add some random words from the text as distractors
#             distractors = list(set(nouns) - {subject})

#             # Ensure there are at least three distractors
#             while len(distractors) < 3:
#                 distractors.append("[Distractor]")  # Placeholder for missing distractors

#             random.shuffle(distractors)
#             for distractor in distractors[:3]:
#                 answer_choices.append(distractor)

#             # Shuffle the answer choices
#             random.shuffle(answer_choices)

#             # Append the generated MCQ to the list
#             correct_answer = chr(64 + answer_choices.index(subject) + 1)  # Convert index to letter
#             mcqs.append((question_stem, answer_choices, correct_answer))

#     return mcqs

def generate_mcqs(text, num_questions=5):
    if text is None:
        return []

    # Process the text with spaCy
    doc = nlp(text)

    # Extract sentences from the text
    sentences = [sent.text for sent in doc.sents]

    # Extract all nouns from the text
    all_nouns = [token.text for token in doc if token.pos_ == "NOUN"]
    unique_nouns = list(set(all_nouns))

    # Initialize list to store generated MCQs
    mcqs = []

    # Generate MCQs for each sentence until the requested number of questions is reached
    for sentence in sentences:
        # Process the sentence with spaCy
        sent_doc = nlp(sentence)

        # Extract nouns from the sentence
        nouns = [token.text for token in sent_doc if token.pos_ == "NOUN"]

        # Ensure there are enough nouns to generate MCQs
        if len(nouns) < 2:
            continue

        # Count the occurrence of each noun
        noun_counts = Counter(nouns)

        # Select the most common noun as the subject of the question
        if noun_counts:
            subject = noun_counts.most_common(1)[0][0]

            # Generate the question stem
            question_stem = sentence.replace(subject, "______")

            # Generate answer choices
            answer_choices = [subject]

            # Add some random nouns from the entire text as distractors
            distractors = list(set(nouns) - {subject})
            additional_distractors = list(set(unique_nouns) - {subject})

            # Ensure there are at least three distractors
            while len(distractors) < 3:
                if additional_distractors:
                    distractors.append(additional_distractors.pop())
                else:
                    distractors.append("RandomNoun")  # Fallback in case we run out of nouns

            random.shuffle(distractors)
            for distractor in distractors[:3]:
                answer_choices.append(distractor)

            # Shuffle the answer choices
            random.shuffle(answer_choices)

            # Append the generated MCQ to the list
            correct_answer = chr(64 + answer_choices.index(subject) + 1)  # Convert index to letter
            mcqs.append((question_stem, answer_choices, correct_answer))

        # Break the loop if the requested number of questions is reached
        if len(mcqs) >= num_questions:
            break

    return mcqs


# def process_pdf(file):
#   text = ""
#   pdf_reader = PdfReader(file) 

#   for page_num in range(len(pdf_reader.pages)):
#     page_text = pdf_reader.pages[page_num].extract_text()
#     text += page_text
#   return text 


def process_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

@app.route("/", methods=["GET", "POST"])
def index():
  if request.method == "POST":
    text = ""
    # CHeck if  files were uploaded
    if 'files[]' in request.files:
      files = request.files.getlist("files[]")
      for file in files:
        if file.filename.endswith(".pdf"):
          # process pdf files
          text += process_pdf(file)
        elif file.filename.endswith(".txt"):
          # process txt files
          text += file.read().decode('utf-8')
    else:
      #  Process manual input
      text = request.form['text']
  
    # Get the selected number of questions from the dropdown menu
    num_questions = int(request.form['num_questions'])

    mcqs = generate_mcqs(text, num_questions=num_questions) # Pass the selected no. of questions

    # print(mcqs)
    # Ensure each MCQ is formatted correctly as (question_stem, answer_choices, correct_answer)
    mcqs_with_index = [(i+1,mcq) for i, mcq in enumerate(mcqs)]
    # print(mcqs_with_index)
    return render_template('mcqs.html', mcqs = mcqs_with_index)

  return render_template("index.html")



# python main ====
if __name__ == "__main__":
  app.run(debug=True)