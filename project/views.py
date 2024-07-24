import uuid
import requests
import json
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from .models import Exam, Question, Session, Answer
from . import db
import os
from fpdf import FPDF
from flask import send_file
from flask import send_from_directory

views = Blueprint('views', __name__)

@views.route('/')
def main():
    exams = Exam.query.all()
    return render_template("home.html", exams=exams)


@views.route('/create_exam')
def create_exam():
    return render_template('create_exam.html')


@views.route('/add_exam', methods=['POST'])
def add_exam():
    name = request.form['name']
    description = request.form['description']
    initial_prompt = request.form['initial_prompt']
    questions = request.form.getlist('questions[]')
    answers = request.form.getlist('answers[]')

    new_exam = Exam(name=name, description=description, initial_prompt=initial_prompt)
    db.session.add(new_exam)
    db.session.commit()

    for question_text, answer in zip(questions, answers):
        new_question = Question(exam_id=new_exam.id, question_text=question_text, answer=answer)
        db.session.add(new_question)

    db.session.commit()
    return redirect(url_for('views.main'))


@views.route('/start_exam/<int:exam_id>')
def start_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    questions = Question.query.filter_by(exam_id=exam.id).all()
    return render_template('start_exam.html', exam=exam, questions=questions)


@views.route('/edit_exam/<int:exam_id>')
def edit_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    questions = Question.query.filter_by(exam_id=exam.id).all()
    return render_template('edit_exam.html', exam=exam, questions=questions)

@views.route('/delete_exam/<int:exam_id>', methods=['POST', 'DELETE'])
def delete_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    return redirect(url_for('views.main'))


@views.route('/update_exam/<int:exam_id>', methods=['POST'])
def update_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    exam.name = request.form['name']
    exam.description = request.form['description']
    exam.initial_prompt = request.form['initial_prompt']

    # Update existing questions
    for question_id, question_data in request.form.getlist('questions'):
        question = Question.query.get(question_id)
        if question:
            question.question_text = question_data['text']
            question.answer = question_data['answer']

    # Add new questions
    for question_data in request.form.getlist('new_questions'):
        new_question = Question(
            exam_id=exam.id,
            question_text=question_data['text'],
            answer=question_data['answer']
        )
        db.session.add(new_question)

    # Delete questions
    for question_id in request.form.getlist('delete_questions'):
        question = Question.query.get(question_id)
        if question:
            db.session.delete(question)

    db.session.commit()
    return redirect(url_for('views.main'))

@views.route('/generate_session/<int:exam_id>', methods=['GET'])
def generate_session(exam_id):
    session_id = str(uuid.uuid4())
    new_session = Session(id=session_id, exam_id=exam_id)
    db.session.add(new_session)
    db.session.commit()

    initialize_conversation(session_id)  # Initialize the conversation with the initial prompt

    return jsonify({'session_id': session_id})


@views.route('/take_exam/<session_id>', methods=['GET'])
def take_exam(session_id):
    exam_session = Session.query.get_or_404(session_id)
    exam = Exam.query.get_or_404(exam_session.exam_id)
    questions = Question.query.filter_by(exam_id=exam.id).all()

    questions_data = [{'id': q.id, 'question_text': q.question_text} for q in questions]

    return render_template('take_exam.html', session_id=session_id, exam=exam, questions=questions_data)

@views.route('/submit_exam/<session_id>', methods=['POST'])
def submit_exam(session_id):
    data = request.json
    question_answers = data.get('questions', [])

    for qa in question_answers:
        question_id = qa.get('id')
        answer_text = qa.get('answer')
        if question_id and answer_text:
            answer = Answer(
                session_id=session_id,
                question_id=question_id,
                answer_text=answer_text
            )
            db.session.add(answer)

    db.session.commit()
    return redirect(url_for('views.generate_report', session_id=session_id))

server_url = 'http://localhost:11434/api/chat'

# Initialize conversation_history as a dictionary of lists
conversation_histories = {}

