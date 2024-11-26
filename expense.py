import streamlit as st
import pyodbc
from datetime import datetime
import pandas as pd

# Connect to MS SQL Server
server_name = "YOUR_SERVER_NAME"
database_name = "YOUR_DATABASE_NAME"
connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server_name};DATABASE={database_name};Trusted_Connection=yes;"
conn = pyodbc.connect(connection_string)
cursor = conn.cursor()

# Function to create table if it doesn't exist
def create_table():
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Expenses' AND xtype='U')
    CREATE TABLE Expenses (
        id INT IDENTITY(1,1) PRIMARY KEY,
        date DATE NOT NULL,
        description NVARCHAR(255) NOT NULL,
        category NVARCHAR(50) NOT NULL,
        amount FLOAT NOT NULL
    );
    """)
    conn.commit()

# Ensure table is created
create_table()

# Function to add an expense
def add_expense(description, category, amount):
    date = datetime.now().strftime("%Y-%m-%d")  # This Auto-generate today's date
    cursor.execute("INSERT INTO Expenses (date, description, category, amount) VALUES (?, ?, ?, ?)",
                   (date, description, category, amount))
    conn.commit()

# Function to fetch all expenses
def fetch_expenses():
    query = "SELECT * FROM Expenses ORDER BY date DESC, id DESC"
    df = pd.read_sql(query, conn)
    return df

# Function to delete an expense
def delete_expense(expense_id):
    cursor.execute("DELETE FROM Expenses WHERE id = ?", (expense_id,))
    conn.commit()

# Function to edit an expense
def edit_expense(expense_id, description, category, amount):
    cursor.execute("UPDATE Expenses SET description = ?, category = ?, amount = ? WHERE id = ?",
                   (description, category, amount, expense_id))
    conn.commit()

# Streamlit app UI Title Header
st.title("Personal Expense Tracker")

# Add Expense Section
with st.form("add_expense_form", clear_on_submit=True):
    st.header("Add New Expense")
    description = st.text_input("Description")
    category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Bills", "Other"])
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    submit = st.form_submit_button("Add Expense")

    if submit and description and amount > 0:
        add_expense(description, category, amount)
        st.success("Expense added successfully!")

# Show Expenses Section
st.header("Your Expenses")
expenses = fetch_expenses()

if not expenses.empty:
    # Group by date and display expenses
    grouped = expenses.groupby("date")
    for date, group in grouped:
        st.subheader(f"Date: {date}")
        for _, row in group.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
            col1.text(row["description"])
            col2.text(row["category"])
            col3.text(f"${row['amount']:.2f}")
            edit_btn = col4.button("Edit", key=f"edit_{row['id']}")
            delete_btn = col5.button("Delete", key=f"delete_{row['id']}")

            if delete_btn:
                delete_expense(row["id"])
                st.experimental_rerun()

            if edit_btn:
                with st.form(f"edit_form_{row['id']}", clear_on_submit=False):
                    new_description = st.text_input("Description", value=row["description"])
                    new_category = st.selectbox("Category", ["Food", "Transport", "Shopping", "Bills", "Other"],
                                                 index=["Food", "Transport", "Shopping", "Bills", "Other"].index(row["category"]))
                    new_amount = st.number_input("Amount", value=row["amount"], format="%.2f")
                    save_changes = st.form_submit_button("Save Changes")

                    if save_changes:
                        edit_expense(row["id"], new_description, new_category, new_amount)
                        st.success("Expense updated successfully!")
                        st.experimental_rerun()

# Download csv Button
st.header("Download Expenses")
if not expenses.empty:
    csv = expenses.to_csv(index=False)
    st.download_button("Download as CSV", data=csv, file_name="expenses.csv", mime="text/csv")
else:
    st.info("No expenses to download yet.")
