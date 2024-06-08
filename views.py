import uuid
import openai

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from .models import Exam,Question, Session, Answer
from . import db


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
    final_answer = data.get('final_answer')
    question_answers = data.get('questions')

    for qa in question_answers:
        answer = Answer(
            session_id=session_id,
            question_id=qa['id'],
            answer_text=final_answer
        )
        db.session.add(answer)

    db.session.commit()
    return jsonify({"message": "Exam submitted successfully!"}), 200



openai.api_key = 'sk-proj-RWOAyJjwGynJOGwFabITT3BlbkFJU4o92ggy8BHPKTXt4GN5'
# openai.base_url = "http://localhost:3040/v1"

conversation_history = []  # Initialize conversation history

@views.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data['message']
    question_id = data['question']['id']
    initial_prompt = data['initial_prompt']

    # Append the user's message to the conversation history
    conversation_history.append({'role': 'user', 'content': message})

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{'role': 'system', 'content': initial_prompt}] + conversation_history
    )

    reply = response.choices[0].message['content'].strip()

    # Append the assistant's reply to the conversation history
    conversation_history.append({'role': 'assistant', 'content': reply})

    return jsonify({'reply': reply})


















