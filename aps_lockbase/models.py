import pandas as pd
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename
import camelot
import fitz

def allowed_file(app, filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def create_df_from_csv(app, csv_filename):
    df = pd.read_csv(app.config['UPLOAD_FOLDER'] + csv_filename, delimiter=';', encoding='ANSI')
    # Chosing and naming colums needed for an order
    df = df.iloc[:, [2, 3, 7, 11, 13, 14, 17, 18]]
    df.columns = ['Room', 'Finish', 'Lenght', 'All_pins', 'Profile', 'Sys_quantity', 'Number', 'Type']
    # Removing all columns not containing system combinations
    df = df.dropna(subset=['Number']).reset_index(drop=True)

    # Creating new columns with individual pinning from All_pins column
    df['All_pins'] = df['All_pins'].str.replace('\r', '')
    df['All_pins'] = df['All_pins'].str.replace('\n', '|')

    df['Body_pins'] = df['All_pins'].str.split(' ').str[0]
    # Additional operation needed for old system where side pins fields are empty
    if (df['Body_pins'].str.contains('|')).any():
        df['Body_pins'] = df['Body_pins'].str.split('|').str[0]

    df['Side_pins'] = df['All_pins'].str.split('|').str[0].str.split(' ').str[1]

    df['Extension_pins_sums'] = df['All_pins'].str.split('|').str[1:]

    # Fill all empty fields with 0 up to the lenght of body_pins
    length = df['Body_pins'].str.len().max()
    df['Extension_pins_sums'] = df['Extension_pins_sums'].apply(
        lambda x: ["0".join(string.replace(" ", "0").split()).ljust(length, "0") for string in x])

    # Change all pins fields into lists
    df['Body_pins'] = df['Body_pins'].apply(lambda x: [i for i in x])
    # Additional operation needed for old system where side pins fields are empty
    if (df['Side_pins']).any():
        df['Side_pins'] = df['Side_pins'].apply(lambda x: [i for i in x])

    df['Extension_pins_sums'] = df['Extension_pins_sums'].apply(lambda x: [list(i) for i in x])

    # Counting proper number for extension pins, to match order style
    df['Extension_pins'] = df.apply(lambda row: ext_pins_recounting(row['Body_pins'], row['Extension_pins_sums']),
                                    axis=1)

    df = df.reindex(
        columns=['Body_pins', 'Side_pins', 'Extension_pins', 'Finish',
                 'Lenght', 'Profile', 'Sys_quantity', 'Type', 'Number'])

    return df


def ext_pins_recounting(body_pins, extension_pins_sums):
    # Substracts previous number of pins from next element in extension_pins_sums(substract body pins for first element)
    extension_pins = [[] for _ in range(len(extension_pins_sums))]
    if extension_pins_sums:
        for idx, x in enumerate(extension_pins_sums[0]):
            y = body_pins[idx]
            x = x.replace('a', '10').replace('b', '11')
            y = y.replace('a', '10').replace('b', '11')
            if x != "0":
                extension_pins[0].append(int(x) - int(y))
            else:
                extension_pins[0].append("0")
        if len(extension_pins_sums) > 1:
            for idx, pins in enumerate(extension_pins_sums):
                if idx > 0:
                    for inner_idx, x in enumerate(pins):
                        y = extension_pins_sums[idx - 1][inner_idx]
                        x = x.replace('a', '10').replace('b', '11')
                        y = y.replace('a', '10').replace('b', '11')
                        if x != "0":
                            extension_pins[idx] = extension_pins[idx] + [int(x) - int(y)]
                        else:
                            extension_pins[idx] = extension_pins[idx] + ["0"]

    return extension_pins


def extract_txt_from_pdf(app, pdf_filename):
    # Extract the text from the order PDF file
    pdf_file = open(app.config['UPLOAD_FOLDER'] + pdf_filename, 'rb')
    pdf_reader = PdfReader(pdf_file)
    text = ''
    for page_num in range(pdf_reader.numPages):
        text += pdf_reader.getPage(page_num).extractText() + '\n'
    pdf_file.close()

    # Extract the tables from the PDF file
    tables = camelot.read_pdf(app.config['UPLOAD_FOLDER'] + pdf_filename,pages='all')
    print (tables)
    df_list = []
    # Create a dataframe from the first table
    for table in tables:
        df_list.append(table.df)
    df = pd.concat(df_list)
    df = df.drop(df.columns[0], axis=1)
    column = df.iloc[:,0]
    column.to_csv('column.csv', index=False, header=False, sep='\n')

    # Read the CSV file into a variable
    with open('column.csv', 'r') as f:
        data = f.read()

    print(data)


    html_table = df.to_html()

    return text,html_table


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