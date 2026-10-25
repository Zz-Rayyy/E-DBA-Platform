from flask import Blueprint, request, jsonify
from app.models.course import Course
from app.models.base import db

provide_courseBP = Blueprint('provide_course', __name__)

# 获取指定组织的所有课程
@provide_courseBP.route('/api/courses/<int:organization_id>', methods=['GET'])
def get_courses(organization_id):
    courses = Course.query.filter_by(organizationID=organization_id).all()
    data = [{
        'cid': c.cid,
        'title': c.title,
        'units': c.units,
        'description': c.description
    } for c in courses]
    return jsonify({'status': 'success', 'data': data})

# 添加课程
@provide_courseBP.route('/api/course/<int:organization_id>', methods=['POST'])
def add_course(organization_id):
    title = request.form.get('title')
    units = request.form.get('units')
    description = request.form.get('description')
    if not all([title, units, description]):
        return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
    try:
        course = Course(title=title, units=int(units), description=description, organizationID=organization_id)
        db.session.add(course)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Course added'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Fail to add course: {e}'})

# 编辑课程
@provide_courseBP.route('/api/course/<int:organization_id>/<int:cid>', methods=['POST'])
def edit_course(organization_id, cid):
    course = Course.query.filter_by(cid=cid, organizationID=organization_id).first()
    if not course:
        return jsonify({'status': 'error', 'message': 'Course not found'}), 404
    title = request.form.get('title')
    units = request.form.get('units')
    description = request.form.get('description')
    if not all([title, units, description]):
        return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
    course.title = title
    course.units = int(units)
    course.description = description
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Course updated'})

# 删除课程
@provide_courseBP.route('/api/course/<int:organization_id>/<int:cid>', methods=['DELETE'])
def delete_course(organization_id, cid):
    course = Course.query.filter_by(cid=cid, organizationID=organization_id).first()
    if not course:
        return jsonify({'status': 'error', 'message': 'Course not found'}), 404
    db.session.delete(course)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Course deleted'})