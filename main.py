from colorama import Fore, Style
from retrievalScript import oregon_job_list_retrieval
from businessProcessing import trimColumns, location_filter, status_filter, spreadsheet_transform
def main():
    print(Fore.GREEN + "Welcome to the ARSBIMH" + Style.RESET_ALL)
    print(Fore.GREEN + "Automated Retrieval System for Business Information Meant for Hiring" + Style.RESET_ALL)
    print(Fore.GREEN + "This set of scripts does a set of tasks for hiring information" + Style.RESET_ALL)
    print(Fore.BLUE + "1. Retrieve an information sheet from Oregon Gov that has a list of active businesses" + Style.RESET_ALL)
    print(Fore.BLUE + "2. Sanitize the data sheet by removing undesired fields (i.e. Registry Number, Registration Date, Anniversary)" + Style.RESET_ALL)
    print(Fore.BLUE + "3. Filter out undesirable parts of Oregon to work that are too far by personal standards" + Style.RESET_ALL)
    print(Fore.BLUE + "   (For me, its everything but Portland, Gresham, Troutdale)" + Style.RESET_ALL)
    print(Fore.BLUE + "4. Transform the CSV into a spreadsheet" + Style.RESET_ALL)
    print(Fore.BLUE + "   The preferable application I am doing spreadsheets in is Libreoffice Calc to replace Excel" + Style.RESET_ALL)
    print()
    print()
    task_menu()
    
def task_menu():
    task = 0
    while task >= 0:
        print(Fore.GREEN + "List of Tasks" + Style.RESET_ALL)
        print(Fore.BLUE + "1. Information Sheet Retrieval" + Style.RESET_ALL)
        print(Fore.BLUE + "2. Sanitization of Data Sheet" + Style.RESET_ALL)
        print(Fore.BLUE + "3. Filter out locations" + Style.RESET_ALL)
        print(Fore.BLUE + "4. Spreadsheet Transformation" + Style.RESET_ALL)
        print(Fore.BLUE + "5. Automatically do the process with default values" + Style.RESET_ALL)
        print(Fore.RED + "6. Quit." + Style.RESET_ALL)
        try:
            task = int(input("Please select a task: "))
        except ValueError:
            print(Fore.RED + "Invalid Input: Please make your selection an integer" + Style.RESET_ALL)
            task = 0
            continue
        if task == 1:
            oregon_job_list_retrieval()
        elif task == 2:
            trimColumns()
        elif task == 3:
            location_filter()
        elif task == 4:
            spreadsheet_transform()
        elif task == 5:
            oregon_job_list_retrieval()
            trimColumns()
            location_filter()
            status_filter()
            spreadsheet_transform()
        elif task == 6:
            print(Fore.GREEN + "Thank you for using this application" + Style.RESET_ALL)
            task = -1

if __name__ == "__main__":
    main()
