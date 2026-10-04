"""Builds data/synthetic_examples.json (requirement -> category) across business domains."""
import json
import random
from pathlib import Path

random.seed(7)
PREFIX = ["Create a Python", "Write a Python", "Implement a Python", "I need a Python", "Build a Python", "Develop a Python"]
PHRASES = {
    "Functions": ["function to check whether a number is prime", "function to reverse a string", "function that validates email addresses",
                  "function to convert Celsius to Fahrenheit", "function to calculate simple interest for a loan", "function to count vowels in text",
                  "utility function to format a phone number", "function that checks if a year is a leap year", "helper to calculate GST on an invoice"],
    "Algorithms": ["function to calculate factorial using recursion", "implementation of binary search", "function to sort a list using merge sort",
                   "function to generate the Fibonacci series", "algorithm to find the shortest path in a graph", "function to find the GCD of two numbers",
                   "solution to detect a palindrome using two pointers", "function to find the second largest element in a list", "algorithm to aggregate sales by month"],
    "APIs": ["REST endpoint to return customer details", "FastAPI route to create a new order", "API endpoint to fetch patient appointments",
             "REST API that returns product list as JSON", "endpoint for user login with token response", "FastAPI service to list hotel bookings",
             "GET endpoint to retrieve insurance policy by id", "POST endpoint to register a student"],
    "Classes": ["class to model an Employee with salary methods", "class for a bank account with deposit and withdraw", "class representing a Product in a retail store",
                "class for a Student with grade calculation", "class that models a hotel Booking", "class for a shopping Cart with add and remove items",
                "object oriented model of a Patient record", "class for an Insurance Policy with premium calculation"],
    "CRUD Operations": ["module with create, read, update and delete for customers in SQLite", "CRUD functions for an employees table",
                        "database operations to insert and update product records", "functions to add, fetch, update and delete student records",
                        "CRUD layer for a booking database using sqlite3", "script to insert and delete patient rows in a database",
                        "functions to manage orders in a SQLite database"],
    "Data Processing": ["script to filter rows of a CSV file by a column value", "function to read a JSON file and compute totals", "program to clean missing values in a dataset",
                        "function to merge two CSV files on a key", "script to parse a log file and count errors", "function to group dataset rows and compute averages",
                        "program to convert CSV data into JSON", "function to remove duplicate records from a dataset"],
    "Automation": ["script to rename all files in a folder", "script to generate a daily sales report", "workflow script to batch process invoices",
                   "automation that backs up a directory to a zip file", "script to send a summary report file after processing", "script to organize downloads by file type",
                   "batch script to process monthly payroll reports", "automation to archive old log files"],
}
rows = []
for cat, phrases in PHRASES.items():
    for ph in phrases:
        for pre in random.sample(PREFIX, 3):
            rows.append({"requirement": f"{pre} {ph}.", "category": cat})
random.shuffle(rows)
out = Path(__file__).parent.parent / "data" / "synthetic_examples.json"
out.write_text(json.dumps(rows, indent=1))
print(len(rows), "examples ->", out)
