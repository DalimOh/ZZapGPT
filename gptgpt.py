import openai
import tkinter as tk
import sqlite3
import datetime

# Connect to the database
conn = sqlite3.connect('your_database.db')
cursor = conn.cursor()

# personal openai keys
openai.api_key = "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"

def init_user():

    # user 정보 한번만 기입
    cursor.execute('''
    INSERT INTO user (userID, name, email, regDate, age, location)
    SELECT "U-00000000", "홍길동", "honggildong@naver.com", "2023/05/31", 20, "Seoul"
    WHERE NOT EXISTS (
        SELECT 1 FROM user
    )
    ''')


def init_table():

    #create tables if not exists!
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chatGPT (
        ID CHAR(8) PRIMARY KEY,
        name VARCHAR(16) NOT NULL,
        version VARCHAR(4) NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        userID TEXT PRIMARY KEY,
        name VARCHAR(256),
        email VARCHAR(256) NOT NULL UNIQUE,
        regDate TEXT,
        age INTEGER,
        location TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE conversation (
        cID TEXT PRIMARY KEY,
        status INTEGER NOT NULL DEFAULT 0,
        startTime TEXT,
        endTime TEXT,
        curUser TEXT,
        FOREIGN KEY (curUser) REFERENCES user(userID)
    )
    ''')

    cursor.execute('''
    CREATE TABLE category (
        cgID CHAR(8) PRIMARY KEY,
        name TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE question (
        qID TEXT PRIMARY KEY,
        query TEXT NOT NULL,
        timeQu TEXT,
        qCg CHAR(8),
        curConv TEXT,
        FOREIGN KEY (qCg) REFERENCES category(cgID),
        FOREIGN KEY (curConv) REFERENCES conversation(cID)
    )
    ''')

    cursor.execute('''
    CREATE TABLE feedback (
        fID TEXT PRIMARY KEY,
        answer TEXT,
        rating INTEGER,
        timeFeed TEXT,
        curConv TEXT,
        FOREIGN KEY (curConv) REFERENCES conversation(cID)
    )
    ''')

    cursor.execute('''
    CREATE TABLE chatHistory (
        chatID TEXT PRIMARY KEY,
        duration TEXT DEFAULT '0',
        chatUser TEXT,
        curConv TEXT,
        subject TEXT,
        FOREIGN KEY (chatUser) REFERENCES user(userID),
        FOREIGN KEY (curConv) REFERENCES conversation(cID)
    )
    ''')

    cursor.execute('''
    CREATE TABLE preference (
        prefUser TEXT,
        prefCg CHAR(8),
        preTime TEXT NOT NULL,
        FOREIGN KEY (prefUser) REFERENCES user(userID),
        FOREIGN KEY (prefCg) REFERENCES category(cgID),
        PRIMARY KEY (prefUser)
    )
    ''')


def init_gui():
    # Create the GUI window
    window = tk.Tk()
    window.title("ZZapGPT")

    # Create the text box to display the conversation
    text_box = tk.Text(window, height=20, width=50)
    text_box.pack()

    # Create the entry field for user input
    entry = tk.Entry(window, width=50)
    entry.pack()

    # Create the button to submit user input
    button = tk.Button(window, text="Send", command=lambda: gpt_conv(entry, text_box))
    button.pack()

    # Return the necessary GUI components
    return window, text_box, entry

def generate_answer(user_input):
    # Create the chat completion using OpenAI API
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": user_input}]
    )

    return response.choices[0].message.content

def gpt_conv(entry, text_box):

    # openai
    openai_version = openai.__version__

    # list models
    models = openai.Model.list()

    # first model's id
    openai_id = models.data[0].id

    # update if has diffrent values, or insert if not exists
    query = '''
    INSERT INTO chatGPT(ID, name, version)
    VALUES (?, ?, ?)
    ON CONFLICT(ID) DO UPDATE SET
        name = excluded.name,
        version = excluded.version
    WHERE excluded.name <> chatGPT.name OR excluded.version <> chatGPT.version
    '''

    cursor.execute(query, (openai_id, "openai", openai_version))

    user_input = entry.get()

    # Extracting and storing the attributes
    status = 0  # Set the initial status as "closed"
    timequ = None  # Current timestamp
    timeFeed = None  # Current timestamp
    rating = None  # Initialize rating as None
    duration = None  # Placeholder for duration, will be calculated later
    subject = None  # Placeholder for subject, extract from conversation context
    preference = None  # Placeholder for preference, extract from user input

    # create a chat completion
    answer = generate_answer(user_input)

    # Display the user input and chatbot response in the text box
    text_box.insert(tk.END, "User: " + user_input + "\n")
    text_box.insert(tk.END, "ChatGPT: " + answer + "\n\n")

    # Clear the entry field
    entry.delete(0, tk.END)

    conn.commit()


def main():
    # create Tables
    init_table()

    # Setup the GUI window and components
    window, text_box, entry = init_gui()

    # Start the GUI event loop
    window.mainloop()

if __name__ == '__main__':
    main()
