import pandas as pd
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine
from pdfminer.pdfdocument import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from werkzeug.utils import secure_filename
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch
from datetime import datetime


def allowed_file(app, filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def create_df_from_csv(app, csv_filename):
    df = pd.read_csv(app.config['UPLOAD_FOLDER'] + csv_filename, delimiter=';', encoding='ANSI')
    # Chosing and naming colums needed for an order
    df = df.iloc[:, [2, 3, 7, 11, 12, 13, 14, 15, 17, 18]]
    df.columns = ['Room', 'Finish', 'Lenght', 'All_pins', 'Date', 'Profile', 'Sys_quantity', 'Special_eq', 'Number',
                  'Type']
    # Removing all columns not containing system combinations
    df = df.dropna(subset=['Number']).reset_index(drop=True)

    # Creating new columns with individual pinning from All_pins column
    df['All_pins'] = df['All_pins'].str.replace('\r', '').str.replace('\n', '|')
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
        columns=['Number', 'Finish', 'Lenght', 'Profile', 'Sys_quantity', 'Type', 'Special_eq', 'Body_pins',
                 'Side_pins',
                 'Extension_pins', 'Date'])
    # in case of duplicates drop older row
    df.sort_values(by='Date', ascending=False, inplace=True)
    df.drop_duplicates(subset=['Number', 'Finish', 'Lenght', 'Profile', 'Type', 'Special_eq'], keep='first',
                       inplace=True)
    df.sort_values(by='Number', ascending=True, inplace=True)

    # replace NaN values with empty string and change all types to object for comparision with order df
    df.fillna(value='', inplace=True)
    df = df.astype(object)
    return df


def ext_pins_recounting(body_pins, extension_pins_sums):
    # Substracts previous number of pins from next element in extension_pins_sums(substract body pins for first element)
    extension_pins = [[int(x.replace('a', '10').replace('b', '11')) - int(y.replace('a', '10').replace('b', '11'))
                       if x != "0" else "0" for x, y in zip(extension_pins_sums[0], body_pins)]
                      for _ in extension_pins_sums]
    return extension_pins


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


def pdf_to_dataframe(app, pdf_filename):
    # Extract the text from the order PDF file
    pdf_path = app.config['UPLOAD_FOLDER'] + pdf_filename
    text_location = []
    # Extract text with its location coordinates and save them to a dataframe
    with open(pdf_path, 'rb') as pdf_file:
        resource_manager = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(resource_manager, laparams=laparams)
        interpreter = PDFPageInterpreter(resource_manager, device)
        # Extracting text and its location coordinates
        for page in PDFPage.get_pages(pdf_file):
            try:
                interpreter.process_page(page)
            except PDFTextExtractionNotAllowed:
                continue
            layout = device.get_result()
            for element in layout:
                if isinstance(element, LTTextBox) or isinstance(element, LTTextLine):
                    text_location.append((element.get_text(), element.bbox))
    df = pd.DataFrame(text_location, columns=['text', 'location'])
    # Get name of the system which is in first row of first column after "System:"
    header = df.iloc[0, 0].split("\n")
    system_name = ''
    for part in header:
        if "System:" in part:
            system_name = part[8:].strip()

    # Filter first column by system name, drop other columns
    # Droping all lines too short (usually grid lines of system) and those containing LOCKBASE
    df = df[df['text'].str.contains(system_name)].iloc[:, 0:1].reset_index(drop=True)
    df = df[~df['text'].str.contains('LOCKBASE')]
    df = df[df['text'].map(len) >= 20]

    # Split the string into list and furhter into columns
    def split_string(string):
        return string.split("\n")

    new_df = df['text'].apply(split_string)
    new_df = pd.DataFrame(new_df.tolist(), index=new_df.index)
    df = pd.concat([df, new_df], axis=1)
    df.drop('text', axis=1, inplace=True)
    df.columns = df.columns.astype(str)
    df = df.rename(
        columns={'0': 'Number', '3': 'Finish', '2': 'Lenght', '4': 'Profile', '5': 'Quantity', '1': 'Type',
                 '6': 'Special_eq', '7': 'Others'})
    df = df.reindex(
        columns=['Number', 'Finish', 'Lenght', 'Profile', 'Quantity', 'Type', 'Special_eq', 'Others'])

    df = df.astype(object)
    df.loc['System'] = system_name
    return df


def add_order_pinning(order_df, system_df):
    # Adds pinns to order from pdf by merging with system dataframe
    merged_df = pd.merge(order_df, system_df, on=['Number', 'Finish', 'Lenght', 'Profile', 'Type', 'Special_eq'])
    merged_df.drop(columns=['Others', 'Date', 'Sys_quantity'], inplace=True)
    merged_df.index += 1
    merged_df.loc['System'] = order_df.loc['System']

    return merged_df


def get_order_types(df):
    order_types = df.Type.unique().tolist()
    return order_types


def create_aps_file(df, file_path):
    table_name = df.loc['System', 'Number']
    today = datetime.today().date()

    return '--aps file created successfully-- '


def create_aps_pdf(automatic):
    df = automatic

    pdf_file = 'data.pdf'
    doc = SimpleDocTemplate(pdf_file, pagesize=letter)

    data = [df.columns] + df.values.tolist()

    table = Table(data, colWidths=[1.5 * inch] * 5)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    # doc.build([table])

    return '--aps pdf file created successfully-- '


def creat_non_aps_pdf(manual):
    return ' --non aps pdf file created successfully-- '
