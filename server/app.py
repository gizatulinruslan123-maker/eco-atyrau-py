# Flask-сервер: отдаёт сайт (public/) и REST API для карты, модерации и рейтинга.

import os
from flask import Flask, jsonify, request, send_from_directory

from db import (
    get_approved_reports,
    get_pending_reports,
    approve_report,
    reject_report,
    get_leaderboard,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')

app = Flask(__name__, static_folder=PUBLIC_DIR, static_url_path='')

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')


def is_admin(req):
    pw = req.headers.get('X-Admin-Password') or req.args.get('password')
    return pw == ADMIN_PASSWORD


# ---------- Страницы сайта ----------

@app.route('/')
def index():
    return send_from_directory(PUBLIC_DIR, 'index.html')


@app.route('/admin.html')
def admin_page():
    return send_from_directory(PUBLIC_DIR, 'admin.html')


@app.route('/uploads/<path:filename>')
def uploads(filename):
    return send_from_directory(UPLOADS_DIR, filename)


# ---------- Публичные API ----------

@app.route('/api/reports')
def api_reports():
    type_ = request.args.get('type') or None
    return jsonify(get_approved_reports(type_))


@app.route('/api/leaderboard')
def api_leaderboard():
    return jsonify(get_leaderboard())


# ---------- Административные (модерация) API ----------

@app.route('/api/admin/pending')
def api_admin_pending():
    if not is_admin(request):
        return jsonify({'error': 'Неверный пароль администратора'}), 401
    return jsonify(get_pending_reports())


@app.route('/api/admin/reports/<int:report_id>/approve', methods=['POST'])
def api_admin_approve(report_id):
    if not is_admin(request):
        return jsonify({'error': 'Неверный пароль администратора'}), 401
    if not approve_report(report_id):
        return jsonify({'error': 'Заявка не найдена'}), 404
    return jsonify({'ok': True})


@app.route('/api/admin/reports/<int:report_id>/reject', methods=['POST'])
def api_admin_reject(report_id):
    if not is_admin(request):
        return jsonify({'error': 'Неверный пароль администратора'}), 401
    if not reject_report(report_id):
        return jsonify({'error': 'Заявка не найдена'}), 404
    return jsonify({'ok': True})
