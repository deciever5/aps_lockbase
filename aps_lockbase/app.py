import os
from datetime import datetime
import pandas as pd
from flask import Flask, render_template, request, url_for
import models

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'aps_lockbase/static/archive/'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'csv'}


@app.route('/', methods=['GET'])
def index():
    return render_template('upload.html')

@app.route('/contact', methods=['GET'])
def contact():
    return render_template('contact.html')

@app.route('/archive', methods=['GET'])
def archive():
    archive_path = os.path.join(app.root_path, 'static', 'archive')
    files = []
    for file in os.listdir(archive_path):
        if os.path.isfile(os.path.join(archive_path, file)):
            file_size = os.path.getsize(os.path.join(archive_path, file))
            creation_time = os.path.getctime(os.path.join(archive_path, file))
            creation_time = datetime.fromtimestamp(creation_time)
            creation_time = creation_time.strftime("%Y-%m-%d %H:%M")
            files.append({'name': file, 'size': file_size, 'date': creation_time})
    return render_template('archive.html', files=files)


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
    order_with_pinning.to_pickle('order_with_pinning.pkl')

    table_from_pdf = order_df.to_html(max_rows=30, header=True)
    table_from_system_csv = system_df.to_html(max_rows=30, header=True)
    table_from_order = order_with_pinning.to_html(max_rows=30, header=True)
    order_types = models.get_order_types(order_with_pinning)

    return render_template('aps_options.html', csv_data=table_from_system_csv, pdf_data=table_from_pdf,
                           csv_filename=csv_filename, order_data=table_from_order, pdf_filename=pdf_filename,
                           fields=order_types)


@app.route('/create_aps', methods=['POST'])
def aps_file_maker():
    # Get lock types to be made on APS
    selected_fields = []
    for field in request.form:
        selected_fields.append(field)

    # Get order from pickle database
    order_with_pinning = pd.read_pickle('order_with_pinning.pkl')
    automatic = order_with_pinning[order_with_pinning['Type'].isin(selected_fields)]
    manual = order_with_pinning[~order_with_pinning['Type'].isin(selected_fields)]

    table_from_automatic = automatic.to_html(max_rows=30, header=True)
    table_from_manual = manual.to_html(max_rows=30, header=True)

    aps_file = models.create_aps_file(automatic)
    aps_pdf = models.create_aps_pdf(automatic)
    non_aps_pdf = models.creat_non_aps_pdf(manual)

    print(aps_pdf,aps_file,non_aps_pdf)

    #print(f'selected = {selected_fields}')

    return render_template('aps_conversion.html', automatic_data = table_from_automatic, manual_data = table_from_manual)


if __name__ == "__main__":
    app.run()
