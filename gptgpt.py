import openai
import tkinter as tk

# personal openai keys
openai.api_key = "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"

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
    # list models
    models = openai.Model.list()

    # print the first model's id
    print(models.data[0].id)

    user_input = entry.get()

    # create a chat completion
    answer = generate_answer(user_input)

    # Display the user input and chatbot response in the text box
    text_box.insert(tk.END, "User: " + user_input + "\n")
    text_box.insert(tk.END, "ChatGPT: " + answer + "\n\n")

    # Clear the entry field
    entry.delete(0, tk.END)




def main():
    # Setup the GUI window and components
    window, text_box, entry = init_gui()

    # Start the GUI event loop
    window.mainloop()

if __name__ == '__main__':
    main()
