from flask import Flask, render_template, request
from PyPDF2 import PdfReader
import csv

from logic import locks, get_locks


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():

    return render_template('index.html')

@app.route('/upload-files', methods=['POST'])
def upload_files():
    pdf_file = request.files.get('pdf-file')
    csv_file = request.files.get('csv-file')
    if not pdf_file or not csv_file:
        return 'Please select both pdf and csv file', 400
    pdf = PdfReader(pdf_file)
    # Extract the text from the PDF file
    text = ''
    for page in pdf.pages:
        text += " " + page.extractText()
    if csv_file:
        csv_reader = csv.reader(csv_file.stream.read().decode("utf-8").splitlines())
        for line in csv_reader:
            print(line)

    return render_template('text.html', text=text )




if __name__ == "__main__":
    app.run()
