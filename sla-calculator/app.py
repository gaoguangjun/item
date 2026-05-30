"""
SLA Calculator - 服务等级协议计算器
支持正常运行时间计算、停机时间换算、SLA 赔偿计算
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import math

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
CORS(app)

# SLA 等级预设配置
SLA_LEVELS = {
    '90': {'name': '90%', 'description': '基本可用', 'color': '#e74c3c'},
    '95': {'name': '95%', 'description': '良好可用', 'color': '#e67e22'},
    '99': {'name': '99%', 'description': '高可用', 'color': '#f39c12'},
    '99.5': {'name': '99.5%', 'description': '很高可用', 'color': '#3498db'},
    '99.9': {'name': '99.9%', 'description': '极高可用 (两个9)', 'color': '#2ecc71'},
    '99.95': {'name': '99.95%', 'description': '极高可用', 'color': '#16a085'},
    '99.99': {'name': '99.99%', 'description': '近乎完美 (三个9)', 'color': '#27ae60'},
    '99.999': {'name': '99.999%', 'description': '近乎完美 (五个9)', 'color': '#1abc9c'},
    '99.9999': {'name': '99.9999%', 'description': '完美可用 (六个9)', 'color': '#9b59b6'},
}


def calculate_downtime(uptime_percentage):
    """
    根据正常运行时间百分比计算允许的停机时间
    """
    downtime_percentage = 100 - uptime_percentage

    # 时间周期（秒）
    periods = {
        'day': 86400,      # 24 * 60 * 60
        'week': 604800,    # 7 * 24 * 60 * 60
        'month': 2592000,  # 30 * 24 * 60 * 60
        'quarter': 7776000,  # 90 * 24 * 60 * 60
        'year': 31536000,  # 365 * 24 * 60 * 60
    }

    result = {}
    for period_name, seconds in periods.items():
        downtime_seconds = (downtime_percentage / 100) * seconds

        # 转换为易读格式
        days = int(downtime_seconds // 86400)
        hours = int((downtime_seconds % 86400) // 3600)
        minutes = int((downtime_seconds % 3600) // 60)
        seconds = int(downtime_seconds % 60)

        result[period_name] = {
            'total_seconds': downtime_seconds,
            'formatted': format_duration(days, hours, minutes, seconds),
            'compact': format_duration_compact(days, hours, minutes, seconds)
        }

    return result


def format_duration(days, hours, minutes, seconds):
    """格式化持续时间"""
    parts = []
    if days > 0:
        parts.append(f"{days}天")
    if hours > 0:
        parts.append(f"{hours}小时")
    if minutes > 0:
        parts.append(f"{minutes}分钟")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}秒")
    return ' '.join(parts)


def format_duration_compact(days, hours, minutes, seconds):
    """紧凑格式"""
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    return ' '.join(parts)


def calculate_sla_credit(sla_level, actual_uptime, monthly_fee=100):
    """
    计算 SLA 赔偿金额
    sla_level: 承诺的 SLA 等级 (如 99.9)
    actual_uptime: 实际达到的正常运行时间
    monthly_fee: 月服务费用
    """
    sla_level = float(sla_level)

    if actual_uptime >= sla_level:
        return {
            'credit_percentage': 0,
            'credit_amount': 0,
            'status': '达标',
            'message': f'服务正常运行时间达到 {actual_uptime:.2f}%，超过承诺的 {sla_level}%'
        }

    # 常见的 SLA 赔偿阶梯
    shortfall = sla_level - actual_uptime

    if shortfall >= 5:  # 低于 95%
        credit_pct = 100
    elif shortfall >= 3:  # 低于 97%
        credit_pct = 50
    elif shortfall >= 1:  # 低于 99%
        credit_pct = 25
    elif shortfall >= 0.5:  # 低于 99.5%
        credit_pct = 10
    elif shortfall >= 0.1:  # 低于 99.9%
        credit_pct = 5
    else:
        credit_pct = 0

    credit_amount = monthly_fee * (credit_pct / 100)

    return {
        'credit_percentage': credit_pct,
        'credit_amount': credit_amount,
        'status': '未达标',
        'message': f'服务正常运行时间 {actual_uptime:.2f}% 低于承诺的 {sla_level}%，获得 {credit_pct}% 赔偿'
    }


def calculate_actual_uptime(total_minutes, downtime_minutes):
    """计算实际正常运行时间"""
    if total_minutes == 0:
        return 0
    uptime_percentage = ((total_minutes - downtime_minutes) / total_minutes) * 100
    return max(0, min(100, uptime_percentage))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/calculate', methods=['POST'])
def calculate():
    """根据正常运行时间百分比计算停机时间"""
    try:
        data = request.get_json() or {}
        uptime = float(data.get('uptime', 99.9))
        if not (0 <= uptime <= 100):
            return jsonify({'error': '百分比必须在 0-100 之间'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': '无效的数值输入'}), 400

    downtime = calculate_downtime(uptime)
    return jsonify({'uptime': uptime, 'downtime': downtime, 'sla_level': get_closest_sla_level(uptime)})


@app.route('/api/sla-levels')
def sla_levels():
    """获取所有 SLA 等级"""
    return jsonify(SLA_LEVELS)


@app.route('/api/compare', methods=['POST'])
def compare():
    """比较多个 SLA 等级"""
    try:
        data = request.get_json() or {}
        levels = [float(l) for l in data.get('levels', [99.9, 99.99, 99.999])]
    except (ValueError, TypeError):
        return jsonify({'error': '无效的数值输入'}), 400

    results = []
    for level in levels:
        downtime = calculate_downtime(level)
        sla_info = get_closest_sla_level(level)
        results.append({'level': level, 'name': sla_info.get('name', f'{level}%'), 'downtime': downtime})
    return jsonify(results)


@app.route('/api/credit', methods=['POST'])
def credit():
    """计算 SLA 赔偿"""
    try:
        data = request.get_json() or {}
        sla_level = float(data.get('sla_level', 99.9))
        actual_uptime = float(data.get('actual_uptime', 99.5))
        monthly_fee = float(data.get('monthly_fee', 100))
    except (ValueError, TypeError):
        return jsonify({'error': '无效的数值输入'}), 400

    result = calculate_sla_credit(sla_level, actual_uptime, monthly_fee)

    # 计算实际停机时间
    if actual_uptime < 100:
        downtime_info = calculate_downtime(actual_uptime)
        result['actual_downtime'] = downtime_info['month']
    else:
        result['actual_downtime'] = None

    return jsonify(result)


@app.route('/api/actual-uptime', methods=['POST'])
def actual_uptime():
    """根据总时间和停机时间计算实际正常运行时间"""
    try:
        data = request.get_json() or {}
        total_minutes = float(data.get('total_minutes', 43200))
        downtime_minutes = float(data.get('downtime_minutes', 0))
    except (ValueError, TypeError):
        return jsonify({'error': '无效的数值输入'}), 400

    uptime_pct = calculate_actual_uptime(total_minutes, downtime_minutes)

    # 转换停机时间为易读格式
    days = int(downtime_minutes // 1440)
    hours = int((downtime_minutes % 1440) // 60)
    minutes = int(downtime_minutes % 60)

    return jsonify({
        'uptime_percentage': uptime_pct,
        'downtime_formatted': format_duration(days, hours, minutes, 0),
        'total_minutes': total_minutes,
        'downtime_minutes': downtime_minutes,
        'closest_sla': get_closest_sla_level(uptime_pct)
    })


@app.route('/api/reverse-calculate', methods=['POST'])
def reverse_calculate():
    """根据允许的停机时间反向计算需要的正常运行时间百分比"""
    data = request.get_json()
    downtime_seconds = float(data.get('downtime_seconds', 60))
    period = data.get('period', 'month')  # day, week, month, quarter, year

    periods_in_seconds = {
        'day': 86400,
        'week': 604800,
        'month': 2592000,
        'quarter': 7776000,
        'year': 31536000,
    }

    total_seconds = periods_in_seconds.get(period, 2592000)
    uptime_percentage = ((total_seconds - downtime_seconds) / total_seconds) * 100

    return jsonify({
        'required_uptime': uptime_percentage,
        'period': period,
        'allowed_downtime_seconds': downtime_seconds,
        'closest_sla': get_closest_sla_level(uptime_percentage)
    })


def get_closest_sla_level(uptime):
    """获取最接近的 SLA 等级"""
    uptime = float(uptime)
    closest_level = min(
        SLA_LEVELS.keys(),
        key=lambda x: abs(float(x) - uptime)
    )
    return {
        'level': closest_level,
        **SLA_LEVELS[closest_level]
    }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
