import re
import pickle

from collections import UserDict
from datetime import datetime, timedelta


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        super().__init__(value)


class Phone(Field):
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("\033[91mPhone number must be 10 digits.\033[0m")
        super().__init__(value)
    
    @staticmethod 
    def validate(value):
        # Phone number verification
        return bool(re.fullmatch(r'\d{10}', value))


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    # Add new number
    def add_phone(self, phone_number):
        phone = Phone(phone_number)
        self.phones.append(phone)

    # Removes a phone number
    def remove_phone(self, phone_number):
        phone_to_remove = self.find_phone(phone_number)
        if phone_to_remove:
            self.phones.remove(phone_to_remove)
        else:
            raise ValueError("\033[91mPhone number not found.\033[0m")
        
    # Change phone number
    def edit_phone(self, old_number, new_number):
        phone_to_edit = self.find_phone(old_number)
        if phone_to_edit:
            self.add_phone(new_number)
            self.remove_phone(old_number)
        else:
            raise ValueError("\033[91mOld phone number not found.\033[0m")
        
    # Search phone number
    def find_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    # Contact list and birthday
    def __str__(self):
        phones_str = '; '.join(p.value for p in self.phones) if self.phones else "No phones"
        birthday_str = str(self.birthday) if self.birthday else "No birthday"
        list_contact = (
            f"\033[93mContact name: \033[1m{self.name.value}\033[0m; " 
            f"\033[93mPhones: \033[1m{phones_str}\033[0m; " 
            f"\033[93mBirthday: \033[1m{birthday_str}\033[0m"
        )
        return list_contact


