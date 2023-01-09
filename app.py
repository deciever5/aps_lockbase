from flask import Flask, render_template, request
from PyPDF2 import PdfReader

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Read the PDF file
        file = request.files['file']
        pdf = PdfReader(file)
        # Extract the text from the PDF file
        text = ''
        for page in pdf.pages:
            text += " " + page.extractText()
        return render_template('text.html', text=text)
    return render_template('index.html')

if __name__ == "__main__":
    app.run()