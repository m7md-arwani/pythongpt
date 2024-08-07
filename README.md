# Interactive Exam with Llama3.1:8B LLM

This project is an interactive exam platform that allows users to take exams with the assistance of a chatbot powered by LLama3.1:8B. Which is an open-source LLM supported by Meta. The chatbot can help users with questions during the exam. The project is built using Flask for the backend and Llama3.1 for the chatbot functionality.

## Table of Contents

- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [Demo Video](#demo-video)

## Features

- Interactive exam interface
- Chatbot assistance during the exam
- Seamless integration between Flask and Llama3.1:8B
- Maintains conversation history during the exam

## Technologies Used

- Python
- Flask
- Llama3.1:8B (locally)
- HTML/CSS/JavaScript

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- Llama3.1:8B

### Setup

1. **Install Ollama Software:**

    https://ollama.com/download

2. **Run Llama3.1:8B for the first time (will take some time):**
   ```bash
    ollama run llama3.1
    ```
   Shut down the program after it finishes.

3. **Install Required Packages**
   ```bash
    pip install -r requirements.txt

    ```

## Usage

1. **Run the Ollama Server**

    ```bash
    ollama serve
    ```
2. **Run the flask project**

    ```bash
    py app.py
    ```
## Demo Video
The Video assumes you have installed Ollama

[Watch the Demo Video](https://youtu.be/zP0V6YDwfeE)


