import sqlite3
from jinja2 import Template

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
        .chart-container {
            width: 50%; /* 그래프 크기를 줄임 */
            margin: 0 auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 2rem;
        }
        table, th, td {
            border: 1px solid #ddd;
        }
        th, td {
            padding: 8px;
            text-align: left;
        }
        th {
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
        <div class="chart-container">
            <canvas id="progressChart"></canvas>
        </div>

        <h2>할 일 목록</h2>
        <table>
            <thead>
                <tr>
                    <th>상태</th>
                    <th>업무</th>
                    <th>마감일</th>
                </tr>
            </thead>
            <tbody>
                {% for task in tasks %}
                <tr>
                    <td>{{ "완료" if task[1] == 'completed' else "진행 중" }}</td>
                    <td>{{ task[0] }}</td>
                    <td>{{ task[2] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <script>
        const taskData = {
            labels: ['완료', '진행 중'],
            datasets: [{
                data: [{{ completed }}, {{ pending }}],
                backgroundColor: ['#28a745', '#ffc107'],
            }]
        };

        const config = {
            type: 'doughnut',
            data: taskData,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                },
            },
        };

        const ctx = document.getElementById('progressChart').getContext('2d');
        new Chart(ctx, config);
    </script>
</body>
</html>
"""

def fetch_tasks():
    conn = sqlite3.connect("reminder.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, status, due_date FROM tasks")
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def generate_dashboard():
    tasks = fetch_tasks()
    completed = sum(1 for task in tasks if task[1] == 'completed')
    pending = sum(1 for task in tasks if task[1] == 'pending')

    template = Template(HTML_TEMPLATE)
    rendered_html = template.render(tasks=tasks, completed=completed, pending=pending)

    with open("dashboard.html", "w", encoding="utf-8") as f:
        f.write(rendered_html)

if __name__ == "__main__":
    generate_dashboard()
