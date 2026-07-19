from colorama import Fore, Style
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
    


if __name__ == "__main__":
    main()
