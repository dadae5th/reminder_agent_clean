import sqlite3
from jinja2 import Template
from datetime import datetime

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>업무 대시보드</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f9;
        }
        header {
            background-color: #007bff;
            color: white;
            padding: 1rem;
            text-align: center;
        }
        .container {
            padding: 2rem;
        }
        .charts {
            display: flex;
            justify-content: space-around;
            align-items: center;
        }
        .chart-container {
            width: 35%;
        }
        .chart-title {
            text-align: center;
            font-weight: bold;
            margin-top: 0.5rem;
        }
        .summary-table {
            width: 60%;
            margin: 1rem auto;
            border-collapse: collapse;
        }
        .summary-table th, .summary-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
        }
        .summary-table th {
            background-color: #007bff;
            color: white;
        }
        .task-table {
            width: 100%;
            margin-top: 2rem;
            border-collapse: collapse;
        }
        .task-table th, .task-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        .task-table th {
            background-color: #007bff;
            color: white;
        }
    </style>
</head>
<body>
    <header>
        <h1>업무 대시보드</h1>
    </header>
    <div class="container">
        <h2>업무 진행 상황</h2>
        <div class="charts">
            <div class="chart-container">
                <canvas id="dailyProgressChart"></canvas>
                <div class="chart-title">하루 기준 진행 상황</div>
            </div>
            <div class="chart-container">
                <canvas id="overallProgressChart"></canvas>
                <div class="chart-title">전체 진행 상황</div>
            </div>
        </div>

        <h2>담당자별 진행 상황</h2>
        <table class="summary-table">
            <thead>
                <tr>
                    <th>담당자</th>
                    <th>진행 중</th>
                    <th>완료</th>
                </tr>
            </thead>
            <tbody>
                {% for assignee, counts in assignee_data.items() %}
                <tr>
                    <td>{{ assignee }}</td>
                    <td>{{ counts['pending'] }}</td>
                    <td>{{ counts['completed'] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <h2>업무 목록</h2>
        <table class="task-table">
            <thead>
                <tr>
                    <th>업무</th>
                    <th>상태</th>
                    <th>마감일</th>
                    <th>담당자</th>
                    <th>담당자 이메일</th>
                </tr>
            </thead>
            <tbody>
                {% for task in tasks %}
                <tr>
                    <td>{{ task[0] }}</td>
                    <td>{{ "완료" if task[1] == 'completed' else "진행 중" }}</td>
                    <td>{{ task[2] }}</td>
                    <td>{{ task[3] }}</td>
                    <td>{{ task[4] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <script>
        const dailyTaskData = {
            labels: ['완료', '진행 중'],
            datasets: [{
                data: [{{ daily_completed }}, {{ daily_pending }}],
                backgroundColor: ['#28a745', '#ffc107'],
            }]
        };

        const overallTaskData = {
            labels: ['완료', '진행 중'],
            datasets: [{
                data: [{{ overall_completed }}, {{ overall_pending }}],
                backgroundColor: ['#28a745', '#ffc107'],
            }]
        };

        const dailyConfig = {
            type: 'doughnut',
            data: dailyTaskData,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                },
            },
        };

        const overallConfig = {
            type: 'doughnut',
            data: overallTaskData,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                },
            },
        };

        const dailyCtx = document.getElementById('dailyProgressChart').getContext('2d');
        new Chart(dailyCtx, dailyConfig);

        const overallCtx = document.getElementById('overallProgressChart').getContext('2d');
        new Chart(overallCtx, overallConfig);
    </script>
</body>
</html>
"""

def fetch_tasks():
    conn = sqlite3.connect("reminder.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE assignee_email = 'sample.user@example.com'")  # sample.user@example.com 관련 데이터 삭제
    conn.commit()
    cursor.execute("SELECT title, status, due_date, assignee, assignee_email FROM tasks")
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def update_daily_tasks():
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect("reminder.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET due_date = ? WHERE frequency = 'daily'", (today,))
    conn.commit()
    conn.close()

def generate_dashboard():
    update_daily_tasks()  # 매일 해야 하는 업무의 날짜를 업데이트
    tasks = fetch_tasks()
    today = datetime.now().strftime('%Y-%m-%d')

    overall_completed = sum(1 for task in tasks if task[1] == 'completed')
    overall_pending = sum(1 for task in tasks if task[1] == 'pending')

    daily_completed = sum(1 for task in tasks if task[1] == 'completed' and task[2] == today)
    daily_pending = sum(1 for task in tasks if task[1] == 'pending' and task[2] == today)

    # 업무 목록 데이터를 기반으로 담당자별 진행 현황 생성
    assignee_data = {}
    for task in tasks:
        assignee = task[3] or "알 수 없음"  # assignee 컬럼 사용, 기본값 설정
        if assignee not in assignee_data:
            assignee_data[assignee] = {"completed": 0, "pending": 0}
        if task[1] == 'completed':
            assignee_data[assignee]['completed'] += 1
        else:
            assignee_data[assignee]['pending'] += 1

    template = Template(HTML_TEMPLATE)
    rendered_html = template.render(
        daily_completed=daily_completed,
        daily_pending=daily_pending,
        overall_completed=overall_completed,
        overall_pending=overall_pending,
        assignee_data=assignee_data,
        tasks=tasks
    )

    with open("dashboard.html", "w", encoding="utf-8") as f:
        f.write(rendered_html)

    print(f"하루 기준 진행 중: {daily_pending}건, 완료: {daily_completed}건")
    print(f"전체 진행 중: {overall_pending}건, 완료: {overall_completed}건")

if __name__ == "__main__":
    generate_dashboard()
