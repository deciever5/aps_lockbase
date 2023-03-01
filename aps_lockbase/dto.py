from dataclasses import dataclass


# class for storing dataframe for use between modules
@dataclass
class DataFrameDTO:
    data_frame = None


dto = DataFrameDTO()
