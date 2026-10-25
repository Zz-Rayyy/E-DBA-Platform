from flask import Blueprint, request, jsonify
from app.models.question import Question
from app.models.base import db
from datetime import datetime

answerBP = Blueprint('answer', __name__)

@answerBP.route('/api/questions', methods=['GET'])
def get_questions():
    """获取所有未回答的问题"""
    questions = Question.query.filter_by(answered='no').order_by(Question.create_time.desc()).all()
    data = []
    for q in questions:
        data.append({
            "questionID": q.questionID,
            "response": q.response,
            "submittedAt": datetime.fromtimestamp(q.create_time).strftime('%Y-%m-%d %H:%M:%S'),
            "answered": q.answered
        })
    return jsonify({"status": "success", "data": data})

@answerBP.route('/api/question/<int:question_id>/answer', methods=['POST'])
def answer_question(question_id):
    """回答指定问题"""
    question = Question.query.get(question_id)
    if not question:
        return jsonify({"status": "error", "message": "Question not found"})
    
    if question.answered == 'yes':
        return jsonify({"status": "error", "message": "Question already answered"})
    
    answer = request.json.get('answer')
    if not answer:
        return jsonify({"status": "error", "message": "Answer is required"})
    
    try:
        question.response = answer
        question.answered = 'yes'
        db.session.commit()
        return jsonify({"status": "success", "message": "Answer submitted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Database error: {str(e)}"})