def initialize_conversation(session_id):
    session = Session.query.get(session_id)
    if not session:
        return

    exam = Exam.query.get(session.exam_id)
    if not exam:
        return

    conversation_history = [
        {"role": "system", "content": exam.initial_prompt}
    ]

    payload = {
        "model": "llama3",
        "messages": conversation_history  # Send the entire conversation history
    }

    # Make an HTTP POST request to the server URL
    response = requests.post(server_url, json=payload)

    # Process the server response
    response_parts = response.text.strip().split("\n")
    combined_messages = ""
    for response_part in response_parts:
        response_data = json.loads(response_part)
        if "message" in response_data:
            message_content = response_data["message"]["content"]
            combined_messages += message_content.strip() + " "

    # Append the assistant's response to the conversation history
    conversation_history.append({"role": "assistant", "content": combined_messages.strip()})

    # Store the conversation history in the dictionary
    conversation_histories[session_id] = conversation_history

@views.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    session_id = data.get("session_id")
    prompt = data.get("prompt")

    # Ensure conversation_history for this session_id exists
    if session_id not in conversation_histories:
        return jsonify({"error": "Session not found."}), 404

    conversation_history = conversation_histories[session_id]

    # Append the user's message to the conversation history
    conversation_history.append({"role": "user", "content": prompt})

    payload = {
        "model": "llama3",
        "messages": conversation_history  # Send the entire conversation history
    }

    # Make an HTTP POST request to the server URL
    response = requests.post(server_url, json=payload)

    # Process the server response
    response_parts = response.text.strip().split("\n")
    combined_messages = ""
    for response_part in response_parts:
        response_data = json.loads(response_part)
        if "message" in response_data:
            message_content = response_data["message"]["content"]
            combined_messages += message_content.strip() + " "

    # Append the assistant's response to the conversation history
    conversation_history.append({"role": "assistant", "content": combined_messages.strip()})

    # Update the conversation history in the dictionary
    conversation_histories[session_id] = conversation_history

    # Return the combined messages
    return jsonify({"message": {"role": "assistant", "content": combined_messages.strip()}})


@views.route('/generate_report/<session_id>', methods=['GET'])
def generate_report(session_id):
    session = Session.query.get_or_404(session_id)
    exam = Exam.query.get(session.exam_id)
    answers = Answer.query.filter_by(session_id=session_id).all()
    conversation_log = conversation_histories.get(session_id, [])

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=f"Exam Report for {exam.name}", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Description: {exam.description}", ln=True, align='C')
    pdf.cell(200, 10, txt="Conversation Log:", ln=True, align='L')
    pdf.ln(10)

    for message in conversation_log:
        role = message.get("role")
        content = message.get("content")
        pdf.multi_cell(0, 10, txt=f"{role.capitalize()}: {content}")

    pdf.ln(10)
    pdf.cell(200, 10, txt="Answers:", ln=True, align='L')
    pdf.ln(10)

    for answer in answers:
        question = Question.query.get(answer.question_id)
        pdf.multi_cell(0, 10, txt=f"Q: {question.question_text}")
        pdf.multi_cell(0, 10, txt=f"A: {answer.answer_text}")
        pdf.ln(5)

    # Save the PDF to a file
    reports_dir = os.path.join(os.getcwd(), 'reports')
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    pdf_filename = os.path.join(reports_dir, f"report_{session_id}.pdf")
    pdf.output(pdf_filename)

    return f"Report generated and saved successfully for session ID: {session_id}."

@views.route('/view_report/<session_id>', methods=['GET'])
def view_report(session_id):
    reports_dir = os.path.join(os.getcwd(), 'reports')
    pdf_filename = os.path.join(reports_dir, f"report_{session_id}.pdf")
    if os.path.exists(pdf_filename):
        return send_file(pdf_filename, as_attachment=True)
    else:
        return "Report not found.", 404


@views.route('/reports')
def list_reports():
    reports_dir = 'reports'
    report_files = [f for f in os.listdir(reports_dir) if f.endswith('.pdf')]
    return render_template('list_reports.html', report_files=report_files)


@views.route('/reports/<filename>')
def get_report(filename):
    reports_dir = os.path.join(os.getcwd(), 'reports')
    return send_from_directory(reports_dir, filename)