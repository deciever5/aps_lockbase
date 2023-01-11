import pandas as pd
from PyPDF2 import PdfReader
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from lock import create_locklist

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'archive/'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'csv'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/upload-files', methods=['POST'])
def upload_files():
    pdf_file = request.files.get('pdf-file')
    csv_file = request.files.get('csv-file')
    if pdf_file and allowed_file(pdf_file.filename) and csv_file and allowed_file(csv_file.filename):
        pdf_filename = secure_filename(pdf_file.filename)
        csv_filename = secure_filename(csv_file.filename)
        pdf_file.save(app.config['UPLOAD_FOLDER'] + pdf_filename)
        csv_file.save(app.config['UPLOAD_FOLDER'] + csv_filename)

        # Extract the text from the PDF file
        pdf_file = open(app.config['UPLOAD_FOLDER'] + pdf_filename, 'rb')
        pdf_reader = PdfReader(pdf_file)
        text = ''
        for page_num in range(pdf_reader.numPages):
            text += pdf_reader.getPage(page_num).extractText() + '\n'
        pdf_file.close()

        df = pd.read_csv(app.config['UPLOAD_FOLDER'] + csv_filename, delimiter=';', encoding='ANSI')
        df.iloc[:, 2] = df.iloc[:, 2].str.slice(stop=58)
        df = df.iloc[6:, [2, 3, 7, 11, 13, 14, 17, 18]]
        create_locklist(df)
        return render_template('text.html', text=text, data=df.to_html(max_rows=33, header=False))


if __name__ == "__main__":
    app.run()
