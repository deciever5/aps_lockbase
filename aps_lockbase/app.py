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

    # create dataframes and tables for display from pdf and csv file
    order_df = models.pdf_to_dataframe(app, pdf_filename)
    system_df = models.create_df_from_csv(app, csv_filename)
    order_with_pinning_df = models.add_order_pinning(order_df, system_df)

    table_from_pdf = order_df.to_html(max_rows=30, header=True)
    table_from_system_csv = system_df.to_html(max_rows=30, header=True)
    table_from_order = order_with_pinning_df.to_html(max_rows=30, header=True)
    details = models.get_order_details(order_with_pinning_df)
    aps_file = models.create_aps_file(order_df, system_df)

    return render_template('table.html', csv_data=table_from_system_csv, pdf_data=table_from_pdf,
                           csv_filename=csv_filename, order_data=table_from_order, pdf_filename=pdf_filename,
                           aps_file=aps_file)


if __name__ == "__main__":
    app.run()
