import datetime
import random
import tkinter as tk
from tkinter import ttk
import requests
import pandas as pd
from io import StringIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading

# Variable to store the Tkinter chart
tk_chart = None

# Function to fetch stock list from Alpha Vantage API
def fetch_stock_list():
    api_key = 'RDHN0ZBMJFQPR6XT'  
    url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'LISTING_STATUS',
        'apikey': api_key
    }

    response = requests.get(url, params=params)
    data = response.text

    load_data(data)

# Function to fetch the current price of a stock from Alpha Vantage API
def fetch_current_price(symbol):
    api_key = 'RDHN0ZBMJFQPR6XT'
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}'
    response = requests.get(url)
    data = response.json()
    try:
        price = data['Global Quote']['05. price']
    except KeyError:
        price = 'N/A'
    return price

# Function to load data into Treeview
def load_data(data):
    global df
    df = pd.read_csv(StringIO(data))
    for item in tree.get_children():
        tree.delete(item)
    
    # Use threading to fetch current prices asynchronously
    def insert_rows():
        for index, row in df.iterrows():
            current_price = fetch_current_price(row['symbol'])
            tree.insert("", "end", values=(row['symbol'], row['name'], row['exchange'], row['assetType'], row['ipoDate'], row['delistingDate'], row['status'], current_price))
        loading_label.grid_forget()  # Remove the loading message after data is loaded

    thread = threading.Thread(target=insert_rows)
    thread.start()

# Function to create the main interface
def create_main_interface():
    global tree, loading_label, canvas
    root = tk.Tk()
    # Get the width and height of the screen
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # Set the geometry of the window to occupy the entire screen
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    root.title("Stock List" if language == "English" else "Lista de Ações")

    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    columns = ("symbol", "name", "exchange", "assetType", "ipoDate", "delistingDate", "status", "currentPrice")
    column_headers = {
        "English": ["Symbol", "Name", "Exchange", "Asset Type", "IPO Date", "Delisting Date", "Status", "Current Price"],
        "Portuguese": ["Símbolo", "Nome", "Bolsa", "Tipo de Ativo", "Data IPO", "Data de Retirada", "Status", "Preço Atual"]
    }

    tree = ttk.Treeview(frame, columns=columns, show='headings')
    for col, header in zip(columns, column_headers[language]):
        tree.heading(col, text=header)

    tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

    loading_label = ttk.Label(frame, text="Loading..." if language == "English" else "Carregando...")
    loading_label.grid(row=1, column=0, sticky=tk.W, pady=10)

    fetch_stock_list()  # Automatically fetch the stock list when creating the interface

    # Bind a function to be called when a row is selected in the Treeview
    tree.bind("<<TreeviewSelect>>", show_stock_chart)

    canvas = tk.Canvas(root, width=600, height=400)
    canvas.grid(row=1, column=0, sticky=(tk.W, tk.E))

    root.mainloop()

# Function to show the stock chart when a row is selected
def show_stock_chart(event):
    selection = tree.selection()  # Get the selected item(s)
    if selection:
        selected_symbol = tree.item(selection[0])['values'][0]  # Get the symbol of the first selected item
        stock_data = get_stock_data(selected_symbol)
        plot_stock_chart(selected_symbol, stock_data)

def get_stock_data(symbol):
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=5*365)  # The lest five year
    num_points = 50
    date_range = pd.date_range(start=start_date, end=end_date, periods=num_points)
    
    stock_data = {'date': date_range,
                  'close': [random.uniform(100, 200) for _ in range(len(date_range))]}
    return stock_data

# Function to plot the stock chart
def plot_stock_chart(symbol, stock_data):
    plt.figure(figsize=(8, 4))
    plt.plot(stock_data['date'], stock_data['close'], marker='o', linestyle='-')
    plt.title(f"Stock Price Chart for {symbol}")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.grid(True)
    plt.xticks(rotation=45)

    # Convert the Matplotlib figure to a Tkinter widget and display it on the Canvas
    global canvas, tk_chart
    if tk_chart:
        tk_chart.get_tk_widget().destroy()  # Destroy the previous chart
    tk_chart = FigureCanvasTkAgg(plt.gcf(), master=canvas)
    tk_chart.draw()
    tk_chart.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

# Function to choose the language and open the main interface
def choose_language(lang):
    global language
    language = lang
    lang_selection_window.destroy()
    create_main_interface()

# Create the initial language selection interface
lang_selection_window = tk.Tk()
lang_selection_window.title("Choose Language")

frame = ttk.Frame(lang_selection_window, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

language_label = ttk.Label(frame, text="Choose your language / Escolha seu idioma")
language_label.grid(row=0, column=0, columnspan=2, pady=10)

english_button = ttk.Button(frame, text="English", command=lambda: choose_language("English"))
english_button.grid(row=1, column=0, padx=5, pady=5)

portuguese_button = ttk.Button(frame, text="Português", command=lambda: choose_language("Portuguese"))
portuguese_button.grid(row=1, column=1, padx=5, pady=5)

# Get the width and height of the screen
screen_width = lang_selection_window.winfo_screenwidth()
screen_height = lang_selection_window.winfo_screenheight()

# Get the dimensions of the language selection window
window_width = lang_selection_window.winfo_reqwidth()
window_height = lang_selection_window.winfo_reqheight()

# Calculate the coordinates for the center of the screen
x = (screen_width - window_width) // 2
y = (screen_height - window_height) // 2

# Set the geometry of the language selection window to appear in the center of the screen
lang_selection_window.geometry(f"+{x}+{y}")

lang_selection_window.mainloop()