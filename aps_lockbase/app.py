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
    text = models.extract_txt_from_pdf(app, pdf_filename)
    df = models.create_df_from_csv(app, csv_filename)

    return render_template('table.html', text=text, data=df.to_html(max_rows=30, header=True),
                           csv_filename=csv_filename)


if __name__ == "__main__":
    app.run()
