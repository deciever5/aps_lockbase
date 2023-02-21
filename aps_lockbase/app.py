import os
import smtplib
from datetime import datetime
import warnings
from flask import Flask, render_template, request, session
from dto import dto
import models

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static\\archive\\')
app.config['APS_FOLDER'] = os.path.join(basedir, 'static\\aps\\')
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'csv'}
app.secret_key = 'RHARHTEHDFWQR$#&^*$#%FDFH'
warnings.filterwarnings("ignore", category=FutureWarning)


@app.route('/', methods=['GET'])
def index():
    return render_template('upload.html')


@app.route('/upload-files', methods=['POST'])
def upload_files():
    pdf_file = request.files.get('pdf-file')
    csv_file = request.files.get('csv-file')

    # save files to archive and get their names
    pdf_filename, csv_filename = models.files_save(app.config['ALLOWED_EXTENSIONS'], app.config['UPLOAD_FOLDER'],
                                                   pdf_file, csv_file)

    # create dataframes and tables for display from pdf and csv file
    order_df = models.pdf_to_dataframe(app.config['UPLOAD_FOLDER'], pdf_filename)
    system_df = models.create_df_from_csv(app.config['UPLOAD_FOLDER'], csv_filename)
    system_df = models.clean_and_refactor(system_df)
    order_with_pinning = models.add_order_pinning(order_df, system_df)
    # saving dataframe for external functions use
    dto.data_frame = order_with_pinning
    order_types = models.get_order_types(order_with_pinning.drop('System'))

    return render_template('aps_options.html', csv_filename=csv_filename, order_data=order_with_pinning,
                           pdf_filename=pdf_filename,
                           fields=order_types, system_data=system_df)


@app.route('/auto_manual_splitter', methods=['POST'])
def auto_manual_splitter():
    # Get lock types to be made on APS
    selected_fields = []
    for field in request.form:
        selected_fields.append(field)
    session['selected_fields'] = selected_fields

    automatic, manual = models.split_order(selected_fields)

    return render_template('aps_conversion.html', automatic_data=automatic, manual_data=manual)


@app.route('/create_aps_file', methods=['GET'])
def create_aps_file():
    # Get lock types to be made on APS
    selected_fields = session.get('selected_fields')
    automatic, manual = models.split_order(selected_fields)

    aps_file = models.create_aps_file(automatic, app.config['APS_FOLDER'])
    aps_pdf = models.create_aps_pdf(automatic, app.config['UPLOAD_FOLDER'])
    non_aps_pdf = models.create_non_aps_pdf(manual, app.config['UPLOAD_FOLDER'])

    print(aps_pdf, aps_file, non_aps_pdf)

    return render_template('conversion_done.html')


@app.route('/archive', methods=['GET'])
def archive():
    # Grabs and displays all files in archive folder
    archive_path = os.path.join(app.root_path, 'static', 'archive')

    files = [{'name': file, 'size': os.path.getsize(os.path.join(archive_path, file)),
              'date': datetime.fromtimestamp(os.path.getctime(os.path.join(archive_path, file))).strftime(
                  "%Y-%m-%d %H:%M")}
             for file in os.listdir(archive_path) if os.path.isfile(os.path.join(archive_path, file))]

    return render_template('archive.html', files=files)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']

        # Create the email message
        msg = f"Name: {name}\nEmail: {email}\nPhone: {phone}\n\n{message}"
        print(msg)
        # Send the email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("sender@example.com", "password")
        server.sendmail("sender@example.com", "recipient@example.com", msg)
        server.quit()

        return render_template('contact.html', success=True)

    return render_template('contact.html')


if __name__ == "__main__":
    app.run()


