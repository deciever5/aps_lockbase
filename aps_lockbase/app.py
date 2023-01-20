from flask import Flask, render_template, request
import models

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'aps_lockbase/archive/'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'csv'}


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/upload-files', methods=['POST'])
def upload_files():
    pdf_file = request.files.get('pdf-file')
    csv_file = request.files.get('csv-file')

    # save files to archive and get their names
    pdf_filename, csv_filename = models.files_save(app, pdf_file, csv_file)
    table_from_pdf = models.extract_text_from_pdf(app, pdf_filename)
    table_from_csv = models.create_df_from_csv(app, csv_filename)

    return render_template('table.html', csv_data=table_from_csv,
                           csv_filename=csv_filename, pdf_data=table_from_pdf, pdf_filename=pdf_filename)


if __name__ == "__main__":
    app.run()
