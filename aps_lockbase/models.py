import logging
import re
from datetime import datetime

import pandas as pd
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine
from pdfminer.pdfdocument import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from werkzeug.utils import secure_filename

from dto import dto

# Create logger object
logger = logging.getLogger(__name__)
# Set log level to INFO or desired level
logger.setLevel(logging.INFO)
# Create formatter object
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Create file handler object
file_handler = logging.FileHandler('app.log', mode='w')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
# Add file handler to logger object
logger.addHandler(file_handler)


def allowed_file(extensions, filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions


def create_df_from_csv(folder, csv_filename):
    df = pd.read_csv(folder + csv_filename, delimiter=';', encoding='ANSI')
    # Choosing and naming columns needed for an order
    df = df.iloc[:, [2, 3, 7, 11, 12, 13, 14, 15, 17, 18]]
    df.columns = ['Room', 'Finish', 'Length', 'All_pins', 'Date', 'Profile', 'Quantity', 'Special_eq', 'Number',
                  'Type']
    # Removing all columns not containing system combinations
    df = df.dropna(subset=['Type']).reset_index(drop=True)
    return df


def clean_and_refactor(df):
    # Creating new columns with individual pinning from All_pins column
    df['All_pins'] = df['All_pins'].str.replace('\r', '').str.replace('\n', '|')
    df['Cylinder_pins'] = df['All_pins'].str.split(' ').str[0]
    # Additional operation needed for old system where side pins fields are empty
    if (df['Cylinder_pins'].str.contains('|')).any():
        df['Cylinder_pins'] = df['Cylinder_pins'].str.split('|').str[0]

    df['Side_pins'] = df['All_pins'].str.split('|').str[0].str.split(' ').str[1]

    df['Extension_pins_sums'] = df['All_pins'].str.split('|').str[1:]

    # Fill all empty fields with 0 up to the length of cylinder_pins
    length = df['Cylinder_pins'].str.len().max()
    # Loop through each list of strings in the DataFrame column

    df = fill_missing_pins(df, length)

    # Change all pins fields into lists
    df['Cylinder_pins'] = df['Cylinder_pins'].apply(lambda x: [i for i in x])
    # Additional operation needed for old system where side pins fields are empty
    if (df['Side_pins']).any():
        df['Side_pins'] = df['Side_pins'].apply(lambda x: [i for i in x])

    df['Extension_pins_sums'] = df['Extension_pins_sums'].apply(lambda x: [list(i) for i in x])
    df['Extension_pins_sums'] = df.apply(
        lambda x: [x['Cylinder_pins']] if len(x['Extension_pins_sums']) == 0 else x['Extension_pins_sums'], axis=1)

    # Counting proper number for extension pins, to match order style
    df['Extension_pins'] = df.apply(lambda row: ext_pins_recounting(row['Cylinder_pins'], row['Extension_pins_sums']),
                                    axis=1)



    df['Body_pins'] = body_pins_recounting(df['Extension_pins_sums'])

    df = df.reindex(
        columns=['Number', 'Type', 'Length', 'Finish', 'Profile', 'Special_eq', 'Quantity', 'Cylinder_pins',
                 'Side_pins',
                 'Extension_pins', 'Body_pins', 'Date'])
    # in case of duplicates drop older row
    df.sort_values(by='Date', ascending=False, inplace=True)
    # df = df.drop_duplicates(subset=['Number', 'Finish', 'Length', 'Profile', 'Type', 'Special_eq'], keep='first')
    df.sort_values(by='Number', ascending=True, inplace=True)
    df = df.reset_index(drop=True)
    # replace NaN values with empty string and change all types to object for comparison with order df
    try:
        df['Quantity'] = df['Quantity'].astype(int)
    except pd.errors.IntCastingNaNError:
        df['Quantity'] = df['Quantity'].fillna(0).astype(int)
    df.fillna(value='', inplace=True)

    # removing all spaces from types as same types are written in different ways
    df['Type'] = df['Type'].apply(lambda x: x.replace(' ', ''))

    return df


def ext_pins_recounting(cylinder_pins, extension_pins_sums):
    # Subtracts previous number of pins from next element in extension_pins_sums(subtract body pins for first element)
    extension_pins = [[int(x.replace('a', '10').replace('b', '11')) - int(y.replace('a', '10').replace('b', '11'))
                       if x != "0" else 0 for x, y in zip(extension_pins_sums[0], cylinder_pins)]]
    for i in range(1,len(extension_pins_sums)):
        extension_pins_2 = [int(x.replace('a', '10').replace('b', '11')) - int(y.replace('a', '10').replace('b', '11'))
                           if x != "0" else 0 for x, y in zip(extension_pins_sums[i], extension_pins_sums[i-1])]
        extension_pins.append(extension_pins_2)

    return extension_pins


def body_pins_recounting(extension_pins_sums):
    total_pins = [value[-1]if value else '' for value in extension_pins_sums]

    body_pins = [[0 if not x.isdigit() else 2 if int(x) <= 3 else 1 if 4 <= int(x) <= 6 else 0 for x in pins] for pins
                 in total_pins]

    return body_pins


def files_save(extensions, folder, pdf_file, csv_file):
    # Extract and store in archive system pdf and order csv
    if pdf_file and allowed_file(extensions, pdf_file.filename) and csv_file and allowed_file(extensions,
                                                                                              csv_file.filename):
        pdf_filename = secure_filename(pdf_file.filename)
        csv_filename = secure_filename(csv_file.filename)
        pdf_file.save(folder + pdf_filename)
        csv_file.save(folder + csv_filename)
        return pdf_filename, csv_filename
    else:
        return False


# Split the string into list and further into columns
def split_string(string):
    return string.split("\n")


def pdf_to_dataframe(folder, pdf_filename):
    df = extract_text(folder, pdf_filename)

    system_name = get_system_name(df)
    df = join_incorect_rows(df, system_name)

    # Filter first column by system name, drop other columns
    # Dropping all lines too short (usually grid lines of system) and those containing LOCKBASE,
    df = df[df['text'].str.contains(system_name)].iloc[:, 0:1].reset_index(drop=True)

    new_df = df['text'].apply(split_string)
    new_df = pd.DataFrame(new_df.tolist(), index=new_df.index)

    df = pd.concat([df, new_df], axis=1)
    df.drop('text', axis=1, inplace=True)

    # making all df 8 columns long
    while df.shape[1] < 8:
        df['Others'] = pd.Series(dtype='object')

    #  shift rows where length,finish or sepcial_eq is empty (padlocks,camlocks)
    df = df.apply(shift_if_length_missing, axis=1, result_type='expand')
    df = df.apply(shift_if_special_missing, axis=1, result_type='expand')
    df = df.apply(shift_if_finish_missing, axis=1, result_type='expand')

    df.columns = ['Number', 'Type', 'Length', 'Finish', 'Profile', 'Quantity', 'Special_eq',
                  'Others']
    df['Type'] = df['Type'].apply(lambda x: x.replace(' ', ''))
    df = df.sort_values(by='Number', ascending=True)
    df = df.reset_index(drop=True)
    df['Quantity'] = df['Quantity'].astype(int)
    df.loc['System'] = system_name
    logger.info('Order dataframe:\n%s', df.to_string(index=False))
    return df


def join_incorect_rows(df, system_name):
    # Get the rows with the system name and lockbase(to mark end of page)
    system_rows = df[(df['text'].str.contains(system_name)) & (~df['text'].str.contains('LOCKBASE'))]
    lockbase_rows = df[df['text'].str.contains('LOCKBASE')]
    new_df = pd.DataFrame()
    # Loop over the rows with the system name
    for _, system_row in system_rows.iterrows():
        # Find the rows from the system row up to the LOCKBASE row
        if lockbase_rows.index.max() == 0:  # for one-page orders
            relevant_rows = df.loc[system_row.name:]
        else:  # for multiple pages, relevant rows are only until end of a page ('lackbase')
            next_index = lockbase_rows.loc[lockbase_rows.index > system_row.name].index[0] - 1
            relevant_rows = df.loc[system_row.name:next_index]
        # Find rows with matching location and within the 160 position difference which means they are in the same box

        matching_rows = relevant_rows[(abs(relevant_rows['location'].str[0] - system_row['location'][0]) < 1)
                                      & ((system_row['location'][1] - relevant_rows['location'].str[1]) < 160) & (
                                              0 <= (system_row['location'][1] - relevant_rows['location'].str[1]))]
        first_row = matching_rows.iloc[0]
        for i, row in matching_rows.iloc[1:].iterrows():
            first_row['text'] += '' + row['text']
        new_df = new_df.append(first_row, ignore_index=True)
    # Return the updated dataframe
    return new_df


def extract_text(folder, pdf_filename):
    # Extract the text from the order PDF file
    pdf_path = folder + pdf_filename
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
    return df


def get_system_name(df):
    # Get name of the system which is in first row of first column after "System:"
    header = df.iloc[0, 0].split("\n")
    system_name = ''
    for part in header:
        if "System:" in part:
            system_name = part[8:].strip()
            if system_name.endswith('000'):
                system_name = system_name[:-3]
    return system_name


def shift_if_length_missing(row):
    # shifts row to the right if length value is missing (padlocks)
    pattern = r'^[-G\d\s]+$'

    if not bool(re.match(pattern, row[2])):
        return [row[0], row[1], ''] + list(row[2:7])
    else:
        return list(row[0:8])


def shift_if_special_missing(row):
    # shifts row to the right if special_eq value is missing (padlocks)
    pattern = r'^[ab\d\s]+$'
    if bool(re.match(pattern, row[6])):
        return list(row[0:6]) + ['', row[6]]
    else:
        return list(row[0:8])


def shift_if_finish_missing(row):
    # shifts row to the right if finish value is missing (padlocks)
    if row[4].isdigit() and not row[5].isdigit():
        return list(row[0:3]) + [''] + list(row[3:7])
    else:
        return list(row[0:8])


def add_order_pinning(order_df, system_df): # TODO: to many positions after merge
    # Adds pinns to order from pdf by merging with system dataframe
    merged_df = pd.merge(order_df, system_df, on=['Number', 'Finish', 'Length', 'Profile', 'Type', 'Special_eq',
                                                  'Quantity'])
    merged_df.drop(columns=['Others', 'Date', 'Quantity'], inplace=True)
    merged_df.index += 1
    merged_df.loc['System'] = order_df.loc['System']

    return merged_df


def get_order_types(df):
    order_types = df.Type.unique().tolist()
    return order_types


def split_order(selected_fields):
    # get pin data stored in dto
    order_with_pins = dto.data_frame
    automatic = order_with_pins[order_with_pins['Type'].isin(selected_fields)].append(order_with_pins.loc['System'])
    manual = order_with_pins[~order_with_pins['Type'].isin(selected_fields)].append(order_with_pins.loc['System'])
    return automatic, manual


def create_aps_file(df, folder_path):
    # create filename and forlder path for coverterd  txt file
    table_name = df.loc['System', 'Number']
    today = datetime.today().date()
    file_name = f'{table_name}_{today}.txt'
    folder_path = folder_path + file_name
    type_dict = {'PL': [], 'CL': [], 'DC EU': ['LC+XT', 'LO+XT', 'LC'], 'BC EU': ['LOG XT', 'LCG'],
                 'HC EU': ['LCJ+XT', 'LOJ XT'], 'HC R': []}

    cylinder_pins_dict = {'0': 'A_B00', '1': 'A_B01', '2': 'A_B02', '3': 'A_B03', '4': 'A_B04', '5': 'A_B05',
                          '6': 'A_B06', '7': 'A_B07', '8': 'A_B08', '9': 'A_B09', '10': 'A_B0A', '11': 'A_B0B'}

    ext_pins_dict = {'2': 'A_U02', '3': 'A_U03', '4': 'A_U04', '5': 'A_U05', '6': 'A_U06', '7': 'A_U07', '8': 'A_U08',
                     '9': 'A_U09'}

    body_pins_dict = {'0': 'A_K00', '1': 'A_K01', '2': 'A_K02'}
    print(type_dict, cylinder_pins_dict, ext_pins_dict, body_pins_dict)
    with open(folder_path, 'w') as f:
        contents = df.to_csv(index=False)
        f.write(contents)
        print(f"APS file saved to {folder_path}")
        df.drop('System').to_csv(f, index=False)

        return '--aps file created successfully-- '


def create_aps_pdf(automatic, folder_path):
    df = automatic

    pdf_file = 'data.pdf'
    doc = SimpleDocTemplate(pdf_file, pagesize=letter)
    data = [df.columns] + df.values.tolist()
    print(folder_path, doc)
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


def create_non_aps_pdf(manual, folder_path):
    print(manual, folder_path)
    # print(manual.drop('System'))
    return ' --non aps pdf file created successfully-- '

def fill_missing_pins(df, x):
    new_df = df.copy()
    # Loop through each list of strings in the DataFrame column
    for i in range(len(new_df['Extension_pins_sums'])):
        # Get the current list of strings and its length
        curr_list = new_df['Extension_pins_sums'][i]
        curr_len = len(curr_list)

        # Loop through each string in the current list
        for j in range(curr_len):
            # Get the current string and its length
            curr_str = curr_list[j]
            str_len = len(curr_str)

            # If the current string is shorter than x, add empty values to the end
            if str_len < x:
                curr_str += ' ' * (x - str_len)

            # If this is the first string in the list, use the corresponding string from the Cylinder_pins column to fill in missing values
            if j == 0:
                for k in range(x):
                    if curr_str[k] == ' ':
                        curr_str = curr_str[:k] + new_df['Cylinder_pins'][i][k] + curr_str[k + 1:]
            # If there is a previous string in the same list, use it to fill in missing values
            elif j > 0:
                for k in range(x):
                    if curr_str[k] == ' ':
                        curr_str = curr_str[:k] + curr_list[j - 1][k] + curr_str[k + 1:]

            # Update the current string in the list with the modified string
            curr_list[j] = curr_str

        # Update the DataFrame with the modified list of strings
        new_df.at[i, 'Extension_pins_sums'] = curr_list

    return  new_df