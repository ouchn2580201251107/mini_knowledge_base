import sqlite3
import csv
import os
from datetime import datetime

DB_PATH = 'knowledge_base.db'
RESOURCE_DIR = 'resource'


def export_to_csv():
    if not os.path.exists(RESOURCE_DIR):
        os.makedirs(RESOURCE_DIR)
        print(f"创建目录: {RESOURCE_DIR}")

    if not os.path.exists(DB_PATH):
        print(f"错误：数据库文件 {DB_PATH} 不存在！")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM questions')
    total = cursor.fetchone()[0]
    print(f"数据库中共有 {total} 条问答记录")

    cursor.execute('''
        SELECT q.id, q.question, q.answer, 
               GROUP_CONCAT(k.keyword, '|') as keywords
        FROM questions q
        LEFT JOIN question_keywords k ON q.id = k.question_id
        GROUP BY q.id
        ORDER BY q.id
    ''')

    rows = cursor.fetchall()
    conn.close()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_path = os.path.join(RESOURCE_DIR, f'qa_data_{timestamp}.csv')

    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ID', '问题', '答案', '关键词'])

        for row in rows:
            qid, question, answer, keywords = row
            writer.writerow([qid, question, answer, keywords if keywords else ''])

    print(f"成功导出 {len(rows)} 条记录到 {csv_path}")


if __name__ == "__main__":
    export_to_csv()
