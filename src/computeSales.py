import sys
import os
import re
import math
from decimal import *
import sqlite3
from sqlite3 import Error
import time
from signal import signal, SIGINT
from sys import exit

def print_menu():      
    print (10 * "-" , "MENU" , 10 * "-")
    print ("1: read new input file")
    print ("2: print statistics for a specific product")
    print ("3: print statistics for a specific AFM")
    print ("4: exit the program")
 
def check_AFM(afm):
    if (afm.isdigit()):
        if( len(afm)==10):
            return 1
        return 0

def check_new_bill(ln):
    checker=re.compile(r'[-]')
    string=checker.search(ln)
    return bool(string)


def read_new_file(conn):
    m_conn=conn
    afm_flag=0
    correct_bill=0
    newBill=0
    f_name=input("give file name: ")
    if not os.path.isfile(f_name):
        print("{} does not exist ".format(f_name))
        return 
    with open(f_name) as fop:
        #The following for loop gets all the lines of the file
        for ln in fop:
            if ln.strip():            
                if "-" in ln:
                    delete_temp_table(m_conn)
                    correct_bill=0
                    bill_total_price=Decimal(0.00)
                    continue
                #if this line is not ----- AND ΑΦΜ: exists in line
                if ("ΑΦΜ:" in ln):             
                    afm=(ln.split()[1])
                    correct_bill=check_AFM(afm)
                    continue
                #if this line is not ----- AND ΣΥΝΟΛΟ: exists in line
                elif("ΣΥΝΟΛΟ:" in ln and correct_bill):
                    synolo=(ln.split()[1])
                    if (bill_total_price==Decimal(synolo)):
                        bill_total_price = float(bill_total_price)
                        insert_in_bills(m_conn)
                        continue
                    else:
                        continue
                elif(correct_bill):
                    try:
                        product_name=(ln.split(':')[0])
                        product_name=product_name.upper()  
                        rest=(ln.split(':')[1])           
                        quantity=(rest.split()[0])
                        price=(rest.split()[1])
                        total=(rest.split()[2]) 
                    except Exception as e:
                        correct_bill=0
                        continue                
                    if ( (Decimal(quantity)*Decimal(price) ) == Decimal(total)):
                        bill_total_price += Decimal(total)
                        float_total = float (bill_total_price)
                        total=float(total)
                        price=float(price)
                        quantity=int(quantity)
                        insert_in_temp(m_conn, afm, product_name, quantity, price, total, float_total)
                    else:
                        correct_bill=0
    return             

def second_question(conn, pr):
    cur = conn.cursor()
    cur.execute("SELECT AFM, SUM(total) FROM bills WHERE product_name=? GROUP BY AFM, product_name",(pr,) )
    pn=cur.fetchall()
    for row in pn:
            t=round(row[1],2)
            afm=str(row[0])
            print(afm,t)

def third_question(conn, afm):
    cur = conn.cursor()
    cur.execute("SELECT product_name, SUM(total) FROM bills WHERE AFM=? GROUP BY product_name",(afm,) )
    pn=cur.fetchall()
    for row in pn:
            t=round(row[1],2)
            print(row[0],t)


def delete_temp_table(conn):
    delete="DELETE FROM temp"
    c = conn.cursor()
    c.execute(delete)


def insert_in_bills(conn):
    cur = conn.cursor()
    cur.execute("INSERT INTO bills SELECT * FROM temp")
    return 


def insert_in_temp(conn, afm, product_name, quantity, price, total, bill_total_price):
    cur = conn.cursor()
    cur.execute("INSERT INTO temp (AFM, product_name, quantity, price, total, bill_total_price) VALUES (?, ?, ?, ?, ?, ?)",
            (afm, product_name, quantity, price, total, bill_total_price))
    return


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
 
    return conn


def create_temp_table(conn):
    sql_create_temp_table = """CREATE TABLE IF NOT EXISTS temp (
                                    AFM text NOT NULL,
                                    product_name text,
                                    quantity integer NOT NULL,
                                    price real NOT NULL,
                                    total real NOT NULL,
                                    bill_total_price real NOT NULL 
                               );"""
    try:
        c = conn.cursor()
        c.execute(sql_create_temp_table)
    except Error as e:
        print(e)

def handler(signal_received, frame):
    # Handle any cleanup here
    delete_files()
    #print('SIGINT or CTRL-C detected. Exiting gracefully')
    exit(0)
    

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def delete_files():
    if os.path.exists("memory"):
        os.remove("memory")
    else:
         pass


if __name__ == '__main__':
    # Tell Python to run the handler() function when SIGINT is recieved
    signal(SIGINT, handler)
    conn = create_connection("memory")
    # drop_bills_table(conn)
    # drop_temp_table(conn)
    sql_create_bills_table = """CREATE TABLE IF NOT EXISTS bills (
                                    AFM text NOT NULL,
                                    product_name text,
                                    quantity integer NOT NULL,
                                    price real NOT NULL,
                                    total real NOT NULL,
                                    bill_total_price real NOT NULL 
                               );"""

    
    # create tables
    if conn is not None: 
        # create bills and temp tables
        create_table(conn, sql_create_bills_table)
        create_temp_table(conn)
    else:
        print("Error! cannot create the database connection.")
    loop=True      
  
    while loop:        
        print_menu()  
        try:
            choice =int(input("Enter your choice [1-4]: "))
            if (choice==1):
                read_new_file(conn)
            elif (choice==2):
                product =(input("ENTER PRODUCT: "))
                product=product.upper()
                second_question(conn,product)
            elif (choice==3):
                afm =input("ENTER AFM: ")
                third_question(conn,afm)
            elif (choice==4):
                loop=False
                delete_files()
            else:
                print("Wrong option selection. ")
        except ValueError:
            print("invalid input")    
