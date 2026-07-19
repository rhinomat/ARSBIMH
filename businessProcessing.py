'''
    businessProcessing.py
    This program:
    * removes unwanted fields from the retrieved business CSV.
    * Trims down CSV for needed area range 
'''

import os
import pandas as pd

folder_area = "businessInfo"

active_directory = os.path.join(os.getcwd(), folder_area)

