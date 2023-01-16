import pandas as pd
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename
import lock


def allowed_file(app, filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def create_df_from_csv(app, csv_filename):
    df = pd.read_csv(app.config['UPLOAD_FOLDER'] + csv_filename, delimiter=';', encoding='ANSI')
    df.iloc[:, 2] = df.iloc[:, 2].str.slice(stop=35)

    # Chosing and naming colums needed for an order
    df = df.iloc[:, [2, 3, 7, 11, 13, 14, 17, 18]]
    df.columns = ['Room', 'Finish', 'Lenght', 'All_pins', 'Profile', 'Sys_quantity', 'Number', 'Type']

    df = df.dropna(subset=['Number']).reset_index(drop=True)

    # Creating new columns with individual pinning from All_pins column
    df['All_pins'] = df['All_pins'].str.replace('\r', '')
    df['All_pins'] = df['All_pins'].str.replace('\n', '|')
    df['Body_pins'] = df['All_pins'].str.split(' ').str[0]
    df['Side_pins'] = df['All_pins'].str.split('|').str[0].str.split(' ').str[1]
    df['Extension_pins_sums'] = df['All_pins'].str.split('|').str[1:]

    length = df['Body_pins'].str.len().max()

#TODO body pins has wrong length for c14 219 rozb 25 ,which makes to many 0 in ext_pins
    df['Extension_pins_sums'] = df['Extension_pins_sums'].apply(
        lambda x: ["0".join(string.replace(" ", "0").split()).ljust(length, "0") for string in x])


    #df['Extension_pins_sums'] = df['Extension_pins_sums'].apply(lambda x: [string.replace(" ", "-") for string in x])


    df = df.reindex(
        columns=['Number', 'Body_pins', 'Side_pins', 'Extension_pins_sums', 'All_pins',  'Finish', 'Lenght',
                 'Key_profile', 'System_quantity', 'Type','Room'])
    print(type(df.iloc[7, 4]))
    return df
    """
    length = len(body_pins)
    ext_pins_from_csv = [[x.replace("a", "10").replace("b", "11").replace(" ", "-") for x in k] for k in
                         [list(j) for j in [k for k in ext_pins]]]
    ext_pins_from_csv = [list(itertools.chain(pin, itertools.repeat('-', length - len(pin)))) for pin in
                         ext_pins_from_csv]"""


def extract_txt_from_pdf(app, pdf_filename):
    # Extract the text from the order PDF file
    pdf_file = open(app.config['UPLOAD_FOLDER'] + pdf_filename, 'rb')
    pdf_reader = PdfReader(pdf_file)
    text = ''
    for page_num in range(pdf_reader.numPages):
        text += pdf_reader.getPage(page_num).extractText() + '\n'
    pdf_file.close()
    return text


def files_save(app, pdf_file, csv_file):
    # Extract and store in archive system pdf and odrer csv
    if pdf_file and allowed_file(app, pdf_file.filename) and csv_file and allowed_file(app, csv_file.filename):
        pdf_filename = secure_filename(pdf_file.filename)
        csv_filename = secure_filename(csv_file.filename)
        pdf_file.save(app.config['UPLOAD_FOLDER'] + pdf_filename)
        csv_file.save(app.config['UPLOAD_FOLDER'] + csv_filename)
        return pdf_filename, csv_filename
    else:
        return False
