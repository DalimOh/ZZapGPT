import openai
import tkinter as tk
import sqlite3
import datetime
import uuid
import re

# Connect to the database
conn = sqlite3.connect('zzapgpt.db')
cursor = conn.cursor()

# personal openai keys
openai.api_key = "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"

def extract_subject(cID):
    query = '''
    SELECT query
    FROM question
    WHERE curConv = ? AND timeQu = (
        SELECT MIN(timeQu)
        FROM question
        WHERE curConv = ?
    )
    '''
    cursor.execute(query, (cID, cID))
    result = cursor.fetchone()
    if result:
        result = result[0]
    else:
        result = ""

    # Define a list of common question words to remove from the user input
    question_words = ['how', 'what', 'where', 'when', 'why', 'which', 'who', 'whom']

    # Remove question words from the user input
    cleaned_input = re.sub(r'\b(?:%s)\b' % '|'.join(question_words), '', result, flags=re.IGNORECASE)

    # Remove leading/trailing whitespace and punctuation marks
    cleaned_input = cleaned_input.strip(' ?.,!')

    # Capitalize the first letter of each word in the subject
    words = cleaned_input.split()
    subject_words = [word.capitalize() for word in words]
    subject = ' '.join(subject_words)

    return subject

def init_user():

    uID = "U-"+str(uuid.uuid4())
    # user 정보 한번만 기입
    query = '''
    INSERT INTO user (userID, name, email, regDate, age, location)
    SELECT ?, "홍길동", "honggildong@naver.com", "2023/05/31", 20, "Seoul"
    WHERE NOT EXISTS (
        SELECT 1 FROM user
    )
    '''
    cursor.execute(query, (uID,))

    return uID


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
    CREATE TABLE IF NOT EXISTS conversation (
        cID TEXT PRIMARY KEY,
        status INTEGER NOT NULL DEFAULT 0,
        startTime TIMESTAMP,
        endTime TIMESTAMP,
        curUser TEXT,
        FOREIGN KEY (curUser) REFERENCES user(userID)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS category (
        cgID CHAR(8) PRIMARY KEY,
        name TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS question (
        qID TEXT PRIMARY KEY,
        query TEXT NOT NULL,
        timeQu TIMESTAMP,
        qCg CHAR(8),
        curConv TEXT,
        FOREIGN KEY (qCg) REFERENCES category(cgID),
        FOREIGN KEY (curConv) REFERENCES conversation(cID)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        fID TEXT PRIMARY KEY,
        answer TEXT,
        rating INTEGER,
        timeFeed TIMESTAMP,
        curConv TEXT,
        FOREIGN KEY (curConv) REFERENCES conversation(cID)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chatHistory (
        chatID TEXT PRIMARY KEY,
        duration INTEGER DEFAULT 0,
        chatUser TEXT,
        curConv TEXT,
        subject TEXT,
        FOREIGN KEY (chatUser) REFERENCES user(userID),
        FOREIGN KEY (curConv) REFERENCES conversation(cID)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS preference (
        prefUser TEXT,
        prefCg CHAR(8),
        preTime TEXT NOT NULL,
        FOREIGN KEY (prefUser) REFERENCES user(userID),
        FOREIGN KEY (prefCg) REFERENCES category(cgID),
        PRIMARY KEY (prefUser)
    )
    ''')


def init_gui(cID):
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
    button = tk.Button(window, text="Send", command=lambda: gpt_conv(entry, text_box, cID))
    button.pack()

    # Return the necessary GUI components
    return window, text_box, entry

def generate_answer(user_input):
    # Create the chat completion using OpenAI API
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": user_input}]
    )

    timeFeed = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return response.choices[0].message.content, timeFeed

def gpt_conv(entry, text_box, cID):

    # Extracting and storing the attributes
    status = 0  # Set the initial status as "closed"
    startT = None
    endT = None
    timeQu = None  # Current timestamp
    timeFeed = None  # Current timestamp
    rating = None  # Initialize rating as None
    duration = None  # Placeholder for duration, will be calculated later
    subject = None  # Placeholder for subject, extract from conversation context
    preference = None  # Placeholder for preference, extract from user input

    timeQu = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current timestamp for user question

    user_input = entry.get()

    # create a chat completion, and the answer's time
    answer, timeFeed = generate_answer(user_input)

    # record Question and Answer
    record_Q(user_input, timeQu, cID)
    record_Fd(answer, timeFeed, cID)

    # Display the user input and chatbot response in the text box
    text_box.insert(tk.END, "User: " + user_input + "\n")
    text_box.insert(tk.END, "ChatGPT: " + answer + "\n\n")

    # Clear the entry field
    entry.delete(0, tk.END)

def init_GPT():
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

def init_conv(user):
    # conversation Attribs
    cID = "C-"+str(uuid.uuid4())

    query = '''
    INSERT INTO conversation(cID, status, curUser)
    VALUES(?, ?, ?)
    '''
    cursor.execute(query, (cID, 0, user))

    return cID

def switch_status(cID):
    query = '''
    UPDATE conversation
    SET status = CASE
        WHEN status = 0 THEN 1
        WHEN status = 1 THEN 0
        ELSE status
    END
    WHERE cID = ?
    '''
    cursor.execute(query, (cID,))

def record_History(cID, uID):

    # switch status to 0
    switch_status(cID)

    # set chat time
    q_st_time ='''
    SELECT MIN(timeQu)
    FROM question
    WHERE curConv = ?
    '''
    q_ed1 ='''
    SELECT MAX(timeFeed)
    FROM feedback
    WHERE curConv = ?
    '''
    q_ed2 ='''
    SELECT MAX(timeQu)
    FROM question
    WHERE curConv = ?
    '''

    cursor.execute(q_st_time, (cID,))
    st_time = cursor.fetchone()[0]

    cursor.execute(q_ed1, (cID,))
    ed1 = cursor.fetchone()[0]

    cursor.execute(q_ed2, (cID,))
    ed2 = cursor.fetchone()[0]

    ed_time = max(ed1, ed2)

    q_time = '''
    UPDATE conversation
    SET startTime = ?, endTime = ?
    WHERE cID = ?
    '''
    cursor.execute(q_time, (st_time, ed_time, cID))

    # chatHistory Attribs
    chat_ID = "CH-"+str(uuid.uuid4())
    duration = calc_duration(cID)
    subject = extract_subject(cID)
    q_ht = '''
    INSERT INTO chatHistory(chatID, duration, chatUser, curConv, subject)
    VALUES(?, ?, ?, ?, ?)
    '''
    cursor.execute(q_ht, (chat_ID, duration, uID, cID, subject))

def record_Q(content, tm, conv):

    q_ID = "Q-"+str(uuid.uuid4())
    qry = content
    qTime = tm
    curConv = conv

    query = '''
    INSERT INTO question(qID, query, timeQu, curConv)
    VALUES(?, ?, ?, ?)
    '''
    cursor.execute(query, (q_ID, qry, qTime, curConv))



def record_Fd(content, tm, conv):

    fd_ID = "FD-"+str(uuid.uuid4())
    feedback = content
    fdTime = tm
    curConv = conv

    query = '''
    INSERT INTO feedback(fID, answer, timeFeed, curConv)
    VALUES(?, ?, ?, ?)
    '''
    cursor.execute(query, (fd_ID, feedback, fdTime, curConv))

def calc_duration(cID):
    q_time ='''
    SELECT startTime, endTime
    FROM conversation
    WHERE cID = ?
    '''
    cursor.execute(q_time, (cID,))
    time = cursor.fetchone()
    if time:
        st_time = datetime.datetime.strptime(time[0], "%Y-%m-%d %H:%M:%S")
        ed_time = datetime.datetime.strptime(time[1], "%Y-%m-%d %H:%M:%S")

    if st_time and ed_time:
        duration = ed_time - st_time
        return duration.total_seconds()

def main():
    # create Tables
    init_table()

    # Init GPT
    init_GPT()

    # Insert user values
    us = init_user()

    # Initialize Conversation
    cID = init_conv(us)

    # Setup the GUI window and components
    window, text_box, entry = init_gui(cID)

    # switch status to 1
    switch_status(cID)

    # Start the GUI event loop
    window.mainloop()

    # record History
    record_History(cID, us)

    # commit
    conn.commit()

if __name__ == '__main__':
    main()
