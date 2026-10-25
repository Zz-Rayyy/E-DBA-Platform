from flask import Blueprint, request, jsonify, session
from app.models.question import Question
from app.models.base import db
from datetime import datetime

askBP = Blueprint('ask', __name__)

# 提交问题
@askBP.route('/api/question', methods=['POST'])
def submit_question():
    data = request.json
    question = data.get('question')
    
    if not question:
        return jsonify({'status': 'error', 'message': 'Question content is required'})
    
    try:
        # 从session中获取userID
        user_id = session.get('userID')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'User not logged in'})
            
        question = Question(
            userID=user_id,
            response=question,
            answered='no'
        )
        db.session.add(question)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Question submitted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Database error: {e}'})

# 获取当前用户的问题列表
@askBP.route('/api/questions', methods=['GET'])
def get_current_user_questions():
    user_id = session.get('userID')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 401
        
    questions = Question.query.filter_by(userID=user_id).order_by(Question.create_time.desc()).all()
    data = []
    for q in questions:
        data.append({
            'questionID': q.questionID,
            'content': q.response,
            'answered': q.answered,
            'answer': q.response if q.answered == 'yes' else '',
            'submittedAt': datetime.fromtimestamp(q.create_time).strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify({'status': 'success', 'data': data})

# 管理员回答问题
@askBP.route('/api/question/<int:question_id>/answer', methods=['POST'])
def answer_question(question_id):
    data = request.json
    answer = data.get('answer')
    
    if not answer:
        return jsonify({'status': 'error', 'message': 'Answer content is required'})
    
    question = Question.query.get(question_id)
    if not question:
        return jsonify({'status': 'error', 'message': 'Question not found'})
    
    try:
        question.response = answer
        question.answered = 'yes'
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Answer submitted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Database error: {e}'})