class Birthday(Field):
    def __init__(self, value):
        if self.validate_date(value):
            self.value = value
        else:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        
    def validate_date(self, date_string):
        try:
            datetime.strptime(date_string, "%d.%m.%Y").date()
            return True
        except ValueError:
            return False
        
    def __str__(self):
        return self.value


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)
    
    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError

    def get_upcoming_birthdays(self):
        upcoming = []
        today = datetime.now().date()
        week_later = today + timedelta(days=7)

        for record in self.data.values():
            if not record.birthday:
                continue
            
            actual_bday = datetime.strptime(record.birthday.value, "%d.%m.%Y").date().replace(year=today.year)
            if actual_bday < today:
                actual_bday = actual_bday.replace(year=today.year + 1)
                
            next_working_day = actual_bday
            if actual_bday.weekday() == 5:
                next_working_day += timedelta(days=2)
            elif actual_bday.weekday() == 6:
                next_working_day += timedelta(days=1)

            if today <= next_working_day <= week_later:
                if next_working_day != actual_bday:
                    upcoming.append(
                        f"Birthday \033[1m{record.name.value} {actual_bday.strftime('%d.%m.%Y')}\033[0m\n"
                        f"Birthday \033[1m{record.name.value}\033[0m has been moved to the next working day: "
                        f"\033[1m{next_working_day.strftime('%d.%m.%Y')}\033[0m"
                    )

                else:
                    upcoming.append(f"Birthday \033[1m{record.name.value} {actual_bday.strftime('%d.%m.%Y')}\033[0m")
        
        return "\n".join(upcoming) if upcoming else "No upcoming birthdays in the next week."
    
    # Save to file
    def save_data(book, filename="addressbook.pkl"):
        with open(filename, "wb") as f:
            pickle.dump(book, f)

    # Loading from file
    def load_data(filename="addressbook.pkl"):
        try:
            with open(filename, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return AddressBook()

    def __str__(self):
        if not self.data:
            return "\033[91mAddress book is empty.\033[0m"
        
        return "\n".join(str(record) for record in self.data.values())


def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

# Decoder for error processing
def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return "\033[91mGive me name and phone please.\033[0m"
        except KeyError:
            return "\033[91mContact not found.\033[0m"
        except IndexError:
            return "\033[91mPlease provide the correct number of arguments.\033[0m"
        except Exception as e:
            return str(e)
    
    return inner

# Add a contact to your address book
@input_error
def add_contact(args, book: AddressBook):
        name, phone, *_ = args
        record = book.find(name)
        message = "Contact update."
        if record is None:
            record = Record(name)
            book.add_record(record)
            message = "Contact added."
        if phone:
            record.add_phone(phone)
        return message

# Delete a contact from the address book
@input_error
def delete_contact(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record:
        book.delete(name)
        return f"Contact {name} has been deleted."
    return f"\033[91mContact {name} not found.\033[0m"

# Delete a number from a contact
@input_error
def delete_phone(args, book: AddressBook):
    name, phone = args
    record = book.find(name)
    if record:
        record.remove_phone(phone)
        return f"Phone number {phone} removed from contact {name}."
    return f"\033[91mContact {name} not found.\033[0m"

# Update number
@input_error
def change_phone(args, book: AddressBook):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return f"Phone number {old_phone} changed to {new_phone} for contact {name}."
    return f"\033[91mContact {name} not found.\033[0m"

# Search for a number by name
@input_error
def get_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record:
        phones = ', '.join(phone.value for phone in record.phones)
        return f"Phone numbers for {name}: {phones}"
    return f"\033[91mContact {name} not found.\033[0m"

#Add a birthday to contact
@input_error
def add_birthday(args, book):
    if len(args) < 2:
        raise IndexError("Please provide name and birthday in format DD.MM.YYYY")
    name, birthday_str = args[0], args[1]
    record = book.find(name)
    if record:
        try:
            record.add_birthday(birthday_str)
            return f"Birthday for {name} added: {birthday_str}"
        except ValueError as e:
            return f"\033[91m{str(e)}\033[0m"
    else:
        return f"Contact {name} not found."

# Show birthday to contact
@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return f"{name}'s birthday is: {record.birthday}"
    return f"{name} has no birthday set."

# Displays contacts whose birthdays are 7 days ahead.
@input_error
def birthdays(args, book):
    upcoming_birthdays = book.get_upcoming_birthdays()
    return upcoming_birthdays

# List of commands to help the user (color)
command_list = (
    "\033[1m\033[92mCommand list:\033[0m\n"
    "\033[93mAdd (username) (phone) - adds a contact;\n"
    "\033[93mDelete-contact, del-cont (username) - delete a contact;\n"
    "\033[93mRemove-phone, rem-ph (username) - delete a contact;\n"
    "\033[93mSave - saved address book;\n"
    "\033[93mPhone (username) - searches for a phone number by username;\n"
    "\033[93mChange (username) (phone) - stores the new phone number for username in memory;\n"
    "\033[93mAll, list - shows all contacts;\n"
    "\033[93mAdd-birthday (name) (date of birth) - add the date of birth for the specified contact;\n"
    "\033[93mShow-birthday (name) - show the date of birth for the specified contact;\n"
    "\033[93mBirthdays - show the birthdays for the next 7 days with the dates when they should be greeted;\n"
    "\033[91mClose, exit - finishes the work.\033[0m"
)


def main():
    book = AddressBook.load_data()
    print("\033[95mWelcome to the assistant bot!\033[0m")
    
    while True:
        user_input = input("\033[96mEnter a command: \033[0m")

        if not user_input: # Handling an error on empty input
            print("\033[91mPlease enter a command.\033[0m")
            continue

        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            AddressBook.save_data(book)
            print(
                "\033[92mSaved\n\033[1mGood bye!\033[0m"
            )
            break
        
        elif command == "hello":
            print("How can I help you?")

        elif command == "save":
            AddressBook.save_data(book)
            print("\033[92m\033[1mSaved successfully.\033[0m")

        elif command in ["help", "command"]:
            print(command_list)
        
        elif command == "add":
            print(add_contact(args, book))
        
        elif command in ["all", "list"]:
            print(book)
        
        elif command == "add-birthday":
            print(add_birthday(args, book))
        
        elif command == "show-birthday":
            print(show_birthday(args, book))
        
        elif command == "birthdays":
            print(birthdays(args, book))
        
        elif command in ["delete-contact", "del-cont"]:
            print(delete_contact(args, book))
        
        elif command in ["remove-phone","rem-ph"]:
            print(delete_phone(args, book))
        
        elif command == "change":
            print(change_phone(args, book))
       
        elif command == "phone":
            print(get_phone(args, book))
        
        else:
            print("\033[91mInvalid command.\033[0m")


if __name__ == "__main__":
    main()