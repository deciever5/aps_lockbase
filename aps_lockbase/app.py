import os
import smtplib
from datetime import datetime

import pandas as pd
from flask import Flask, render_template, request

import models

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'aps_lockbase/static/archive/'
app.config['APS_FOLDER'] = 'aps_lockbase/static/archive'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'csv'}


@app.route('/', methods=['GET'])
def index():
    return render_template('upload.html')


@app.route('/upload-files', methods=['POST'])
def upload_files():
    pdf_file = request.files.get('pdf-file')
    csv_file = request.files.get('csv-file')

    # save files to archive and get their names
    pdf_filename, csv_filename = models.files_save(app, pdf_file, csv_file)

    # create dataframes and tables for display from pdf and csv file
    order_df = models.pdf_to_dataframe(app, pdf_filename)
    system_df = models.create_df_from_csv(app, csv_filename)
    order_with_pinning = models.add_order_pinning(order_df, system_df)
    order_with_pinning.to_pickle('order_with_pins.pkl')

    order_types = models.get_order_types(order_with_pinning.drop('System'))

    return render_template('aps_options.html', csv_filename=csv_filename, order_data=order_with_pinning,
                           pdf_filename=pdf_filename,
                           fields=order_types)


@app.route('/create_aps_file', methods=['POST'])
def aps_file_maker():
    # Get lock types to be made on APS
    selected_fields = []
    for field in request.form:
        selected_fields.append(field)

    # Get order from pickle database
    order_with_pins = pd.read_pickle('order_with_pins.pkl')
    automatic = order_with_pins[order_with_pins['Type'].isin(selected_fields)].append(order_with_pins.loc['System'])
    manual = order_with_pins[~order_with_pins['Type'].isin(selected_fields)].append(order_with_pins.loc['System'])

    aps_file = models.create_aps_file(automatic, app.config['APS_FOLDER'])
    aps_pdf = models.create_aps_pdf(automatic)
    non_aps_pdf = models.creat_non_aps_pdf(manual)

    print(aps_pdf, aps_file, non_aps_pdf)

    return render_template('aps_conversion.html', automatic_data=automatic, manual_data=manual)


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
